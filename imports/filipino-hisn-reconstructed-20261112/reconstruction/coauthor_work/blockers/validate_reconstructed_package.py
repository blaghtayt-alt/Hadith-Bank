#!/usr/bin/env python3
"""Mechanical reconstruction validator; not independent semantic approval.

Run from anywhere:
  python3 scripts/validate_reconstructed_package.py --root /path/to/package
Use --read-only after a manifest is written to avoid rewriting the report.
"""
import argparse
import collections
import copy
import csv
import datetime
import hashlib
import json
from pathlib import Path
import sys
import traceback
import zipfile

V1_NAME = "FIL_HISN_FINAL_PRO_REVIEW_20261112_HOLD_v1"
V1_BYTES = 384986021
V1_SHA = "8043d352e722d8c38ba49bdb54f4f273bb91e3fe4fba111d0d809b36ed17c7ad"
PDF_BYTES = 5321887
PDF_SHA = "3e409dd7266c2a150645ecfea548f266edf80c9c5df5129aa8df7a977d248a07"
PARTITIONS = (
    "hisn_hadith_dhikr_context", "independent_non_prophetic",
    "quran_and_author_only", "attribution_unresolved",
)


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def identical(a, b):
    # Explicit JSON comparison avoids Python treating True as equal to 1.
    return canonical(a) == canonical(b)


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def json_read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def jsonl_read(path):
    return [json.loads(s) for s in Path(path).read_text(encoding="utf-8").splitlines() if s.strip()]


def csv_json_read(path, column):
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            break
        except OverflowError:
            limit //= 10
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if column not in (reader.fieldnames or []):
            raise ValueError(f"{path}: missing lossless {column} column")
        return [json.loads(row[column]) for row in reader]


def tokens(path):
    if path == "":
        return []
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError(f"Not a JSON pointer: {path!r}")
    return [s.replace("~1", "/").replace("~0", "~") for s in path[1:].split("/")]


def pointer_get(obj, path):
    for part in tokens(path):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def pointer_exists(obj, path):
    try:
        pointer_get(obj, path)
        return True
    except (KeyError, IndexError, TypeError, ValueError):
        return False


def pointer_set(obj, path, value, op):
    parts = tokens(path)
    if not parts:
        return copy.deepcopy(value)
    parent = obj
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    leaf = parts[-1]
    if isinstance(parent, list):
        if op == "add":
            index = len(parent) if leaf == "-" else int(leaf)
            if not 0 <= index <= len(parent):
                raise IndexError(path)
            parent.insert(index, copy.deepcopy(value))
        else:
            parent[int(leaf)] = copy.deepcopy(value)
    else:
        if op == "replace" and leaf not in parent:
            raise KeyError(path)
        parent[leaf] = copy.deepcopy(value)
    return obj


class Validation:
    def __init__(self, root):
        self.root = root
        self.checks = []
        self.metrics = {}

    def check(self, label, condition, **details):
        self.checks.append({"check_id": f"MECH-{len(self.checks)+1:06d}",
                            "check": label, "status": "PASS" if condition else "FAIL",
                            **details})
        return condition

    def run(self):
        root = self.root
        archive = root / "preserved_inputs" / (V1_NAME + ".zip")
        self.check("exact_v1_archive_size", archive.stat().st_size == V1_BYTES,
                   expected=V1_BYTES, actual=archive.stat().st_size)
        actual_sha = digest(archive)
        self.check("exact_v1_archive_sha256", actual_sha == V1_SHA,
                   expected=V1_SHA, actual=actual_sha)
        with zipfile.ZipFile(archive) as z:
            bad_crc_member = z.testzip()
            self.metrics["v1_archive_members_crc_checked"] = len(z.infolist())
            self.check("v1_all_members_crc", bad_crc_member is None,
                       member_count=len(z.infolist()), first_bad_member=bad_crc_member)
            def archived_json(name):
                return json.loads(z.read(V1_NAME + "/" + name))
            baseline = archived_json("data/corrected_all_records.json")
            metadata = archived_json("data/book_metadata.json")
            inherited_exceptions = archived_json("audit/unresolved_exceptions.json")
            old_routes = archived_json("coverage/component_partition_map.json")
            old_candidate_bytes = z.read(V1_NAME + "/partitions/prophetic_report_candidates_HOLD.json")
            prior_patch_log = [json.loads(s) for s in z.read(V1_NAME + "/audit/full_before_after_correction_log.jsonl").decode().splitlines()]
            pdf = z.read(V1_NAME + "/inputs/FIL-HISN-PRIVATE.pdf")
            self.check("exact_original_pdf_size", len(pdf) == PDF_BYTES, actual=len(pdf), expected=PDF_BYTES)
            self.check("exact_original_pdf_sha256", hashlib.sha256(pdf).hexdigest() == PDF_SHA,
                       actual=hashlib.sha256(pdf).hexdigest(), expected=PDF_SHA)
        current = json_read(root / "data/corrected_all_records.json")
        records = current["records"]
        old_records = baseline["records"]
        old_map = {r["record_id"]: r for r in old_records}
        new_map = {r["record_id"]: r for r in records}
        ids = [r["record_id"] for r in records]
        self.metrics["records"] = len(records)
        self.check("record_count_323", len(records) == 323, actual=len(records))
        self.check("unique_stable_ordered_record_ids", ids == [r["record_id"] for r in old_records] and len(set(ids)) == len(ids))
        self.check("schema_explicit_reconstruction", "RECONSTRUCTED" in current["schema_version"].upper() and current["schema_version"] != baseline["schema_version"])
        self.check("top_reconstruction_provenance_present", isinstance(current.get("reconstruction_v2"), dict))
        expected_top = set(baseline) | {"reconstruction_v2"}
        self.check("top_key_set_preserved_plus_provenance", set(current) == expected_top,
                   unexpected=sorted(set(current)-expected_top), missing=sorted(expected_top-set(current)))
        for key, value in baseline.items():
            if key not in {"records", "schema_version"}:
                self.check("inherited_top_field_unchanged", key in current and identical(current[key], value), field=key)
        original_components = []
        for old in old_records:
            rid = old["record_id"]
            new = new_map.get(rid, {})
            failed_fields = [k for k, v in old.items() if k not in new or not identical(new[k], v)]
            self.check("all_inherited_record_fields_unchanged", not failed_fields, record_id=rid, changed_or_missing_fields=failed_fields)
            self.check("record_key_set_preserved_plus_overlay", set(new) == set(old) | {"content_classification_reconstructed_v2"}, record_id=rid)
            original_components.extend(old["components"])
        comps = [c for r in records for c in r["components"]]
        comp_ids = [c["segment_id"] for c in comps]
        self.metrics["components"] = len(comps)
        self.check("component_count_1500", len(comps) == 1500, actual=len(comps))
        self.check("unique_stable_ordered_component_ids", comp_ids == [c["segment_id"] for c in original_components] and len(set(comp_ids)) == len(comp_ids))
        old_comp_map = {c["segment_id"]: c for c in original_components}
        for comp in comps:
            sid = comp["segment_id"]
            self.check("complete_source_component_unchanged", sid in old_comp_map and identical(comp, old_comp_map[sid]), segment_id=sid)
        self.check("jsonl_record_lossless_roundtrip", identical(jsonl_read(root / "data/corrected_all_records.jsonl"), records))
        self.check("csv_record_lossless_roundtrip", identical(csv_json_read(root / "data/corrected_all_records.csv", "record_json"), records))
        envelope = json_read(root / "data/records_export_envelope.json")
        self.check("export_envelope_exact", identical(envelope, {k:v for k,v in current.items() if k != "records"}))
        reconstructed = copy.deepcopy(envelope)
        reconstructed["records"] = jsonl_read(root / "data/corrected_all_records.jsonl")
        self.check("envelope_jsonl_complete_document_roundtrip", identical(reconstructed, current))
        self.check("components_jsonl_lossless_roundtrip", identical(jsonl_read(root / "data/components.jsonl"), original_components))
        self.check("components_csv_lossless_roundtrip", identical(csv_json_read(root / "data/components.csv", "component_json"), original_components))
        routed_ids, routed_comps = [], []
        self.metrics["record_partition_counts"] = {}
        for name in PARTITIONS:
            partition = json_read(root / "partitions" / (name + "_HOLD.json"))
            part_records = partition["records"]
            self.metrics["record_partition_counts"][name] = len(part_records)
            for record in part_records:
                rid = record["record_id"]
                routed_ids.append(rid)
                routed_comps.extend(c["segment_id"] for c in record["components"])
                self.check("partition_record_lossless_and_correct_route",
                           rid in new_map and identical(record, new_map[rid]) and
                           record["content_classification_reconstructed_v2"]["record_partition"].removesuffix("_HOLD") == name,
                           record_id=rid, partition=name)
        self.check("record_partitions_disjoint_exhaustive", collections.Counter(routed_ids) == collections.Counter(ids) and len(routed_ids) == len(set(routed_ids)))
        self.check("component_partitions_disjoint_exhaustive", collections.Counter(routed_comps) == collections.Counter(comp_ids) and len(routed_comps) == len(set(routed_comps)))
        candidate_doc = json.loads(old_candidate_bytes)
        candidate_ids = {e["source_component"]["segment_id"] for e in candidate_doc["entries"]}
        self.check("prior_candidate_493_membership", len(candidate_doc["entries"]) == len(candidate_ids) == 493)
        self.check("preserved_candidate_partition_byte_identical", (root / "partitions/prophetic_report_candidates_preserved_HOLD.json").read_bytes() == old_candidate_bytes)
        old_route_map = {r["segment_id"]: r for r in old_routes}
        marked_candidates = set()
        for record in records:
            rid = record["record_id"]
            overlay = record["content_classification_reconstructed_v2"]
            self.check("reconstruction_approval_false", overlay.get("approved_for_bank") is False and overlay.get("approved_for_html") is False, record_id=rid)
            roles = overlay["component_roles"]
            self.check("overlay_component_roles_disjoint_exhaustive", collections.Counter(x["segment_id"] for x in roles) == collections.Counter(c["segment_id"] for c in record["components"]) and len({x["segment_id"] for x in roles}) == len(roles), record_id=rid)
            for role in roles:
                sid = role["segment_id"]
                text_sha = hashlib.sha256(old_comp_map[sid]["text"].encode("utf-8")).hexdigest()
                self.check("component_role_hash_and_prior_route_preserved", role.get("source_text_sha256") == text_sha and role.get("original_partition") == old_route_map[sid]["partition"] and role.get("preserved_prior_candidate") is (sid in candidate_ids), record_id=rid, segment_id=sid)
                if role.get("preserved_prior_candidate") is True:
                    marked_candidates.add(sid)
        self.check("493_candidates_all_preserved_in_overlay", marked_candidates == candidate_ids, count=len(marked_candidates))
        self._check_patches(baseline, current)
        current_meta = json_read(root / "data/book_metadata.json")
        changed_metadata = [k for k, v in metadata.items() if k not in current_meta or not identical(v, current_meta[k])]
        self.check("metadata_all_inherited_values_unchanged", not changed_metadata, changed_or_missing_fields=changed_metadata)
        self.check("metadata_key_set_only_provenance_added", set(current_meta) == set(metadata) | {"reconstruction_v2"})
        self.check("no_invented_edition_date_or_year", current_meta.get("exact_edition_publication_date") is None and current_meta.get("exact_edition_publication_year") is None)
        exceptions = json_read(root / "audit/unresolved_exceptions.json")
        emap = {e["exception_id"]:e for e in exceptions}
        self.check("inherited_exception_ids_preserved_unique", len(emap) == len(exceptions) and {e["exception_id"] for e in inherited_exceptions} <= set(emap))
        for old in inherited_exceptions:
            new = emap.get(old["exception_id"], {})
            bad = [k for k,v in old.items() if k not in new or not identical(new[k],v)]
            self.check("inherited_exception_fields_unchanged", not bad and isinstance(new.get("reconstruction_scope"),dict), exception_id=old["exception_id"], changed_or_missing_fields=bad)
        blocker_doc = json_read(root / "audit/record_blocker_index.json")
        blocker_records = blocker_doc["records"]
        self.check("blocker_index_all_records_exactly_once", collections.Counter(r["record_id"] for r in blocker_records) == collections.Counter(ids))
        preserved_ledger = json_read(root / "audit/v1_dependency_preservation_ledger.json")
        metadata_changes = [p for p in prior_patch_log if p["category"] == "SOURCE_METADATA_CORRECTION"]
        additions = [p for p in metadata_changes if p["path"].endswith("/printed_number_observations")]
        page_changes = [p for p in metadata_changes if p not in additions]
        source_hash_changes = [p for p in prior_patch_log if p["category"] == "DEPENDENT_SOURCE_HASH"]
        self.check("inherited_17_22_39_counts", (len(additions),len(page_changes),len(source_hash_changes)) == (17,22,39))
        for change in metadata_changes + source_hash_changes:
            self.check("inherited_v1_correction_after_value_preserved", identical(pointer_get(current,change["path"]),change["after"]), inherited_change_id=change["change_id"], path=change["path"])
        ledger_rows = preserved_ledger["source_metadata_preserve_values"]
        self.check("preservation_ledger_matches_all_39_metadata_changes", len(ledger_rows) == 39 and {x["path"] for x in ledger_rows} == {x["path"] for x in metadata_changes} and all(identical(pointer_get(current,x["path"]),x["preserve_value"]) for x in ledger_rows))
        self.check("p106_heading_preserved", identical(current["source_heading_supplement_final_pro"],baseline["source_heading_supplement_final_pro"]) and identical(preserved_ledger["p106_heading_preserve_value"],baseline["source_heading_supplement_final_pro"]))
        n260 = new_map["N260"]
        n260_comp = next(c for c in n260["components"] if c["segment_id"] == "p264-r003")
        n260_claim = next(c for c in n260["narrator_attributions_as_printed"] if c["claim_id"] == "NARR-022")
        self.check("n260_three_synchronized_fields_and_anchor", n260["arabic"] == n260_comp["text"] == n260_claim["evidence_quote_as_printed"] and "أَلَا أَدُلُّكَ" in n260["arabic"])
        self.check("n260_ledger_exact_string_and_sha", n260["arabic"] == preserved_ledger["n260_preservation"]["exact_string"] and hashlib.sha256(n260["arabic"].encode()).hexdigest() == preserved_ledger["n260_preservation"]["exact_string_sha256"])
        self._check_manifest()

    def _check_patches(self, baseline, current):
        patch = json_read(self.root / "audit/replayable_patch.json")
        if isinstance(patch, dict):
            patch = patch["operations"]
        work = copy.deepcopy(baseline)
        mutations = []
        for index, operation in enumerate(patch):
            op, path = operation["op"], operation["path"]
            if op == "test":
                self.check("rfc6902_test", pointer_exists(work,path) and identical(pointer_get(work,path),operation["value"]), operation_index=index, path=path)
            elif op in {"add","replace"}:
                existed = pointer_exists(work,path)
                before = copy.deepcopy(pointer_get(work,path)) if existed else None
                work = pointer_set(work,path,operation["value"],op)
                mutations.append({"op":op,"path":path,"before_exists":existed,"before":before,"after":operation["value"]})
            else:
                self.check("rfc6902_operation_supported", False, operation_index=index, op=op)
                raise ValueError(f"Unsupported patch operation {op}")
        self.metrics["rfc6902_operations"] = len(patch)
        self.metrics["patch_mutations"] = len(mutations)
        self.check("rfc6902_patch_exact_replay", identical(work,current))
        log = jsonl_read(self.root / "audit/full_before_after_correction_log.jsonl")
        self.check("change_log_mutation_count",len(log)==len(mutations), actual=len(log), expected=len(mutations))
        for index,(entry,mutation) in enumerate(zip(log,mutations)):
            valid = all(k in entry and identical(entry[k],v) for k,v in mutation.items()) and entry.get("after_exists") is True
            self.check("change_log_exact_before_after_matches_patch",valid, mutation_index=index,path=mutation["path"])
        replay = copy.deepcopy(baseline)
        for index,entry in enumerate(log):
            exists = pointer_exists(replay,entry["path"])
            precondition = exists is entry["before_exists"] and (not exists or identical(pointer_get(replay,entry["path"]),entry["before"]))
            self.check("custom_log_replay_precondition", precondition, mutation_index=index,path=entry["path"])
            replay = pointer_set(replay,entry["path"],entry["after"],entry["op"])
        self.check("custom_log_exact_replay", identical(replay,current))

    def _check_manifest(self):
        manifests = [p for p in [self.root / "SHA256_MANIFEST.json",self.root / "audit/output_sha256_manifest.json"] if p.is_file()]
        self.metrics["output_manifest_files_checked"] = 0
        self.metrics["output_manifest_status"] = "NOT_PRESENT_YET" if not manifests else "CHECKED"
        for manifest in manifests:
            doc = json_read(manifest)
            entries = doc["files"] if isinstance(doc,dict) else doc
            if isinstance(entries,dict):
                entries = [dict(value,path=key) if isinstance(value,dict) else {"path":key,"sha256":value} for key,value in entries.items()]
            seen = set()
            for entry in entries:
                relative = entry["path"]
                path = (self.root / relative).resolve()
                inside = path.is_relative_to(self.root.resolve())
                unique = relative not in seen
                seen.add(relative)
                exists = inside and path.is_file()
                expected_size = entry.get("bytes",entry.get("size_bytes",entry.get("file_size_bytes")))
                actual_size = path.stat().st_size if exists else None
                sha = digest(path) if exists else None
                self.check("output_manifest_entry", exists and unique and sha == entry["sha256"] and (expected_size is None or actual_size == expected_size),
                           path=relative,actual_bytes=actual_size,expected_bytes=expected_size,actual_sha256=sha,expected_sha256=entry["sha256"])
                self.metrics["output_manifest_files_checked"] += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report",type=Path)
    parser.add_argument("--read-only",action="store_true",help="Run all checks without rewriting a report.")
    args = parser.parse_args()
    root = args.root.resolve()
    validation = Validation(root)
    try:
        validation.run()
    except Exception as exc:
        validation.check("validator_completed_without_exception",False,error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
    passed = sum(x["status"] == "PASS" for x in validation.checks)
    failed = sum(x["status"] == "FAIL" for x in validation.checks)
    report = {"validator":"validate_reconstructed_package.py","role":"coauthor mechanical implementation and execution; not separate independent final review",
              "generated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "mechanical_status":"PASS" if failed==0 else "FAIL", "actual_check_count":len(validation.checks),"passed":passed,"failed":failed,
              "semantic_classification_approval":False,"source_fidelity_verdict":"PARTIAL","metadata_verdict":"PARTIAL","bank_readiness":"FAIL/HOLD",
              "separate_independent_final_evaluation":"NOT_RUN","metrics":validation.metrics,"checks":validation.checks}
    if not args.read_only:
        report_path = args.report or root / "validation/mechanical_validation.json"
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "checks"},ensure_ascii=False,indent=2))
    if failed:
        print(json.dumps([x for x in validation.checks if x["status"]=="FAIL"],ensure_ascii=False,indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

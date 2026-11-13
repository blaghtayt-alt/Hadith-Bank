"""Correct one historical field-count description from exact published evidence."""
from pathlib import Path
import collections
import gzip
import hashlib
import json

H=Path(__file__).resolve().parent
W=H.parent
OUT=H/'publish'
PREFIX=Path('reports/web-source-resolution-20261113/fawaz-field-count-clarification')
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
assert not (H/'delivery-manifest.json').exists()
bindings=json.loads((H/'input/fresh-github-bindings.json').read_bytes())
for name,f in bindings.items():
    b=(H/'input'/name).read_bytes()
    assert len(b)==f['bytes'] and sha(b)==f['sha256'] and git(b)==f['git_blob_sha1']
    assert f['commit']=='31c01136611b163683a01b47833bf74354820851'
summary=json.loads((H/'input/summary.json').read_bytes())
ledger=json.loads(gzip.decompress((H/'input/dispositions.json.gz').read_bytes()))
fields=[f for d in ledger['records'] for f in d['source_fields']]
assert len(ledger['records'])==244 and len(fields)==895
assert collections.Counter(f['source_text_is_empty'] for f in fields)=={True:691,False:204}
assert collections.Counter(f['inspection'] for f in fields)=={
    'exact_empty_source_field_verified':691,'complete_nonempty_source_field_read':204}
assert (summary['counts']['source_fields'],summary['counts']['nonempty_source_fields'],summary['counts']['empty_source_fields'])==(895,204,691)
assert (summary['recovered_occurrences'],summary['resolved_excluded_occurrences'])==(6,238)
old_doc=(W/'phase22-final-publication/publish/docs/WEB-SOURCE-RESOLUTION-20261113.md').read_bytes()
assert len(old_doc)==128690 and sha(old_doc)=='533bf1a71e9a9f11587810dab613ad4d2e45ea20eb9e7da4c0cc69fa45db4798'
wrong='with 895 own nonempty fields reviewed'
assert old_doc.decode().count(wrong)==1
old_stage=(W/'phase23-final-publication/manifest.json').read_bytes()
old_prefix=(W/'phase23-final-publication/current-status-prefix.md').read_bytes()
assert sha(old_stage)=='0187f2c5de1d1232479755818ae8039eb4f2e3fbc7b73178f1e00b88c688c860'
assert sha(old_prefix)=='3b0fcbaf243d7e1cedcdde31951d5f2aa10f90406e5f2a0938a3350329579adb'
report={'schema':'hadith-bank-historical-field-count-clarification-v1','status':'PASS',
    'published_evidence_commit':'31c01136611b163683a01b47833bf74354820851',
    'affected_document':'docs/WEB-SOURCE-RESOLUTION-20261113.md',
    'affected_document_sha256':sha(old_doc),'exact_incorrect_historical_phrase':wrong,
    'corrected_description':'with all895 supplied field slots accounted for:204 nonempty fields read and691 empty fields bound',
    'source_occurrences':244,'supplied_field_slots':895,'nonempty_fields_actually_read':204,
    'empty_fields_bound':691,'actual_nonempty_codepoints':summary['counts']['nonempty_codepoints'],
    'source_evidence':bindings,'both_complete_bodies_freshly_read_from_pinned_github':True,
    'complete_disposition_ledger_recount_matches_original_summary':True,
    'parent_outcomes_unchanged':{'registered':6,'resolved_source_only':238},
    'historical_document_preserved_as_exact_suffix':True,
    'correction_to_be_explicit_in_current_top_prefix':True,
    'superseded_unpublished_staging_manifest_sha256':sha(old_stage),
    'superseded_unpublished_prefix_sha256':sha(old_prefix),
    'superseded_staging_was_not_published_to_main':True,
    'source_text_changes':0,'review_decision_changes':0,'new_linguistic_readings':0,
    'source_site_requests':0,'workflow_dispatches':0,'independent_pro_qc':'not_performed',
    'limits':'This verifies the published field-count and inspection ledger and corrects its later prose description. It is not a new semantic review, full-edition revalidation, generated export or deployment.'}
files={
    'clarification-receipt.json':enc(report),
    'published-evidence/summary.json':(H/'input/summary.json').read_bytes(),
    'published-evidence/dispositions.json.gz':(H/'input/dispositions.json.gz').read_bytes(),
    'published-evidence/fresh-github-bindings.json':(H/'input/fresh-github-bindings.json').read_bytes(),
    'before-clarification/unpublished-staging-manifest.json':old_stage,
    'before-clarification/unpublished-status-prefix.md':old_prefix,
    'freeze_clarification.py':Path(__file__).read_bytes()}
entries=[]
for name,b in files.items():
    p=OUT/PREFIX/name;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(b)
    entries.append({'path':(PREFIX/name).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
manifest={'schema':'hadith-bank-field-count-clarification-delivery-v1','status':'PASS',
    'files':entries,'total_files':len(entries),'total_bytes':sum(f['bytes'] for f in entries)}
mb=enc(manifest);(H/'delivery-manifest.json').write_bytes(mb)
print(json.dumps({'status':'FROZEN','manifest_sha256':sha(mb),'report_sha256':sha(enc(report)),
    'files':len(entries),'bytes':manifest['total_bytes']},indent=2))

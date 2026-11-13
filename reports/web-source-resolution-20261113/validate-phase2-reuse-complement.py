#!/usr/bin/env python3
"""Validate exact-review reuse for the complement of all explicit phase 2 IDs.

This consumes the saved eb6061e held-source assignments and the current pinned
Fawaz review catalog. It never calls reuse.commit()/save(), never publishes a
generated reuse ledger, and never makes source requests. Normal export must
generate its own reuse evidence and validate the complete registry.
"""
from __future__ import annotations
import argparse
import collections
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile

REPORTS = 'reports/web-source-resolution-20261113'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def enc(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

def stream(path):
    raw = path.read_bytes()
    text = (gzip.decompress(raw) if path.suffix=='.gz' else raw).decode()
    decoder = json.JSONDecoder()
    rows, offset = [], 0
    while offset < len(text):
        while offset < len(text) and text[offset].isspace():
            offset += 1
        if offset < len(text):
            row,offset = decoder.raw_decode(text,offset)
            rows.append(row)
    return rows

def oid(row):
    return 'deenhindi-' + row['collection'] + ':' + row['number']

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--held-source-directory',type=Path,required=True)
    parser.add_argument('--new-held-source',type=Path,required=True)
    parser.add_argument('--reuse-root',type=Path,required=True)
    args = parser.parse_args()
    root = args.repository_root.resolve()
    reuse_root = args.reuse_root.resolve()
    sys.path.insert(0,str(reuse_root/'scripts'))
    import import_deenhindi as importer
    import deenhindi_review_reuse as reuse_module
    from web_source_reviews import SourceReviews, canonical_hash
    manifest=json.loads((root/REPORTS/'phase2-inputs.json').read_bytes())
    manual_validation=json.loads((root/REPORTS/'phase2-validation.json').read_bytes())
    assert manual_validation['result']=='passed' and manual_validation['source_occurrence_id_count']==2289
    checkpoint_path=root/REPORTS/'phase2-eb6061e-progress-baseline.json'
    checkpoint=json.loads(checkpoint_path.read_bytes())
    assert checkpoint['source_commit']=='eb6061e1d4115d141d3f2d723ec83fc57f34b1b2'
    progress=checkpoint['progress']
    assert progress['imported_count']==12775 and progress['classification_pending_count']==3942
    assert progress['registered_hadith_count']==8833 and progress['non_narration_source_entries']==0
    all_saved, origins, source_inputs={}, {}, []
    source_paths=[*sorted(args.held_source_directory.glob('*.jsonl')), args.new_held_source]
    assert len(source_paths)==8
    for path in source_paths:
        rows=stream(path)
        origin='new_118' if path==args.new_held_source else 'original_3824'
        source_inputs.append({'path':str(path.resolve()),'sha256':sha(path.read_bytes()),
                              'size_bytes':path.stat().st_size,'records':len(rows),'origin':origin})
        for saved in rows:
            identity=oid(saved)
            assert identity not in all_saved,('duplicate held-source ID',identity)
            assert saved['classification']['classification']=='unknown'
            all_saved[identity],origins[identity]=saved,origin
    assert len(all_saved)==3942
    assert collections.Counter(origins.values())=={'original_3824':3824,'new_118':118}
    manual_ids=set()
    for cohort in manifest['cohorts']:
        for saved in stream(root/cohort['source_ledger_path']):
            identity=oid(saved)
            assert identity not in manual_ids and all_saved[identity]==saved
            manual_ids.add(identity)
    assert len(manual_ids)==2289
    complement=sorted(set(all_saved)-manual_ids)
    assert len(complement)==1653
    assert collections.Counter(origins[x] for x in complement)=={'original_3824':1616,'new_118':37}
    for book,stats in progress['by_collection'].items():
        assert sum(r['collection']==book for r in all_saved.values())==stats['classification_pending']
        assert stats['fetched']==stats['registered_hadith']+stats['classification_pending']+stats['non_narration_source_entries']
    reuse=reuse_module.ExactReviewReuse(reuse_root)
    assert reuse.enabled
    prior_inputs_before=copy.deepcopy(reuse.inputs)
    decisions,missing={},[]
    for identity in complement:
        decision=reuse.review(all_saved[identity])
        if decision is None:
            missing.append(identity)
        else:
            assert decision['id']==identity and decision['decision']=='register'
            decisions[identity]=decision
    assert not missing,('uncovered held IDs',missing)
    assert set(decisions)==set(complement) and not (manual_ids & set(decisions))
    receipt=reuse.prepare()  # Prepares bytes in memory only; no commit/save is performed.
    totals=collections.Counter()
    by_book=collections.defaultdict(collections.Counter)
    by_language=collections.defaultdict(collections.Counter)
    bindings=[]
    with tempfile.TemporaryDirectory(prefix='hadith-phase2-reuse-') as temporary:
        adapter=SourceReviews(Path(temporary),'deenhindi')
        adapter.decisions={key:(decision,receipt,'register') for key,decision in decisions.items()}
        for identity in complement:
            saved=all_saved[identity]
            saved_copy=copy.deepcopy(saved)
            decision=decisions[identity]
            before=importer.canonical_record(saved)
            frozen=copy.deepcopy(before)
            after,action=adapter.apply(before,saved=saved)
            assert action=='register' and before==frozen and saved==saved_copy
            for key in set(before)-{'language_versions','text','content_kind','review','report_types','extraction'}:
                assert after[key]==before[key],('metadata changed by reuse',identity,key)
            assert after['number']['canonical'] is None
            assert after['review']['independent_pro_qc']=='not_performed'
            assert after['review']['certified_release_eligible'] is False
            fields={f['language_version_id']:f for f in decision['field_reviews']}
            assert len(before['language_versions'])==len(after['language_versions'])
            selected=[]
            for old,new in zip(before['language_versions'],after['language_versions']):
                text,language=old['text'],old['language']
                field=fields.get(old['id'])
                spans=field['spans'] if field else []
                for key in set(old)-{'text','scope','quotation_status','source','comments'}:
                    assert new[key]==old[key]
                for key in old['source']:
                    assert new['source'][key]==old['source'][key]
                pieces=[]
                if spans:
                    assert field['review_method']==reuse_module.METHOD
                    assert field['text_sha256']==sha(text.encode())
                    assert field['chars_reviewed']==len(text) and field['bytes_reviewed']==len(text.encode())
                    assert new['text']==''.join(text[s['start']:s['end']] for s in spans)
                    for prior in field['prior_review_evidence']:
                        assert prior['full_source_text_sha256']==sha(text.encode())
                        assert prior['repository']==reuse_module.REPOSITORY and prior['revision']==reuse_module.REVISION
                    for s in spans:
                        a,b=s['start'],s['end']
                        assert s['sha256']==sha(text[a:b].encode())
                        pieces.append((a,b,text[a:b]))
                    selected.append({'language':language,'full_field_sha256':sha(text.encode()),
                                     'selected_text_sha256':sha(new['text'].encode()),
                                     'selected_spans':[[s['start'],s['end']] for s in spans]})
                    for dest in (totals,by_book[saved['collection']],by_language[language]):
                        dest['reused_language_fields']+=1
                        dest['exact_matched_full_field_characters']+=len(text)
                        dest['quotation_characters']+=len(new['text'])
                else:
                    assert new['text'] is None
                    totals['unmatched_language_fields_retained_as_context']+=1
                for note in new['comments']:
                    assert note['scope']=='source_context_not_narration'
                    a,b=note['source_span']
                    assert note['text']==text[a:b] and note['source_text_sha256']==sha(text[a:b].encode())
                    pieces.append((a,b,note['text']))
                cursor=0
                for a,b,body in sorted(pieces):
                    assert a==cursor and b>a and body==text[a:b]
                    cursor=b
                assert cursor==len(text) and ''.join(p[2] for p in sorted(pieces))==text
                totals['exact_field_partition_checks']+=1
            admitted={v['language']:v['text'] for v in after['language_versions'] if v['text'] is not None}
            assert after['text']=={'arabic':admitted.get('ar'),'translation':admitted.get('hi')}
            original={k:saved[k] for k in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')}
            original['classification']=saved['intake_classification']
            parsed_sha=sha(importer.json_bytes(original))
            assert Path(saved['parsed_path']).name==parsed_sha+'.json.gz'
            totals['reused_source_occurrences']+=1
            by_book[saved['collection']]['reused_source_occurrences']+=1
            bindings.append({'id':identity,'source_origin':origins[identity],
                'source_record_sha256':decision['source_record_sha256'],
                'source_snapshot_path':saved['snapshot']['path'],'source_snapshot_sha256':saved['snapshot']['sha256'],
                'source_parsed_path':saved['parsed_path'],'reconstructed_parsed_sha256':parsed_sha,
                'generated_decision_sha256':sha(importer.json_bytes(decision)),
                'derived_output_canonical_sha256':canonical_hash(after),'reused_fields':selected})
        adapter.finish()
    assert reuse_module.input_receipts(reuse_root)==prior_inputs_before, 'reuse inputs changed during verification'
    assert not reuse.conflicts,('reuse conflicts',reuse.conflicts)
    whole={}
    for book,prior in sorted(progress['by_collection'].items()):
        manual=manual_validation['per_book'][book]
        reused=by_book[book]['reused_source_occurrences']
        assert prior['classification_pending']==manual['source_occurrences']+reused
        resolved={'fetched':prior['fetched'],'baseline_registered':prior['registered_hadith'],
            'baseline_held':prior['classification_pending'],'manual_registered':manual.get('register',0),
            'manual_source_only':manual.get('exclude',0),'exact_review_reuse_registered':reused,
            'registered_after_review':prior['registered_hadith']+manual.get('register',0)+reused,
            'source_only_after_review':prior['non_narration_source_entries']+manual.get('exclude',0),
            'held_after_review':manual.get('hold',0)}
        assert resolved['fetched']==sum(resolved[k] for k in
            ('registered_after_review','source_only_after_review','held_after_review'))
        whole[book]=resolved
    whole_totals={k:sum(v[k] for v in whole.values()) for k in next(iter(whole.values()))}
    assert whole_totals['registered_after_review']==12654
    assert whole_totals['source_only_after_review']==121 and whole_totals['held_after_review']==0
    assert whole_totals['fetched']==12775
    report={'schema':'hadith-bank-phase2-held-complement-validation-v1','result':'passed',
        'source_commit':checkpoint['source_commit'],
        'checkpoint_receipt':{'path':checkpoint_path.relative_to(root).as_posix(),'sha256':sha(checkpoint_path.read_bytes()),
            'remote_path':checkpoint['path'],'retrieval_method':checkpoint['retrieval_method']},
        'source_inputs':source_inputs, 'held_source_occurrences':len(all_saved),
        'explicit_manual_occurrences':len(manual_ids),'reuse_complement_occurrences':len(complement),
        'reuse_complement_by_origin':dict(collections.Counter(origins[x] for x in complement)),
        'uncovered_occurrence_ids':missing,'duplicate_ids':0,
        'totals':dict(totals),'per_book':{k:dict(v) for k,v in sorted(by_book.items())},
        'reused_fields_by_language':{k:dict(v) for k,v in sorted(by_language.items())},
        'current_prior_review_input_receipts':prior_inputs_before,
        'prepared_in_memory_receipt_not_published':receipt,
        'new_reuse_ledger_written':False,
        'supporting_file_export_verification':'Full-checkout importer/export gate remains required; no material-registry claim is made by this source-object replay.',
        'context_dependent_fields_not_reused':len(reuse.context_dependent),'conflicts':reuse.conflicts,
        'whole_saved_cohort_per_book':whole,'whole_saved_cohort_totals':whole_totals,
        'whole_saved_cohort_basis':'Original registered counts are taken from the hash-bound GitHub progress snapshot; every formerly held source object is covered by a checked manual or exact-reuse decision. This is a source-object preflight projection, not a completed export.',
        'all_original_source_and_field_metadata_preserved':True,
        'raw_response_bytes_reopened':0,'parsed_gzip_bytes_reopened':0,
        'new_manual_reading_claimed_for_reuse':False,'independent_pro_qc':'not_performed',
        'source_http_requests':0}
    folder=root/REPORTS
    (folder/'phase2-reuse-complement-validation.json').write_bytes(enc(report))
    (folder/'phase2-reuse-output-bindings.jsonl.gz').write_bytes(gzip.compress(
        b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() for r in bindings),mtime=0))
    print(json.dumps({'result':'passed','totals':dict(totals),'whole_saved_cohort_totals':whole_totals,
                      'per_book':whole,'reuse_ledger_written':False},indent=2))

if __name__=='__main__':
    main()

"""Independently validate the exact candidate after the frozen full source-first pass."""
from pathlib import Path
import collections, copy, gzip, hashlib, json, sys

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
OWNER=WORK/'phase22-checkpoint17cd-nasai22-review'
CENTRAL=WORK/'phase21-successor-acquisition-monitor/held-evidence'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpoint17cd-nasai22-20261113.json.gz'
PIN='17cd396eb858a29162505d545aad556ac73ce9ce'
MANIFEST_SHA='50c8ee57e971cba885cb163fc85491d3d427730ee6694687b9fcec3de1416ecd'
ACTIVE_SHA='b2bc29aec394390a33b679322842e9ce3fb807081807775fac27a2c3d5b14ce7'
READ_SHA='2fbf9deda88c1b6290c9286862730192d44153821d58f68d80a59cae93b8f778'
ASSESS_SHA='a1acf7dbe9f403ade626c831eb8139f8ce4334c6e13c567d8f15c7c5bcb192dd'
FIELDS={'ar':'textArabic','hi':'translationHindi','ur':'translationUrdu','ur-Latn':'translationUrduRoman','en':'translationEnglish'}
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews

def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):
    b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def bind(p):
    b=p.read_bytes();return {'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,('immutable output mismatch',str(p))
    else:p.write_bytes(b)
def leaves(x):
    if isinstance(x,dict):return sum(leaves(v) for v in x.values())
    if isinstance(x,list):return sum(leaves(v) for v in x)
    return 1
def equal(a,b):assert a==b;return leaves(a)

def main():
    original_input=(ROOT/'input/cohort.jsonl').read_bytes()
    reading=read(ROOT/'complete-independent-source-first-readings.json')
    assert bind(ROOT/'complete-independent-source-first-readings.json')['sha256']==READ_SHA
    assert not reading['primary_candidate_or_semantic_notes_opened']
    read_fields={(r['occurrence_id'],r['language']):r for r in reading['fields']}
    assert len(read_fields)==47
    assert bind(ROOT/'independent-boundary-assessment-v1.json')['sha256']==ASSESS_SHA
    assessment=read(ROOT/'independent-boundary-assessment-v1.json')
    accepted={(r['id'],r['language']):r for r in assessment['all_candidate_field_checks']}
    assert set(accepted)==set(read_fields) and not assessment['required_amendments']
    assert all(r['accepted'] and r['complete_candidate_mask_and_voice_inspected'] for r in accepted.values())
    source_rows=list(map(json.loads,original_input.splitlines()))
    source_by={'deenhindi-'+r['collection']+':'+r['number']:r for r in source_rows}
    assert len(source_by)==len(source_rows)==22
    shared={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,(CENTRAL/'held-source-records.jsonl').read_bytes().splitlines())}
    assert all(shared[k]==v for k,v in source_by.items())
    manifest_path=OWNER/'delivery-manifest-v1.json'
    assert bind(manifest_path)['sha256']==MANIFEST_SHA
    manifest=read(manifest_path);repo=ROOT/'validation/final';payload=[]
    for item in manifest['files']:
        relative=Path(item['path']);assert not relative.is_absolute() and '..' not in relative.parts
        path=Path(item['local_path']);assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(OWNER)
        observed=bind(path)
        assert all(observed[k]==item[k] for k in ['bytes','sha256','git_blob_sha1'])
        put(repo/relative,path.read_bytes());payload.append({'path':str(relative),'owner_path':str(path),**observed})
    assert len(payload)==len({r['path'] for r in payload})==25
    assert bind(repo/ACTIVE)['sha256']==ACTIVE_SHA
    ledger=read(repo/ACTIVE);baseline=repo/ledger['source_ledger_path']
    assert bind(baseline)['sha256']==ledger['source_ledger_sha256']
    assert list(map(json.loads,gzip.decompress(baseline.read_bytes()).splitlines()))==source_rows
    decisions={r['id']:r for r in ledger['records']}
    assert len(decisions)==len(ledger['records'])==22 and set(decisions)==set(source_by)
    authority=read(CENTRAL/'evidence-manifest.json');state=read(CENTRAL/'held-state-entries.json')
    assert authority['saved_head']==PIN
    engine=SourceReviews(repo,'deenhindi');counts=collections.Counter();metadata=collections.Counter()
    source_proofs=[];field_proofs=[];component_proofs=[]
    for ident,saved in source_by.items():
        entry=state[saved['collection']+':'+saved['number']]
        assert entry['parsed']['path']==saved['parsed_path']
        for desc in [saved['snapshot'],entry['parsed']]:
            src=ROOT/'sources'/desc['path'];b=bind(src);given=authority['files'][desc['path']]
            assert all(b[k]==given[k] for k in ['bytes','sha256','git_blob_sha1'])
            plain=importer.checked_bytes(ROOT/'sources',desc)
            source_proofs.append({'id':ident,'path':desc['path'],**b,'plain_bytes':len(plain),'plain_sha256':sha(plain)})
        parsed=json.loads(importer.checked_bytes(ROOT/'sources',entry['parsed']))
        for k in ['collection','number','source_record','source_reference_verbatim','snapshot']:assert parsed[k]==saved[k]
        assert parsed['classification']==saved.get('intake_classification',saved['classification'])
        obj,ref=importer.parse_record(importer.checked_bytes(ROOT/'sources',saved['snapshot']),saved['collection'],saved['number'])
        assert obj==saved['source_record'] and ref==saved['source_reference_verbatim']
        decision=decisions[ident]
        assert decision['source_record_sha256']==sha(importer.json_bytes(obj))
        assert decision['collection']==saved['collection'] and decision['number']==saved['number']
        assert decision['source_snapshot']==saved['snapshot'] and decision['source_reference_verbatim']==ref
        assert decision['verified_external_reference'] is None
        original=importer.canonical_record(saved);untouched=copy.deepcopy(original)
        revised,action=engine.apply(copy.deepcopy(original),saved=saved)
        assert original==untouched and action==decision['decision']
        assert action in ['register','exclude'];counts[action]+=1
        assert revised['review']['independent_pro_qc']=='not_performed' and revised['review']['certified_release_eligible'] is False
        for k,v in original.items():
            if k not in ['text','language_versions','review','content_kind','extraction']:metadata['parent']+=equal(v,revised[k])
        fields={f['language']:f for f in decision['field_reviews']}
        assert len(fields)==len(decision['field_reviews'])==5
        original_versions={v['language']:v for v in original['language_versions']}
        revised_versions={v['language']:v for v in revised['language_versions']}
        assert set(fields)==set(original_versions)==set(revised_versions)==set(FIELDS)
        for lang,name in FIELDS.items():
            key=(ident,lang);text=obj[name];counts['source_slots']+=1
            assert isinstance(text,str) and text
            before=original_versions[lang];after=revised_versions[lang];field=fields[lang]
            assert before['text']==text and field['source_field']==name
            assert field['language_version_id']==ident+':'+lang
            assert field['text_sha256']==sha(text.encode()) and field['text_chars']==len(text)
            reviewed=key in read_fields
            assert field['reviewed'] is reviewed
            assert field['chars_reviewed']==(len(text) if reviewed else 0)
            assert field['bytes_reviewed']==(len(text.encode()) if reviewed else 0)
            selected=[False]*len(text);cursor=0
            for span in field['spans']:
                a,b=span['start'],span['end'];assert cursor<=a<b<=len(text)
                assert span['sha256']==sha(text[a:b].encode())
                assert span['component_id'] and span['report_type'] and span['speaker'] and span['source_report_family_id']
                selected[a:b]=[True]*(b-a);cursor=b
            counts['selected_spans']+=len(field['spans'])
            counts['selected_characters']+=sum(selected)
            counts['selected_utf8_bytes']+=sum(len(text[s['start']:s['end']].encode()) for s in field['spans'])
            if reviewed:
                own=read_fields[key]
                assert own['text']==text and own['text_sha256']==sha(text.encode())
                assert field==accepted[key]['candidate_field_decision']
                assert sha(enc(field))==accepted[key]['candidate_field_sha256']
                if action=='exclude':
                    assert not any(selected) and field['action']=='source_context'
                    counts['reviewed_context_fields']+=1
                else:
                    assert any(selected) and field['action'] in ['whole','excerpts']
                    counts['admitted_fields']+=1
                if field['action']=='whole':assert all(selected) and len(field['spans'])==1
                counts['complete_fields_read']+=1;counts['characters_read']+=len(text);counts['utf8_bytes_read']+=len(text.encode())
                component_proofs.append({'id':ident,'language':lang,'components':list(dict.fromkeys(s['component_id'] for s in field['spans'])),
                    'families':list(dict.fromkeys(s['source_report_family_id'] for s in field['spans']))})
            else:
                assert not field['spans'] and field['action']=='unreviewed' and after['text'] is None
                counts['unread_context_fields']+=1
            assert (after['text'] or '')==''.join(text[s['start']:s['end']] for s in field['spans'])
            pieces=[(s['start'],s['end'],text[s['start']:s['end']]) for s in field['spans']]
            context=[(c['source_span'][0],c['source_span'][1],c['text']) for c in after.get('comments',[]) if c.get('source_span') is not None]
            pieces+=context;cursor=0
            for a,b,t in sorted(pieces):assert a==cursor and text[a:b]==t;cursor=b
            assert cursor==len(text) and ''.join(t for a,b,t in sorted(pieces))==text
            counts['lossless_nonempty_partitions']+=1
            if reviewed:counts['reviewed_field_context_gaps']+=len(context)
            assert 'observed_script' not in field and before['script']==after['script']
            for k,v in before.items():
                if k not in ['text','scope','source','comments']:metadata['language']+=equal(v,after[k])
            for k,v in before['source'].items():metadata['source']+=equal(v,after['source'][k])
            for i,c in enumerate(before.get('comments',[])):
                for k,v in c.items():metadata['previous_comments']+=equal(v,after['comments'][i][k])
            field_proofs.append({'id':ident,'language':lang,'source_field_sha256':sha(text.encode()),'characters':len(text),'utf8_bytes':len(text.encode()),
                'complete_own_field_read':reviewed,'selected_mask_sha256':sha(bytes(selected)),'selected_spans':field['spans'],
                'retained_context_ranges':[[a,b] for a,b,t in context],'lossless_partition_pass':True})
    engine.finish()
    assert (counts['register'],counts['exclude'],counts['source_slots'],counts['lossless_nonempty_partitions'])==(21,1,110,110)
    assert (counts['complete_fields_read'],counts['characters_read'],counts['utf8_bytes_read'])==(47,12443,26863)
    assert (counts['admitted_fields'],counts['reviewed_context_fields'],counts['unread_context_fields'])==(42,5,63)
    assert len(source_proofs)==44 and len(field_proofs)==110 and len(component_proofs)==47
    for b in payload:assert bind(Path(b['owner_path']))=={k:b[k] for k in ['bytes','sha256','git_blob_sha1']}
    assert bind(manifest_path)['sha256']==MANIFEST_SHA and (ROOT/'input/cohort.jsonl').read_bytes()==original_input
    proof={'schema':'independent-field-source-native-proof-v1','source_files':source_proofs,'fields':field_proofs,'components':component_proofs,'primary_payload':payload}
    proof_bytes=gzip.compress(enc(proof),mtime=0);put(ROOT/'field-and-source-proof-final.json.gz',proof_bytes)
    report={'schema':'independent-complete-reading-native-audit-v1','status':'PASS','source_checkpoint':PIN,
        'primary_manifest':'delivery-manifest-v1.json','primary_manifest_sha256':MANIFEST_SHA,'primary_payload_files_verified':len(payload),
        'primary_active_path':ACTIVE,'primary_active_sha256':ACTIVE_SHA,'source_baseline_path':ledger['source_ledger_path'],'source_baseline_sha256':ledger['source_ledger_sha256'],
        'independent_source_first_receipt_sha256':READ_SHA,'independent_boundary_assessment_sha256':ASSESS_SHA,
        'counts':dict(counts),'metadata_leaf_equalities':dict(metadata),'metadata_leaf_equalities_total':sum(metadata.values()),
        'source_files_reopened':44,'complete_source_reparses':22,'stored_plain_git_hashes_pass':True,'native_apply_and_finish_pass':True,
        'exact_full_source_objects_references_and_original_bytes_preserved':True,'all_independently_accepted_field_decisions_match':True,
        'unread_siblings_have_no_selected_text':True,'all_source_grades_and_unknown_metadata_preserved':True,
        'source_script_corrections':[],'primary_candidate_input_mutation':False,'required_amendments':[],
        'transparent_initial_refinements':assessment['explicit_initial_judgement_refinements'],
        'field_source_proof_sha256':sha(proof_bytes),'source_http_requests':0,'github_writes':0,
        'limitations':'No independent authenticity grading, external canonical-identity verification or publication/deployment claim. Only the44 complete Hindi/Urdu fields and all three remaining2636 sibling fields were linguistically read; the other63 fields remain unread source context.'}
    b=enc(report);put(ROOT/'independent-final-audit.json',b)
    print(json.dumps({'sha256':sha(b),'status':'PASS','counts':dict(counts),'metadata_leaf_equalities':sum(metadata.values()),'source_files':44,'reparses':22}))

if __name__=='__main__':main()

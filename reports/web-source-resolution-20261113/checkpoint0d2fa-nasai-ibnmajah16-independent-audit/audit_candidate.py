"""Independently validate the exact candidate after the frozen full source-first pass."""
from pathlib import Path
import collections, copy, gzip, hashlib, json, sys

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
OWNER=WORK/'phase21-checkpoint0d2fa-nasai-ibnmajah16-review'
CENTRAL=WORK/'phase19-successor-acquisition-monitor/held-evidence'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpoint0d2fa-nasai-ibnmajah16-20261113.json.gz'
PIN='0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a'
MANIFEST_SHA='75b39b220c619859b998b513b79dee87074cce550ac4f249e4ffb10824097e33'
ACTIVE_SHA='3ae6d94ea8a5ecd7e048543d57218fa94e33126333c745d110db5c2c39ffa1d6'
READ_SHA='8ad705d9d3d92d2051fa7a1c5a4fc2439926579eebbbcdfb7d3761cfa5f20b8c'
ASSESS_SHA='58877052abd9ba57fd5efec9db73c6be09cbdb77bed4bfe9612bcbd6910958e5'
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
    assert len(read_fields)==32
    assert bind(ROOT/'independent-boundary-assessment-v1.json')['sha256']==ASSESS_SHA
    assessment=read(ROOT/'independent-boundary-assessment-v1.json')
    accepted={(r['id'],r['language']):r for r in assessment['all_candidate_field_checks']}
    assert set(accepted)==set(read_fields) and not assessment['required_amendments']
    assert all(r['accepted'] and r['complete_candidate_mask_and_voice_inspected'] for r in accepted.values())
    source_rows=list(map(json.loads,original_input.splitlines()))
    source_by={'deenhindi-'+r['collection']+':'+r['number']:r for r in source_rows}
    assert len(source_by)==len(source_rows)==16
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
    assert len(payload)==len({r['path'] for r in payload})==21
    assert bind(repo/ACTIVE)['sha256']==ACTIVE_SHA
    ledger=read(repo/ACTIVE);baseline=repo/ledger['source_ledger_path']
    assert bind(baseline)['sha256']==ledger['source_ledger_sha256']
    assert list(map(json.loads,gzip.decompress(baseline.read_bytes()).splitlines()))==source_rows
    decisions={r['id']:r for r in ledger['records']}
    assert len(decisions)==len(ledger['records'])==16 and set(decisions)==set(source_by)
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
        assert original==untouched and action==decision['decision']=='register';counts['register']+=1
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
                assert any(selected) and field['action'] in ['whole','excerpts']
                if field['action']=='whole':assert all(selected) and len(field['spans'])==1
                counts['complete_fields_read']+=1;counts['characters_read']+=len(text);counts['utf8_bytes_read']+=len(text.encode())
                counts['admitted_fields']+=1
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
    assert (counts['register'],counts['source_slots'],counts['lossless_nonempty_partitions'])==(16,80,80)
    assert (counts['complete_fields_read'],counts['characters_read'],counts['utf8_bytes_read'])==(32,13693,29601)
    assert (counts['admitted_fields'],counts['unread_context_fields'])==(32,48)
    assert len(source_proofs)==32 and len(field_proofs)==80 and len(component_proofs)==32
    for b in payload:assert bind(Path(b['owner_path']))=={k:b[k] for k in ['bytes','sha256','git_blob_sha1']}
    assert bind(manifest_path)['sha256']==MANIFEST_SHA and (ROOT/'input/cohort.jsonl').read_bytes()==original_input
    proof={'schema':'independent-field-source-native-proof-v1','source_files':source_proofs,'fields':field_proofs,'components':component_proofs,'primary_payload':payload}
    proof_bytes=gzip.compress(enc(proof),mtime=0);put(ROOT/'field-and-source-proof-final.json.gz',proof_bytes)
    report={'schema':'independent-complete-reading-native-audit-v1','status':'PASS','source_checkpoint':PIN,
        'primary_manifest':'delivery-manifest-v1.json','primary_manifest_sha256':MANIFEST_SHA,'primary_payload_files_verified':len(payload),
        'primary_active_path':ACTIVE,'primary_active_sha256':ACTIVE_SHA,'source_baseline_path':ledger['source_ledger_path'],'source_baseline_sha256':ledger['source_ledger_sha256'],
        'independent_source_first_receipt_sha256':READ_SHA,'independent_boundary_assessment_sha256':ASSESS_SHA,
        'counts':dict(counts),'metadata_leaf_equalities':dict(metadata),'metadata_leaf_equalities_total':sum(metadata.values()),
        'source_files_reopened':32,'complete_source_reparses':16,'stored_plain_git_hashes_pass':True,'native_apply_and_finish_pass':True,
        'exact_full_source_objects_references_and_original_bytes_preserved':True,'all_independently_accepted_field_decisions_match':True,
        'unread_siblings_have_no_selected_text':True,'all_source_grades_and_unknown_metadata_preserved':True,
        'source_script_corrections':[],'primary_candidate_input_mutation':False,'required_amendments':[],
        'transparent_initial_refinements':assessment['explicit_initial_judgement_refinements'],
        'field_source_proof_sha256':sha(proof_bytes),'source_http_requests':0,'github_writes':0,
        'limitations':'No independent authenticity grading, external canonical-identity verification or publication/deployment claim. Only the 32 complete Hindi/Urdu fields were linguistically read; every other language is retained as unread source context.'}
    b=enc(report);put(ROOT/'independent-final-audit.json',b)
    print(json.dumps({'sha256':sha(b),'status':'PASS','counts':dict(counts),'metadata_leaf_equalities':sum(metadata.values()),'source_files':32,'reparses':16}))

if __name__=='__main__':main()

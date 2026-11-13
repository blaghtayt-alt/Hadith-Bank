"""Independent exact-final-byte, source-first, semantic-mask and native audit."""
from pathlib import Path
import argparse,copy,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
PRIMARY=WORK/'phase16-checkpoint5589-abudawud-tirmidhi25-review'
PIN='5589a3ffc3b43c3324ae26f2b6c4d33152834456'
EVID=WORK/'phase15-successor-acquisition-monitor/held-evidence'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):return json.loads(p.read_bytes())
def leaf_count(x):
    if isinstance(x,dict):return sum(leaf_count(v) for v in x.values()) or 1
    if isinstance(x,list):return sum(leaf_count(v) for v in x) or 1
    return 1
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,p
    else:p.write_bytes(b)
parser=argparse.ArgumentParser();parser.add_argument('--manifest-sha256',required=True);parser.add_argument('--active-sha256',required=True);args=parser.parse_args()
mp=PRIMARY/'delivery-manifest-v2.json';mb=mp.read_bytes();assert sha(mb)==args.manifest_sha256
m=json.loads(mb)
for f in m['files']:
    b=Path(f.get('local_path',f.get('source_path'))).read_bytes()
    assert len(b)==f.get('bytes',f.get('size_bytes')) and sha(b)==f['sha256']
    if f.get('git_blob_sha1'):assert git(b)==f['git_blob_sha1']
active=next(f for f in m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
ap=Path(active.get('local_path',active.get('source_path')));ab=ap.read_bytes();assert sha(ab)==args.active_sha256
out_root=Path(str(ap)[:-len(active['path'])]);ledger=json.loads(gzip.decompress(ab))
baseline=(out_root/ledger['source_ledger_path']).read_bytes();assert sha(baseline)==ledger['source_ledger_sha256']
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,gzip.decompress(baseline).splitlines())}
decisions={r['id']:r for r in ledger['records']};assert len(sources)==len(decisions)==25 and sources.keys()==decisions.keys()
ownp=ROOT/'complete-independent-source-first-readings.json';ownb=ownp.read_bytes();assert sha(ownb)=='9c43db15281646afead594e6e9e313ec32f5c0ce9521134c660968ee3c898af4'
own=json.loads(ownb);assert own['candidate_inspected'] is False and own['full_fields_read_before_candidate']
assert (own['complete_source_fields'],own['characters'],own['utf8_bytes'])==(59,25470,52806)
readings={(f['occurrence_id'],f['language']):f for f in own['fields']}
planp=ROOT/'accepted-final-field-plan.json';assert sha(planp.read_bytes())=='8d179a06414e49543410b88c1be6a0714fbb93f8919f7b37e5a987ac5d9c926b'
plan={r['id']:r for r in read(planp)['rows']};assert plan.keys()==sources.keys()
findingp=ROOT/'independent-boundary-findings-v1.json';assert sha(findingp.read_bytes())=='ec424ce3205fe1ff438df8b4fdc5a94412e1069ad5e55877a9ee64fd497af4c5'
proofp=ROOT/'independent-source-proof.json';assert sha(proofp.read_bytes())=='d36fc848955ac8f14190a06d4a172093625c07d961deb135efc4f93dcfa33b6a'
for r in read(proofp)['rows']:
    for f in r['files']:
        b=(EVID/'sources'/f['path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256'] and git(b)==f['git_blob_sha1']
previous=read(WORK/'phase13-successor-acquisition-monitor/saved-checkpoint/state.json');assert len(previous['imported'])==15672
assert not {i.removeprefix('deenhindi-') for i in sources}.intersection(previous['imported'])
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
engine=SourceReviews(out_root,'deenhindi');assert set(engine.decisions)==set(sources)
assert engine.engine_sha256=='cc253d0d89d839f79a99e5209824b953fa6ac21be80fdb898a130025cbc7114b'
v1m=read(PRIMARY/'delivery-manifest-v1.json');v1f=next(f for f in v1m['files'] if '/reviews/source-review-' in f['path']);v1b=Path(v1f.get('local_path',v1f.get('source_path'))).read_bytes();assert sha(v1b)=='b2f5305335c2a896ea850a2ef79b7f6b878a6f6f72e5301972c256cd1d8296af'
v1={r['id']:r for r in json.loads(gzip.decompress(v1b))['records']}
counts={'partitions':0,'metadata_value_equalities':0,'admitted':0,'read_context':0,'unread_context':0,'read_fields':0,'characters':0,'utf8_bytes':0,'spans':0,'unchanged_explicit_fields':0,'unchanged_implicit_slots':0,'unchanged_whole_parents':0}
field_reports=[]
for ident,saved in sources.items():
    d=decisions[ident];expected=plan[ident];assert d['decision']==expected['decision']
    assert d['source_record_sha256']==sha(importer.json_bytes(saved['source_record'])) and d['source_reference_verbatim']==saved['source_reference_verbatim']
    original=importer.canonical_record(saved);frozen=copy.deepcopy(original);after,disposition=engine.apply(original,saved=saved)
    assert original==frozen and disposition==d['decision']
    for key in ['id','number','narrator','grading','references','source_locator','source','translator','translation_provenance','rights','source_headings']:
        assert after[key]==frozen[key];counts['metadata_value_equalities']+=leaf_count(frozen[key])
    assert after['review']['independent_pro_qc']=='not_performed' and not after['review']['certified_release_eligible']
    bylang={f['language']:f for f in d['field_reviews']};oldfields={f['language']:f for f in v1[ident]['field_reviews']}
    if d==v1[ident]:counts['unchanged_whole_parents']+=1
    expectedlangs={f['language']:f for f in expected['fields']}
    assert len(frozen['language_versions'])==len(after['language_versions'])==5
    for old,new in zip(frozen['language_versions'],after['language_versions']):
        lang=old['language'];text=old['text'];e=expectedlangs[lang];f=bylang.get(lang)
        for key in ['id','language','script','references','translation_provenance']:
            assert old[key]==new[key];counts['metadata_value_equalities']+=leaf_count(old[key])
        assert e['source_text_sha256']==sha(text.encode())
        assert new['source']['manual_review']['field_reviewed']==e['reviewed']
        if not e['allowed_semantic_change']:
            if e['v1_field_decision_explicit']:
                assert f==oldfields[lang] and sha(enc(f))==e['v1_field_sha256'];counts['unchanged_explicit_fields']+=1
            else:assert f is None;counts['unchanged_implicit_slots']+=1
        if e['reviewed']:
            assert f and f['reviewed'];r=readings[ident,lang]
            assert r['complete_own_field_read'] and r['text']==text and r['sha256']==sha(text.encode())
            assert f['text_sha256']==sha(text.encode()) and f['chars_reviewed']==len(text) and f['bytes_reviewed']==len(text.encode())
            counts['read_fields']+=1;counts['characters']+=len(text);counts['utf8_bytes']+=len(text.encode())
        else:assert not f or not f['reviewed']
        spans=new['source'].get('text_spans',{}).get('quotation_spans',[])
        mask=lambda ranges:{i for a,b in ranges for i in range(a,b)}
        assert mask(spans)==mask(e['accepted_positions']),(ident,lang,spans,e['accepted_positions'])
        assert (new['text'] or '')==''.join(text[a:b] for a,b in spans)
        if f:
            assert spans==[[s['start'],s['end']] for s in f['spans']]
            for s in f['spans']:assert s['sha256']==sha(text[s['start']:s['end']].encode())
        if ident in ['deenhindi-abudawud:2306','deenhindi-tirmidhi:2363'] and lang in ['hi','ur']:
            signature=lambda s:(s['report_type'],s['speaker'],s['source_report_family_id'])
            allowed={signature(s) for s in oldfields[lang]['spans'] if ident!='deenhindi-abudawud:2306' or s['start']<(1395 if lang=='hi' else 1260)}
            assert {signature(s) for s in f['spans']}==allowed
        pieces=[(a,b,text[a:b]) for a,b in spans];gaps=[]
        for c in new['comments']:
            a,b=c['source_span'];assert c['scope']=='source_context_not_narration' and c['text']==text[a:b] and c['source_text_sha256']==sha(text[a:b].encode())
            pieces.append((a,b,c['text']));gaps.append({'start':a,'end':b,'text':c['text'],'sha256':c['source_text_sha256']})
        cursor=0
        for a,b,t in sorted(pieces):assert a==cursor and a<b<=len(text) and t==text[a:b];cursor=b
        assert cursor==len(text) and ''.join(t for a,b,t in sorted(pieces))==text
        counts['partitions']+=1;counts['spans']+=len(spans)
        counts['admitted' if spans else 'read_context' if e['reviewed'] else 'unread_context']+=1
        if e['reviewed']:field_reports.append({'id':ident,'language':lang,'source_sha256':sha(text.encode()),'complete_source_first_reading':True,'selected_spans':f['spans'],'context_gaps':gaps,'original_blind_note':readings[ident,lang]['independent_reading_note'],'accepted_final_plan':e})
engine.finish()
assert (counts['partitions'],counts['read_fields'],counts['characters'],counts['utf8_bytes'])==(125,59,25470,52806)
assert (counts['admitted'],counts['read_context'],counts['unread_context'])==(44,15,66)
assert (counts['unchanged_explicit_fields'],counts['unchanged_implicit_slots'],counts['unchanged_whole_parents'])==(45,66,21)
assert sum(d['decision']=='register' for d in decisions.values())==22
assert {i for i,d in decisions.items() if d['decision']=='exclude'}=={'deenhindi-abudawud:2330','deenhindi-abudawud:2331','deenhindi-tirmidhi:2296'}
report={'schema':'hadith-bank-independent-final-source-review-audit-v1','status':'PASS','source_commit':PIN,'primary_manifest_sha256':sha(mb),'active_ledger_sha256':sha(ab),'independent_source_first_sha256':sha(ownb),'source_proof_sha256':sha(proofp.read_bytes()),'findings_sha256':sha(findingp.read_bytes()),'accepted_field_plan_sha256':sha(planp.read_bytes()),'occurrences':25,'registered':22,'source_only':3,'source_only_ids':sorted(i for i,d in decisions.items() if d['decision']=='exclude'),'counts':counts,'source_files_independently_reopened_and_hashed':50,'exact_raw_reparses_in_source_first_proof':25,'native_apply_finish':'PASS','all_initial_findings_resolved':True,'open_findings':[],'all_source_metadata_unchanged':True,'initial_notes_preserved':True,'independent_pro_qc':'not_performed','full_saved5589_state_history_comparison':False,'source_http_requests':0,'github_writes':0,'fields':field_reports}
out=ROOT/'publish';rel=Path('reports/web-source-resolution-20261113/checkpoint5589-abudawud-tirmidhi25-independent-audit')
payload={'final-audit.json':enc(report),'complete-independent-source-first-readings.json':ownb,'independent-source-proof.json':proofp.read_bytes(),'independent-boundary-findings-v1.json':findingp.read_bytes(),'accepted-final-field-plan.json':planp.read_bytes(),'freeze_source_first.py':(ROOT/'freeze_source_first.py').read_bytes(),'freeze_findings.py':(ROOT/'freeze_findings.py').read_bytes(),'audit_final.py':Path(__file__).read_bytes(),'additional-abudawud2330-2331-originals.jsonl':(ROOT/'input/additional-abudawud2330-2331-source-fields.jsonl').read_bytes()}
files=[]
for name,b in payload.items():
    p=out/rel/name;put(p,b);files.append({'path':p.relative_to(out).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
delivery={'schema':'hadith-bank-independent-final-audit-delivery-v1','status':'PASS','source_commit':PIN,'primary_manifest_sha256':sha(mb),'files':files};put(ROOT/'delivery-manifest.json',enc(delivery))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(delivery)),'files':len(files),'bytes':sum(f['bytes'] for f in files),'report_sha256':sha(enc(report)),'registered':22,'source_only':3,**counts},indent=2))

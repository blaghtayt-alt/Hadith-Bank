"""Restore two finite source continuations after independent review, preserving V1."""
from pathlib import Path
import copy,gzip,hashlib,importlib.util,json,pprint,subprocess,sys
ROOT=Path(__file__).resolve().parent
EVID=Path('imports/web-deenhindi-20261112/reviews/checkpoint5589-nasai-ibnmajah25-20261113')
ACTIVE=Path('imports/web-deenhindi-20261112/reviews/source-review-checkpoint5589-nasai-ibnmajah25-20261113.json.gz')
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,p
    else:p.write_bytes(b)
old_manifest=ROOT/'delivery-manifest-v1.json';assert sha(old_manifest.read_bytes())=='de0399c89be6d422c9c738404ec2c2474f695aef174da7ecd9a810da0c81ec74'
old=json.loads(old_manifest.read_bytes());out=ROOT/'publish-v2';archive=EVID/'independent-boundary-amendment-v2'
for f in old['files']:
    b=Path(f['local_path']).read_bytes();assert sha(b)==f['sha256'] and len(b)==f['bytes']
    put(out/archive/'previous-v1'/f['path'],b)
put(out/archive/'previous-delivery-manifest-v1.json',old_manifest.read_bytes())
before=json.loads(gzip.decompress((ROOT/'publish'/ACTIVE).read_bytes()))
spec=importlib.util.spec_from_file_location('frozen_v1_rules',ROOT/'manual_rules.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
rules=copy.deepcopy(module.SPECS);r=rules['nasai:2322']
assert r['exclude_substrings']=={'hi':['(मगर खाऊँगा)'],'ur':['۱؎','( مگر کھاؤ گا )']}
r['exclude_substrings']={'ur':['۱؎']}
for lang in ['hi','ur']:
    r['field_notes'][lang]='The complete original field was read before V1. After independent review, retain its finite first-person but-I-will-eat continuation as supplied source wording. It is not merely a lexical synonym or a report pointer. The initial preview interpretation remains in the frozen source-first receipt as review history. The Urdu source places this parenthesis outside quotation marks; no independent direct-speech verification is asserted. Preserve both visits, food object, prior intention, actual eating, voluntary-charity qualifier and all alternatives; only the Urdu footnote pointer remains context.'
    r.setdefault('annotations',{})[lang]='The source supplies a finite first-person parenthetic continuation about eating. It remains in the same narrated report family. The Urdu field prints it outside quotation marks, so retention does not certify its status as exact direct Prophetic speech.'
(ROOT/'manual_rules.py').write_text('"""V2: two independently reviewed finite continuations restored; V1 is archived."""\nSPECS = '+pprint.pformat(rules,sort_dicts=True,width=120)+'\n')
run=subprocess.run([sys.executable,str(ROOT/'build_delivery.py'),'--output-dir',str(out),'--manifest-file',str(ROOT/'delivery-manifest-v2.json')],capture_output=True,text=True)
assert run.returncode==0,run.stdout+run.stderr
after=json.loads(gzip.decompress((out/ACTIVE).read_bytes()));changes=[];unchanged_fields=0;unchanged_parents=0
for oldr,newr in zip(before['records'],after['records']):
    assert oldr['id']==newr['id']
    if oldr==newr:unchanged_parents+=1
    for a,b in zip(oldr['field_reviews'],newr['field_reviews']):
        assert a['language']==b['language']
        if a==b:unchanged_fields+=1;continue
        assert oldr['id']=='deenhindi-nasai:2322' and a['language'] in ['hi','ur']
        oldset={i for s in a['spans'] for i in range(s['start'],s['end'])};newset={i for s in b['spans'] for i in range(s['start'],s['end'])}
        assert oldset<=newset
        reading=json.loads((ROOT/'source-first-complete-reading.json').read_bytes())
        f=next(f for f in reading['fields'] if f['id']==oldr['id'] and f['language']==a['language'])
        literal='(मगर खाऊँगा)' if a['language']=='hi' else '( مگر کھاؤ گا )';start=f['text'].index(literal);end=start+len(literal)
        assert newset-oldset==set(range(start,end))
        assert {(s['report_type'],s['speaker'],s['source_report_family_id']) for s in a['spans']}=={(s['report_type'],s['speaker'],s['source_report_family_id']) for s in b['spans']}
        changes.append({'id':oldr['id'],'language':a['language'],'start':start,'end':end,'text':literal,'characters':len(literal),'utf8_bytes':len(literal.encode()),'action':'restore_finite_source_continuation','source_field_sha256':a['text_sha256'],'old_field_sha256':sha(enc(a)),'new_field_sha256':sha(enc(b))})
assert len(changes)==2 and unchanged_fields==123 and unchanged_parents==24
assert sum(c['characters'] for c in changes)==27
receipt={'status':'PASS','source_commit':'5589a3ffc3b43c3324ae26f2b6c4d33152834456','prior_manifest_sha256':sha(old_manifest.read_bytes()),'prior_active_sha256':sha((ROOT/'publish'/ACTIVE).read_bytes()),'final_active_sha256':sha((out/ACTIVE).read_bytes()),'initial_source_first_receipt_sha256':sha((ROOT/'source-first-complete-reading.json').read_bytes()),'independent_source_first_receipt_sha256':'91561405fa1e9423fa291f31adb4b86dae06ea6d2a276e784f83710118e4b258','changes':changes,'unchanged_field_decisions':unchanged_fields,'unchanged_whole_parent_decisions':unchanged_parents,'new_linguistic_readings':0,'primary_counts_unchanged':True,'source_bytes_changed':False,'report_voices_families_unchanged':True,'initial_notes_preserved':True,'reason':'Independent source-first review identified two actually supplied finite first-person continuations. Restore them with an explicit quotation-scope annotation; retain the initial contrary interpretation as immutable history. The source does not label these as lexical definitions or compiler discussion.'}
put(out/archive/'amendment-receipt.json',enc(receipt));put(out/archive/'amend_v2.py',Path(__file__).read_bytes())
manifest=json.loads((ROOT/'delivery-manifest-v2.json').read_bytes());portable=out/EVID/'package-file-manifest.json'
def bind(p,local=False):
    b=p.read_bytes();d={'path':p.relative_to(out).as_posix(),'bytes':len(b),'size_bytes':len(b),'sha256':sha(b),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}
    if local:d.update(local_path=str(p),source_path=str(p))
    return d
port=json.loads(portable.read_bytes());port['files']=[bind(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=portable];port['versioned_amendment']=receipt;portable.write_bytes(enc(port))
manifest['files']=[bind(p,True) for p in sorted(out.rglob('*')) if p.is_file()];manifest['versioned_amendment']=receipt
(ROOT/'delivery-manifest-v2.json').write_bytes(enc(manifest))
print(json.dumps({'manifest_sha256':sha((ROOT/'delivery-manifest-v2.json').read_bytes()),'files':len(manifest['files']),'bytes':sum(f['bytes'] for f in manifest['files']),'active_sha256':receipt['final_active_sha256'],'restored_characters':sum(c['characters'] for c in changes),'restored_utf8_bytes':sum(c['utf8_bytes'] for c in changes),'unchanged_fields':unchanged_fields,'unchanged_parents':unchanged_parents}))

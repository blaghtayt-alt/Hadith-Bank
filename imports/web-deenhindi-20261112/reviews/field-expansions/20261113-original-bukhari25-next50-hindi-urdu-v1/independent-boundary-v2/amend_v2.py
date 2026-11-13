"""Rebuild only the accepted seven field definitions and archive every v1 byte."""
from pathlib import Path
import copy,gzip,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parent
EVID=Path('imports/web-deenhindi-20261112/reviews/field-expansions/20261113-original-bukhari25-next50-hindi-urdu-v1')
ARCH=EVID/'independent-boundary-v2'
OUT=ROOT/'publish-v2'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,p
 else:p.write_bytes(b)
assert not (ROOT/'delivery-manifest-v2.json').exists(), 'Frozen v2 already exists'
mb=(ROOT/'delivery-manifest-v1.json').read_bytes();assert sha(mb)=='9f3b6612ee3dd871f47b2741f55570a07567554eb569807dfaa48b2663d35e51'
m=json.loads(mb)
for f in m['files']:
 b=Path(f['local_path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256'] and git(b)==f['git_blob_sha1']
fb=(ROOT.parent/'phase20-original-bukhari25-hi-ur-independent-audit/independent-boundary-findings-v1.json').read_bytes()
assert sha(fb)=='ecc345ed2f2c3f34316267769bef30ec7fedcea043001db70a7f9cae36f7d1a1'
findings=json.loads(fb)
# Derive a separate producer without modifying or rerunning the frozen v1 producer.
source=(ROOT/'build_extension.py').read_text()
replacements=[
 ('from manual_readings import READINGS','from manual_readings_v2 import READINGS'),
 ("OUT = ROOT / 'publish-v1'","OUT = ROOT / 'publish-v2'"),
 ("VALID = ROOT / 'validation-repo-v1'","VALID = ROOT / 'validation-repo-v2'"),
 ("OLD_VALID = ROOT / 'validation-before-repo'","OLD_VALID = ROOT / 'validation-before-repo-v2'"),
 ('delivery-manifest-v1.json','native-v2-core-manifest.json'),
 ("note=first['initial_primary_reading_note']","note=spec.get('refined_reading_note',first['initial_primary_reading_note'])")
]
for old,new in replacements:
 assert old in source,old
 source=source.replace(old,new)
put(ROOT/'build_extension_v2.py',source.encode())
subprocess.run([sys.executable,str(ROOT/'build_extension_v2.py')],check=True)
active=next(f for f in m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
old=json.loads(gzip.decompress(Path(active['local_path']).read_bytes()))
new=json.loads(gzip.decompress((OUT/active['path']).read_bytes()))
assert {k:v for k,v in old.items() if k not in ['records','field_review_extensions']}=={k:v for k,v in new.items() if k not in ['records','field_review_extensions']}
assert old['field_review_extensions'][:-1]==new['field_review_extensions'][:-1]
assert {k:v for k,v in old['field_review_extensions'][-1].items() if k!='reading_notes'}=={k:v for k,v in new['field_review_extensions'][-1].items() if k!='reading_notes'}
oldrows={r['occurrence_id']:r for r in old['records']};newrows={r['occurrence_id']:r for r in new['records']}
cuts={(x['occurrence_id'],x['language']):x for x in findings['requested_source_mask_changes']}
special=('deenhindi-bukhari:1536','hi')
inputrows=[json.loads(s) for s in (ROOT/'input/full-hi-ur-reading-input-50.jsonl').read_text().splitlines()]
texts={(r['occurrence_id'],r['language']):r['text'] for r in inputrows}
def mask(field):return {i for s in field['selected_spans'] for i in range(s['start'],s['end'])}
def identity(span):return {k:span[k] for k in ['component_id','source_report_family_id','report_type','speaker']}
unchanged=whole=0;removed=[];changes=[]
for ident,oldrow in oldrows.items():
 newrow=newrows[ident]
 assert {k:v for k,v in oldrow.items() if k!='fields'}=={k:v for k,v in newrow.items() if k!='fields'}
 if oldrow==newrow:whole+=1
 for of,nf in zip(oldrow['fields'],newrow['fields']):
  key=(ident,of['language']);assert nf['language']==of['language']
  if key not in cuts and key!=special:assert of==nf;unchanged+=1;continue
  assert {k:v for k,v in of.items() if k not in ['reason','selected_spans','source_text_annotations','speaker']}=={k:v for k,v in nf.items() if k not in ['reason','selected_spans','source_text_annotations','speaker']}
  if key in cuts:
   c=cuts[key];text=texts[key];a,b=c['start'],c['end'];assert text[a:b]==c['text']
   assert mask(nf)==mask(of)-set(range(a,b)) and set(range(a,b))<=mask(of)
   assert nf['speaker']==of['speaker']
   for ns in nf['selected_spans']:
    os=next(s for s in of['selected_spans'] if s['start']<=ns['start']<ns['end']<=s['end'])
    assert identity(ns)==identity(os)
   removed.append({'id':ident,'language':of['language'],'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode())})
  else:
   assert mask(of)==mask(nf) and len(of['selected_spans'])==len(nf['selected_spans'])
   for os,ns in zip(of['selected_spans'],nf['selected_spans']):
    assert {k:v for k,v in os.items() if k not in ['reason','speaker']}=={k:v for k,v in ns.items() if k not in ['reason','speaker']}
   assert 'अत' in nf['speaker'] and 'अत' in nf['selected_spans'][1]['speaker']
  changes.append({'id':ident,'language':of['language'],'before_field_sha256':sha(enc(of)),'after_field_sha256':sha(enc(nf))})
assert len(changes)==7 and unchanged==2378 and whole==473
assert sum(len(x['text']) for x in removed)==89 and sum(len(x['text'].encode()) for x in removed)==179
for f in m['files']:put(OUT/ARCH/'before-v1/payload'/f['path'],Path(f['local_path']).read_bytes())
put(OUT/ARCH/'before-v1/delivery-manifest-v1.json',mb)
put(OUT/ARCH/'independent-boundary-findings-v1.json',fb)
for name in ['amend_v2.py','manual_readings_v2.py','build_extension_v2.py']:put(OUT/ARCH/name,(ROOT/name).read_bytes())
core=json.loads((ROOT/'native-v2-core-manifest.json').read_bytes())
receipt={'schema':'hadith-bank-original50-bounded-independent-amendment-v2','status':'PASS','previous_manifest_sha256':sha(mb),'independent_findings_sha256':sha(fb),'previous_active_sha256':active['sha256'],'final_active_sha256':sha((OUT/active['path']).read_bytes()),'changes':changes,'removed_ranges':removed,'removed_characters':89,'removed_utf8_bytes':179,'new_selected_positions':0,'metadata_only_fields':1,'unchanged_other_field_definitions':2378,'unchanged_whole_parents_against_v1':473,'all477_parent_dispositions_unchanged':True,'all2335_pre_extension_other_fields_unchanged':True,'v1_payload_files_archived':len(m['files']),'v1_manifest_archived':True,'initial_source_first_notes_unchanged':True,'original_extension_identity_preserved':True,'final_independent_gate_pending':True,'native_validation':core['summary'],'canonical_queue_changed_on_github':False,'github_writes':0}
put(OUT/ARCH/'amendment-receipt.json',enc(receipt))
files=[]
for p in sorted(OUT.rglob('*')):
 if p.is_file():
  b=p.read_bytes();files.append({'path':p.relative_to(OUT).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
final={'schema':'hadith-bank-original-language-extension-delivery-v2','status':'PASS','summary':core['summary'],'independent_amendment':receipt,'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}
put(ROOT/'delivery-manifest-v2.json',enc(final))
print(json.dumps({'manifest_sha256':sha(enc(final)),'active_sha256':receipt['final_active_sha256'],'files':len(files),'bytes':final['total_bytes'],'other_fields_exact':unchanged,'other_parents_exact':whole},indent=2))

"""Exact accepted-plan, native-engine and immutable-source gate; never mutates primary."""
import collections,copy,gzip,hashlib,json,sys
from pathlib import Path
from verify_original_sources import verify as verify_original_sources
ROOT=Path(__file__).resolve().parent
PRIMARY=ROOT.parent/'phase22-checkpoint17cd-bukhari-ibnmajah22-review'
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
leaf=lambda x:sum(leaf(v) for v in x.values()) if isinstance(x,dict) and x else sum(leaf(v) for v in x) if isinstance(x,list) and x else 1

mp=Path(sys.argv[1]).resolve()
assert mp.parent==PRIMARY and mp.name=='delivery-manifest-v2.json'
mb=mp.read_bytes();assert sha(mb)==sys.argv[2];m=json.loads(mb)
op=PRIMARY/'delivery-manifest-v1.json';ob=op.read_bytes()
assert sha(ob)=='95967f1f4950735e7b1b03188911367c39dfaf8b1eb590af23148fb470581ff3'
om=json.loads(ob)
def verify_manifest(man):
 assert len({x['path'] for x in man['files']})==len(man['files'])
 for x in man['files']:
  b=Path(x['local_path']).read_bytes();assert len(b)==x['bytes'] and sha(b)==x['sha256'],x['path']
  if 'git_blob_sha1' in x:assert git(b)==x['git_blob_sha1']
verify_manifest(m);verify_manifest(om)
ap='imports/web-deenhindi-20261112/reviews/source-review-checkpoint17cd-bukhari-ibnmajah22-20261113.json.gz'
ae=next(x for x in m['files'] if x['path']==ap);oe=next(x for x in om['files'] if x['path']==ap)
ab=Path(ae['local_path']).read_bytes();oab=Path(oe['local_path']).read_bytes()
assert sha(ab)==sys.argv[3] and sha(oab)=='e1c976355261853f38ee258aaade04f3ff332743b0790fdf43937f900dacf705'
a=json.loads(gzip.decompress(ab));old=json.loads(gzip.decompress(oab))
assert {k:v for k,v in a.items() if k!='records'}=={k:v for k,v in old.items() if k!='records'}
new_by_id={x['id']:x for x in a['records']};old_by_id={x['id']:x for x in old['records']}
source_rows=[json.loads(x) for x in (ROOT/'input/cohort.jsonl').read_text().splitlines()]
assert len(source_rows)==len(new_by_id)==len(old_by_id)==22
assert set(new_by_id)==set(old_by_id)=={'deenhindi-'+x['collection']+':'+x['number'] for x in source_rows}
receipt_b=(ROOT/'complete-independent-source-first-readings.json').read_bytes()
assert sha(receipt_b)=='77f1c3afb7025d99cccba3f4dfd766dc1be3513bef6e42504000273203485917'
receipt=json.loads(receipt_b)
notes_b=(ROOT/'independent-complete-field-notes.json').read_bytes()
assert sha(notes_b)==receipt['source_first_notes']['sha256']=='bd26ec1e81dc8a83e26a55ab015ec4b0d993e898e6f5ab070ae9db030c50bd22'
own={(x['occurrence_id'],x['language']):x for x in json.loads(notes_b)['readings']}
for x in receipt['batch_files']:
 b=Path(x['path']).read_bytes();assert sha(b)==x['sha256'] and len(b)==x['bytes']
find_b=(ROOT/'independent-boundary-findings-v1.json').read_bytes()
plan_b=(ROOT/'accepted-reviewed-field-plan-v1.json').read_bytes()
assert sha(find_b)=='fb24b7bf48b3ae07b1cd79a4f96871f94d94f8ebfab6e9ead90dedb42b710303'
assert sha(plan_b)=='4ade18cd65ca10054e4e6befdf70424f331ddb68cf915324f22c5eef811877c6'
find=json.loads(find_b);plan={(x['occurrence_id'],x['language']):x for x in json.loads(plan_b)['fields']}
changes={(x['occurrence_id'],x['language']):x for x in find['requested_changes']}
changed_parents={x[0] for x in changes}
assert len(own)==len(plan)==44 and len(changes)==8 and len(changed_parents)==4
root=Path(ae['local_path'])
for _ in Path(ae['path']).parts:root=root.parent
assert root.name=='publish-v2'
sb=(root/a['source_ledger_path']).read_bytes();assert sha(sb)==a['source_ledger_sha256']
assert [json.loads(x) for x in gzip.decompress(sb).splitlines()]==source_rows
archives=[]
for x in om['files']:
 matches=[z['path'] for z in m['files'] if z['sha256']==x['sha256'] and z['bytes']==x['bytes']]
 assert matches,('v1 payload missing from durable final package',x['path'])
 archives.append({'original_path':x['path'],'sha256':x['sha256'],'final_paths':matches})
assert any(x['sha256']==sha(ob) for x in m['files'])
counts=collections.Counter();languages=collections.defaultdict(collections.Counter);checks=[];amended=[]
engine=SourceReviews(root,'deenhindi')
for saved in source_rows:
 oid='deenhindi-'+saved['collection']+':'+saved['number'];d=new_by_id[oid];before=old_by_id[oid]
 assert before['decision']==d['decision']=='register'
 if oid not in changed_parents:
  assert d==before;counts['unchanged_whole_v1_parents']+=1
 else:
  assert {k:v for k,v in d.items() if k not in ('field_reviews','reason')}=={k:v for k,v in before.items() if k not in ('field_reviews','reason')}
 base=importer.canonical_record(saved);original=copy.deepcopy(base)
 result,action=engine.apply(base,saved=saved);assert base==original and action=='register'
 assert d['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))
 for k,v in original.items():
  if k not in ('text','language_versions','review','extraction','content_kind','report_types'):
   assert result.get(k)==v,(oid,k);counts['parent_metadata_leaf_equalities']+=leaf(v)
 assert result['review']['independent_pro_qc']=='not_performed' and result['review']['certified_release_eligible'] is False
 assert result['number']['canonical'] is None
 assert len(original['language_versions'])==len(result['language_versions'])==len(d['field_reviews'])==len(before['field_reviews'])==5
 admitted={};fchecks=[]
 for initial,version,field,prior in zip(original['language_versions'],result['language_versions'],d['field_reviews'],before['field_reviews']):
  lang=initial['language'];text=initial['text'];key=(oid,lang);spans=field['spans'];parts=[]
  assert isinstance(text,str) and text and field['language']==lang
  assert version['id']==initial['id']==field['language_version_id']
  assert text==saved['source_record'][field['source_field']] and sha(text.encode())==field['text_sha256'] and len(text)==field['text_chars']
  assert bool(field['reviewed'])==(key in own)
  assert 'observed_script' not in prior and 'observed_script' not in field
  oldmask={i for s in prior['spans'] for i in range(s['start'],s['end'])};newmask={i for s in spans for i in range(s['start'],s['end'])}
  if key not in changes:
   assert field==prior,(key,'unexpected field mutation');counts['unchanged_v1_complete_field_definitions']+=1
  else:
   assert {k:v for k,v in field.items() if k not in ('spans','reason','action')}=={k:v for k,v in prior.items() if k not in ('spans','reason','action')}
   counts['amended_reviewed_fields']+=1
   restored=newmask-oldmask;assert not oldmask-newmask
   counts['restored_characters']+=len(restored);counts['restored_utf8_bytes']+=sum(len(text[i].encode()) for i in restored)
   if not restored:counts['metadata_only_amended_fields']+=1
   amended.append({'occurrence_id':oid,'language':lang,'kind':changes[key]['kind'],'before_field_sha256':sha(canon(prior)),'after_field_sha256':sha(canon(field)),'restored_positions':sorted(restored),'removed_positions':[],'final_field_reason':field['reason']})
  if field['reviewed']:
   q=own[key];p=plan[key]
   assert sha(canon(prior))==p['before_field_definition_sha256']
   assert [{k:v for k,v in s.items() if k!='reason'} for s in spans]==p['expected_spans'],(key,'accepted semantic span plan mismatch')
   assert sorted(newmask-oldmask)==p['expected_added_positions'] and sorted(oldmask-newmask)==p['expected_removed_positions']
   assert q['text_sha256']==field['text_sha256'] and q['characters']==len(text) and q['utf8_bytes']==len(text.encode())
   assert field['chars_reviewed']==len(text) and field['bytes_reviewed']==len(text.encode())
   for c in (counts,languages[lang]):c['complete_fields_read']+=1;c['characters_read']+=len(text);c['utf8_bytes_read']+=len(text.encode())
  else:
   assert not spans and field['chars_reviewed']==field['bytes_reviewed']==0;counts['unread_context_fields']+=1
  for k,v in initial.items():
   if k not in ('text','source','comments','scope','quotation_status'):
    assert version.get(k)==v,(key,k);counts['language_metadata_leaf_equalities']+=leaf(v)
  for k,v in initial['source'].items():
   assert version['source'].get(k)==v,(key,'source',k);counts['source_metadata_leaf_equalities']+=leaf(v)
  if spans:
   assert field['reviewed'] and version['text']==''.join(text[s['start']:s['end']] for s in spans)
   admitted[lang]=version['text']
   for s in spans:
    a0,b0=s['start'],s['end'];assert sha(text[a0:b0].encode())==s['sha256']
    parts.append((a0,b0,text[a0:b0]));assert s['component_id'] and s['speaker'] and s['report_type'] and s['source_report_family_id']
   for c in (counts,languages[lang]):
    c['admitted_fields']+=1;c['selected_spans']+=len(spans);c['selected_characters']+=len(version['text']);c['selected_utf8_bytes']+=len(version['text'].encode())
   for comp in version['source']['report_component_classifications']:
    members=[s for s in spans if s['component_id']==comp['component_id']]
    assert comp['spans']==[[s['start'],s['end']] for s in members]
    assert all(s['speaker']==comp['speaker_description'] and s['report_type']==comp['report_type'] and s['source_report_family_id']==comp['source_report_family_id'] for s in members)
    counts['typed_source_components']+=1
  else:assert version['text'] is None
  assert not initial.get('comments')
  for comment in version['comments']:
   lo,hi=comment['source_span'];assert comment['text']==text[lo:hi] and sha(text[lo:hi].encode())==comment['source_text_sha256']
   assert comment['scope']=='source_context_not_narration';parts.append((lo,hi,comment['text']))
  pos=0
  for lo,hi,words in sorted(parts):assert lo==pos and lo<hi and text[lo:hi]==words;pos=hi
  assert pos==len(text) and ''.join(words for lo,hi,words in sorted(parts))==text
  counts['lossless_partitions']+=1
  if field['reviewed']:counts['reviewed_context_gaps']+=len(version['comments'])
  fchecks.append({'language':lang,'source_sha256':sha(text.encode()),'reviewed':field['reviewed'],'selected_spans':len(spans),'source_context_parts':len(version['comments']),'lossless':True})
 assert set(admitted)=={'hi','ur'} and result['text']=={'arabic':None,'translation':admitted['hi']}
 counts['register_occurrences']+=1;checks.append({'occurrence_id':oid,'decision':'register','fields':fchecks})
engine.finish()
assert counts['register_occurrences']==22 and counts['lossless_partitions']==110
assert counts['complete_fields_read']==counts['admitted_fields']==44 and counts['unread_context_fields']==66
assert counts['characters_read']==30058 and counts['utf8_bytes_read']==65003
assert counts['restored_characters']==103 and counts['restored_utf8_bytes']==216
assert counts['amended_reviewed_fields']==8 and counts['metadata_only_amended_fields']==2
assert counts['unchanged_v1_complete_field_definitions']==102 and counts['unchanged_whole_v1_parents']==18
spb=(ROOT/'independent-source-verification.json').read_bytes()
assert sha(spb)=='d8264c6714aaf0388170830562a3f88d248b86e006341921b169e472a9c72292' and enc(verify_original_sources())==spb
verify_manifest(m);verify_manifest(om)
report={'schema':'hadith-bank-independent-complete-review-amendment-audit-v2','result':'PASS','source_commit':'17cd396eb858a29162505d545aad556ac73ce9ce','reviewer':'OpenAI assistant /root/queue_audit','primary_manifest_v1_sha256':sha(ob),'primary_manifest_v2_sha256':sha(mb),'active_v1_sha256':sha(oab),'active_v2_sha256':sha(ab),'source_first_reading_receipt_sha256':sha(receipt_b),'independent_source_verification_sha256':sha(spb),'complete_boundary_findings_sha256':sha(find_b),'accepted_plan_sha256':sha(plan_b),'all_frozen_primary_payload_hashes_verified':len(m['files']),'native_SourceReviews_apply_finish':'PASS','counts':dict(counts),'language_coverage':{k:dict(v) for k,v in languages.items()},'exact_eight_field_amendments':amended,'all24_v1_payloads_durably_preserved':archives,'initial_readings_preserved':True,'source_based_refinement':find['refinement_to_immutable_initial_notes'],'source_files_reopened':44,'complete_raw_reparses':22,'all22_original_parent_source_metadata_and_dispositions_preserved':True,'source_wording_changes':0,'original_source_metadata_changes':0,'candidate_mutations':0,'github_writes':0,'source_http_requests':0,'canonical_identity_asserted':False,'independent_pro_qc':'not_performed','open_findings':[],'checks':checks,'code_inputs':{'import_deenhindi':sha(Path(importer.__file__).read_bytes()),'web_source_reviews':sha(Path(sys.modules['web_source_reviews'].__file__).read_bytes())}}
data=enc(report);target=ROOT/'independent-final-v2-audit.json'
if target.exists():assert target.read_bytes()==data
else:target.write_bytes(data)
print(json.dumps({'result':'PASS','report_sha256':sha(data),'bytes':len(data),'counts':dict(counts),'manifest':sha(mb),'active':sha(ab)},indent=2))

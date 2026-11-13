"""Independent source-byte, attribution, metadata and native partition audit."""
from pathlib import Path
import collections,copy,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
OWNER=BASE/'phase16-checkpoint5589-muslim-ibnmajah25-review'
PUBLISHED=OWNER/'publish-v1'
SOURCE=BASE/'phase15-successor-acquisition-monitor/held-evidence'
COMMIT='5589a3ffc3b43c3324ae26f2b6c4d33152834456'
MANIFEST_SHA='ec9239b35946aedf1b3a0bd29d13c9c4b94a6956f644527ab0ab8c37aa6495ca'
ACTIVE_SHA='7d3941ff3ffe97a6ba7dd96b389219a4fb61b85f89210b3f1222da80cb01f403'
READING_SHA='ee7c46ba293881c48bd3d2db92296b68656731ae9aebfcffe8080712573614b9'
INPUT_SHA='690a23138e7f05dfc04e9aebeb9a40644e11d1673f97a25ddc5af4291f6f9b17'
ARTIFACT_SHA='90817d73a72aad32e9faa5f46063cf54946c607fea7aafbd025b6b67208d14ab'
LANGUAGES={'ar':'textArabic','hi':'translationHindi','ur':'translationUrdu','ur-Latn':'translationUrduRoman','en':'translationEnglish'}
COMPONENTS={'ibnmajah:2310':2,'ibnmajah:2349':2,'muslim:2313':2,'muslim:2331':2,
 'muslim:2344':2,'muslim:2352':2,'muslim:2353':2,'muslim:2355':3}
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda o:(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def checked(root,relative):
 p=root/relative
 assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
 assert p.is_file() and p.resolve().is_relative_to(root.resolve())
 assert not any(x.is_symlink() for x in [p,*p.parents] if x.is_relative_to(root))
 return p.read_bytes()
def leaves(a,b):
 assert a==b
 if isinstance(a,dict):return sum(leaves(a[k],b[k]) for k in a)
 if isinstance(a,list):return sum(leaves(x,y) for x,y in zip(a,b,strict=True))
 return 1
def put(root,relative,data):
 p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 return {'path':relative,'bytes':len(data),'sha256':sha(data),'git_blob_sha1':git(data)}

def main():
 config=json.loads((ROOT/'final-candidate-binding.json').read_bytes())
 assert config['all53_complete_source_fields_and_boundaries_independently_assessed'] is True
 assert config['candidate_amendments_requested']==0
 sys.path.insert(0,str(BASE/'hindi-resolve/work/scripts'))
 import import_deenhindi as importer
 import web_source_reviews as reviews
 import web_commentary_quotes as quotes
 assert sha(Path(importer.__file__).read_bytes())=='c2b6df1d243b7e9c695358d9f06221c4cba45e880a1a215e4ef697008ed144d0'
 assert sha(Path(reviews.__file__).read_bytes()+Path(quotes.__file__).read_bytes())=='cc253d0d89d839f79a99e5209824b953fa6ac21be80fdb898a130025cbc7114b'
 mb=(OWNER/'delivery-manifest-v1.json').read_bytes();assert sha(mb)==MANIFEST_SHA
 manifest=json.loads(mb);file_bindings=[]
 for item in manifest['files']:
  data=checked(PUBLISHED,item['path']);assert len(data)==item['bytes'] and sha(data)==item['sha256']
  if 'git_blob_sha1' in item:assert git(data)==item['git_blob_sha1']
  file_bindings.append({'path':item['path'],'bytes':len(data),'sha256':sha(data),'git_blob_sha1':git(data)})
 ab=checked(PUBLISHED,manifest['active_ledger_path']);assert sha(ab)==ACTIVE_SHA==manifest['active_ledger_sha256']
 doc=json.loads(gzip.decompress(ab));assert doc['source_commit']==COMMIT
 records={r['occurrence_id']:r for r in doc['records']};assert len(records)==len(doc['records'])==25
 input_bytes=(ROOT/'input/cohort.jsonl').read_bytes();assert sha(input_bytes)==INPUT_SHA
 keyed=lambda seq:{r['collection']+':'+r['number']:r for r in seq}
 input_rows=keyed(map(json.loads,input_bytes.decode().splitlines()))
 bb=checked(PUBLISHED,doc['source_ledger_path']);assert sha(bb)==doc['source_ledger_sha256']
 plain=gzip.decompress(bb);assert sha(plain)==doc['source_ledger_uncompressed_sha256']
 rows=keyed(map(json.loads,plain.decode().splitlines()));assert rows==input_rows
 artifact_bytes=(SOURCE/'evidence-manifest.json').read_bytes();assert sha(artifact_bytes)==ARTIFACT_SHA
 artifact=json.loads(artifact_bytes);assert artifact['saved_head']==COMMIT
 artifact_rows=keyed(map(json.loads,(SOURCE/'held-source-records.jsonl').read_text().splitlines()))
 assert len(artifact_rows)==217 and all(artifact_rows[k]==v for k,v in rows.items())
 states=json.loads((SOURCE/'held-state-entries.json').read_bytes())
 first_bytes=(ROOT/'complete-independent-readings.json').read_bytes();assert sha(first_bytes)==READING_SHA
 first=json.loads(first_bytes);readings={(r['occurrence_id'].removeprefix('deenhindi-'),r['language']):r for r in first['fields']}
 assert len(readings)==first['complete_fields']==53 and first['characters']==21060 and first['utf8_bytes']==44597
 assert all(r['complete_own_field_read'] and not r['candidate_inspected_before_this_reading'] for r in readings.values())
 native=reviews.SourceReviews(PUBLISHED,'deenhindi');assert set(native.decisions)==set(records)
 totals=collections.Counter();books=collections.defaultdict(collections.Counter)
 source_receipts=[];field_receipts=[];attributions=[]
 for key,row in rows.items():
  identity='deenhindi-'+key;record=records[identity];action='exclude' if key=='muslim:2365' else 'register'
  assert record['decision']==action and record['source_snapshot']==row['snapshot']
  assert record['source_record_sha256']==sha(importer.json_bytes(row['source_record']))
  assert record['source_parsed_path']==row['parsed_path'] and record['source_reference_verbatim']==row['source_reference_verbatim']
  assert record['collection']==row['collection'] and record['number']==row['number']
  assert record['external_canonical_identity'] is None and record['verified_external_reference'] is None
  entry=states[key];verified=[]
  for relative in (row['snapshot']['path'],row['parsed_path']):
   stored=checked(SOURCE/'sources',relative);binding=artifact['files'][relative];body=gzip.decompress(stored)
   assert len(stored)==binding['bytes']==binding['stored_bytes'] and sha(stored)==binding['sha256']==binding['stored_sha256']
   assert git(stored)==binding['git_blob_sha1']
   verified.append({'path':relative,'stored_bytes':len(stored),'stored_sha256':sha(stored),'git_blob_sha1':git(stored),'bytes':len(body),'sha256':sha(body)})
   if relative==row['snapshot']['path']:
    raw=body;assert sha(raw)==row['snapshot']['sha256'] and len(raw)==row['snapshot']['bytes']
   else:
    parsed=body;assert sha(parsed)==entry['parsed']['sha256'] and sha(stored)==entry['parsed']['stored_sha256']
    assert sha(parsed)==record['source_parsed_sha256']
  expected={k:row[k] for k in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')}
  expected['classification']=row['intake_classification'];assert parsed==importer.json_bytes(expected)
  actual,reference=importer.parse_record(raw,row['collection'],row['number'])
  assert actual==row['source_record'] and reference==row['source_reference_verbatim']
  assert sha(importer.json_bytes(actual))==artifact['source_record_sha256'][key]
  source_receipts.append({'id':identity,'exact_reparse':True,'source_record_sha256':sha(importer.json_bytes(actual)),'files':verified})
  totals.update(raw_parsed_files_verified=2,exact_html_reparses=1)
  original=importer.canonical_record(row);before=copy.deepcopy(original);row_before=copy.deepcopy(row)
  after,native_action=native.apply(original,saved=row)
  assert native_action==action and original==before and row==row_before
  for name in set(before)-{'language_versions','text','content_kind','review','report_types','extraction'}:
   totals['metadata_leaf_equalities']+=leaves(before[name],after[name])
  for name in before['extraction']:
   if name!='is_excerpt':totals['metadata_leaf_equalities']+=leaves(before['extraction'][name],after['extraction'][name])
  fields={f['language']:f for f in record['fields']};assert set(fields)==set(LANGUAGES)
  selected={}
  for old,new in zip(before['language_versions'],after['language_versions'],strict=True):
   language=old['language'];text=old['text'];f=fields[language];rk=(key,language)
   assert f['source_field']==LANGUAGES[language] and f['text_sha256']==sha(text.encode())
   assert f['reviewed']==(rk in readings)
   if rk in readings:
    reading=readings[rk];assert reading['text']==text and reading['text_sha256']==sha(text.encode())
    assert f['chars_reviewed']==reading['characters']==len(text)
    assert f['bytes_reviewed']==reading['utf8_bytes']==len(text.encode())
    totals.update(complete_fields_independently_read=1,characters_read=len(text),utf8_bytes_read=len(text.encode()))
   else:assert f['chars_reviewed']==f['bytes_reviewed']==0
   for name in set(old)-{'text','scope','quotation_status','source','comments'}:
    totals['metadata_leaf_equalities']+=leaves(old[name],new[name])
   for name in old['source']:totals['metadata_leaf_equalities']+=leaves(old['source'][name],new['source'][name])
   pieces=[];contexts=[];spans=f['selected_spans']
   for span in spans:
    a,b=span['start'],span['end'];assert 0<=a<b<=len(text) and text[a:b].strip()
    assert sha(text[a:b].encode())==span['sha256'];pieces.append((a,b,text[a:b]))
    totals['selected_spans']+=1;totals['selected_characters']+=b-a
   if spans:
    positions=[[s['start'],s['end']] for s in spans]
    assert new['source']['text_spans']['quotation_spans']==positions
    assert new['text']==''.join(text[a:b] for a,b in positions)
    assert not any('؎' in text[a:b] for a,b in positions)
    selected[language]=new['text'];totals['admitted_fields']+=1
    classification=new['source']['report_component_classifications']
    assert len(classification)==COMPONENTS.get(key,1) and new['source'].get('source_report_count',1)==1
    assert all(c['speaker_description'] and c['report_type'] and c['spans'] for c in classification)
    attributions.append({'id':identity,'language':language,'source_report_families':1,'classifications':classification})
   else:
    assert new['text'] is None;totals['reviewed_context_fields' if f['reviewed'] else 'unread_context_fields']+=1
   assert new['source']['manual_review']['field_reviewed']==f['reviewed']
   for comment in new['comments']:
    a,b=comment['source_span'];assert comment['text']==text[a:b] and comment['source_text_sha256']==sha(text[a:b].encode())
    assert comment['scope']=='source_context_not_narration'
    pieces.append((a,b,comment['text']));contexts.append({'start':a,'end':b,'text':comment['text'],'sha256':comment['source_text_sha256']})
   cursor=0
   for a,b,body in sorted(pieces):assert a==cursor and b>a;cursor=b
   assert cursor==len(text) and ''.join(p[2] for p in sorted(pieces))==text
   totals['lossless_field_partitions']+=1
   if f['reviewed']:field_receipts.append({**readings[rk],'final_field_review':f,'selected_source_spans':[{**s,'text':text[s['start']:s['end']]} for s in spans],'source_context_spans':contexts,'all_boundaries_independently_accepted':True})
  if action=='register':assert after['text']=={'arabic':selected.get('ar'),'translation':selected.get('hi')}
  else:assert after['text']==before['text'] and all(f['reviewed'] for f in fields.values())
  assert after['number']['canonical'] is None and after['review']['independent_pro_qc']=='not_performed'
  assert after['review']['certified_release_eligible'] is False
  totals[action]+=1;totals['source_occurrences']+=1;books[row['collection']][action]+=1
 native.finish()
 assert totals['source_occurrences']==25 and totals['register']==24 and totals['exclude']==1
 assert totals['complete_fields_independently_read']==53 and totals['characters_read']==21060 and totals['utf8_bytes_read']==44597
 assert totals['admitted_fields']==48 and totals['reviewed_context_fields']==5 and totals['unread_context_fields']==72
 assert totals['lossless_field_partitions']==125 and totals['raw_parsed_files_verified']==50 and totals['exact_html_reparses']==25
 out=ROOT/'publish';prefix='reports/web-source-resolution-20261113/checkpoint5589-muslim-ibnmajah25-independent-audit'
 source_report={'status':'PASS','source_commit':COMMIT,'artifact_manifest_sha256':ARTIFACT_SHA,'raw_parsed_files_verified':50,'raw_responses_reparsed':25,'records':source_receipts,'source_http_requests':0}
 put(out,prefix+'/independent-source-verification.json.gz',gzip.compress(enc(source_report),mtime=0))
 (ROOT/'independent-source-verification.json').write_bytes(enc(source_report))
 put(out,prefix+'/complete-independent-readings.json.gz',gzip.compress(first_bytes,mtime=0))
 put(out,prefix+'/independent-source-first-notes.json',(ROOT/'independent-source-first-notes.json').read_bytes())
 put(out,prefix+'/final53-field-boundaries-and-native-partitions.json.gz',gzip.compress(enc(field_receipts),mtime=0))
 put(out,prefix+'/final-native-attributions.json.gz',gzip.compress(enc(attributions),mtime=0))
 put(out,prefix+'/final-candidate-binding.json',(ROOT/'final-candidate-binding.json').read_bytes())
 put(out,prefix+'/audit_peer.py',Path(__file__).read_bytes())
 report={'schema':'hadith-bank-independent-source-review-audit-v1','result':'PASS','source_commit':COMMIT,
  'owner_manifest_sha256':MANIFEST_SHA,'active_ledger_path':manifest['active_ledger_path'],'active_ledger_sha256':ACTIVE_SHA,
  'source_first_reading_receipt_sha256':READING_SHA,'scope':'Independent complete53-field source-first reading, then every candidate boundary/voice, all50 saved source files,25 HTML reparses and native apply/finish.',
  'totals':dict(totals),'by_book':dict(books),'source_only_ids':['deenhindi-muslim:2365'],'all_source_only_nonempty_siblings_read':True,
  'owner_files_verified':file_bindings,'source_baseline_sha256':sha(bb),'open_findings':[],
  'semantic_source_first_refinements':config['semantic_source_first_refinements'],
  'qualifications':['Actual finite variants keep unknown actors and missing context explicit; a bare prepositional replacement stays source-only.','IbnMajah2346 and Muslim2357 retain their own qualified honorific attribution, without outside actor names.','Selected ellipses in2352-2354 remain exact punctuation marking abbreviation; explicit same-as/to-end textual pointers stay source context.','Actual quoted Quran renderings and substantive role/count/time/recipient qualifiers are retained; explicit footnotes and repeated lexical apparatus remain context.'],
  'candidate_mutations':0,'engine_mutations':0,'source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed','certified_release_eligible':False,
  'limits':'This validates the frozen25-parent candidate against its saved source evidence. Complete5589 saved-state history, full repository export, current reader/browser run and actual deployment are separate checks; none is inferred from this review.'}
 report_path='reports/web-source-resolution-20261113/checkpoint5589-muslim-ibnmajah25-independent-audit.json'
 rr=put(out,report_path,enc(report))
 files=[]
 for p in sorted(out.rglob('*')):
  if p.is_file():files.append({'path':p.relative_to(out).as_posix(),'local_path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'git_blob_sha1':git(p.read_bytes())})
 delivery={'schema':'hadith-bank-independent-audit-delivery-v1','result':'PASS','source_commit':COMMIT,'owner_manifest_sha256':MANIFEST_SHA,'active_ledger_sha256':ACTIVE_SHA,'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}
 (ROOT/'delivery-manifest.json').write_bytes(enc(delivery))
 print(json.dumps({'result':'PASS','manifest_sha256':sha(enc(delivery)),'report_sha256':rr['sha256'],'files':len(files),'bytes':delivery['total_bytes'],'totals':dict(totals)},indent=2))
if __name__=='__main__':main()

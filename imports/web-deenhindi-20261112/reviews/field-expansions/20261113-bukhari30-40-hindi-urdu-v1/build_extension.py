"""Serialize40 individually read fields and validate all477 original decisions."""
from pathlib import Path
import collections,copy,gzip,hashlib,json,shutil,sys
from manual_readings import READINGS
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
EXT='20261113-bukhari30-40-hindi-urdu-v1'
EVID=Path('imports/web-deenhindi-20261112/reviews/field-expansions')/EXT
OUT=ROOT/'publish-v1';VALID=ROOT/'validation-repo-v1'
assert not (ROOT/'delivery-manifest-v1.json').exists(),'Candidate already frozen'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def lines(v):return b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() for r in v)
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def read(p):return json.loads(p.read_bytes())
def locate(text,literal):
    assert text.count(literal)==1,('Boundary not unique',literal)
    start=text.index(literal);return start,start+len(literal)
def gaps(text,spans):
    result=[];cursor=0
    for s in spans:
        if cursor<s['start']:result.append((cursor,s['start']))
        cursor=s['end']
    if cursor<len(text):result.append((cursor,len(text)))
    return result

selection=read(ROOT/'selection.json');pin=selection['source_commit']
assert pin=='6b20d4578c85ec2a8fb00bb7a7796f487cde755f'
input_raw=(ROOT/'full-field-reading-input-40.jsonl').read_bytes();assert sha(input_raw)==selection['reading_input_sha256']=='6e37908f2f15ae4da13b650a6a12df2cf5206c0a3e19c71a9c5356288d5b78eb'
inputs=list(map(json.loads,input_raw.splitlines()));targets={(r['occurrence_id'],r['language']):r for r in inputs}
assert len(targets)==40 and {(i.split(':')[1],l) for i,l in targets}==set(READINGS)
own_raw=(ROOT/'source-first-complete-reading.json').read_bytes();assert sha(own_raw)=='e1e3227257c15f235fe717864723874d2b33daa5ecbfa3329d88407a31f7977e'
own=read(ROOT/'source-first-complete-reading.json');own_fields={(r['occurrence_id'],r['language']):r for r in own['fields']}
assert own['all_full_source_fields_read_before_candidate_creation'] and own['complete_fields']==40
proof_raw=(ROOT/'source-verification.json').read_bytes();assert sha(proof_raw)=='1578da644028c7f36683abf2edd3e0357d9f05b4c77c47a8c1dae1f20d41d15b'
proof=read(ROOT/'source-verification.json');assert proof['status']=='PASS' and proof['raw_reparses']==30 and proof['saved_github_files_fully_verified']==60
for row in proof['records']:
    for f in row['files']:
        b=(ROOT/'sources'/f['path']).read_bytes();plain=gzip.decompress(b)
        assert len(b)==f['stored_bytes'] and sha(b)==f['stored_sha256'] and git(b)==f['git_blob_sha1']
        assert len(plain)==f['plain_bytes'] and sha(plain)==f['plain_sha256']
old_raw=(ROOT/'pinned-inputs'/selection['active_ledger_path']).read_bytes();assert sha(old_raw)==selection['active_ledger_sha256']=='925f5b3b70b6b3a23274ab7667b23d8577495c6a313c4cf0a66f786622352864'
queue_raw=(ROOT/'pinned-inputs'/selection['priority_queue_path']).read_bytes();assert sha(queue_raw)==selection['priority_queue_sha256']=='f5fa86ff645098396c7daf978f7491bddff6fd9104f5e50acc72f7d02701a660'
baseline=(ROOT/'pinned-inputs'/selection['source_baseline_path']).read_bytes();assert sha(baseline)==selection['source_baseline_sha256']=='5c9598c1c61cee509155013dde44221de2e17f11bd29d0f475092f2a6e86fb36'
old=json.loads(gzip.decompress(old_raw));new=copy.deepcopy(old)
assert sha(baseline)==old['source_ledger_sha256'] and sha(gzip.decompress(baseline))==old['source_ledger_uncompressed_sha256']
old_rows={r['occurrence_id']:r for r in old['records']};new_rows={r['occurrence_id']:r for r in new['records']};assert len(old_rows)==477
sources={ 'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,(ROOT/'source-ledger-30.jsonl').read_bytes().splitlines())}
assert len(sources)==30 and set(sources)=={i for i,l in targets}
notes=[];changes=[];apparatus=[];parentheses=[];spans_total=0
for (ident,language),item in targets.items():
    number=ident.split(':')[1];spec=READINGS[(number,language)];saved=sources[ident]
    row=new_rows[ident];assert row['decision']=='register' and row['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))==item['source_record_sha256']
    field=next(f for f in row['fields'] if f['language']==language);prior=copy.deepcopy(field)
    assert field['reviewed'] is False and field['decision']=='unreviewed' and not field['selected_spans']
    assert sha(enc(field))==item['current_field_decision_sha256']
    text=saved['source_record'][field['source_field']];assert text==item['text']==own_fields[(ident,language)]['text']
    assert sha(text.encode())==item['text_sha256']==field['text_sha256'] and own_fields[(ident,language)]['complete_field_read']
    assert own_fields[(ident,language)]['reading_note']==spec['note']
    cuts=sorted(locate(text,x) for x in spec.get('context',[]));assert all(a[1]<=b[0] for a,b in zip(cuts,cuts[1:]))
    spans=[];last=0
    for n,part in enumerate(spec.get('segments',[{'start':None,'end':None}]),1):
        a=0 if part['start'] is None else locate(text,part['start'])[0]
        b=len(text) if part['end'] is None else locate(text,part['end'])[0]
        assert 0<=last<=a<b<=len(text);last=b;pieces=[(a,b)]
        for left,right in cuts:
            next_pieces=[]
            for x,y in pieces:
                if y<=left or right<=x:next_pieces.append((x,y))
                else:
                    assert a<=left<right<=b
                    if x<left:next_pieces.append((x,left))
                    if right<y:next_pieces.append((right,y))
            pieces=next_pieces
        for x,y in pieces:
            assert text[x:y].strip()
            spans.append({'start':x,'end':y,'sha256':sha(text[x:y].encode()),'component_id':language+'-report-'+str(n),'source_report_family_id':part.get('source_report_family_id',ident+':report-1'),'report_type':part.get('type',spec['type']),'speaker':part.get('speaker',spec['speaker']),'reason':spec['note']})
    assert spans;context=gaps(text,spans);assert all(any(a<=x<y<=b for a,b in context) for x,y in cuts)
    action='whole' if len(spans)==1 and spans[0]['start']==0 and spans[0]['end']==len(text) else 'excerpts'
    field.update(decision=action,reviewed=True,chars_reviewed=len(text),bytes_reviewed=len(text.encode()),review_scope='complete_current_language_field',review_extension_id=EXT,review_method='complete_own_field_manual_reading_and_exact_span_decisions',reason=spec['note'],selected_spans=spans,report_type=spec['type'],speaker=spec['speaker'],independent_pro_qc='not_performed')
    notes.append({'occurrence_id':ident,'language':language,'source_field':field['source_field'],'version_id':field['version_id'],'complete_field_text':text,'full_field_sha256':sha(text.encode()),'chars_read':len(text),'utf8_bytes_read':len(text.encode()),'complete_own_field_read':True,'semantic_reading':spec['note'],'decision':action,'selected_spans':spans,'retained_context':[{'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode())} for a,b in context]})
    changes.append({'occurrence_id':ident,'language':language,'version_id':field['version_id'],'source_text_sha256':field['text_sha256'],'before_field_decision_sha256':sha(enc(prior)),'after_field_decision_sha256':sha(enc(field)),'before_decision':prior['decision'],'after_decision':action,'parent_disposition_unchanged':True})
    apparatus.extend({'occurrence_id':ident,'language':language,'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode()),'reason':spec['note']} for a,b in context)
    stack=[]
    for index,char in enumerate(text):
        if char=='(':stack.append(index)
        elif char==')' and stack:
            a=stack.pop();b=index+1;coverage=sum(max(0,min(b,s['end'])-max(a,s['start'])) for s in spans)
            assert coverage in (0,b-a),('Partial parenthetical',ident,language,text[a:b])
            parentheses.append({'occurrence_id':ident,'language':language,'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode()),'disposition':'retained_report_qualification_or_honorific' if coverage else 'retained_context','decision_basis':'Individual complete-field reading; parentheses are not an automatic exclusion rule.'})
    assert not stack
    spans_total+=len(spans)
assert len(notes)==40 and sum(n['chars_read'] for n in notes)==26147 and sum(n['utf8_bytes_read'] for n in notes)==51287
notes_raw=gzip.compress(enc({'schema':'hadith-bank-field-reading-extension-v1','extension_id':EXT,'reader':'/root','source_commit':pin,'independent_pro_qc':'not_performed','input_sha256':sha(input_raw),'source_first_receipt_sha256':sha(own_raw),'fields':notes}),mtime=0)
new['field_review_extensions'].append({'extension_id':EXT,'source_commit':pin,'previous_active_ledger':{'path':str(EVID/'previous-review-ledger.json.gz'),'sha256':sha(old_raw)},'reading_notes':{'path':str(EVID/'complete-field-reading-notes.json.gz'),'sha256':sha(notes_raw)},'occurrences':30,'complete_fields_read':40,'complete_fields_by_language':{'hi':10,'ur':30},'already_reviewed_hindi_fields_preserved':20,'existing_record_dispositions_unchanged':True,'all_other_field_decisions_unchanged':True,'independent_pro_qc':'not_performed'})
assert {k:v for k,v in old.items() if k not in ['records','field_review_extensions']}=={k:v for k,v in new.items() if k not in ['records','field_review_extensions']}
assert new['field_review_extensions'][:-1]==old['field_review_extensions']
active_raw=gzip.compress(enc(new),mtime=0);put(OUT/selection['active_ledger_path'],active_raw)
if VALID.exists():shutil.rmtree(VALID)
put(VALID/selection['active_ledger_path'],active_raw);put(VALID/selection['source_baseline_path'],baseline)
engine=SourceReviews(VALID,'deenhindi');assert len(engine.decisions)==477
partitions=untouched_rows=unchanged_fields=parents=languages=scripts=0
for saved in map(json.loads,gzip.decompress(baseline).splitlines()):
    ident='deenhindi-'+saved['collection']+':'+saved['number'];prior=old_rows[ident];decision=new_rows[ident]
    assert {k:v for k,v in prior.items() if k!='fields'}=={k:v for k,v in decision.items() if k!='fields'}
    if ident not in sources:assert decision==prior;untouched_rows+=1
    original=importer.canonical_record(saved);frozen=copy.deepcopy(original);result,action=engine.apply(original,saved=saved)
    assert original==frozen and action=='register'
    for name in ['id','number','narrator','grading','references','source_locator','source','translator','translation_provenance','rights','source_headings']:assert result[name]==frozen[name];parents+=1
    assert len(prior['fields'])==len(decision['fields'])==len(result['language_versions'])==len(frozen['language_versions'])==5
    for of,nf,ov,nv in zip(prior['fields'],decision['fields'],frozen['language_versions'],result['language_versions']):
        key=(ident,nf['language'])
        if key not in targets:assert of==nf;unchanged_fields+=1
        if 'observed_script' in of:assert of['observed_script']==nf['observed_script']==nv['script'] and of.get('source_script_note')==nf.get('source_script_note');scripts+=1
        for name in ['id','language','references','translation_provenance']:assert ov[name]==nv[name];languages+=1
        text=ov['text'];selected=nv['source'].get('text_spans',{}).get('quotation_spans',[])
        assert (nv['text'] or '')==''.join(text[a:b] for a,b in selected)
        parts=[(a,b,text[a:b]) for a,b in selected]
        for c in nv['comments']:
            a,b=c['source_span'];assert c['scope']=='source_context_not_narration' and c['text']==text[a:b] and c['source_text_sha256']==sha(text[a:b].encode());parts.append((a,b,c['text']))
        cursor=0
        for a,b,t in sorted(parts):assert a==cursor and a<b<=len(text) and t==text[a:b];cursor=b
        assert cursor==len(text) and ''.join(t for a,b,t in sorted(parts))==text;partitions+=1
engine.finish();assert partitions==2385 and untouched_rows==447 and unchanged_fields==2345 and scripts==19
queue=list(map(json.loads,gzip.decompress(queue_raw).splitlines()));after=[];removed=[]
for row in queue:
    matches=[f for f in row['fields'] if (row['id'],f['language']) in targets]
    if matches:
        assert len(matches)==len(row['fields']);removed.append(row)
    else:after.append(row)
assert len(removed)==30 and len(after)==3454 and sum(len(r['fields']) for r in after)==6461
counts=collections.Counter(f['language'] for r in after for f in r['fields']);assert counts=={'hi':3310,'ur':3151}
queue_after=gzip.compress(lines(after),mtime=0)
delta={'schema':'hadith-bank-exact-language-priority-queue-delta-v1','source_commit':pin,'extension_id':EXT,'before_sha256':sha(queue_raw),'after_sha256':sha(queue_after),'before_occurrences':3484,'after_occurrences':3454,'before_fields':6501,'after_fields':6461,'after_language_counts':dict(counts),'removed_fields':changes,'removed_occurrence_ids':[r['id'] for r in removed],'remaining_rows_and_order_exact':True,'parent_registration_delta':0,'scope':'This candidate delta removes only the40 actually read fields. A co-published disjoint extension requires an independently verified combined queue.'}
validation={'schema':'hadith-bank-bukhari30-field-extension-native-validation-v1','status':'PASS','source_commit':pin,'active_before_sha256':sha(old_raw),'active_after_sha256':sha(active_raw),'occurrences_extended':30,'complete_fields_read':40,'characters_read':26147,'utf8_bytes_read':51287,'new_fields_by_language':{'hi':10,'ur':30},'admitted_fields':40,'selected_spans':spans_total,'context_gaps':len(apparatus),'all477_parent_dispositions_unchanged':True,'all477_native_apply_finish':'PASS','lossless_partitions':partitions,'untouched_parent_records':untouched_rows,'unchanged_other_field_decisions':unchanged_fields,'existing_hindi_fields_unchanged':20,'preserved_script_corrections':scripts,'parent_metadata_equalities':parents,'language_metadata_equalities':languages,'source_files_verified':60,'raw_reparses':30,'source_first_reading_sha256':sha(own_raw),'source_verification_sha256':sha(proof_raw),'engine_sha256':engine.engine_sha256,'remaining_priority_fields_candidate':6461,'remaining_priority_occurrences_candidate':3454,'independent_pro_qc':'not_performed','source_http_requests':0,'github_writes':0,'source_count_delta':0,'parent_registration_delta':0}
for name,b in [('previous-review-ledger.json.gz',old_raw),('previous-priority-field-queue.jsonl.gz',queue_raw),('candidate-priority-field-queue.jsonl.gz',queue_after),('complete-field-reading-notes.json.gz',notes_raw),('full-field-reading-input-40.jsonl.gz',gzip.compress(input_raw,mtime=0)),('source-ledger-30.jsonl.gz',gzip.compress((ROOT/'source-ledger-30.jsonl').read_bytes(),mtime=0)),('priority-field-queue-delta.json',enc(delta)),('native-validation.json',enc(validation)),('field-decision-delta.json',enc(changes)),('source-apparatus-inventory.json',enc({'context_gaps':apparatus,'parenthetical_inventory':parentheses,'blanket_parenthesis_exclusion':False}))]:put(OUT/EVID/name,b)
for name in ['selection.json','source-first-complete-reading.json','source-verification.json','source-fetch-receipts.json','manual_readings.py','build_extension.py']:put(OUT/EVID/name,(ROOT/name).read_bytes())
# The canonical queue is intentionally left to the publisher's combined delta.
# This exact candidate queue remains archived above for independent review.
files=[]
for p in sorted(x for x in OUT.rglob('*') if x.is_file()):
    b=p.read_bytes();files.append({'path':str(p.relative_to(OUT)),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
manifest={'schema':'hadith-bank-original-language-extension-delivery-v1','status':'PASS','summary':validation,'canonical_queue_publication':'Publisher must compose this exact40-field delta with any independently approved disjoint extension; archived candidate bytes and delta are included.','files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}
(ROOT/'delivery-manifest-v1.json').write_bytes(enc(manifest));print(json.dumps(validation,indent=2));print(json.dumps({'manifest_sha256':sha(enc(manifest)),'files':len(files),'bytes':manifest['total_bytes']},indent=2))

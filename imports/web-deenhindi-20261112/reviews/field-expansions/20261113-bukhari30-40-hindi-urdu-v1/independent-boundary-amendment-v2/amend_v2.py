"""Apply only the ten independently specified apparatus cuts; retain full v1 evidence."""
from pathlib import Path
import copy,gzip,hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
EVID=Path('imports/web-deenhindi-20261112/reviews/field-expansions/20261113-bukhari30-40-hindi-urdu-v1')
AMEND=EVID/'independent-boundary-amendment-v2';OUT=ROOT/'publish-v2';VALID=ROOT/'validation-repo-v2'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def read(p):return json.loads(p.read_bytes())
assert not (ROOT/'delivery-manifest-v2.json').exists()
manifest_raw=(ROOT/'delivery-manifest-v1.json').read_bytes();assert sha(manifest_raw)=='945689866dcc3dbfb52e2b7eb1ca90b9f86ad67a5808380a123902160a656cad'
v1manifest=read(ROOT/'delivery-manifest-v1.json')
for f in v1manifest['files']:
    b=Path(f['local_path']).read_bytes();assert sha(b)==f['sha256'] and git(b)==f['git_blob_sha1'] and len(b)==f['bytes'];put(OUT/f['path'],b)
findings_raw=(WORK/'phase14-original-bukhari30-independent-audit/independent-boundary-findings-v1.json').read_bytes()
assert sha(findings_raw)=='df6f9c19c45a523a7d5e0b9d4f3ed0ebc47241197ba551c3df9d1f34694db7ac'
findings=json.loads(findings_raw);assert len(findings['changes'])==10
selection=read(ROOT/'selection.json');active_path=selection['active_ledger_path']
v1raw=(ROOT/'publish-v1'/active_path).read_bytes();assert sha(v1raw)=='8eb09778ae069c2d6250c40e58c15a112776907be03c3d87f9ef136949542e6d'
v1=json.loads(gzip.decompress(v1raw));v2=copy.deepcopy(v1)
rows={r['occurrence_id']:r for r in v2['records']};v1rows={r['occurrence_id']:r for r in v1['records']}
inputs={(r['occurrence_id'],r['language']):r for r in map(json.loads,(ROOT/'full-field-reading-input-40.jsonl').read_bytes().splitlines())}
reasons={
 ('1180','ur'):'Complete own480-character reading preserves all ten-rakah details, nafl qualification, home locations and dawn sequence. The already stated morning prayer makes the parenthetic fajr term a duplicate lexical label; only that exact label is source context. Ibn Umar and Hafsa remain separately attributed ordered components in one family, distinct from occurrence1181.',
 ('1181','ur'):'Separately read all480 own characters. Preserve the complete ten-rakah routine, nafl qualifier, private dawn interval and Hafsa testimony. Only the duplicate parenthetic fajr lexical equivalent is contextual; the actual morning-prayer and subsequent dawn wording remain. The provider identity and two same-family voices remain separate from1180.',
 ('1200','ur'):'Complete449-character reading retains Zayd prayer-conversation report, the actually printed Arabic revelation quotation and the command of silence with its in-prayer qualification. The exact unsupplied-continuation abbreviation is context rather than Quran quotation. No omitted verse words or named issuer of the passive command are supplied.',
 ('1211','ur'):'Complete871-character historical reading preserves the prayer, horse, unnamed Khariji curse, Abu Barza six-or-seven-or-eight campaigns uncertainty and his observed ease/retrieval explanation. The geographical definition and duplicate parenthetic identity gloss are context. Shuba actual separately voiced identity statement remains selected in the same report family, so no actor is lost or turned into Prophetic speech.',
 ('1223','ur'):'Complete554-character reading retains Abu Hurayra transmission criticism, his actual question, the unnamed participant attendance and failure to recall, and Abu Hurayra stated memory. Only the interpretive testing-purpose parenthesis is context. The rhetorical framing remains; the unspecified surahs stay such-and-such and no motive or missing name is invented.',
 ('1241','ur'):'Complete1280-character reading preserves Aisha farewell account and Ibn Abbas public-address account through Abu Salama as two source-attributed families in one occurrence. Retain every actual event, speech and printed partial Quran quotation with its ellipsis. Only the parenthetical pointer to unsupplied continuation is context; no verse continuation or canonical number is fabricated.',
 ('1242','ur'):'Separately read all1280 own characters and preserve both actual Aisha and Ibn Abbas/AbuSalama historical families, the entire farewell/public-address sequence and printed partial recitation with its ellipsis. Only the unsupplied-continuation pointer is contextual. The identical1241 wording remains a different provider occurrence.',
 ('1341','hi'):'Complete709-character Hindi reading retains its defective chain, printed reporter name and final wording defect. The illness, church, pictures, response and following narrative sentence naming UmmSalama and UmmHabiba and their Abyssinian travel all remain. Only the earlier duplicate parenthetic wife-name gloss moves to context; no actor is lost and no Urdu chain words are imported.',
 ('1341','ur'):'Complete719-character Urdu reading retains its own chain through Aisha, illness, church name and images, head-raising and response. The actual following sentence naming both wives and their Abyssinian travel stays selected; only the earlier duplicate identity gloss is context. The defective Hindi field remains unaltered.',
 ('1362','ur'):'Complete1145-character own reading retains Ali supplied chain, the Baqi gathering, stick movement, all person-or-soul and destiny wording, the actual question and reply, and the printed Arabic recitation. Only its final marker for unsupplied verse continuation is context; quotation delimiters and final punctuation remain exact. No missing verse text or Hindi chain repair is supplied.',
}
assert {(c['id'].split(':')[1],c['language']) for c in findings['changes']}==set(reasons)
amendments=[];removed_chars=removed_bytes=0
for c in findings['changes']:
    key=(c['id'],c['language']);text=inputs[key]['text'];a,b=c['start'],c['end']
    assert sha(text.encode())==c['text_sha256'] and text[a:b]==c['text'] and sha(text[a:b].encode())==c['span_sha256']
    row=rows[c['id']];assert row['source_record_sha256']==c['source_record_sha256']
    f=next(x for x in row['fields'] if x['language']==c['language']);before=copy.deepcopy(f);new_spans=[]
    assert sum(max(0,min(b,s['end'])-max(a,s['start'])) for s in f['selected_spans'])==b-a
    for span in f['selected_spans']:
        x,y=span['start'],span['end']
        pieces=[(x,y)] if y<=a or b<=x else ([(x,a)] if x<a else [])+([(b,y)] if b<y else [])
        for left,right in pieces:
            s=copy.deepcopy(span);s.update(start=left,end=right,sha256=sha(text[left:right].encode()),reason=reasons[(c['id'].split(':')[1],c['language'])]);new_spans.append(s)
    f.update(selected_spans=new_spans,decision='excerpts',reason=reasons[(c['id'].split(':')[1],c['language'])])
    for s in f['selected_spans']:s['reason']=f['reason']
    before_mask={i for s in before['selected_spans'] for i in range(s['start'],s['end'])};after_mask={i for s in new_spans for i in range(s['start'],s['end'])}
    assert before_mask-after_mask==set(range(a,b)) and not after_mask-before_mask
    for name in ['report_type','speaker','reviewed','chars_reviewed','bytes_reviewed','text_sha256']:assert f[name]==before[name]
    amendments.append({**c,'before_field_sha256':sha(enc(before)),'after_field_sha256':sha(enc(f)),'only_exact_requested_positions_changed':True,'final_reason':f['reason']});removed_chars+=b-a;removed_bytes+=len(text[a:b].encode())
assert removed_chars==195
changed_fields=0;unchanged_fields=0;unchanged_parents=0
for prior,after in zip(v1['records'],v2['records']):
    assert {k:v for k,v in prior.items() if k!='fields'}=={k:v for k,v in after.items() if k!='fields'}
    unchanged_parents+=prior==after
    for a,b in zip(prior['fields'],after['fields']):
        if a!=b:changed_fields+=1
        else:unchanged_fields+=1
assert changed_fields==10 and unchanged_fields==2375 and unchanged_parents==468
notes_path=EVID/'complete-field-reading-notes.json.gz';old_notes=(ROOT/'publish-v1'/notes_path).read_bytes();notes=json.loads(gzip.decompress(old_notes))
apparatus=[];parentheses=[]
for n in notes['fields']:
    key=(n['occurrence_id'],n['language']);text=n['complete_field_text'];f=next(x for x in rows[key[0]]['fields'] if x['language']==key[1]);spans=f['selected_spans']
    if (key[0].split(':')[1],key[1]) in reasons:n['initial_source_first_reading_note']=n['semantic_reading']
    n.update(semantic_reading=f['reason'],decision=f['decision'],selected_spans=spans)
    context=[];cursor=0
    for s in spans:
        if cursor<s['start']:context.append((cursor,s['start']))
        cursor=s['end']
    if cursor<len(text):context.append((cursor,len(text)))
    n['retained_context']=[{'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode())} for a,b in context]
    apparatus.extend({'occurrence_id':key[0],'language':key[1],**c,'reason':f['reason']} for c in n['retained_context'])
    stack=[]
    for i,char in enumerate(text):
        if char=='(':stack.append(i)
        elif char==')' and stack:
            a=stack.pop();b=i+1;coverage=sum(max(0,min(b,s['end'])-max(a,s['start'])) for s in spans);assert coverage in [0,b-a]
            parentheses.append({'occurrence_id':key[0],'language':key[1],'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode()),'disposition':'retained_report_qualification_or_honorific' if coverage else 'retained_context'})
    assert not stack
notes['independent_boundary_amendment']={'findings_sha256':sha(findings_raw),'exact_changed_fields':10,'source_first_reading_receipt_unchanged':True}
notes_raw=gzip.compress(enc(notes),mtime=0);put(OUT/notes_path,notes_raw)
v2['field_review_extensions'][-1]['reading_notes']['sha256']=sha(notes_raw)
v2['field_review_extensions'][-1]['independent_boundary_amendment']={'path':str(AMEND/'amendment-receipt.json'),'previous_active_sha256':sha(v1raw),'exact_changed_fields':10,'source_characters_moved_to_context':195}
new_raw=gzip.compress(enc(v2),mtime=0);put(OUT/active_path,new_raw)
if VALID.exists():shutil.rmtree(VALID)
baseline=(ROOT/'pinned-inputs'/selection['source_baseline_path']).read_bytes();put(VALID/active_path,new_raw);put(VALID/selection['source_baseline_path'],baseline)
engine=SourceReviews(VALID,'deenhindi');partitions=0
original=json.loads(gzip.decompress((ROOT/'pinned-inputs'/active_path).read_bytes()));original_rows={r['occurrence_id']:r for r in original['records']}
for saved in map(json.loads,gzip.decompress(baseline).splitlines()):
    ident='deenhindi-'+saved['collection']+':'+saved['number'];before=importer.canonical_record(saved);frozen=copy.deepcopy(before);result,action=engine.apply(before,saved=saved);assert before==frozen and action=='register'
    for k in ['id','number','narrator','grading','references','source_locator','source','translator','translation_provenance','rights','source_headings']:assert result[k]==frozen[k]
    for old_field,new_field,old_version,new_version in zip(original_rows[ident]['fields'],rows[ident]['fields'],frozen['language_versions'],result['language_versions']):
        if (ident,new_field['language']) not in inputs:assert old_field==new_field
        for k in ['id','language','references','translation_provenance']:assert old_version[k]==new_version[k]
        text=old_version['text'];selected=new_version['source'].get('text_spans',{}).get('quotation_spans',[]);assert (new_version['text'] or '')==''.join(text[a:b] for a,b in selected)
        parts=[(a,b,text[a:b]) for a,b in selected]+[(c['source_span'][0],c['source_span'][1],c['text']) for c in new_version['comments']];cursor=0
        for a,b,t in sorted(parts):assert a==cursor and t==text[a:b];cursor=b
        assert cursor==len(text) and ''.join(t for a,b,t in sorted(parts))==text;partitions+=1
engine.finish();assert partitions==2385 and len(apparatus)==16
receipt={'schema':'hadith-bank-independent-boundary-amendment-v2','status':'PASS','base_manifest_sha256':sha(manifest_raw),'base_active_sha256':sha(v1raw),'final_active_sha256':sha(new_raw),'independent_findings_sha256':sha(findings_raw),'source_first_reading_receipt_unchanged':True,'changed_fields':10,'other_fields_exact':2375,'other_complete_parent_rows_exact':468,'parent_dispositions_and_metadata_exact':True,'characters_moved_to_context':removed_chars,'utf8_bytes_moved_to_context':removed_bytes,'characters_added':0,'native477_apply_finish':'PASS','lossless_partitions':partitions,'field_changes':amendments,'scope':'Only individually inspected source apparatus; actual recitations, actor statements, scope conditions and all source bytes remain. No automatic parenthesis or duplication rule.'}
for name,b in [('previous-active-review.json.gz',v1raw),('previous-complete-field-reading-notes.json.gz',old_notes),('previous-native-validation.json',(ROOT/'publish-v1'/EVID/'native-validation.json').read_bytes()),('previous-source-apparatus-inventory.json',(ROOT/'publish-v1'/EVID/'source-apparatus-inventory.json').read_bytes()),('previous-field-decision-delta.json',(ROOT/'publish-v1'/EVID/'field-decision-delta.json').read_bytes()),('previous-delivery-manifest.json',manifest_raw),('independent-findings-v1.json',findings_raw),('amendment-receipt.json',enc(receipt)),('amend_v2.py',Path(__file__).read_bytes())]:put(OUT/AMEND/name,b)
put(OUT/EVID/'source-apparatus-inventory.json',enc({'context_gaps':apparatus,'parenthetical_inventory':parentheses,'blanket_parenthesis_exclusion':False}))
delta=read(OUT/EVID/'field-decision-delta.json')
for d in delta:
    f=next(x for x in rows[d['occurrence_id']]['fields'] if x['language']==d['language']);d['after_field_decision_sha256']=sha(enc(f));d['after_decision']=f['decision']
put(OUT/EVID/'field-decision-delta.json',enc(delta))
validation=read(OUT/EVID/'native-validation.json');validation.update(active_after_sha256=sha(new_raw),selected_spans=sum(len(n['selected_spans']) for n in notes['fields']),context_gaps=len(apparatus),independent_boundary_amendment_receipt_sha256=sha(enc(receipt)),candidate_revision='v2')
put(OUT/EVID/'native-validation.json',enc(validation))
files=[]
for p in sorted(x for x in OUT.rglob('*') if x.is_file()):
    b=p.read_bytes();files.append({'path':str(p.relative_to(OUT)),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
manifest={**v1manifest,'summary':validation,'candidate_revision':'v2','independent_boundary_amendment':receipt,'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}
(ROOT/'delivery-manifest-v2.json').write_bytes(enc(manifest));print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(manifest)),'active_sha256':sha(new_raw),'files':len(files),'bytes':manifest['total_bytes'],'exact_context_characters_added':removed_chars,'exact_context_utf8_bytes_added':removed_bytes,'selected_spans':validation['selected_spans'],'context_gaps':len(apparatus),'other_field_definitions_exact':2375,'native_partitions':partitions},indent=2))

"""Freeze already authored and native-validated source-review evidence; no fetching."""
from pathlib import Path
import collections,gzip,hashlib,json,runpy
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'publish'
REV='imports/web-deenhindi-20261112/reviews'
COHORT='checkpointc2ab-abudawud-tirmidhi20-20261113'
PREFIX=REV+'/'+COHORT
ACTIVE=REV+'/source-review-'+COHORT+'.json.gz'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(path,b):
    p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    return {'path':path,'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
def parentheses(text):
    stack=[];out=[]
    for i,c in enumerate(text):
        if c=='(':stack.append(i)
        elif c==')':
            assert stack;start=stack.pop();out.append((start,i+1))
    assert not stack
    return sorted(out)
HONORIFICS={
 '(Radi Allahu Anhu)','(Sallallahu Alaihi Wasallam)','(रदी अल्लाहू अन्हु)',
 '(सल्लल्लाहु अलैहि वसल्लम)','(रज़ियल्लाहु अन्हा)','(रदी अल्लाहु अन्हु)',
 '(रदी अल्लाहु अन्हा)','(रदियल्लाहु अन्हुम)','(रदियल्लाहु अन्हु)',
 '(रज़ि अल्लाहु अन्हु)','(रज़ियल्लाहु अन्हु)'}
RETAINED={
 '(जी में)':'The group’s own inner-thought framing is part of the actual reported question.',
 '(तो यह क्योंकर दुरुस्त होगा)':'Finite rhetorical predicate of the group’s reported inner question.',
 '( جی میں )':'The group’s own inner-thought framing is part of the actual reported question.',
 '( تو یہ کیونکر درست ہو گا )':'Finite rhetorical predicate of the group’s reported inner question.',
 '(अपने अक़्द में रहने या न रहने का)':'Actual source-supplied domain of the reported marital choice.',
 '( اپنے عقد میں رہنے یا نہ رہنے کا )':'Actual source-supplied domain of the reported marital choice.',
 '(आप यह दे दीजिये)':'Finite give-this-basket request supplied inside the woman’s actual dialogue.',
 '( آپ یہ دے دیجئیے )':'Finite give-this-basket request supplied inside the woman’s actual dialogue.',
 '(तो उनसे कहा जाएगा)':'Address connective within the source’s supplied scripture rendering; the literal verse locator remains separate context.',
 '( تو ان سے کہا جائے گا )':'Address connective within the source’s supplied scripture rendering; the literal verse locator remains separate context.',
 '( میرے والد )':'Source-provided father relationship qualifying the named actor; no external identification is inferred.',
 '(रात को)':'Source-supplied time qualification of the actual sleeping statement.',
 '(और जब वह सुबह को उठेगा)':'Finite temporal condition supplied in the reported withdrawal statement.',
 '( رات کو )':'Source-supplied time qualification of the actual sleeping statement.',
 '( اور جب وہ صبح کو اٹھے گا )':'Finite temporal condition supplied in the reported withdrawal statement.',
 '(यह उसका ठिकाना है)':'Actual supplied translation of the quoted recitation, not a chapter/verse locator.',
 '(हाथ की उंगलियों से)':'Instrument of the source’s actual narrated gesture.',
 '( ہاتھ کی انگلیوں سے )':'Instrument of the source’s actual narrated gesture.',
 '(रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम))':'Source-supplied identification of the advisor in Ahban’s narrated report, retained as actor attribution.',
 '( رسول اللہ صلی اللہ علیہ وسلم )':'Source-supplied identification of the advisor in Ahban’s narrated report, retained as actor attribution.',
 '(गुज़रे हुए साल से)':'Actual comparison object restricting the reported claim.',
 '( گزرے ہوئے سال سے )':'Actual comparison object restricting the reported claim.'}
def main():
    active=(OUT/ACTIVE).read_bytes()
    assert sha(active)=='0abfafac0c086155db3f38564a75f0f9c93f72e54dec7021c875f29967747186'
    ledger=json.loads(gzip.decompress(active))
    rows={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,gzip.decompress((OUT/ledger['source_ledger_path']).read_bytes()).splitlines())}
    first=(ROOT/'complete-source-first-readings.json').read_bytes()
    reads=json.loads(first);notes={(r['id'],r['language']):r for r in reads['fields']}
    parts=json.loads(gzip.decompress((OUT/PREFIX/'field-partitions.json.gz').read_bytes()))
    partitions={r['id']:r for r in parts}
    readings=[];parenthetical=[];counts=collections.Counter()
    for record in ledger['records']:
        for field in record['field_reviews']:
            identity,lang=record['id'],field['language'];text=rows[identity]['source_record'][field['source_field']]
            mask={i for s in field['spans'] for i in range(s['start'],s['end'])}
            assert field['text_sha256']==sha(text.encode())==notes[(identity,lang)]['source_text_sha256']
            assert len(text)==field['chars_reviewed']==notes[(identity,lang)]['characters']
            assert not any('؎' in text[s['start']:s['end']] for s in field['spans'])
            contexts=[{**p,'text':text[p['start']:p['end']]} for p in partitions[identity+':'+lang]['parts'] if p['role']=='context']
            readings.append({**notes[(identity,lang)],'complete_source_text':text,'selected_spans':field['spans'],
                             'retained_context':contexts,'observed_script':field.get('observed_script'),
                             'source_script_note':field.get('source_script_note')})
            for a,b in parentheses(text):
                positions=set(range(a,b));literal=text[a:b]
                if positions<=mask:
                    if literal in HONORIFICS:reason='Printed honorific formula retained unchanged.';category='honorific';counts['selected_honorific_parentheses']+=1
                    else:
                        assert literal in RETAINED,(identity,lang,literal)
                        reason=RETAINED[literal];category='individually_read_narrative_qualification';counts['selected_narrative_parentheses']+=1
                    parenthetical.append({'id':identity,'language':lang,'source_text_sha256':sha(text.encode()),
                       'start':a,'end':b,'text':literal,'sha256':sha(literal.encode()),'category':category,'reason':reason})
            counts.update(complete_fields_read=1,characters_read=len(text),utf8_bytes_read=len(text.encode()))
    assert counts['complete_fields_read']==40 and counts['characters_read']==25926 and counts['utf8_bytes_read']==54943
    assert counts['selected_honorific_parentheses']==70 and counts['selected_narrative_parentheses']==22
    put(PREFIX+'/complete-field-readings-and-boundaries.json.gz',gzip.compress(enc({'source_checkpoint':ledger['source_checkpoint'],
        'active_ledger_sha256':sha(active),'fields':readings}),mtime=0))
    put(PREFIX+'/complete-source-first-readings.json.gz',gzip.compress(first,mtime=0))
    put(PREFIX+'/retained-source-parentheses.json',enc({'scope':'Exact individual source ranges already completely read. This is an evidence inventory, not a rule approving arbitrary parentheses. Nested source parentheses are both inventoried.',
        'counts':dict(counts),'items':parenthetical,'selected_footnote_markers':0}))
    # Preserve provisional notes before the root's explicit actor-attribution clarification.
    before_script=(ROOT/'pre-independent-attribution/manual_readings.py').read_bytes()
    before_readings=(ROOT/'pre-independent-attribution/complete-source-first-readings.json').read_bytes()
    put(PREFIX+'/before-actor-qualification/manual_readings.py.gz',gzip.compress(before_script,mtime=0))
    put(PREFIX+'/before-actor-qualification/complete-source-first-readings.json.gz',gzip.compress(before_readings,mtime=0))
    before={r['key']:r for r in runpy.run_path(str(ROOT/'pre-independent-attribution/manual_readings.py'))['records']}
    after={r['key']:r for r in runpy.run_path(str(ROOT/'manual_readings.py'))['records']}
    changes=[]
    for key in after:
        assert {k:v for k,v in before[key].items() if k!='fields'}=={k:v for k,v in after[key].items() if k!='fields'}
        for lang in ('hi','ur'):
            if before[key]['fields'][lang]!=after[key]['fields'][lang]:
                changes.append({'id':'deenhindi-'+key,'language':lang,'before':before[key]['fields'][lang],
                                'after':after[key]['fields'][lang]})
    assert {(r['id'],r['language']) for r in changes}=={
        ('deenhindi-tirmidhi:2203','hi'),('deenhindi-tirmidhi:2203','ur'),('deenhindi-tirmidhi:2161','ur')}
    put(PREFIX+'/actor-qualification-refinements.json',enc({'status':'Applied before first frozen primary delivery.',
        'basis':'Independent root complete-field reading identified T2203 own-language advisor identification as actual attribution. The same source-actor principle retains T2161 Urdu father relationship. No source words or parent decision changed.',
        'initial_notes_sha256':sha(before_readings),'initial_manual_specification_sha256':sha(before_script),
        'changes':changes,'all37_other_field_specifications_identical':True}))
    validation=json.loads((OUT/PREFIX/'validation.json').read_bytes())
    source=json.loads((OUT/PREFIX/'source-evidence.json').read_bytes())
    context=json.loads((OUT/PREFIX/'explicit-source-apparatus-context.json').read_bytes())
    counts['explicit_literal_context_cuts']=context['literal_omissions']
    assert context['literal_omissions']==19
    report={'schema':'hadith-bank-source-bound-primary-review-v1','result':'PASS',
       'source_checkpoint':ledger['source_checkpoint'],'source_worker_run_id':source['source_worker_run_id'],
       'cohort':'20 new93 occurrences:11 Abu Dawud and9 Tirmidhi; distinct from the previous114 held cohort.',
       'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(active),
       'source_baseline_path':ledger['source_ledger_path'],'source_baseline_sha256':ledger['source_ledger_sha256'],
       'actual_reading':dict(counts),'native_and_saved_source_validation':validation['totals'],
       'by_book':validation['by_book'],'by_language':validation['by_language'],
       'parent_decisions':{'register':20,'source_only':0,'unresolved':0},
       'source_http_requests':0,'github_writes':0,'engine_changes':False,
       'scope_exceptions':[
        {'id':'deenhindi-abudawud:823','decision':'Hindi identity retained, individually verified Latin-script transliteration correction with visible source note.'},
        {'id':'deenhindi-abudawud:2166','decision':'Damaged Hindi ending preserved; no Urdu continuation imported.'},
        {'id':'deenhindi-abudawud:2188','decision':'Finite Ibn Abbas ruling fragment and Urdu-only named Ibn Mubarak-to-Mamar question have separate actual attributions. No omitted predecessor, answer or transmitter identity is filled. Bare biography/grading tail remains source context.'},
        {'id':'deenhindi-abudawud:2191','decision':'Finite oath addition admitted with ultimate speaker unspecified; not promoted to a Prophetic saying.'},
        {'id':'deenhindi-abudawud:2213','decision':'Case/dialogue and Salama return appraisal are two ordered components of one source episode family; sixty-sa and source uncertainty unchanged.'},
        {'id':'deenhindi-abudawud:2214','decision':'Woman’s account and unnamed narrator’s sixty-sa measure share one case family. Actual recitation/translation and finite basket request retained; compiler deduction/identity notes remain context.'},
        {'id':'deenhindi-tirmidhi:2179','decision':'Four source-attributed ordered components across three specified families: trust descent; withdrawal with Hudhayfa’s explicitly printed gesture/prediction; his personal trading memory. This is one provider occurrence, not an external canonical report assignment.'},
        {'id':'deenhindi-tirmidhi:2198','decision':'Hasan Basri’s own named explanatory saying under expanded source scope. Different own Hindi/Urdu object lists remain exact; no ultimate speaker for the internally quoted hadith wording is supplied.'},
        {'id':'deenhindi-tirmidhi:2203','decision':'Own-source Messenger identification retained with Ahban’s relay; no external canonical identity inferred.'}],
       'formal_independent_pro_qc':'not_performed','certified_release_eligible':False,
       'limits':'Primary complete-field review and native saved-source validation. Root independent source-first reading and semantic comparison have been reported, but its final hash-bound source/native audit remains a separate deliverable. Full repository export, current-main reader/browser checks and deployment remain separate gates.'}
    put('reports/web-source-resolution-20261113/checkpointc2ab-abudawud-tirmidhi20-primary-review.json',enc(report))
    put(PREFIX+'/package_review.py',Path(__file__).read_bytes())
    files=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name!='portable-manifest.json':
            b=p.read_bytes();files.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
    portable={'schema':'hadith-bank-portable-review-package-v1','source_checkpoint':ledger['source_checkpoint'],
              'active_ledger_sha256':sha(active),'files':files,'total_files':len(files),'total_bytes':sum(x['bytes'] for x in files)}
    put(PREFIX+'/portable-manifest.json',enc(portable))
    files=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            b=p.read_bytes();files.append({'path':p.relative_to(OUT).as_posix(),'local_path':str(p),
              'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
    manifest={'schema':'hadith-bank-source-review-delivery-v1','source_checkpoint':ledger['source_checkpoint'],
       'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(active),'source_baseline_sha256':ledger['source_ledger_sha256'],
       'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files),'files':files}
    dest=ROOT/'delivery-manifest.json';dest.write_bytes(enc(manifest))
    print(json.dumps({'status':'frozen','manifest_sha256':sha(dest.read_bytes()),'files':len(files),'bytes':manifest['total_bytes'],
                      'active_sha256':sha(active),'actual_reading':dict(counts)}))
if __name__=='__main__':main()


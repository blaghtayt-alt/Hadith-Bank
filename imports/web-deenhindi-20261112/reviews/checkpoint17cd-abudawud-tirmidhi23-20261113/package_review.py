#!/usr/bin/env python3
"""Freeze exact primary23 review bytes, explicit apparatus inventory and native evidence."""
import collections,gzip,hashlib,json,re
from pathlib import Path
from manual_boundaries_v2 import records as instructions
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'publish-v2'
COHORT='checkpoint17cd-abudawud-tirmidhi23-20261113'
PREFIX='imports/web-deenhindi-20261112/reviews/'+COHORT
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-'+COHORT+'.json.gz'
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(path,data):
    p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    return {'path':path,'bytes':len(data),'sha256':sha(data),'git_blob_sha1':blob(data)}

RETAINED={
 ('abudawud:2624','hi',"(ए ईमान वालो! फ़रमाँबरदारी करो अल्लाह त'आला की और फ़रमाँबरदारी करो रसूल (सल्लल्लाहु अलैहि वसल्लम) की और अपने में से इख़्तियार वालों की)"):'Actual complete source translation of the expressly quoted verse, including its printed honorific; no missing verse text is added.',
 ('abudawud:2624','hi','(कैस बिन अदि)'):'Source-printed participant-name/lineage qualification in the claimed revelation occasion, preserved without external identity repair.',
 ('abudawud:2624','ur','( عبداللہ بن حذافہ )'):'Source-printed identification of the participant called Abdullah; material attribution is preserved without harmonizing the adjacent name wording.',
 ('abudawud:2643','hi','(इसके बावजूद)'):'Narrative contrast between the confession and subsequent killing, as this source renders the account.',
 ('abudawud:2643','hi','(तलवार के डर से)'):'Actual repeated intention-domain alternative within the reported question; removing it would weaken the source restriction.',
 ('abudawud:2643','hi','(बल्कि इस्लाम के लिए)'):'Actual source-rendered alternative intention in the reported question; no external or verbatim-historical assertion is made.',
 ('abudawud:2643','ur','( اس کے باوجود )'):'Source-rendered narrative contrast between the confession and subsequent killing.',
 ('abudawud:2643','ur','( تلوار کے ڈر سے )'):'The stated fear-of-sword alternative restricts the question’s intention domain.',
 ('abudawud:2643','ur','( بلکہ اسلام کے لیے )'):'The source expressly renders this alternative intention within the question; preserve its qualification.',
 ('abudawud:2649','hi','(काफ़िरों के ग़लबा की)'):'Material complaint domain supplied in the source, not a detached word definition.',
 ('abudawud:2649','hi','(ये सुन कर)'):'Actual hearing/response narrative transition.',
 ('abudawud:2649','ur','( کافروں کے غلبہ کی )'):'Material source-rendered object/domain of the complaint.',
 ('abudawud:2649','ur','( یہ سن کر )'):'Actual hearing/response transition within the narrated encounter.',
 ('abudawud:2654','hi','(जब लोगों को मालूम हुआ के ये जासूस है)'):'Finite source-rendered discovery/participant assessment causing the pursuit; preserve its attribution to the account.',
 ('abudawud:2654','ur','( جب لوگوں کو معلوم ہوا کہ یہ جاسوس ہے )'):'Finite discovery/participant assessment in the narrated causal sequence, qualified as the source’s rendering.',
 ('abudawud:2690','hi','(काफिरों)'):'Material object/participant restriction within the source’s supplied verse rendering; the defective surrounding translation remains exact.',
 ('abudawud:2690','ur','( کافروں کا )'):'Material object restriction in the actual supplied rendering, not an external completion.',
 ('tirmidhi:2665','hi','(इब्तिदा-इ-इस्लाम में)'):'Material temporal restriction on the reported writing request/refusal.',
 ('tirmidhi:2665','hi','(हदीथ)'):'Material object scope specifying the writing request; no unrestricted all-knowledge rule is substituted.',
 ('tirmidhi:2665','ur','( ابتداء اسلام میں )'):'The source’s explicit early-Islam temporal restriction on the event.',
 ('tirmidhi:2665','ur','( حدیث )'):'The source’s explicit hadith-writing object restriction.',
 ('tirmidhi:2680','ur','( کہیں بھی )'):'Material universal domain of the negative scholar comparison.',
 ('tirmidhi:2690','hi','(दिल में)'):'Material inner-speech qualification distinguishing the reported response from audible permission.',
 ('tirmidhi:2690','hi','(मज़ीद)'):'Actual additional-waiting sequence qualification.',
 ('tirmidhi:2690','hi','(दिल में कहा)'):'Finite inner-speech attribution qualification of the third response.',
 ('tirmidhi:2690','hi','(इजाज़त तलबी)'):'Source rendering of the actual quoted Arabic/transliterated permission-seeking wording.',
 ('tirmidhi:2690','hi','(यह सुन कर)'):'Narrated hearing/response transition after the bounded embedded instruction.',
 ('tirmidhi:2690','hi','(अबू सईद)'):'Material identification of the otherwise ambiguous visitor in the final testimony scene.',
 ('tirmidhi:2690','ur','( دل میں )'):'Material inner-speech qualification distinguishing the response from audible permission.',
 ('tirmidhi:2690','ur','( مزید )'):'Actual additional-waiting sequence qualification.',
 ('tirmidhi:2690','ur','( دل میں کہا )'):'Finite inner-speech attribution qualification of the third response.',
 ('tirmidhi:2690','ur','( اجازت طلبی )'):'Source rendering of the expressly quoted permission-seeking wording.',
 ('tirmidhi:2690','ur','( یہ سن کر )'):'Narrated hearing/response transition following the embedded instruction.',
 ('tirmidhi:2690','ur','( ابوسعید )'):'Material actor identification for the final visitor/testimony scene.',
 ('tirmidhi:2694','hi','(वह पहल करेगा)'):'Finite source-rendered answer predicate completing the greeting question; not a claim of verbatim historical parenthetical wording.',
 ('tirmidhi:2694','ur','( وہ پہل کرے گا )'):'Finite source-rendered predicate in the answer, preserved with its attribution limits.',
}

RETAINED.update({('abudawud:2645', 'hi', '(यानी इस्लाम और कुफ़्र की)'): 'The parenthetical Islam/kufr words specify the source-rendered referents of both fires. Preserve that material subject/domain qualification within the actual reply, explicitly qualified as this provider rendering rather than independently certified verbatim Prophetic wording.', ('abudawud:2645', 'ur', '( یعنی اسلام اور کفر کی )'): 'Preserve the source-rendered Islam/kufr referents of both fires as material reply scope. Keep compiler transmission criticism and note markers as context, and do not claim that this explanatory wording is independently certified verbatim speech.', ('abudawud:2658', 'hi', '(यानि शिकस्त खा कर इधर उधर भाग खड़े हुए)'): 'Defeat and fleeing here and there are substantive finite historical circumstances in this source rendering, beyond the damaged scattering word. Preserve that action/sequence qualification while leaving the plural participant unidentified and every printed defect unchanged.', ('abudawud:2658', 'ur', '( یعنی شکست کھا کر ادھر ادھر بھاگ کھڑے ہوئے )'): 'The source adds a finite defeat-and-flight circumstance, not only an interchangeable lexical label. Preserve it with a source-rendering qualification, without resolving which group fled from another version or external history.'})

def main():
    assert not (ROOT/'delivery-manifest-v2.json').exists()
    raw=(OUT/ACTIVE).read_bytes();assert sha(raw)=='df5f95b418a90dbb02dec25cf930e2162e9b17aa85af217df6b67c9be6a5be54'
    doc=json.loads(gzip.decompress(raw));v=json.loads((OUT/PREFIX/'validation.json').read_bytes());totals=v['totals']
    assert totals['source_occurrences']==totals['register']==23 and totals.get('exclude',0)==0
    assert (totals['complete_fields_read'],totals['admitted_language_fields'],totals.get('read_context_fields',0),totals['unread_context_fields'])==(46,46,0,69)
    assert totals['quotation_spans']==71 and totals['selected_characters']==21113
    fields=json.loads(gzip.decompress((OUT/PREFIX/'complete-field-readings-and-boundaries.json.gz').read_bytes()))['fields'];assert len(fields)==46
    rules={(r['key'],lang):f for r in instructions for lang,f in r['fields'].items()}
    inventory=[];used=set();counts=collections.Counter();views=[];separators=[]
    for f in fields:
        text=f['text'];key=(f['occurrence_id'].removeprefix('deenhindi-'),f['language']);rule=rules[key]
        mask={i for s in f['selected_spans'] for i in range(s['start'],s['end'])}
        assert all(s['text'].strip() and '؎' not in s['text'] for s in f['selected_spans'])
        assert not any(re.search(r'(?:سورۃ|सौराह)\s*[^()]{0,24}:',s['text']) for s in f['selected_spans'])
        stack=[]
        for i,char in enumerate(text):
            if char=='(':stack.append(i)
            elif char==')':
                assert stack;a=stack.pop();literal=text[a:i+1]
                if not set(range(a,i+1))<=mask:continue
                specific=key+(literal,)
                if specific in RETAINED:
                    reason=RETAINED[specific];used.add(specific);category='individually_read_material_scope_or_quotation';counts['material_scopes_or_quotations']+=1
                else:
                    assert re.fullmatch(r'\(\s*(?:सल्लल्लाहु|रज़ियल्लाहु|रज़ियल्लाहु|रदि अल्लाहु|रदी अल्लाहु|صلی اللہ|رضی (?:اللہ|الله)|ﷺ)[^()]*\)',literal),(specific,literal)
                    reason='Exact printed honorific retained without normalization.';category='source_honorific';counts['honorifics']+=1
                inventory.append({'id':f['occurrence_id'],'language':f['language'],'field_sha256':f['text_sha256'],'start':a,'end':i+1,'text':literal,'sha256':sha(literal.encode()),'category':category,'reason':reason})
        assert not stack
        base=set()
        for s in rule['spans']:
            a=0 if s['from'] is None else text.index(s['from']);b=len(text) if s['to'] is None else text.index(s['to'],a);base.update(range(a,b))
        literal_cuts=set()
        for cut in rule['omit_source_context']:
            a=0
            for _ in range(cut['expected_count']):
                a=text.index(cut['text'],a);b=a+len(cut['text']);literal_cuts.update(range(a,b));a=b
        extras=sorted(base-mask-literal_cuts)
        groups=[]
        for i in extras:
            if groups and groups[-1][1]==i:groups[-1][1]=i+1
            else:groups.append([i,i+1])
        for a,b in groups:
            assert not text[a:b].strip()
            separators.append({'id':f['occurrence_id'],'language':f['language'],'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode()),'reason':'Isolated whitespace between individually excluded source apparatus, preserved as context instead of a whitespace-only quotation.'})
        views.append({'id':f['occurrence_id'],'language':f['language'],'text':text,'reason':f['actual_field_review']['reason'],'selected_spans':f['selected_spans'],'retained_context':f['retained_context']})
    assert used==set(RETAINED) and counts['material_scopes_or_quotations']==42
    cuts=json.loads((OUT/PREFIX/'explicit-source-apparatus-context.json').read_bytes());assert cuts['literal_omissions']==20
    put(PREFIX+'/retained-source-parentheses.json',enc({'scope':'All balanced selected parentheses, including nested complete verse translations. Non-honorific reasons were authored individually after complete own-field reading; this inventory is not an automatic admission rule.','counts':dict(counts),'items':inventory,'selected_footnote_markers':0,'selected_explicit_verse_locator_labels':0,'isolated_context_separators':separators}))
    (ROOT/'boundary-view-v2.json').write_bytes(enc(views))
    original=(ROOT/'input/full-field-reading-input-46.jsonl').read_bytes();assert sha(original)=='1c6567cef512392b28923d0ab271219e07e89d01b723daa87605deacb346f93f'
    put(PREFIX+'/original-full-field-reading-input-46.jsonl.gz',gzip.compress(original,mtime=0))
    put(PREFIX+'/original-source-verification.json',(ROOT/'source-verification.json').read_bytes())
    put(PREFIX+'/original-partition-source-verification.json',(ROOT/'input/source-verification.json').read_bytes())
    put(PREFIX+'/original-partition-delivery-manifest.json',(ROOT/'input/original-partition-delivery-manifest.json').read_bytes())
    for name in ('freeze_source_first.py','prepare_originals.py'):put(PREFIX+'/'+name,(ROOT/name).read_bytes())
    report={'revision':'v2 after exact independent scope and compiler-commentary refinements; all v1 bytes and initial source-first judgments archived','amendment_receipt_path':PREFIX+'/independent-source-scope-v2/amendment-receipt.json','schema':'hadith-bank-source-bound-primary-review-v1','result':'PASS','source_commit':doc['source_checkpoint'],'cohort':'Exactly23 new17cd occurrences:17 AbuDawud and6 Tirmidhi, disjoint from the other three assigned new85 groups.','source_worker_run_id':43473810778,'artifact_id':14064254681,'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(raw),'source_baseline_path':doc['source_ledger_path'],'source_baseline_sha256':doc['source_ledger_sha256'],'source_first_receipt_sha256':'429027e9525d6ce2e4965262523a3c7f20181b425251c864f01fe79f539345ff','source_first_notes_sha256':'ec61368ae08341d30a624049b8ee835aaba21a71991fe64f908b9444876094d3','actual_readings':{'full_fields':46,'characters':24000,'utf8_bytes':51211,'admitted':46,'reviewed_context_only':0,'unread_siblings':69,'empty_siblings':0},'dispositions':{'registered':23,'source_only':0,'unresolved':0},'native_validation':v,'literal_context_cuts_inside_components':20,'retained_parentheses':dict(counts),'isolated_context_separator_characters':sum(s['end']-s['start'] for s in separators),'source_files_reopened':46,'exact_raw_reparses':23,'scope_qualifications':[
        'Abu2630 retains only the supplied finite campaign observation; Abu2674 retains its actual commission and abbreviated if-you-find condition, with no invented consequent or unnamed-person identities. Both same-meaning pointers remain context.',
        'Abu2698 preserves the main returning-actor account and the explicit other-version Khalid clause as separate components of one source report family; the differing actors are not reconciled.',
        'T2622 retains the actual Companion-view report under Abdullah ibn Shaqiq. The complete appended Abu Musab doctrinal/legal ruling, explicitly heard by Tirmidhi, is preserved as attributed compiler legal commentary. This source-role determination follows the owner rule rather than severity, speaker date or a Prophetic-only restriction. Hindi’s absent repentance contrast remains unfilled; the initial broader selection and its reasons remain archived with the explicit reconsideration.',
        'T2680’s later named-scholar identifications, grading and genealogy interpret its anonymous referent and remain full source context. T2665’s route discussion and Abu2696’s compiler chronology likewise remain context.',
        'T2690 preserves the reception/proof dialogue, bounded embedded Prophetic instruction and resumed testimony as three ordered components in one account family. Inner-speech, waiting, hearing and visitor-identity scopes remain source-rendered and visibly qualified.',
        'Actual quoted scripture and supplied translations remain with their attributed event. Explicit verse locators and omitted-remainder pointers are context; absent verse wording is never completed.',
        'Source-rendered participant, temporal, object, alternative-intention and answer-predicate qualifications remain exact without claims that their parentheses are verbatim historical speech. Independently identified lexical synonyms and apparatus remain context.',
        'All names, defects, source-local numbers, grades, references, credits, scripts and raw/parsed bytes remain preserved. No sibling language was read or admitted in this packet, and no canonical identity or translation was generated.'
    ],'peer_notes_inspected_before_primary_freeze':False,'source_http_requests':0,'github_writes':0,'shared_engine_changes':0,'independent_pro_qc':'not_performed','certified_release_eligible':False,'limitations':'Primary complete own-field review and local native/source preservation only. Independent second reading, combined repository export and actual deployment remain separate gates.'}
    put('reports/web-source-resolution-20261113/checkpoint17cd-abudawud-tirmidhi23-primary-review.json',enc(report))
    put(PREFIX+'/package_review.py',Path(__file__).read_bytes())
    def files(local=False):
        result=[]
        for p in sorted(OUT.rglob('*')):
            if not p.is_file() or (not local and p.relative_to(OUT).as_posix()==PREFIX+'/portable-manifest.json'):continue
            b=p.read_bytes();f={'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':blob(b)}
            if local:f['local_path']=str(p)
            result.append(f)
        return result
    fs=files();put(PREFIX+'/portable-manifest.json',enc({'schema':'hadith-bank-portable-review-package-v1','source_commit':doc['source_checkpoint'],'active_ledger_sha256':sha(raw),'files':fs,'total_files':len(fs),'total_bytes':sum(f['bytes'] for f in fs)}))
    fs=files(True);m={'schema':'hadith-bank-source-review-delivery-v1','source_commit':doc['source_checkpoint'],'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(raw),'source_baseline_sha256':doc['source_ledger_sha256'],'files':fs,'total_files':len(fs),'total_bytes':sum(f['bytes'] for f in fs)}
    mb=enc(m);(ROOT/'delivery-manifest-v2.json').write_bytes(mb)
    print(json.dumps({'status':'FROZEN','manifest_sha256':sha(mb),'active_ledger_sha256':sha(raw),'files':len(fs),'bytes':m['total_bytes'],'actual_readings':report['actual_readings'],'dispositions':report['dispositions'],'retained_parentheses':dict(counts),'isolated_separator_characters':report['isolated_context_separator_characters']},indent=2))

if __name__=='__main__':main()

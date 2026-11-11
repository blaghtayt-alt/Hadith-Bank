#!/usr/bin/env python3
"""Remove separable editorial material while retaining source hadith occurrences.

The primary extraction remains immutable audit evidence. This file creates the
commentary-free integration payload and an exact annotation-removal ledger.
"""
from pathlib import Path
import json,re,hashlib,unicodedata,copy

ROOT=Path(__file__).resolve().parent
ps={p['paragraph_index']:p for p in map(json.loads,(ROOT/'source-paragraphs.jsonl').open())}
raw=json.loads((ROOT/'records-primary.json').read_text())
SYMS={'\uf049':'سبحانه وتعالى','\uf072':'ﷺ','\uf074':'رضي الله عنه','\uf079':'رضي الله عنهم','\uf075':'عليه السلام','\uf055':'عز وجل'}
CT={'ج':'صلى الله عليه وسلم','س':'رضي الله عنه','ب':'رضي الله عنهما','ل':'رضي الله عنها','/':'رحمه الله','÷':'عليه السلام','ش':'رضي الله عنهم','†':'عليهم السلام','‡':'عليهم السلام','إ':'عليهما السلام','أ':'جل جلاله'}
FONT_SOURCE='https://hadithmv.github.io/tools/textEditor'
FONT_FILE=ROOT.parent/'font-evidence/hadithmv-fonts.html'
FONT_PROOF_FILE=ROOT.parent/'font-evidence/font-decoding-evidence.json'
font_evidence={'url':FONT_SOURCE,'sha256':hashlib.sha256(FONT_FILE.read_bytes()).hexdigest() if FONT_FILE.exists() else None,
               'mapping':{f'U+{ord(k):04X}':v for k,v in SYMS.items()},
               'ctraditional_mapping':CT,'ctraditional_evidence_file_sha256':hashlib.sha256(FONT_PROOF_FILE.read_bytes()).hexdigest() if FONT_PROOF_FILE.exists() else None,
               'scope':'AGA Arabesque w:sym codes and explicit CTraditional Arabic runs only; raw OOXML tokens preserved; ordinary Arabic text is unchanged'}

def decoded_range(i,start,end):
    p=ps[i];out='';cursor=start
    for token in p['tokens']:
        a=max(start,token['start']);b=min(end,token['end'])
        if a>=b:continue
        if cursor<a:out+=p['text'][cursor:a]
        val=p['text'][a:b]
        if token['kind']=='sym' and token.get('font')=='AGA Arabesque':val=SYMS.get(val,val)
        elif token['kind']=='t' and any('CTraditional Arabic'==str(f) for f in token['fonts'].values()):
            val=''.join(CT.get(c,c) for c in val)
        out+=val;cursor=b
    if cursor<end:out+=p['text'][cursor:end]
    return out

def decode_paragraph(i):return decoded_range(i,0,len(ps[i]['text']))

def display(t,indices=None):
    if t is None:return None
    if indices:
        lines=[]
        for line in t.split('\n'):
            replacement=None
            for i in indices:
                p=ps[i]['text'];start=p.find(line)
                if start>=0:
                    replacement=decoded_range(i,start,start+len(line));break
            lines.append(replacement if replacement is not None else line)
        t='\n'.join(lines)
    for a,b in SYMS.items():t=t.replace(a,b)
    return t

def dump(name,obj):
    (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def jsonl(name,items):
    with (ROOT/name).open('w',encoding='utf8') as f:
        for x in items:f.write(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n')

def normmap(t):
    out='';indices=[]
    for i,c in enumerate(t):
        if unicodedata.combining(c) or c=='ـ':continue
        out+=c;indices.append(i)
    return out,indices

def norm(t):return normmap(t)[0]

num_re=re.compile(r'^\s*([0-9۰-۹٠-٩]+)\s*(?:[-–.]\s*|(?=[و«]))')
removed=[];attributions=[]
manual_drop={
    529,991,1204,1328,1621,1773,2424,2494,2495,2498,2499,2500,2501,2502,2503,
    2536,2537,2722,3810,3811,3812,3813,3815,5988,6658,
    8096,8106,8107,8245,8281,8311,8314,8541,8551,8554,8698,8791,9029,9234,
    8258,8259,
    9556,9557,9558,9559,9560,9561,9562,9563,9618,9621,9706,9991,
}
# The numbered entry 335 is complete at p2493 (Arabic) and p2497 (Persian).
# A separate explicitly quoted report follows; it is extracted separately below.

# These complete, explicitly delimited definitions/interpretations are translator
# comments embedded in narration paragraphs. Compare against the paired Arabic;
# do not remove ordinary translation wording or explanations spoken by a narrator.
persian_editorial_spans={
    2914:[' – مراد هر مرد و زن است –'],
    3085:[' "یعنی شباهت به آفتاب پرستان می‌شود، زیرا آنان در این اوقات آفتاب را پرستش می‌کنند. والله اعلم"'],
    3277:[' – گیاهی معروف و خوش بو است –'],
    3900:[' – خراج این است که سید به غلامش بگوید روزانه بمن اینقدر پول بده و بقیه برای خودت است - .'],
    5106:[' – سخنی که از آن خیر آخرت متصور نیست –'],
    5705:[' (مراد از آن چیز بزرگ و بلند است، مانند کوه و پشتهء ریگی و ساختمان)'],
    6064:[' مراد از باطل شدن عمل، باطل شدن ثواب آنست (یعنی ثواب عملش باطل می‌شود)'],
    7533:[' (مراد از درود گفتن خدا فرستادن رحمت از جانب اوست)'],
    9517:[' شرحش قبلا گذشت.'],
}

def log_removed(rid,i,text,reason):
    if text.strip():removed.append({'record_id':rid,'paragraph_index':i,'text':text,'reason':reason})

def clean_ar(rid,i,t,first=False):
    original=t
    if first:
        m=num_re.match(t)
        if m:t=t[m.end():]
        n,im=normmap(t)
        # Numbered ordinal/chapter narration introducers are editorial labels.
        m=re.match(r'^\s*«?\s*(?:(?:وأما الأحاديث،?\s*)?(?:ف?الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|الحادي عشر|الثاني عشر|الثالث عشر|الرابع عشر|الخامس عشر|السادس عشر|السابع عشر|الثامن عشر|التاسع عشر|العشرون)\s*[:：،]\s*)',n)
        if m:
            cut=im[m.end()-1]+1
            log_removed(rid,i,t[:cut],'source_enumeration_not_narration')
            t=t[cut:]
    n,im=normmap(t)
    # A collection attribution or grade following a completed quotation is metadata.
    m=re.search(r'(?P<citation>(?:(?:حديث|حدیث)\s+(?:حسن|صحيح|صحیح)[^«»]{0,35}\s+)?\b(?:متفق\s+عل|رواه\b|رواها\b|رواهما\b))',n)
    if m:
        cut=im[m.start('citation')]
        # Leading collection labels may introduce a real alternative narration.
        if cut<5:
            return t
        tail=t[cut:]
        # Occasionally an additional variant follows the attribution in one paragraph.
        nt,it=normmap(tail)
        vm=re.search(r'(?:وفي رواية|وفی روایة|وفي روایة|وفی رواية|ورواه|ورواهما|وزاد)\b',nt)
        if vm and vm.start()>0 and any(x in tail[it[vm.start()]:] for x in ['«','قال','قالت']):
            vi=it[vm.start()]
            attributions.append({'record_id':rid,'paragraph_index':i,'text':tail[:vi].strip()})
            log_removed(rid,i,tail[:vi],'printed_attribution_moved_to_metadata')
            t=t[:cut].rstrip()+'\n'+clean_ar(rid,i,tail[vi:])
        else:
            attributions.append({'record_id':rid,'paragraph_index':i,'text':tail.strip()})
            log_removed(rid,i,tail,'printed_attribution_and_detached_editorial_tail')
            t=t[:cut].rstrip()
    return t

# Exact, detached editorial spans embedded after variants in otherwise useful paragraphs.
span_trims={
    1147:(' وهو بمعناه:',None),
    7918:(' بالثاء المثلثة',None),
    8253:(' وهو تفسير',None),
    8607:(' يعني:',None),
    8611:(' یعنی',None),
    9161:(' جمع طاغوت',None),
    3177:(' وقد سبق',None),
    4477:(' وذكر الحديث',None),
    4479:(' که این حدیث را قبلاً',None),
    2625:(' ابوداود این حدیث',None),
    3243:('، و این لفظ مسلم است',None),
    5705:(' مسلم / این حدیث',None),
    5708:(' و ابو داود این حدیث',None),
    5992:(' این حدیث را مسلم',None),
    8061:(' رواه البخاري',None),
    8063:(' این حدیث را بخاری',None),
    9189:(' این حدیث را بخاری',None),
}

# Pronunciation instructions and detached author cross-references are editorial,
# while explanatory parentheticals inside the translated narration are preserved.
normalized_removals={
    677:['بضم النون وفتح الجيم'],
    1078:['بكسر السين المهملة وفتحها'],
    1824:['بضم الخاء المعجمة'],
    2555:['بضم الهمزة وفتح السين'],
    2602:['بفتح الحاء المهملة وإسكان الثاء المثلثة'],
    2699:['وهو «بضم الهمزة وفتح السين المهملة»'],
    3068:['بفتح العين والباء'],
    3300:['«بكسر الشين والخاء المشددة المعجمتين»'],
    3539:['بفتح التاء المثناة فوق وإسكان الغين المعجمة وكسر اللام'],
    3889:['بكسر السين المهملة وفتحها'],
    7829:['­ بضم الخاء المعجمة ­'],
    8211:['وقد سبق في باب التوبة.'],
}

def printed_citations(rec):
    citations=[]
    marker=re.compile(r'(?:(?:حديث|حدیث)\s+(?:حسن|صحيح|صحیح)[^«»]{0,35}?)?\b(?:رواه|رواها|رواهما)\b|\bمتفق\s+(?:عليه|علیه|على\s+صحته)|(?:وفي\s+رواية|وفی\s+روایة|وفي\s+روایة)|(?:و?قد\s+)?ذكره\s+(?:مسلم|البخاري|الحاكم)')
    collection_patterns=[('sahih-bukhari',r'البخاري|البخاری|بخاري|بخاری'),('sahih-muslim',r'\bمسلم\b'),('jami-tirmidhi',r'الترمذي|الترمذی'),('sunan-abu-dawud',r'(?:أبو|أبي|ابو|ابی)\s+داود'),('sunan-nasai',r'النسائ[يیى]'),('sunan-ibn-majah',r'ابن\s+ماج[ةه]'),('muwatta-malik',r'مالك|مالک'),('musnad-ahmad',r'أحمد|احمد')]
    for p in rec['source_components']:
        if not p['role'].startswith('arabic_'):continue
        t=p['text'];n,im=normmap(t);prior_end=-1
        for m in marker.finditer(n):
            a=m.start()
            if a<prior_end:continue
            # A reference ends before narration/lexical explanation restarts.
            end=len(n)
            suffix=n[m.end():]
            stop=re.search(r'[.\n]|(?:[،,]\s*)?(?:ومعناه|معناه|وهو تفسير|وقد سبق|فهذا|فهذه|وذكره|وفي رواية|وفی روایة|وقال:\s*معنى|وفي روايتهما قال)|(?::\s*«)',suffix)
            if stop:end=m.end()+stop.start()
            # If a variant directly proceeds to its matn, preserve only its source label.
            q=n.find('«',m.end())
            if 0<=q<end:end=q
            # Bound any unexpected long span to a genuine citation introduction.
            if end-a>220:
                stop2=re.search(r'(?:\sعن\s|\sقال\s|\sقالت\s)',n[m.end():end])
                if stop2:end=m.end()+stop2.start()
            if end<=a:continue
            aa=im[a];bb=im[end-1]+1;rawtail=t[aa:bb].strip()
            if len(rawtail)>500:continue
            tailnorm=norm(rawtail);collections=[code for code,pat in collection_patterns if re.search(pat,tailnorm)]
            if re.search(r'متفق\s+(?:عليه|علیه|على\s+صحته)',tailnorm):collections=sorted(set(collections+['sahih-bukhari','sahih-muslim']))
            citations.append({'text_as_printed':display(rawtail,[p['paragraph_index']]),'collection_ids':collections,
                'hadith_number':None,'numbering_system':None,'scope':{'paragraph_index':p['paragraph_index'],'source_character_start':aa,'source_character_end':bb},
                'evidence':'printed source attribution; no external canonical matching asserted'})
            prior_end=end
    return citations

def printed_grades(rec):
    statements=[]
    pat=re.compile(r'(?:(?:قال\s+(?:الترمذي|الترمذی|الحاكم|الحاکم)|وقال)\s*:?\s*)?(?:حديث|حدیث)\s+(?:حسن\s+صحيح|حسن\s+صحیح|حسن|صحيح|صحیح|غريب|غریب|ضعيف|ضعیف)(?:\s+(?:غريب|غریب|صحيح|صحیح|حسن))?')
    for p in rec['source_components']:
        if not p['role'].startswith('arabic_'):continue
        t=p['text'];n,im=normmap(t)
        for m in pat.finditer(n):
            a=im[m.start()];b=im[m.end()-1]+1
            statements.append({'text_as_printed':display(t[a:b],[p['paragraph_index']]),
                               'scope':{'paragraph_index':p['paragraph_index'],'source_character_start':a,'source_character_end':b},
                               'grade_application':'printed source statement; no additional chain or clause scope is inferred'})
    return statements

primary=[]
for rec in raw:
    rid=rec['id'];out=copy.deepcopy(rec);ars=[];fas=[];kept=[]
    for p in rec['source_components']:
        i=p['paragraph_index'];role=p['role'];t=decode_paragraph(i)
        if role in ('arabic_editorial_note','persian_translator_commentary') or i in manual_drop:
            log_removed(rid,i,t,'separable_editorial_commentary_or_cross_reference')
            continue
        if role=='blank_paragraph':continue
        # A separately cited alternative at entry356 is a real narration; its
        # framing and detached comments on the chain belong in metadata.
        if i==2561:
            q=re.search('«([^«»]*)»',t);assert q
            log_removed(rid,i,t[:q.start()]+t[q.end():],'variant_source_label_and_lexical_explanation')
            t=q.group(0)
        elif i==2623:
            q=re.search('«([^«»]*)»',t);assert q
            log_removed(rid,i,t[:q.start()]+t[q.end():],'editorial_framing_around_preserved_alternative')
            t=q.group(0)
        elif i==2626:
            a=t.index('و از عایشه');b=t.index(' و حاکم')
            log_removed(rid,i,t[:a]+t[b:],'editorial_framing_around_preserved_alternative')
            t=t[a:b]
        elif i==4602:
            nt,it=normmap(t);a=nt.index('الذي سبق');b=nt.index('قام رسول',a)
            aa=it[a];bb=it[b];log_removed(rid,i,t[aa:bb],'author_cross_reference');t=t[:aa]+t[bb:]
        elif i==4603:
            a=t.index('گفت که: ')+len('گفت که: ');b=t.index(' و حدیث را')
            log_removed(rid,i,t[:a]+t[b:],'author_cross_reference');t=t[a:b]
        elif i==8085:
            nt,it=normmap(t);a=nt.index('وفي بعضها')
            aa=it[a];log_removed(rid,i,t[:aa],'collection_attribution_moved_to_metadata');t=t[aa:]
        elif i==8087:
            a=t.index(' این حدیث را بخاری');b=t.index(' و در بعضی آمده',a)
            log_removed(rid,i,t[a:b],'collection_attribution_moved_to_metadata');t=t[:a]+t[b:]
        if i in span_trims:
            phrase,_=span_trims[i];nt,it=normmap(t);np=norm(phrase)
            # Font decoding changes only the explicit source glyph, not wording.
            np=np.replace('مسلم /','مسلم رحمه الله')
            pos=nt.find(np)
            if pos>=0:
                cut=it[pos];log_removed(rid,i,t[cut:],'detached_lexical_explanation_after_variant');t=t[:cut]
        if role=='arabic_source_text':
            for phrases in normalized_removals.values():
                for phrase in phrases:
                    n,im=normmap(t);needle=norm(phrase);pos=n.find(needle)
                    if pos>=0:
                        a=im[pos];b=im[pos+len(needle)-1]+1
                        log_removed(rid,i,t[a:b],'narrator_pronunciation_or_editorial_cross_reference')
                        t=t[:a]+t[b:]
            t=clean_ar(rid,i,t,i==rec['source_locator']['arabic_start'])
            if t.strip():ars.append(t)
        elif role=='persian_source_translation':
            for phrase in persian_editorial_spans.get(i,[]):
                assert t.count(phrase)==1,(rid,i,phrase)
                log_removed(rid,i,phrase,'detached_translator_explanation_inside_translation')
                t=t.replace(phrase,'',1)
            if i==rec['source_locator']['translation_start']:
                m=num_re.match(t)
                if m:t=t[m.end():]
            if t.strip():fas.append(t)
        else:raise AssertionError((rid,role))
        kept.append({'paragraph_index':i,'role':role,'text':display(t)})
    out['text']={'arabic':display('\n'.join(ars)),'translation':display('\n'.join(fas))}
    out.pop('commentary');out.pop('doctrinal_notes');out.pop('source_components')
    # Do not place source paragraphs containing side notes back into a visible reference field.
    exact_citations=printed_citations(rec)
    out['references']['original_collections']=[{k:v for k,v in c.items() if k!='text_as_printed'} for c in exact_citations if c['collection_ids']]
    out['references']['attributions_as_printed']=exact_citations
    out['references']['grading_as_printed']=printed_grades(rec)
    out['source_text_segments']=kept
    out['source_headings']=[{k:display(v,[h['paragraph_index']]) if isinstance(v,str) else v for k,v in h.items()} for h in out['source_headings']]
    out['narrator']['as_printed']=display(out['narrator']['as_printed'],[rec['source_locator']['arabic_start']])
    out['font_decoding']='evidenced AGA Arabesque and explicit CTraditional Arabic run mappings; exact raw tokens retained in audit'
    out['authenticity']={'grade':None,'grader':None,'basis':'No new overall grade is inferred from compilation membership.',
                        'source_attributions_and_grades':[c for c in exact_citations if re.search(r'حديث|حدیث|متفق',norm(c['text_as_printed']))]+out['references']['grading_as_printed']}
    assert out['text']['arabic'] and out['text']['translation'],rid
    primary.append(out)

def text(i):return ps[i]['text']
def between(i,a,b=None):
    s=text(i);start=s.index(a)+len(a);end=s.index(b,start) if b else len(s)
    return s[start:end]
def quote(i,index=0):
    return re.findall('«([^«»]*)»',text(i))[index]
def cut_before(s,needle):return s[:s.index(needle)]

anc=[]
def add(key,indices,ar=None,fa=None,kind='explicit_hadith_quotation',parent=None,narrator=None,collections=None,grade=None):
    assert ar or fa,key
    loc={'file':ps[0].get('file','tarjomeye-farsi-reyaz-al-salehin-heravi-Word.docx'),'part':'word/document.xml','paragraph_indices':indices,'page':None}
    item={'id':'fa-riyadh-heravi-extra-'+key,'language':'fa','record_type':'hadith_quote',
          'occurrence_kind':kind,'collection':'riyadh-al-salihin','book_title':'ترجمه فارسی ریاض الصالحین',
          'edition_id':'fa-riyadh-heravi-1394-digital','source_local_number':None,'local_sequence':None,
          'translator':'عبد الله خاموش هروی','text':{'arabic':display(ar,indices),'translation':display(fa,indices)},
          'content_kind':kind,
          'narrator':{'as_printed':narrator,'identification':'printed_source_only' if narrator else None},'isnad':None,
          'references':{'original_collections':collections or [],'canonical_numbers':None},'footnotes':[],
          'source_locator':loc,'parent_record_id':parent,
          'provenance':{'translation_method':'human','translation_method_basis':'Named translator printed in source front matter','input_kind':'native_docx_text','source_website_as_printed':'www.aqeedeh.com','extraction':'exact explicitly attributed quotation; surrounding commentary excluded'},
          'authenticity':{'grade':grade,'grader':None,'basis':'Source explicitly attributes the quotation; authenticity and canonical mapping not newly established.'}}
    # Every quote must be an exact substring of its source paragraphs before font decoding.
    joined='\n'.join(text(i) for i in indices)
    for lang,txt in [('ar',ar),('fa',fa)]:
        if txt and txt not in joined:
            # Multi-paragraph text may use only a start/end slice from each source paragraph.
            assert all(part in joined for part in txt.split('\n')),(key,lang,txt)
    anc.append(item)

# Four explicit narrated quotations in the author's translated introduction.
for j,i in enumerate([494,496,498,500],1):add(f'intro-{j:02}',[i],fa=text(i).strip())
# Repeated textual occurrences in chapter introductions remain distinct.
add('p1067',[1067,1068],ar=quote(1067),kind='hadith_quote_fragment')
add('p1495',[1495,1497],ar=between(1495,'«',' وَقَدْ'),fa=quote(1497),narrator='عایشه')
add('p2808',[2808,2810],ar=quote(2808),kind='hadith_quote_fragment',narrator='أَبی هریرة')
add('p2809',[2809,2811],ar=quote(2809),kind='hadith_quote_fragment',narrator='سعد بن أَبی وقاص')
add('p5713-a',[5713],ar=quote(5713,0),kind='hadith_quote_fragment')
add('p5713-b',[5713],ar=quote(5713,1),kind='hadith_quote_fragment')
add('p6360-a',[6360,6361],ar=between(6360,'«','، وحدیث'),fa=between(6361,'«',' و حدیث'),narrator='ابن عمر',kind='hadith_quote_fragment')
add('p6360-b',[6360,6361],ar=quote(6360),fa=between(6361,'که ','»').split('که ')[-1],narrator='عبد الله بن مغفل',kind='hadith_quote_fragment')
add('p6363',[6363,6364],ar=between(6363,'أَنَّهُ ','»'),fa=between(6364,'که ','»'),narrator='ابن عمر',kind='hadith_quote_fragment')
add('p8357',[8357,8363],ar=quote(8357),fa=between(8363,'که گفت: '),narrator='أم كلثوم',collections=[{'collection_ids':['sahih-bukhari','sahih-muslim'],'hadith_number':None,'basis':'متفق عليه printed at p8357'}])
add('p8358',[8358,8364,8365],ar=quote(8358),fa=between(8364,'که ')+'\n'+text(8365),narrator='أم كلثوم',collections=[{'collection_ids':['sahih-muslim'],'hadith_number':None,'basis':'Muslim attribution printed at p8358'}])
# Eleven explicit quoted fragments and one stated action in the chapter introduction.
qa=re.findall('«([^«»]*)»',text(8429))
fa_parts=[
    between(8431,'رسول الله \uf072 ',' و هم'),
    'و هم سودخوار،',
    between(8432,'فرمود: '),
    between(8433,'فرمود: '),
    between(8434,'فرمود \uf075: '),
    between(8435,'فرمود: '),
    between(8436,'فرمود: '),
    between(8437,'فرمود: ',' و این'),
    between(8437,'وهم فرمود: '),
    between(8438,'و اینکه \uf075 ',' و همهء'),
]
assert len(qa)==10,len(qa)
for j,a in enumerate(qa):add(f'p8429-{j+1:02}',[8429,8431,8432,8433,8434,8435,8436,8437,8438],ar=a,fa=fa_parts[j],kind='hadith_quote_fragment')
# The source reports cursing image-makers in narration rather than a direct matn quotation.
add('p8429-action',[8429,8431],ar='وأنَّهُ لَعَنَ المُصَوِّرین',fa='و مصوران را نیز لعنت نمود.',kind='reported_prophetic_action')
# Clearly delimited hadith quotations inside the excluded side notes.
add('p0521',[521],ar=between(521,'چنانچه در حدیث دیگر آمده: ',' (مترجم)'),kind='attributed_hadith_quote',parent='fa-riyadh-heravi-0001')
add('p0847',[847],fa=between(847,'حدیث دیگری نیز آمده است که: ',' (مترجم)'),kind='attributed_hadith_quote',parent='fa-riyadh-heravi-0058')
add('p1326',[1326],ar=between(1326,'در حدیث دیگر آمده: ',' یعنی'),fa=between(1326,'یعنی ',' زیرا'),kind='attributed_hadith_quote',parent='fa-riyadh-heravi-0131')
add('p1383',[1383],ar=quote(1383,0),fa=quote(1383,1),kind='attributed_hadith_quote',parent='fa-riyadh-heravi-0141')
for j in [0,1]:add(f'p1600-{j+1}',[1600],ar=quote(1600,j),kind='attributed_hadith_quote',parent='fa-riyadh-heravi-0168')
add('p2199',[2199],ar=between(2199,'(المرأة',' )') if '(المرأة' in text(2199) and ' )' in text(2199) else 'المرأة کالضلع',kind='hadith_quote_fragment',parent='fa-riyadh-heravi-0273')
add('p2495',[2495,2498,2499,2500,2501,2502,2503],ar=cut_before(text(2495),' وذكر تَمامَ الحديث.'),fa=between(2498,'وی گفته: ')+'\n'+'\n'.join(text(i) for i in [2499,2500,2501,2502])+'\n'+cut_before(text(2503),' و تمام حدیث'),kind='explicit_hadith_quotation',parent='fa-riyadh-heravi-0335',narrator='عمرو بن عبسه')
for j in [0,1]:add(f'p2536-{j+1}',[2536,2537],ar=quote(2536,j),fa=quote(2537,j),kind='hadith_quote_fragment',parent='fa-riyadh-heravi-0340')
add('p3820',[3820],fa=between(3820,'چنانچه در حدیث دیگری آمده که: '),kind='attributed_hadith_quote',parent='fa-riyadh-heravi-0578')
add('p3848',[3848],ar=between(3848,'رسول اکرم \uf072: '),kind='attributed_hadith_quote',parent='fa-riyadh-heravi-0581')
add('p3964',[3964],fa=between(3964,'و در حدیث آمده است: '),kind='attributed_hadith_quote',parent='fa-riyadh-heravi-0602')
add('p4118-a',[4118],fa=between(4118,'فرمود: ',' و بدلیل'),kind='hadith_quote_fragment',parent='fa-riyadh-heravi-0637',collections=[{'collection_ids':['sahih-muslim'],'hadith_number':None,'basis':'Muslim explicitly named in surrounding source text'}])
add('p4118-b',[4118],ar=between(4118,'بدلیل آنچه در حدیث آمده که: ',' در حدیث'),kind='attributed_hadith_quote',parent='fa-riyadh-heravi-0637')
add('p4118-c',[4118],fa=between(4118,'در حدیث آمده که ',' که:'),kind='attributed_hadith_quote',parent='fa-riyadh-heravi-0637')
add('p4307',[4307],ar=quote(4307),kind='explicit_hadith_quotation',parent='fa-riyadh-heravi-0674')
add('p7017',[7017,7018],fa=between(7017,'ش: ')+'\n'+text(7018),kind='hadith_quote_fragment',parent='fa-riyadh-heravi-1282')
add('p7550',[7550],ar=between(7550,'فرمود: '),kind='attributed_hadith_quote',parent='fa-riyadh-heravi-1401')
add('p8551',[8551,8554],ar=quote(8551),kind='hadith_quote_fragment',parent='fa-riyadh-heravi-1577',narrator='أبي هريرة')
add('p8096',[8096,8107],ar=between(8096,'يقولُ: ','، وغيرُ'),fa=between(8107,'می‌گوید، ',' وغیر'),kind='hadith_quote_fragment',parent='fa-riyadh-heravi-1509')
q9551=re.findall('«([^«»]*)»',text(9551))
add('p9551-a',[9551,9560],ar=q9551[0],fa=cut_before(text(9560),'، یعنی'),kind='hadith_quote_fragment',parent='fa-riyadh-heravi-1790')
add('p9551-b',[9551,9561],ar=q9551[1],fa=between(9561,'که: ','، یعنی'),kind='hadith_quote_fragment',parent='fa-riyadh-heravi-1790')
add('p9551-c',[9551,9562],ar=q9551[2],fa=between(9562,'فرمود: '),kind='hadith_quote_fragment',parent='fa-riyadh-heravi-1790')

allrecords=primary+anc
assert len({r['id'] for r in allrecords})==len(allrecords)
assert all(not re.search(r'(^|\n)\s*ش\s*:',r['text']['arabic'] or '') and not re.search(r'(^|\n)\s*ش\s*:',r['text']['translation'] or '') for r in allrecords)
assert not any('در بینش شیعه' in (r['text']['translation'] or '') for r in allrecords)
dump('integration-primary.json',primary)
dump('integration-ancillary.json',anc)
dump('integration-records.json',allrecords)
jsonl('integration-records.jsonl',allrecords)
dump('annotation-removal-log.json',removed)
dump('printed-attributions.json',attributions)
dump('font-decoding-evidence.json',font_evidence)
dump('integration-summary.json',{'primary_numbered_occurrences':len(primary),'additional_quote_occurrences':len(anc),
    'total_integration_records':len(allrecords),'source_number_anomalies':31,
    'removed_annotation_or_attribution_spans':len(removed),
    'removed_commentary_paragraphs':len({x['paragraph_index'] for x in removed if x['reason']=='separable_editorial_commentary_or_cross_reference'}),
    'no_source_text_limit':True,'no_deduplication':True,'source_commentary_in_payload':False,
    'all_originals_and_raw_source_tokens_retained':True,
    'canonical_reference_policy':'Only printed collection attributions retained. Source-local Riyadh numbers are never asserted as Bukhari/Muslim original numbering.',
    'grade_policy':'Attribution to hadith in source is distinct from authenticity. Missing canonical matches and overall grades remain null.',
    'page_policy':'Stable zero-based OOXML paragraph locators; printed chapter start page retained from TOC where exact heading matches; per-occurrence page null.'})
print(json.dumps({'primary':len(primary),'ancillary':len(anc),'total':len(allrecords),'removed_spans':len(removed)},ensure_ascii=False))

#!/usr/bin/env python3
"""Source-aware extraction prototype. Original DOCX and exact decoded spans stay in audit.
No fuzzy recovery, generated translation, canonical-number inference or deduplication.
"""
from pathlib import Path
import json,re,collections,hashlib,gzip
BASE=Path(__file__).resolve().parents[1]/'audit'
SOURCE=BASE/'native-paragraphs'; OUT=BASE/'recomputed-candidates';OUT.mkdir(exist_ok=True)
REPO=Path(__file__).resolve().parents[3]
EVIDENCE=json.loads((REPO/'imports/persian-docx-20261111/audit/font-evidence/font-decoding-evidence.json').read_text())
CMAP=EVIDENCE['ctraditional']['map']; AMAP={chr(int(k,16)):v for k,v in EVIDENCE['aga']['map'].items()}
AMAP.update({'\uf020':' '})
PROFILES={1:{'start':769,'ar':{'20','a6'},'fa':{'a7','2'},'heading':{'a4','a3','10','1','Heading2'},'fahead':{'a3','1'},'book':{'a4','a3'}},2:{'start':240,'ar':{'11','a4'},'fa':{'a3','1','af2'},'heading':{'ac','ad','12','10','a1'},'fahead':{'ad','10'},'book':{'ac','ad'}},3:{'start':192,'ar':{'14'},'fa':{'10','af6'},'heading':{'ab','ac','13','11'},'fahead':{'ac','11'},'book':{'ab','ac'}}}
def read_frozen(path):
 return path.read_text() if path.exists() else gzip.decompress(Path(str(path)+'.gz').read_bytes()).decode('utf-8')
DECISIONS={}
for decision_path in sorted(BASE.glob('v*-ambiguity-decisions.json.gz')):
 for d in json.loads(gzip.decompress(decision_path.read_bytes()).decode('utf-8')):DECISIONS[d['paragraph_id']]=d
DASH=r'[-‐‑‒–—―ـ]'
GRADE_RE=re.compile(r'\((?:صحيح|صحیح|حسن|ضعيف|ضعیف|موضوع|منكر|منکر|موقوف|مرسل|لا أصل|لا يصح|\؟|\?)[^)]*\)')
NUM_RE=re.compile(r'^\s*\[?\s*(\d+)(?:/م)?\s*(?:'+DASH+r'+|/|(?=\())')
FA_WORDS=re.compile(r'(?:^|\s)(?:از|که|را|است|برای|بود|گفت|فرمود|فرمودند|روایت|می\S*|آمده|خداوند|یعنی|این|آن|در|اگر|هرکس|هرگاه|وارد|ابن|رسول|نماز)(?=\s|[،.؛:»]|$)')
FA_STRONG=re.compile(r'[پچژگ]|\b(?:که|است|فرمود|فرمودند|می\S+|آمده|یعنی|خداوند|هرکس|هرگاه|نیست)\b')
AR_DIAC=re.compile(r'[\u064b-\u065f]')
QUOTE_RE=re.compile(r'«([^»]{5,})»|"([^"\n]{5,})"')
AR_VARIANT=re.compile(r'^(?:[ووف]\s*)?(?:في\s+(?:رواية|روايته|لفظ)|وفي\s+(?:رواية|روايته|لفظ)|ولفظ|واللفظ|ورواه|رواه|وروى|روى|زاد|وزاد|وعند|عند|ولمسلم|وللبخاري|وعن|عَن|وَعَن|وفي|فِي|ولأحمد|ولهما|ورُوِي|وَرُوِي|وفيه|وعنه|وَعَنْ|وَعَنْه|قال في رواية)')
FA_EXPLICIT_VARIANT=re.compile(r'^(?:و\s*)?(?:(?:در|به)\s+(?:روایت|لفظ|متن|عبارت)|روایت\s+(?:دیگر|دیگری)|(?:بخاری|مسلم|ترمذی|نسائی|ابوداود|ابن ماجه|حاکم|احمد|طبرانی|بزار|بیهقی|ابو الشیخ|ابوشیخ)\s+(?:روایت|می\S*|در|آن|اضافه)|در\s+حدیث|همچنین\s+در)')
FA_VARIANT=re.compile(r'^(?:و\s*)?(?:(?:در|به)\s+(?:روایت|لفظ|متن|عبارت)|روایت\s+(?:دیگر|دیگری)|(?:بخاری|مسلم|ترمذی|نسائی|ابوداود|ابن ماجه|حاکم|احمد|طبرانی|بزار|بیهقی|ابو الشیخ|ابوشیخ)\s+(?:روایت|می\S*|در|آن|اضافه)|در\s+حدیث|از\s+.{0,65}?(?:روایت است|روایت شده|روایت می|نقل است)|همچنین\s+در)')
AR_COMMENT=re.compile(r'^\s*(?:\(?قال الحافظ\)?|\(?قال المملي\)?|قال المصنف|قال المؤلف|قوله\b|قولهما|قولُه|قولُهُ|قال الألباني|قال المنذري|قال الخطابي|قال أبو عبيد|\(?الـ?حافظ\)?|قلت[:، ])')
FA_COMMENT=re.compile(r'^\s*(?:توضیح|توضیحات|شرح[:： ]|مترجم[:： ]|نکته|فایده|فواید|می[‌\s]?گویم|حافظ\s+(?:می\S*|گفته)|منذری\s+(?:می\S*|گفته)|آلبانی\s+(?:می\S*|گفته)|البانی\s+(?:می\S*|گفته))')
GLOSS=re.compile(r'^\s*(?:قوله|\(?[«"(][^»")]{1,90}[»")].{0,25}(?:به (?:فتح|ضم|کسر|كسر|سكون|سکون)|یعنی|يعني|يعنی|أي[:： ]|بفتح|بضم|بكسر)|\([^)]{1,55}\)\s*(?:به |یعنی|يعنی|أي|هو |هي |بفتح|بضم|بكسر))')
REFONLY=re.compile(r'^\s*(?:رواه|ورواه|أخرجه|اخرجه|وروى|روى|ذكره|قال الترمذي|وقال الترمذي|قال أبو داود|قال الطبراني|قال البزار|قال البخاري|وقال البخاري|إسناده|وإسناده|اسناده|وهو في|والبيهقي|وأحمد|قال الحاكم|وقال الحاكم|والنسائي|وهو حديث|[وف]?في إسناده|[وف]?رجاله|[وف]?رواته|رُوِي)')
AR_NARR=re.compile(r'(?:رَسُول|رَسول|رسول|النَّبِي|النبي|نَبِي|قال الله|قَالَ اللَّه|قَالَ الله|سَمِعْتُ|عن|عَنْ|رُوِي|روي|قَالَ|قال|يقول|يَقُول)')
GRADE_QUOTE=re.compile(r'^(?:حديث\s+|إسناد|اسناد|صحيح|صحیح|حسن|ضعيف|ضعیف|منكر|لا نعرف|رواته|رجاله|[ووف]?(?:له|هذا)\s+(?:شاهد|طريق|حديث))')

def clean(t):return re.sub(r'[\t\r ]+',' ',t).strip()
def lite(t):return re.sub(r'[\u064b-\u065f\u0670ـ]','',t)
def pmatch(pattern,t):return pattern.match(lite(t))
def psearch(pattern,t):return pattern.search(lite(t))
def decode(r):
 text='';events=[];tokens=[]
 for run in r['runs']:
  s=run['text'];fonts=list(run['properties'].get('rFonts',{}).values());old=s
  if 'CTraditional Arabic' in fonts:
   s=''.join(CMAP.get(c,c) for c in s)
   if s!=old:events.append({'run':run['index'],'font':'CTraditional Arabic','original':old,'decoded':s,'evidence':'prior verified exact font-family map'})
  elif any(f.startswith('AGA Arabesque') for f in fonts):
   s=''.join(AMAP.get(c,c) for c in s)
   if s!=old:events.append({'run':run['index'],'font':'AGA Arabesque','original':old,'decoded':s,'evidence':'prior verified exact font-family map'})
  text+=s
  for token in run.get('tokens',[]):
   tokens.append({'offset':len(text),'run':run['index'],**token})
   if token['kind']=='sym':
    char=chr(int(token['char'],16));f=token.get('font','');decoded=AMAP.get(char) if f.startswith('AGA Arabesque') else CMAP.get(char) if f=='CTraditional Arabic' else None
    annotation=f=='MRT_Nazanin' and token['char'].upper()=='F020' and any(t['kind']=='footnoteReference' and t.get('customMarkFollows')=='1' for t in run.get('tokens',[]))
    if annotation:decoded=' '
    if decoded is not None:
     text+=decoded;events.append({'run':run['index'],'font':f,'original_code':token['char'],'decoded':decoded,'role':'custom_footnote_annotation_replaced_with_word_boundary' if annotation else 'font_symbol'})
    else:text+=char;events.append({'run':run['index'],'font':f,'original_code':token['char'],'unresolved':True})
 r['decoded']=text;r['decoding_events']=events;r['tokens']=tokens;return r

class GradeMatch:
 def __init__(self,text,start,end):self.text,self.a,self.b=text,start,end
 def start(self):return self.a
 def end(self):return self.b
 def group(self,n=0):return self.text[self.a:self.b]

def grade_prefix(t):
 for opening in re.finditer(r'\(',t[:180]):
  start=opening.start();probe=lite(t[start+1:start+60])
  if not re.match(r'(?:صحيح|صحیح|حسن|ضعيف|ضعیف|موضوع|منكر|منکر|موقوف|مرسل|لا أصل|لا يصح|؟|\?)',probe):continue
  if re.search(r'[«»]|(?:عَن|عن|قال|رواه|وفي|از)\s',t[:start]):return None
  depth=0
  for end in range(start,len(t)):
   if t[end]=='(':depth+=1
   elif t[end]==')':
    depth-=1
    if depth==0:return GradeMatch(t,start,end+1)
  return None
 return None

def is_header(r,v):
 if r['id'] in DECISIONS:return DECISIONS[r['id']]['classification']=='heading'
 t=r['decoded'].strip();p=PROFILES[v]
 return bool((r['style'] in p['heading'] and not (GRADE_RE.search(t[:160]) and NUM_RE.match(t))) or re.match(r'^\d+\s*'+DASH+r'\s*\(?(?:الترغيب|الترهيب|ترغیب|ترهيب|تشویق)',t))

def numbered(r,v):
 t=r['decoded'];m=NUM_RE.match(t)
 if v==1 and r['index']==774:return True
 if not m or is_header(r,v):return False
 n=int(m[1]);tail=t[m.end():]
 if re.match(r'\s*\d',tail):return True
 if n>=100 or n==0:return bool(GRADE_RE.search(t[:170]) or re.search(r'(?:عَن|عن|رواه|روى|تقدم|وفي|وفي|وَرُوِي|ورُوِي|وفي)',tail[:130]))
 return False

def language(r,v,t):
 if numbered(r,v):return 'ar'
 if REFONLY.match(lite(t)) and not FA_STRONG.search(t):return 'ar'
 p=PROFILES[v]
 fa=FA_STRONG.search(t);diac=len(AR_DIAC.findall(t))
 if fa and (r['style'] in p['fa'] or len(FA_WORDS.findall(t))>=2):return 'fa'
 if r['style'] in p['fa'] and not (diac>15 and not fa):return 'fa'
 if r['style'] in p['ar']:return 'ar'
 if fa:return 'fa'
 return 'ar'

def quotes(t):
 return [{'start':m.start(),'end':m.end(),'text':m.group(0),'inner':m[1] or m[2]} for m in QUOTE_RE.finditer(t)]

def is_narrative_quote(q):
 x=lite(clean(q['inner']))
 return len(x)>=14 and not GRADE_QUOTE.match(x) and not re.fullmatch(r'[\w\s،-]{1,45}(?:صحيحه|الکبير|الكبير|الأوسط|الترغيب|الترهيب)',x)

def body_content(t):
 # Remove printed label and grade, retaining every original body character thereafter.
 m=grade_prefix(t)
 if m:return m.end(),len(t),m.group(0)[1:-1]
 m=NUM_RE.match(t)
 if m:
  pos=m.end();rest=t[pos:]
  mm=re.match(r'\s*(?:\d+\s*(?:/\d+)?\s*'+DASH+r'?\s*)?(?:\([^)]{1,12}\)\s*)?',rest)
  if mm:pos+=mm.end()
  return pos,len(t),None
 return 0,len(t),None

def citation_split(t):
 # Deterministic suffix outside the last narration quote; full original remains audit.
 q=quotes(t);last=max((x['end'] for x in q if is_narrative_quote(x)),default=0)
 if last:
  suffix=t[last:]
  m=re.search(r'(?:رواه|أخرجه|اخرجه|وقال[: ]|قال[: ]|وإسناده|وهو مرسل|وإسناد|هذا حديث)',suffix)
  if m:return last+m.start()
 return len(t)

def classify(r,v):
 t=r['decoded'];lang=language(r,v,t);offset,end,grade=body_content(t) if numbered(r,v) or grade_prefix(t) else (0,len(t),None)
 d=DECISIONS.get(r['id'])
 if d:
  assert hashlib.sha256(t.encode()).hexdigest()==d['decoded_sha256'],('decision source mismatch',r['id'])
  return d['classification'],d.get('language_override',lang),d.get('start',offset),d.get('end',end),d.get('source_grade_override',grade)
 s=t[offset:end].strip();left=len(t[offset:end])-len(t[offset:end].lstrip());offset+=left
 if not s:return 'empty',lang,offset,end,grade
 if is_header(r,v):return 'heading',lang,offset,end,grade
 if pmatch(GLOSS,s) or FA_COMMENT.match(s) or pmatch(AR_COMMENT,s):return 'commentary',lang,offset,end,grade
 if re.match(r'^\s*\([^)]{1,100}\)\s*(?:[:：]|ب(?:ال|فتح|ضم|كسر)|به |کلمه|كلمه|عبارت|هو |هي )',lite(s)) and not re.match(r'^\s*\(قال\)',lite(s)):return 'commentary',lang,offset,end,grade
 narrq=[q for q in quotes(s) if is_narrative_quote(q)]
 if lang=='ar':
  if pmatch(REFONLY,s):
   if numbered(r,v) and local_numbers(r)['unified']!='0' and (narrq or re.search(r'(?:قال|كان|سمع|نهى|دخل|يقول|وقفت|كتب).{5,}',lite(s))):return 'narration',lang,offset,end,grade
   marker=re.search(r'(?:لفظه|لفظهما|لفظها|بلفظ|وزاد|زاد فيه|زاد بعض|إلا أنه قال|إلا انه قال|قالا فيه|قال فيه|وفيه[:：]|وفي رواية|وفي لفظ|قال رسول|عن النبي.{0,25}قال)',lite(s))
   if not narrq or not marker:return 'reference',lang,offset,end,grade
  if re.match(r'^(?:و)?(?:تقدم|سيأتي|يأتي|يذكر|ذكر)',s) and not narrq:return 'cross_reference',lang,offset,end,grade
  if numbered(r,v):
   if not narrq and not (AR_NARR.search(s) and re.search(r'[:«»]|(?:كَانَ|كان|نهى|أَنَّهُ|أنه|عَنِ النَّبِي|عن النبي)',s)):return 'ambiguous_numbered',lang,offset,end,grade
   return 'narration',lang,offset,end,grade
  if narrq:return 'narration',lang,offset,end,grade
  if re.match(r'^(?:و)?(?:قَالَ|فَقَالَ|قَالَت|قَالُوا|فقال|قال|قالت|فقالت|["«])',s):return 'continuation',lang,offset,end,grade
  if re.match(r'^(?:و)?(?:في|وفي) (?:رواية|لفظ)',s) and not narrq:return 'ambiguous_variant',lang,offset,end,grade
  if re.match(r'^(?:[وف]?(?:إسناده|اسناده|رجاله|رواته|قوله)|رواه|[وف]?قال (?:الحافظ|المنذري|الترمذي|البخاري|مسلم|أحمد)|هذا الحديث|[وف]?رواية)',s):return 'commentary',lang,offset,end,grade
  return 'ambiguous',lang,offset,end,grade
 # Persian: explicit definition or author note was already excluded.
 if re.match(r'^\(?[^)]{1,65}\)\s*(?:به|یعنی|عبارت|مقصود)',s):return 'commentary',lang,offset,end,grade
 if re.match(r'^(?:و)?(?:در این حدیث|این حدیث|مراد از|منظور از|به این معنا|معنای|همانگونه که|همان گونه که|با این|چنانکه|چنان که)',s) and not ('فرمود' in s or narrq):return 'commentary',lang,offset,end,grade
 if re.match(r'^\(?[\w\u200c ]{1,30}\)?\s*(?:به فتح|به ضم|به کسر|به كسر|به سکون|به سكون)',s):return 'commentary',lang,offset,end,grade
 if re.match(r'^(?:و)?(?:پیش[‌\s]?تر|قبلا|قبلاً|پیشتر)',s) and not narrq:return 'cross_reference',lang,offset,end,grade
 return 'translation',lang,offset,end,grade

def extract_span(r,start,end):
 text=r['decoded'][start:end];adjust=[]
 # Empty footnote-anchor brackets have no narration characters. Remove only if this
 # paragraph actually contains OOXML footnote-reference tokens; record each span.
 if any(x['kind']=='footnoteReference' for x in r['tokens']):
  for m in re.finditer(r'\(\s*\)',text):adjust.append({'operation':'remove_empty_footnote_anchor_parentheses','start':start+m.start(),'end':start+m.end(),'original':m.group(0)})
  text=re.sub(r'\(\s*\)','',text)
 text=text.strip()
 return text,{'paragraph_id':r['id'],'start':start,'end':end,'coordinate_system':'font-decoded paragraph Unicode codepoints','raw_decoded_span':r['decoded'][start:end],'transformations':adjust}

def reference_minimal(raw):
 # Citation only; never expose grading criticism or commentary as a reference.
 books=[]
 for pattern,name in [(r'البخاري','البخاري'),(r'مسلم','مسلم'),(r'أحمد','أحمد'),(r'ابن ماجه','ابن ماجه'),(r'الترمذي','الترمذي'),(r'النسائي','النسائي'),(r'أبو داود|أبي داود','أبو داود'),(r'ابن حبان','ابن حبان'),(r'الحاكم','الحاكم'),(r'الطبراني','الطبراني'),(r'البيهقي','البيهقي'),(r'البزار','البزار'),(r'أبو يعلى|أبي يعلى','أبو يعلى'),(r'الدارمي','الدارمي'),(r'الأصبهاني','الأصبهاني'),(r'ابن أبي الدنيا','ابن أبي الدنيا'),(r'أبو الشيخ|أبي الشيخ','أبو الشيخ'),(r'أبو نعيم|أبي نعيم','أبو نعيم')]:
  if re.search(pattern,raw):books.append(name)
 return books

def local_numbers(r):
 t=r['decoded'];g=grade_prefix(t);prefix=t[:g.start()] if g else t[:body_content(t)[0]]
 m=NUM_RE.match(t);first=m[1] if m else None
 # Preserve source tokens, never repair erroneous or absent printed numbering.
 numbers=re.findall(r'\d+(?:/\d+)?',prefix)
 return {'printed_prefix':prefix.strip(),'unified':first,'classified':numbers[1] if len(numbers)>1 else None,'chapter_local':numbers[2] if len(numbers)>2 else (numbers[0] if not first and numbers else None),'all_printed_tokens':numbers,'scheme':'source-local multi-series; not canonical collection numbering','note':'first numbered narration has no literal unified number in w:t' if r['index']==774 and r['id'].startswith('v1:') else None}

def process(v):
 profile=PROFILES[v];rows=[decode(json.loads(s)) for s in read_frozen(SOURCE/f'v{v}-document.jsonl').splitlines()]
 ledger=[];blocks=[];cur=None;heads={};records=[];ambiguous=[];excluded=[];all_refs=[]
 for r in rows:
  if r['index']<profile['start']:
   ledger.append({'id':r['id'],'classification':'front_matter','text':r['decoded']});continue
  if is_header(r,v):
   if cur:blocks.append(cur);cur=None
   level='book' if r['style'] in profile['book'] else 'chapter';lang='fa' if r['style'] in profile['fahead'] else 'ar'
   if level=='book':heads={k:x for k,x in heads.items() if k.startswith('book')}
   heads[level+'_'+lang]={'text':r['decoded'],'paragraph_id':r['id']}
   ledger.append({'id':r['id'],'classification':'heading','text':r['decoded']});continue
  anchor=numbered(r,v)
  if anchor:
   if cur:blocks.append(cur)
   cur={'anchor':r,'rows':[],'headings':dict(heads),'numbered':True}
  if cur is None:
   cur={'anchor':r,'rows':[],'headings':dict(heads),'numbered':False}
  typ,lang,start,end,grade=classify(r,v)
  item={'row':r,'type':typ,'lang':lang,'start':start,'end':end,'grade':grade};cur['rows'].append(item)
  ledger.append({'id':r['id'],'classification':typ,'language':lang,'text':r['decoded'],'font_decoding':r['decoding_events'],'footnote_refs':[x for x in r['tokens'] if x['kind']=='footnoteReference']})
 if cur:blocks.append(cur)
 for b in blocks:
  anchor=b['anchor'];bid=f'fa-targhib-v{v}-p{anchor["index"]:05d}';units={'ar':[],'fa':[]};refs=[];last_lang=None;last_narr=None;review=[]
  for it in b['rows']:
   r=it['row'];typ=it['type'];lang=it['lang'];start,end,grade=it['start'],it['end'],it['grade'];s=r['decoded'][start:end]
   if typ in ('reference','cross_reference'):
    refs.append({'paragraph_id':r['id'],'type':typ,'text':r['decoded']});continue
   if typ in ('commentary','non_hadith_report','ambiguous','ambiguous_variant','ambiguous_numbered','empty'):
    excluded.append({'block_id':bid,'paragraph_id':r['id'],'type':typ,'text':r['decoded']})
    if typ.startswith('ambiguous'):
     ambiguous.append({'block_id':bid,'paragraph_id':r['id'],'type':typ,'text':r['decoded']});review.append(r['id'])
    continue
   if typ not in ('narration','continuation','translation'):continue
   original_body=r['decoded'][body_content(r['decoded'])[0]:] if lang=='ar' else r['decoded']
   source_variant=DECISIONS.get(r['id'],{}).get('source_variant',bool((pmatch(AR_VARIANT,original_body) if lang=='ar' else FA_VARIANT.match(original_body))))
   explicit_variant=DECISIONS.get(r['id'],{}).get('explicit_variant',source_variant if lang=='ar' else bool(FA_EXPLICIT_VARIANT.match(original_body)))
   decision=DECISIONS.get(r['id'],{})
   if decision and start>0:
    refs.append({'paragraph_id':r['id'],'type':'reviewed_decision_prefix','text':r['decoded'][:start],'offset':0})
   if decision and end<len(r['decoded']):
    refs.append({'paragraph_id':r['id'],'type':'reviewed_decision_suffix','text':r['decoded'][end:],'offset':end})
   # Source-attribution sentences are metadata, not narration. Explicit variants
   # retain their precise quoted wording, avoiding grader/book-name quotations.
   if lang=='ar' and (pmatch(REFONLY,s) or re.match(r'^(?:و)?(?:في رواية|وفي رواية|في لفظ|وفي لفظ|زاد|وزاد|ولفظه|ولفظهما|واللفظ|والطبراني|وابن حبان|والبيهقي|ولمسلم|ولـمسلم|ولهما|وللبخاري|وعند)',lite(s))):
    q=[q for q in quotes(s) if is_narrative_quote(q)]
    if q:
     qstart=q[0]['start'];qend=q[-1]['end']
     # A numbered report can begin with compiler attribution before its narrator.
     nmatch=re.search(r'(?:عَنْ|عَنِ|عَن|عن)\s',s[:qstart]) if numbered(r,v) else None
     newstart=nmatch.start() if nmatch else qstart
     if newstart:refs.append({'paragraph_id':r['id'],'type':'removed_source_attribution_prefix','text':s[:newstart],'offset':start})
     if qend<len(s):refs.append({'paragraph_id':r['id'],'type':'removed_source_suffix','text':s[qend:],'offset':start+qend})
     end=start+qend;start+=newstart;s=r['decoded'][start:end]
   cut=citation_split(s) if lang=='ar' else len(s)
   if cut<len(s):
    refs.append({'paragraph_id':r['id'],'type':'inline_reference_suffix','text':s[cut:],'offset':start+cut});end=start+cut
   text,span=extract_span(r,start,end)
   if not text:continue
   variant=source_variant
   new=not units[lang] or (last_lang and last_lang!=lang) or variant or (grade is not None and lang=='ar')
   if last_narr and DECISIONS.get(last_narr['row']['id'],{}).get('join_next') and last_lang==lang:new=False
   if new:units[lang].append({'parts':[],'grade':grade,'variant_marker':variant,'explicit_variant':explicit_variant,'first_paragraph':r['id']})
   units[lang][-1]['parts'].append({'text':text,'span':span});last_lang=lang;last_narr=it
  if not units['ar'] and not units['fa']:
   b['classification']='cross_reference_or_comment_only';b['record_ids']=[];continue
  ar,fa=units['ar'],units['fa'];align=[]
  # Exactly matching ordered segments provide safe structural correspondence.
  if len(ar)==len(fa):align=list(zip(ar,fa));alignment='equal_ordered_language_units'
  elif len(ar)==1 and not fa:align=[(ar[0],None)];alignment='arabic_only'
  elif len(fa)==1 and not ar:align=[(None,fa[0])];alignment='persian_only'
  else:
   # Do not fabricate counterpart links. Preserve each clear source unit independently
   # pending paragraph-level reconciliation of mismatched unit boundaries.
   align=[];used_ar=set();used_fa=set()
   # Adjacent alternating Arabic/Persian units are directly linked by source order.
   timeline=sorted([(int(u['first_paragraph'].split('p')[-1]),'ar',i) for i,u in enumerate(ar)]+[(int(u['first_paragraph'].split('p')[-1]),'fa',i) for i,u in enumerate(fa)])
   for ti,(pos,lang,ui) in enumerate(timeline):
    if lang!='fa' or not ti:continue
    prev=timeline[ti-1]
    if prev[1]=='ar' and prev[2] not in used_ar:
     # For a contiguous group of Arabic alternatives followed by one main Persian,
     # the first primary text is the defensible link; alternatives stay unpaired.
     aj=prev[2]
     if not fa[ui]['explicit_variant']:
      candidates=[j for j,u in enumerate(ar) if j not in used_ar and int(u['first_paragraph'].split('p')[-1])<pos]
      if candidates:aj=candidates[0]
     align.append((ar[aj],fa[ui]));used_ar.add(aj);used_fa.add(ui)
   align += [(u,None) for i,u in enumerate(ar) if i not in used_ar]
   align += [(None,u) for i,u in enumerate(fa) if i not in used_fa]
   align.sort(key=lambda pair:min(int(u['first_paragraph'].split('p')[-1]) for u in pair if u))
   alignment='structural_partial_alignment'
   ambiguous.append({'block_id':bid,'type':'language_unit_count_mismatch','arabic_count':len(ar),'persian_count':len(fa),'arabic_paragraphs':[[x['span']['paragraph_id'] for x in u['parts']] for u in ar],'persian_paragraphs':[[x['span']['paragraph_id'] for x in u['parts']] for u in fa]})
  b['record_ids']=[];b['classification']='has_narration';b['ar_units']=len(ar);b['fa_units']=len(fa)
  for no,(au,fu) in enumerate(align,1):
   rid=f'{bid}-u{no:02d}';b['record_ids'].append(rid)
   parts=(au['parts'] if au else [])+(fu['parts'] if fu else [])
   ids=[p['span']['paragraph_id'] for p in parts]
   kind='numbered_hadith' if b['numbered'] and no==1 else 'hadith_variant'
   if alignment=='structural_partial_alignment' and (not au or not fu):kind='unpaired_hadith_source_unit'
   grade=au.get('grade') if au else fu.get('grade') if fu else None
   artext='\n'.join(p['text'] for p in au['parts']) if au else ''
   fatext='\n'.join(p['text'] for p in fu['parts']) if fu else ''
   if grade and 'موقوف' in grade:kind='companion_report'
   if au and DECISIONS.get(au['first_paragraph'],{}).get('kind_override'):kind=DECISIONS[au['first_paragraph']]['kind_override']
   citations=[]
   for x in refs:
    for book in reference_minimal(x['text']):
     if book not in citations:citations.append(book)
   rec={'id':rid,'volume':v,'kind':kind,'local_numbers':local_numbers(anchor) if b['numbered'] else None,'source_grade':grade,'text':{'arabic':artext,'translation':fatext},'source_locator':{'part':'word/document.xml','anchor_paragraph':anchor['id'],'paragraphs':ids},'source_headings':b['headings'],'references':[{'collection':x,'origin':'surrounding_block_context; not asserted as direct unit identity; canonical number unavailable'} for x in citations],'related_parent_id':bid,'source_notes':{'alignment':('structural_paired' if au and fu else 'arabic_only' if au else 'persian_only') if alignment=='structural_partial_alignment' else alignment,'pending_paragraph_review':review,'source_grade_attribution':'source printed assessment, not new bank authentication','is_source_excerpt':not b['numbered'] or no>1 or any(DECISIONS.get(pid,{}).get('is_source_excerpt',False) for pid in ids)},'extraction_spans':{'arabic':[x['span'] for x in au['parts']] if au else [],'translation':[x['span'] for x in fu['parts']] if fu else []}}
   grade_unit=au or fu
   for key in ('source_grade_grader','source_grade_grader_override','source_grade_attribution','source_grade_attribution_basis'):
    if grade_unit and key in DECISIONS.get(grade_unit['first_paragraph'],{}):rec[key]=DECISIONS[grade_unit['first_paragraph']][key]
   records.append(rec)
  all_refs.extend({'block_id':bid,**r} for r in refs)
 serial=[]
 for b in blocks:
  if b['numbered']:serial.append({'block_id':f'fa-targhib-v{v}-p{b["anchor"]["index"]:05d}','anchor':b['anchor']['id'],'local_numbers':local_numbers(b['anchor']),'classification':b['classification'],'record_ids':b.get('record_ids',[]),'ar_units':b.get('ar_units',0),'fa_units':b.get('fa_units',0)})
 for name,items in [('records',records),('paragraph-ledger',ledger),('blocks',serial),('excluded',excluded),('references-audit',all_refs),('ambiguities',ambiguous)]:
  (OUT/f'v{v}-{name}.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in items))
 summary={'volume':v,'paragraphs':len(rows),'numbered_blocks':sum(b['numbered'] for b in blocks),'numbered_with_narration':sum(b['numbered'] and b['classification']=='has_narration' for b in blocks),'numbered_without_narration':sum(b['numbered'] and b['classification']!='has_narration' for b in blocks),'candidate_records':len(records),'classification_counts':dict(collections.Counter(x['classification'] for x in ledger)),'alignment_counts':dict(collections.Counter(x['source_notes']['alignment'] for x in records)),'ambiguous_paragraphs':sum(x.get('type')!='language_unit_count_mismatch' for x in ambiguous),'mismatched_blocks':sum(x.get('type')=='language_unit_count_mismatch' for x in ambiguous),'separate_font_decodings':sum(len(r['decoding_events']) for r in rows)}
 (OUT/f'v{v}-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':
 for volume in (1,2,3):process(volume)

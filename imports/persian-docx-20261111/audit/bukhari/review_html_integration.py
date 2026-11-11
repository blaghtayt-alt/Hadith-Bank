#!/usr/bin/env python3
"""Independent read-only check of the final embedded Persian reader payload."""
from pathlib import Path
from collections import Counter
import base64, gzip, hashlib, json, re, subprocess

BASE=Path(__file__).resolve().parent
REPO=BASE.parents[1]/'hadith-bank'
OUT=BASE/'html-integration-review.json'

def sha(data): return hashlib.sha256(data).hexdigest()
def textsha(value): return None if value is None else sha(value.encode())
def embedded(path):
    raw=path.read_bytes();html=raw.decode()
    m=re.search(r'<script\b[^>]*\bid="hadith-records"[^>]*>(.*?)</script>',html,re.S)
    assert m, path
    tag=m.group(0).split('>',1)[0]
    data=gzip.decompress(base64.b64decode(m.group(1))) if 'gzip-base64' in tag else m.group(1).encode()
    records=json.loads(data)
    sm=re.search(r'<script\b[^>]*\bid="hadith-snapshot"[^>]*>(.*?)</script>',html,re.S)
    snap=json.loads(sm.group(1))
    fa=[r for r in records if r.get('language')=='fa']
    return html,snap,fa,{'path':str(path.relative_to(REPO)),'html_sha256':sha(raw),'html_bytes':len(raw),'uncompressed_payload_sha256':sha(data),'all_records':len(records),'persian_records':len(fa),'snapshot_record_count':snap['record_count'],'snapshot_count_matches':snap['record_count']==len(records)}

canonical=[];files=[];bounds=[]
for path in sorted((REPO/'materials').glob('fa-*/records.jsonl')):
    raw=path.read_bytes();rs=[json.loads(line) for line in raw.splitlines() if line.strip()]
    canonical+=rs
    main=[r for r in rs if r.get('extraction',{}).get('occurrence_role')=='primary']
    def brief(r):
        return {k:r.get(k) for k in ['id','title','record_type','content_kind','number']} | {'arabic_sha256':textsha(r['text'].get('arabic')),'translation_sha256':textsha(r['text'].get('translation'))}
    files.append({'path':str(path.relative_to(REPO)),'sha256':sha(raw),'records':len(rs),'role_counts':dict(Counter(r['extraction']['occurrence_role'] for r in rs)),'record_type_counts':dict(Counter(r['record_type'] for r in rs))})
    bounds.append({'source_id':path.parent.name,'file_first':brief(rs[0]),'file_last':brief(rs[-1]),'primary_first':brief(main[0]),'primary_last':brief(main[-1]),'all_four_boundary_texts_checked':True})
byid={r['id']:r for r in canonical}
assert len(canonical)==len(byid)==6805 and len(files)==9
html,snapshot,fa,first=embedded(REPO/'hadith-bank-reader.html')
html2,snapshot2,fa2,second=embedded(REPO/'_site/index.html')
faids=[r['id'] for r in fa];emb={r['id']:r for r in fa}
missing=sorted(set(byid)-set(emb));extra=sorted(set(emb)-set(byid))
dupes=[rid for rid,n in Counter(faids).items() if n>1]
text_errors=[];metadata_errors=[];comments=[];qc=[];origin=[];glyphs=[];glyph_hints=[]
metadata_fields=['record_type','content_kind','number','narrator','translator','source_headings','source_structure_tags','references','grading','page','source_defects','source_locator','extraction']
for rid,r in byid.items():
    e=emb.get(rid)
    if e is None:continue
    for key in ['arabic','translation']:
        if r['text'].get(key)!=e.get('text_'+key):text_errors.append({'id':rid,'field':key})
    for key in metadata_fields:
        if r.get(key)!=e.get(key):metadata_errors.append({'id':rid,'field':key})
    tags=r.get('editorial_tags',{}).get('values',[])
    if tags!=e.get('editorial_tags'):metadata_errors.append({'id':rid,'field':'editorial_tags'})
    if any(v for v in (e.get('commentary') or {}).values()) or e.get('footnotes') or any(v for v in (e.get('benefits') or {}).values()):comments.append(rid)
    if e.get('display_policy',{}).get('qc_tags') is not False or any(re.search(r'(?:^|:)qc(?:$|:)|review|certified',str(t),re.I) for t in e.get('editorial_tags',[])):qc.append(rid)
    if e.get('translation_provenance',{}).get('label')!='Human' or e.get('ai_translation') is not False:origin.append(rid)
    for field,value in [('arabic',e.get('text_arabic')),('translation',e.get('text_translation'))]+[(f'heading:{i}',v) for i,v in enumerate(e.get('source_headings') or [])]:
        if not isinstance(value,str):continue
        for pos,ch in enumerate(value):
            cp=ord(ch)
            if 0xE000<=cp<=0xF8FF or 0xF0000<=cp<=0xFFFFD or 0x100000<=cp<=0x10FFFD or cp==0xFFFD:
                glyphs.append({'id':rid,'field':field,'position':pos,'codepoint':f'U+{cp:04X}','context':value[max(0,pos-80):pos+81]})
        for pattern,label in [(r'(?:U\+[EFef][0-9A-Fa-f]{3}|(?:SYM|SYMBOL|w:sym|F072|F074|AGA Arabesque|CTraditional))','placeholder_token'),(r'[†‡÷]','possible_glyph_code'),(r'(?:پیامبر(?:\s+خدا)?|رسول\s+(?:الله|اللَّه|خدا)|نبی\s+کریم)\s*[جص](?![\w\u064b-\u065f])','possible_honorific_abbreviation')]:
            for match in re.finditer(pattern,value):glyph_hints.append({'id':rid,'field':field,'kind':label,'position':match.start(),'match':match.group(),'context':value[max(0,match.start()-60):match.end()+80],'assessment':'Needs original font/run inspection; not a global letter-replacement authorization.'})

# Resolve only the exact ordinary-font abbreviations independently inspected in OOXML.
# They are preserved source characters, not an authorization for global expansion.
font_audit_path=BASE.parent/'muslim'/'font-review-explicit-targets.json'
font_audit=json.loads(font_audit_path.read_text()) if font_audit_path.exists() else []
exception_paragraphs={
 ('fa-muslim-mundhiri-tarshabi-v1-p04522','translation'):(1,[4523]),
 ('fa-muslim-mundhiri-tarshabi-v1-p04554','translation'):(1,[4556,4558]),
 ('fa-muslim-mundhiri-tarshabi-v1-p04696','translation'):(1,[4697]),
 ('fa-muslim-mundhiri-tarshabi-v2-p02988','heading:2'):(2,[2987]),
 ('fa-muslim-mundhiri-tarshabi-v2-p02992','heading:2'):(2,[2991]),
}
for item in glyph_hints:
    key=(item['id'],item['field'])
    if key not in exception_paragraphs:continue
    volume,paragraphs=exception_paragraphs[key]
    evidence=[a for a in font_audit if a.get('volume')==volume and a.get('source_part')=='word/document.xml' and a.get('paragraph_index_zero_based') in paragraphs]
    ordinary=[]
    for a in evidence:
        for run in a['runs']:
            raw=run.get('source_run_text','')
            font=run.get('effective_fonts',{}).get('cs')
            if any(ch in raw for ch in 'ص÷') and font in ['IRNazli','IRZar','KFGQPC Uthman Taha Naskh']:
                ordinary.append({'paragraph':a['paragraph_index_zero_based'],'run':run['run_index_zero_based'],'raw_text':raw,'effective_complex_script_font':font})
    if ordinary:
        item['assessment']='Source-run inspection confirms an ordinary-font source abbreviation; retained exactly under the parent task’s source-preservation policy. It is not an unresolved custom-font glyph.'
        item['status']='retained_ordinary_font_source_abbreviation'
        item['source_font_evidence']={'path':str(font_audit_path),'sha256':sha(font_audit_path.read_bytes()),'matching_source_runs':ordinary}

# Exercise the actual card code from this exact HTML, using a minimal DOM object.
# This verifies branch execution and text nodes, without claiming visual browser QA.
js=html[html.rfind('<script>')+8:html.rfind('</script>')]
helpers='const valueText ='+js.split('const valueText =',1)[1].split('function fillFilter(',1)[0]
card_code='function meta('+js.split('function meta(',1)[1].split('function updateSelection(',1)[0]
harness=r'''
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
class MiniNode {
  constructor(tag,text=''){this.tagName=tag;this.childNodes=[];this._text=text;this.className='';this.attributes={};}
  append(...items){for(const x of items)this.childNodes.push(x instanceof MiniNode?x:new MiniNode('#text',String(x)));}
  set textContent(value){this._text=String(value);this.childNodes=[];}
  get textContent(){return this._text+this.childNodes.map(x=>x.textContent).join('');}
  setAttribute(k,v){this.attributes[k]=v;}
  addEventListener(){}
}
const Node=MiniNode;
const document={createElement:t=>new MiniNode(t),createTextNode:t=>new MiniNode('#text',t)};
const window={location:{protocol:'https:'}};
const $=id=>({checked:true});
const records=input.records,names={fa:'Persian'},site=input.site||{},offline=false,state={selected:new Set()};
const nf=new Intl.NumberFormat('en');
'''+helpers+'\n'+card_code+r'''
function walk(n,out=[]){out.push(n);for(const c of n.childNodes)walk(c,out);return out;}
function detailsNamed(tree,name){return tree.find(n=>n.tagName==='details' && n.childNodes[0]?.textContent===name);}
const errors=[],weak=[],special=[],rendered=[];
for(let i=0;i<records.length;i++){
 const r=records[i],root=card(r,i),tree=walk(root),hasT=typeof r.text_translation==='string'&&r.text_translation.length>0;
 const narr=tree.filter(n=>n.tagName==='p'&&n.className.split(' ').includes('narration'));
 if(!narr.length || narr[0].textContent!==(hasT?r.text_translation:r.text_arabic||'Text not supplied in this projection.'))errors.push({id:r.id,kind:'main_narration_text'});
 const ar=detailsNamed(tree,'Arabic source text');
 if(Boolean(ar)!==Boolean(r.text_arabic&&hasT))errors.push({id:r.id,kind:'arabic_detail_presence'});
 if(ar && !walk(ar).some(n=>n.tagName==='p'&&n.textContent===r.text_arabic))errors.push({id:r.id,kind:'arabic_detail_text'});
 if(detailsNamed(tree,'Commentary & footnotes')||detailsNamed(tree,'Benefits supplied by the source'))errors.push({id:r.id,kind:'commentary_rendered'});
 const badges=tree.find(n=>n.className==='badges');
 if(badges && /QC|Source review|review pending|Independent Pro/i.test(badges.textContent))errors.push({id:r.id,kind:'qc_badge_rendered',text:badges.textContent});
 if(showQCLabels(r)||needsIndependentReview(r))errors.push({id:r.id,kind:'qc_policy_function'});
 if(originLabel(r)!=='Human')errors.push({id:r.id,kind:'human_label'});
 if(/(?:^| · )Cited:\s*(?:$| · )/.test(numberLabel(r)))errors.push({id:r.id,kind:'empty_citation_label',label:numberLabel(r)});
 const refs=detailsNamed(tree,'References'),items=r.references?.items||[];
 if(items.length && (!refs||!walk(refs).some(n=>n.tagName==='pre'&&n.textContent===JSON.stringify(items,null,2))))errors.push({id:r.id,kind:'reference_items_not_rendered'});
 const headings=tree.find(n=>n.className==='source-headings');
 if((r.source_headings||[]).length && headings?.textContent!==r.source_headings.join(' › '))errors.push({id:r.id,kind:'source_headings'});
 if(['fa-faiz-al-bari-v5-fn324-p2-q001','fa-faiz-al-bari-v6-fn353-p2-q001'].includes(r.id)){
   const grade=r.grading?.source_assessment;const ok=Boolean(grade&&grade.normalized==='weak'&&refs?.textContent.includes(grade.evidence_text)&&refs?.textContent.includes('source_assessment'));
   weak.push({id:r.id,source_grade:grade?.normalized,evidence:grade?.evidence_text,rendered_in_references:ok});if(!ok)errors.push({id:r.id,kind:'weak_source_assessment'});
 }
 if(['fa-faiz-al-bari-v5-p01882','fa-faiz-al-bari-v5-p00697','fa-faiz-al-bari-v5-fn225-p0-q001'].includes(r.id))special.push({id:r.id,title:tree.find(n=>n.tagName==='h3')?.textContent,record_type:r.record_type,content_kind:r.content_kind,arabic_detail_present:Boolean(ar),number_label:numberLabel(r)});
 rendered.push(r.id);
}
process.stdout.write(JSON.stringify({method:'Exact built-HTML card() and helper functions executed using a minimal DOM; no live-browser or visual-layout claim.',cards_rendered:rendered.length,errors,weak_grade_reference_checks:weak,special_record_rendering:special,all_card_ids_sha256:require('crypto').createHash('sha256').update(rendered.join('\n')).digest('hex')}));
'''
node_result=subprocess.run(['node','-e',harness],input=json.dumps({'records':fa,'site':snapshot.get('site')},ensure_ascii=False),text=True,capture_output=True)
if node_result.returncode: raise RuntimeError(node_result.stderr)
render=json.loads(node_result.stdout)
checks={
 'nine_canonical_material_files':len(files)==9,
 'canonical_count_6805':len(canonical)==6805,
 'embedded_count_6805':len(fa)==6805 and len(fa2)==6805,
 'all_ids_unique':not dupes,
 'no_missing_or_extra_ids':not missing and not extra,
 'all_arabic_and_persian_text_equal':not text_errors,
 'metadata_classifications_references_and_tags_equal':not metadata_errors,
 'no_commentary_footnotes_or_benefits':not comments,
 'qc_display_disabled_and_no_qc_tags':not qc,
 'all_human_origin':not origin,
 'both_html_artifacts_identical':first['html_sha256']==second['html_sha256'],
 'both_embedded_persian_payloads_identical':fa==fa2,
 'snapshot_counts_match':first['snapshot_count_matches'] and second['snapshot_count_matches'],
 'all_6805_card_functions_rendered_without_errors':render['cards_rendered']==6805 and not render['errors'],
 'both_weak_chain_assessments_rendered_in_references':len(render['weak_grade_reference_checks'])==2 and all(x['rendered_in_references'] for x in render['weak_grade_reference_checks']),
 'zero_private_use_or_replacement_characters_in_narrations_and_headings':not glyphs,
 'no_unexplained_custom_font_placeholder_hints':all(x.get('status')=='retained_ordinary_font_source_abbreviation' for x in glyph_hints),
}
report={
 'schema':'independent-html-integration-review/v1','reviewer_scope':'Independent agent read-only embedded-payload and rendering-code comparison; this is not a certified theological or source-authenticity QC release.',
 'passed':all(checks.values()),'checks':checks,'html_artifacts':[first,second],'canonical_inputs':files,
 'expected_persian_records':6805,'actual_persian_records':len(fa),'source_boundary_checks':bounds,
 'missing_ids':missing,'extra_ids':extra,'duplicate_ids':dupes,'text_mismatches':text_errors,'metadata_mismatches':metadata_errors,
 'commentary_payload_violations':comments,'qc_tag_policy_violations':qc,'origin_violations':origin,
 'record_type_counts':dict(Counter(r['record_type'] for r in fa)),
 'content_kind_counts':dict(Counter(r['content_kind'] for r in fa)),
 'private_use_and_replacement_character_findings':glyphs,
 'other_possible_glyph_or_source_abbreviation_findings':glyph_hints,
 'actual_html_card_execution':render,
 'limits':['Canonical and embedded text equality does not independently establish translation accuracy or narration authenticity.','The rendering check executes the exact final card function with a minimal DOM; a real browser is still needed for visual and live-publication verification.','Ordinary Arabic letters are not globally replaced or automatically called glyph errors. Suspicious honorific abbreviations require source font/run inspection.']
}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks':checks,'private_use_characters':len(glyphs),'other_glyph_hints':len(glyph_hints),'output':str(OUT)},ensure_ascii=False,indent=2))

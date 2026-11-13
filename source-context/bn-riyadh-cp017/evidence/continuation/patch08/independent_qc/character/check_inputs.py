from pathlib import Path
import json,hashlib,datetime,io
import fitz
from PIL import Image,ImageChops
from fontTools.ttLib import TTFont
ROOT=Path('/workspace/scratch/9965d2d3679f')
PAR=ROOT/'work/cp016_parent/bn_riyadh_20261113_v2_cp016_patch07'
OUT=ROOT/'patches/patch08/independent_qc/character'
TAIL=ROOT/'patches/patch08/tail_review'; PART=ROOT/'patches/patch08/partial_review'
(OUT/'renders').mkdir(exist_ok=True)
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pathfix(p):return ROOT/p.replace('continuation/patch08/','patches/patch08/')
raw={(v,p.stem.split('_',1)[1][:-4]):p.read_bytes().decode('utf-8') for v in [1,2] for p in (PAR/'all_source_text').glob(f'v{v:02d}_*_raw.txt')}
errors=[];checks=[]
def check(n,ok,details=None):
 row={'check':n,'passed':bool(ok)}
 if details is not None:row['details']=details
 checks.append(row)
 if not ok:errors.append(row)
def sourcecheck(v,s,label):
 actual=raw[(v,s.get('story','main'))][s['cp_start']:s['cp_end']]
 check(label,actual==s['text_verbatim'],None if actual==s['text_verbatim'] else {'actual':actual,'expected':s['text_verbatim']})
PDF={v:fitz.open(PAR/'originals'/f'bn_riyadh_{v:02d}.pdf') for v in [1,2]}
check('original_pdf_page_counts',[len(PDF[1]),len(PDF[2])]==[1023,1031],[len(PDF[1]),len(PDF[2])])
manifest=json.loads((OUT/'reviewed_inputs.json').read_text())
for row in manifest['files']:check('input_unchanged:'+row['path'],sha(ROOT/row['path'])==row['sha256'])
# Independently re-render images from immutable originals. Equality is pixel equality, not presumed from filenames.
imgs=json.loads((TAIL/'image_inventory.json').read_text())
imgs += json.loads((PART/'actually_observed_images.json').read_text())
print(type(imgs),len(imgs))
renderrows=[]
for j in imgs:
 v=j.get('source_volume',j.get('volume'));p=j['pdf_page'];s=j['render_scale'];clip=j.get('crop_bbox_pdf_points')
 f=pathfix(j['path']);pix=PDF[v][p-1].get_pixmap(matrix=fitz.Matrix(s,s),clip=fitz.Rect(clip) if clip else None,alpha=False)
 out=OUT/'renders'/f.name;pix.save(out)
 a=Image.open(f).convert('RGB');b=Image.open(out).convert('RGB');same=a.size==b.size and ImageChops.difference(a,b).getbbox() is None
 check('image_original_pixels:'+str(f.relative_to(ROOT)),same)
 check('image_declared_hash:'+str(f.relative_to(ROOT)),sha(f)==j['sha256'])
 renderrows.append({'source_volume':v,'pdf_page':p,'render_scale':s,'crop_bbox_pdf_points':clip,'author_image':str(f.relative_to(ROOT)),'author_sha256':sha(f),'independent_render':str(out.relative_to(ROOT)),'independent_sha256':sha(out),'identical_pixels':same,'actually_viewed_in_this_review':False})
(OUT/'render_authentication.json').write_text(json.dumps(renderrows,ensure_ascii=False,indent=2)+'\n')
# Exact before-state checks against authenticated parent, plus unmodified source spans.
prs=jl(PAR/'continuation/integration/character_reviews.jsonl');prg=jl(PAR/'continuation/integration/character_regions.jsonl');pex=jl(PAR/'unresolved_exceptions.jsonl');psm=jl(PAR/'continuation/integration/semantic_interval_decisions.jsonl')
ridx={x['review_id']:x for x in prs};gidx={x['region_id']:x for x in prg};eidx={x['exception_id']:x for x in pex if 'exception_id' in x}
reviews=jl(PART/'character_review_corrections.jsonl');regions=jl(PART/'character_region_corrections.jsonl');decisions=jl(PART/'character_resolution_decisions.jsonl');resolutions=jl(PART/'source_exception_resolutions.jsonl')
for r in reviews:
 check('exact_parent_before_review:'+r['review_id'],r['before_review']==ridx[r['review_id']])
 check('parent_review_hash:'+r['review_id'],r['parent_review_ledger_sha256']==sha(PAR/'continuation/integration/character_reviews.jsonl'))
 check('target_only_review:'+r['review_id'],r['after_review']['full_page_reread_in_patch08_followup'] is False)
for r in regions:
 check('exact_parent_before_region:'+r['region_id'],r['before_region']==gidx[r['region_id']])
 check('parent_region_hash:'+r['region_id'],r['parent_region_ledger_sha256']==sha(PAR/'continuation/integration/character_regions.jsonl'))
 check('unchanged_region_source_spans:'+r['region_id'],r['before_region']['source_spans']==r['after_region']['source_spans'])
 for s in r['after_region']['source_spans']:sourcecheck(r['source_volume'],s,'region_exact_source:'+r['region_id']+':'+str(s['cp_start']))
for r in decisions:
 v=r['source_volume'];p=r['pdf_page'];rid=r['decision_id'];sourcecheck(v,r['source_span'],'decision_exact_source:'+rid)
 check('parent_exception_exists:'+rid,r['parent_exception_id'] in eidx)
 check('parent_exception_hash:'+rid,r['parent_exception_ledger_sha256']==sha(PAR/'unresolved_exceptions.jsonl'))
 tr=PDF[v][p-1].get_texttrace()
 for i,g in enumerate(r['glyph_evidence']['selected_glyphs']):
  sp=tr[g['span_index_0_based']];ch=sp['chars'][g['character_index_0_based']]
  actual={'font':sp['font'],'font_size_points':sp['size'],'unicode':ch[0],'glyph_id':ch[1],'origin':list(ch[2]),'bbox':list(ch[3])}
  expected={k:g[k] for k in actual}
  check('original_PDF_selected_glyph:'+rid+':'+str(i),actual==expected,None if actual==expected else {'actual':actual,'expected':expected})
 for ei,im in enumerate(r['image_evidence']):check('decision_image_exists:'+rid+':'+str(ei),pathfix(im['path']).is_file() and sha(pathfix(im['path']))==im['sha256'])
for r in resolutions:
 check('resolved_exception_exists:'+r['exception_id'],all(e in eidx for e in r['resolution_of_exception_ids']) and r['supersedes_exception_id'] in eidx)
 check('resolution_nonmutating:'+r['exception_id'],r['source_wording_modified'] is False and r['intended_authorial_vocalization_inferred'] is False)
check('partial_counts',len(reviews)==len(regions)==len(decisions)==14 and len(resolutions)==13)
check('partial_full_credit',sum(x['full_page_completion_delta'] for x in reviews)==13)
check('one_retained_exception',len(jl(PART/'remaining_character_uncertainties.jsonl'))==1 and decisions[-1]['source_span']=={'story':'main','cp_start':1076183,'cp_end':1076184,'text_verbatim':'\uf079'})
# Re-extract every embedded-font input; check selected glyph outline metadata, not merely Unicode map.
for f in json.loads((PART/'font_glyph_evidence.json').read_text()):
 v=f['source_volume'];xf=f['font_xref'];data=PDF[v].extract_font(xf)[3];font=TTFont(io.BytesIO(data));order=font.getGlyphOrder();glyphs=font['glyf'];metrics=font['hmtx'].metrics;cmaps=font['cmap'].tables
 check(f'font_original_bytes:v{v}:xref{xf}',hashlib.sha256(data).hexdigest()==f['sha256']==sha(pathfix(f['path'])))
 check(f'font_upm:v{v}:xref{xf}',font['head'].unitsPerEm==f['units_per_em'])
 for gid,m in f['glyphs'].items():
  name=order[int(gid)];g=glyphs[name];actual={'name':name,'contours':g.numberOfContours,'bounds':[getattr(g,k,None) for k in ['xMin','yMin','xMax','yMax']],'advance':list(metrics[name]),'cmap_unicode_mappings':sorted({hex(cp) for t in cmaps if t.isUnicode() for cp,n in t.cmap.items() if n==name})}
  if 'components' in m:actual['components']=[c.glyphName for c in g.components] if g.isComposite() else None
  check(f'font_glyph_metadata:v{v}:xref{xf}:gid{gid}',actual==m,None if actual==m else {'actual':actual,'expected':m})
# All tail exact source spans; link checks against the parent ledger row and digest.
treg=jl(TAIL/'character_regions.jsonl');trev=jl(TAIL/'character_reviews.jsonl');bridges=jl(TAIL/'appendix_row_character_semantic_bridge.jsonl');links=jl(TAIL/'semantic_evidence_links.jsonl');sem=jl(TAIL/'semantic_decisions.jsonl')
for r in treg:
 for s in r['source_spans']:sourcecheck(r['source_volume'],s,'tail_region_exact_source:'+r['region_id']+':'+str(s['cp_start']))
for r in sem:sourcecheck(r['source_volume'],r,'tail_semantic_exact_source:'+r['decision_id'])
for r in links:
 sourcecheck(r['source_volume'],r,'tail_link_exact_source:'+r['link_id']);x=psm[r['parent_semantic_ledger_1_based_row']-1]
 check('tail_link_parent:'+r['link_id'],r['parent_decision_id']==x['decision_id'] and r['text_verbatim']==x['text_verbatim'])
 check('tail_link_parent_hash:'+r['link_id'],r['parent_semantic_ledger_sha256']==sha(PAR/'continuation/integration/semantic_interval_decisions.jsonl'))
for r in bridges:
 check('appendix_three_content_cells_plus_empty_row_terminator:'+str(r['appendix_row']),len(r['cells'])==4 and r['cells'][3]['text_verbatim']=='')
 for c in r['cells']:
  sourcecheck(2,c,'appendix_cell_exact_source:'+str(r['appendix_row'])+':'+str(c['column_index']))
  check('appendix_cell_terminator:'+str(c['cell_terminator_cp']),raw[(2,'main')][c['cell_terminator_cp']]=='\x07')
  check('appendix_no_canonical_inference:'+str(r['appendix_row'])+':'+str(c['column_index']),c['canonical_value'] is None)
check('tail_region_review_counts',len(treg)==220 and len(trev)==13)
check('appendix_row_count',len(bridges)==53 and len([r for r in bridges if r['printed_reference'] is not None])==52)
blank=[c for r in bridges for c in r['cells'] if c['column_index']==3 and c['empty_cell']]
check('appendix_blank_critic_cells',len(blank)==5)
blankledger=jl(TAIL/'blank_critic_cells.jsonl')
check('appendix_blank_regions',len(blankledger)==7 and len({r['empty_cell_cp'] for r in blankledger})==5)
report={'schema':'patch08-independent-character-structural-checks-1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'failed_count':len(errors),'errors':errors,'independent_original_rerenders':len(renderrows),'viewing_is_separate_from_rendering':True}
(OUT/'structural_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failures':len(errors),'errors':errors,'renders':len(renderrows)},ensure_ascii=False,indent=2))

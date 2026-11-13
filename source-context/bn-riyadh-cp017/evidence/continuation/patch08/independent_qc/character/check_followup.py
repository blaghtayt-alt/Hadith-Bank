from pathlib import Path
import fitz,json,io,hashlib,datetime
from fontTools.ttLib import TTFont
R=Path('/workspace/scratch/9965d2d3679f');P=R/'work/cp016_parent/bn_riyadh_20261113_v2_cp016_patch07';O=R/'patches/patch08/independent_qc/character'
rows=[json.loads(l) for l in (R/'patches/patch08/partial_review/character_region_corrections.jsonl').read_text().splitlines()];checks=[]
for row in rows:
 b=row['before_region'];a=row['after_region'];m=[]
 for d in b.get('differences',[]):
  if isinstance(d,dict) and 'observed_visible' in d:m.append((d['cp_start'],d['cp_end'],d['source_verbatim'],d['observed_visible']))
 for d in b.get('source_rendering_mappings',[]):
  q=d['source_span'];m.append((q['cp_start'],q['cp_end'],q['text_verbatim'],d['observed_visible_text']))
 text=[];valid=True
 for span in b['source_spans']:
  s=span['text_verbatim'];start=span['cp_start'];end=span['cp_end']
  for x,y,raw,new in sorted(set(m),reverse=True):
   if start<=x and y<=end:
    if s[x-start:y-start]!=raw:valid=False
    s=s[:x-start]+new+s[y-start:]
  text.append(s)
 derived=''.join(text).replace('\r','').replace('\x1f','').strip()
 if row['pdf_page']==962:ok=a['visible_text_transcription'] is None
 else:ok=valid and derived==a['visible_text_transcription']
 checks.append({'check':'after_transcription_uses_only_source_and_exact_inherited_rendering_maps','source_volume':row['source_volume'],'pdf_page':row['pdf_page'],'passed':ok,'source_maps_inherited':len(m),'mismatch':None if ok else {'derived':derived,'after':a['visible_text_transcription']}})
 # Inspected glyph/multiplicity only; all inherited display mappings remain inherited.
 checks.append({'check':'inherited_difference_records_preserved','source_volume':row['source_volume'],'pdf_page':row['pdf_page'],'passed':a['differences']==b['differences'] and a.get('source_rendering_mappings')==b.get('source_rendering_mappings')})
doc=fitz.open(P/'originals/bn_riyadh_01.pdf');font=TTFont(io.BytesIO(doc.extract_font(9919)[3]));gs=[]
for li,lookup in enumerate(font['GSUB'].table.LookupList.Lookup):
 for si,sub in enumerate(lookup.SubTable):
  for first,ligs in getattr(sub,'ligatures',{}).items():
   for lig in ligs:
    if lig.LigGlyph in ['glyph00308','glyph00436']:gs.append({'lookup_index':li,'subtable_index':si,'first':first,'components':lig.Component,'result':lig.LigGlyph})
checks.append({'check':'bengali_ra_phala_from_virama_plus_ra','passed':any(r['first']=='uni09CD' and r['components']==['uni09B0'] and r['result']=='glyph00436' for r in gs)})
checks.append({'check':'bengali_pra_from_pa_plus_ra_phala','passed':any(r['first']=='uni09AA' and r['components']==['glyph00436'] and r['result']=='glyph00308' for r in gs)})
stream=doc[640].read_contents().decode('latin1');lines=stream.splitlines();font_state=None;evidence=[]
for idx,line in enumerate(lines):
 import re
 match=re.search(r'/(F\w+)\s+[\d.]+\s+Tf',line)
 if match:font_state=match.group(1)
 if '<013401B4005C018C0003>' in line:evidence.append({'line_index_0_based':idx,'preceding_lines':lines[max(0,idx-3):idx],'text_array':line,'active_font_resource':font_state})
checks.append({'check':'bengali_duplicate_ra_actual_content_resource_F2','passed':len(evidence)==1 and evidence[0]['active_font_resource']=='F2' and any(f[0]==9919 and f[4]=='F2' for f in doc[640].get_fonts())})
# Report exact reviewed branches still immutable after inspection.
manifest=json.loads((O/'reviewed_inputs.json').read_text());changed=[]
for entry in manifest['files']:
 if hashlib.sha256((R/entry['path']).read_bytes()).hexdigest()!=entry['sha256']:changed.append(entry['path'])
checks.append({'check':'reviewed_input_manifest_unchanged_at_visual_review_completion','passed':not changed,'changed_paths':changed})
result={'schema':'patch08-independent-character-followup-checks-1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'failed_count':sum(not c['passed'] for c in checks),'bengali_actual_GSUB_entries':gs,'bengali_original_PDF_content_evidence':evidence,'important_limit':'Source-derived broader-region transcriptions are structurally checked against inherited rendering mappings; this is not a fresh visual reading outside the localized target crops.'}
(O/'followup_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))

#!/usr/bin/env python3
"""Build source-preserving bank records from adjudicated PDF spans."""
from pathlib import Path
import json, re, hashlib, collections, csv, argparse

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-dir',type=Path,default=Path(__file__).resolve().parent)
BASE = parser.parse_args().work_dir.resolve()
OUT = BASE/'intake'
SOURCE_ID = 'ja-muslim-web-c859ce57c211ea1b'
SOURCE_SHA = 'c859ce57c211ea1bfddb98b268241da25fe077782dd4d6be4cd9e10628b18d6a'
EDITION = 'pdf-c859ce57c211ea1b'
TITLE = 'WEB版　日訳サヒーフ・ムスリム'
EDITION_PATH = f'languages/ja/books/muslim/editions/{EDITION}'
UNITS = json.loads((OUT/'units.json').read_text())
SECTIONS = json.loads((OUT/'sections-intermediate.json').read_text())
LINES = json.loads((BASE/'pdf/lines.json').read_text())
BYLINE = {l['id']:l for l in LINES}
BYSECTION = {s['section_id']:s for s in SECTIONS}
META = json.loads((BASE/'metadata-review/source-metadata-evidence.json').read_text())
ARABIC = re.compile(r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]+')

def dump(path,data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n',encoding='utf8')

def txt(pieces):
    return ''.join(p['text'] for p in pieces)

def spans(pieces):
    return [{k:p[k] for k in ['line_id','start','end','role','component_id']} for p in pieces]

def narrator(unit, translation):
    pp=[p for p in unit['pieces'] if p['role']=='translation']
    # Only the opening attribution is parsed. Neither identities nor missing chains
    # are filled by matching names to a different edition.
    opening=''.join(p['text'] for p in pp[:3])
    flat=opening.replace('\n','').strip()
    name=None; basis='unresolved_source_attribution'; evidence=None
    kat=r'[ァ-ヶー・･．.·－]+'
    blocked={'ハディース','ハデイース','クルアーン','アッラー','イスラーム','ムアッジン','スンナ','ウドゥー','ウドウー','イマーム'}
    # A leading name, a pair of names or an explicit family descriptor. Arbitrary
    # prose preceding は is never treated as a personal name.
    m=re.match(r'^('+kat+r'(?:[（(][^）)]+[）)])?(?:(?:及び|と|、または、|の息子|の父|の母|の娘|の元奴隷|の解放奴隷|の書記|のマウラー[、・]?)(?:'+kat+r')?)*)'
               r'(?:によると|によれば|は|が|も|による|の伝える|の伝えた|の語る|の前記|からの同様)',flat)
    if m and m[1] not in blocked:
        name=m[1];basis='literal_leading_attribution_not_normalized_identity'
    if name is None:
        # The named reporter within a descriptive prefix or a wrapped opening.
        candidates=list(re.finditer(r'('+kat+r')(?:[（(][^）)]+[）)])?(?:は|が)(?=[、\s]*(?:(?:次のように|こう|以下のように|別の伝承者経路で|アッラーの使徒の言葉として|それぞれ)?(?:伝え|述べ|語)|アッラー|預言者))',flat))
        for m in candidates:
            if m[1] not in blocked and not m[1].startswith(('・','･','·')):
                name=m[1];basis='name_in_opening_source_attribution_not_normalized_identity';break
    if name is None:
        for m in re.finditer(r'('+kat+r')(?:によって(?:も)?|からの伝聞|の語る所|の語るところ|の伝える所|の伝えるハディース)',flat):
            if m[1] not in blocked and not m[1].startswith(('・','･','·')):
                name=m[1];basis='name_in_opening_route_attribution_not_normalized_identity';break
    if name:
        evidence={'source_spans':spans(pp[:3]),'scope':'opening source attribution; lexical extraction, independent identity review pending'}
    return {'name':name,'verbatim':opening or None,'verbatim_scope':'first_three_source_fragments_as_attribution_context_not_full_isnad',
            'language':'ja','name_status':basis,
            'normalized_person_id':None,'evidence':evidence,'isnad':None,
            'isnad_status':'source_preface_says_full_chains_omitted_except_initial_speaker',
            'source_preface_evidence_pdf_page':5}

def note_object(n, record_id):
    t=txt(n['pieces']);m=re.match(r'\s*([（(](?:注|註)[^）)]*[）)])',t)
    return {'note_id':n['note_id'],'language':'ja','label_verbatim':m[1] if m else None,
            'text_verbatim':t,'source_spans':spans(n['pieces']),
            'pdf_pages':sorted({x['pdf_page'] for x in n['pieces']}),
            'attachment_basis':'source position after this occurrence; semantic note-marker scope may include earlier variants',
            'attached_record_id':record_id,'semantic_attachment_status':'not_independently_verified',
            'contains_quotation':bool(re.search(r'[「『“]',t)),
            'ancillary_quotation_segmentation':'pending' if re.search(r'[「『“]',t) else 'no_quotation_marker_detected'}

def classify(u,t):
    first=t.replace('\n','')[:230]
    explicit=(u['start_reason']['reason'] in {'explicit_route_or_variant_summary','named_variant_attribution'} or
              bool(re.search(r'(?:前記|前述|同様|同内容|同一).{0,45}(?:ハディース|伝承)|(?:別の|別な|同一の)伝承者経路',first)))
    if explicit and not re.search(r'[「『“"\']',t) and len(t)<300 and re.search(r'伝え|同じ|同一|同内容|同様|もたら',t):
        return 'variant_reference','abbreviated_source_route_reference_no_expanded_matn',True
    if explicit:
        return 'variant_occurrence','source_variant_wording_or_report_as_printed',True
    return 'narration','source_report_text_present_semantic_classification_pending',False

records=[]
allnotes=[]
previous=None
for u in UNITS:
    s=BYSECTION[u['section_id']]
    translation=txt([p for p in u['pieces'] if p['role']=='translation'])
    raw=txt(u['pieces'])
    record_type,text_status,variant=classify(u,translation)
    footnotes=[note_object(n,u['id']) for n in u['notes'] if n.get('kind','footnote')=='footnote']
    commentaries=[note_object(n,u['id']) for n in u['notes'] if n.get('kind')=='commentary']
    allnotes.extend(footnotes)
    issues=['independent_character_fidelity_review_pending','independent_semantic_boundary_review_pending',
            'canonical_collection_number_not_supplied','full_arabic_narration_not_supplied']
    if footnotes:
        issues.append('note_attachment_and_ancillary_quotation_scope_pending')
    fragments=[]
    for p in u['pieces']:
        for m in ARABIC.finditer(p['text']):
            fragments.append({'text_verbatim':m[0],'line_id':p['line_id'],'line_start':p['start']+m.start(),
                              'line_end':p['start']+m.end(),'pdf_page':p['pdf_page'],'context_role':p['role'],
                              'logical_order_status':'unreviewed_raw_pdf_text_layer','canonical_arabic_substitution':False})
    if fragments:issues.append('embedded_arabic_snippet_visual_order_and_glyph_review_pending')
    if s['pdf_page_start']==470:issues.append('source_section_print_page_order_anomaly')
    if s['pdf_page_start'] in [356,358]:issues.append('source_repeated_section_preserved')
    tags=[]
    for field,value,lines in [('chapter',s['header'],[s['header_line_id']]),('section',s['title_verbatim'],s['title_line_ids']),('volume','1巻',[s['printed_reference_line_id']])]:
        if not value:continue
        taghash=hashlib.sha256((s['section_id']+'|'+field+'|'+value).encode()).hexdigest()[:16]
        tags.append({'tag_id':f'structure:{SOURCE_SHA[:16]}:{taghash}','origin':'source_book_structure','language':'ja',
                     'field':field,'value_verbatim':value,'source_id':SOURCE_ID,
                     'evidence':{'source_field':'source_section.'+field,'source_line_ids':lines,
                                 'extraction_record_id':u['id'],'record_location':{'pdf':[s['pdf_page_start']],'printed':[s['printed_reference']],'sheet':None,'row':None},
                                 'location_scope':'exact source section heading/label, not inferred canonical chapter'}})
    related=None
    if variant:
        related={'relation':'refers_to_preceding_source_context','source_wording':translation[:250],
                 'previous_source_occurrence_id':previous['id'] if previous and previous['book']['section_id']==u['section_id'] else None,
                 'resolved_canonical_target':None,'link_status':'contextual_adjacency_only_not_verified_hadith_equivalence'}
    refs=[]
    for p in u['pieces']:
        for m in re.finditer(r'第\s*[0-9０-９]+章(?:\s*[0-9０-９]+(?:[―–\-][0-9０-９]+)?節(?:以下)?)?',p['text']):
            refs.append({'kind':'printed_quran_or_chapter_reference_candidate','text_verbatim':m[0],
                         'line_id':p['line_id'],'start':p['start']+m.start(),'end':p['start']+m.end(),
                         'pdf_page':p['pdf_page'],'resolved_reference':None})
    r={
        'schema_version':'hadith-bank-attachment-candidate-v1','extraction_schema_version':'1.0.0',
        'id':u['id'],'record_id':u['id'],'occurrence_id':u['id'],'sequence_in_source':u['sequence'],
        'language':'ja','source_language_code':'ja','record_type':record_type,'narration_unit':'source_occurrence',
        'content_kind':'source_narration_occurrence_not_independently_classified',
        'text':{'arabic':None,'translation':translation,'translation_format':'verbatim_embedded_pdf_text_with_original_line_endings',
                'translation_contains_source_narrator_attribution':True,'text_presence_status':text_status},
        'source_unit_text_verbatim':raw,'embedded_arabic_fragments':fragments,
        'book':{'catalog_key':'muslim','collection_id':'sahih-muslim','title':TITLE,'chapter':s['header'],
                'section':s['title_verbatim'],'section_display':s['title_display'],'section_id':s['section_id'],
                'chapter_number':None,'canonical_book_number':None,'volume':'1',
                'edition':{'edition_id':EDITION,'edition_label':'WEB版','scope':'supplied volume 1 web-PDF asset',
                           'exact_print_edition':None,'publication_date':None,'source_metadata_path':'source.json'},
                'compiler':{'name_verbatim':META['collection']['compiler_ja_as_printed'],'evidence_pdf_pages':[3,4]},
                'section_notes_ids':[n['note_id'] for n in s['notes']]},
        'number':{'in_book':None,'canonical':None,'printed_label':None,'source_entry_id':None,
                  'status':'no_printed_hadith_number_in_supplied_source','sequence_is_hadith_number':False},
        'narrator':narrator(u,translation),
        'source':{'source_id':SOURCE_ID,'file':'WEB版_日訳サヒーフ_ムスリム.pdf','sha256':SOURCE_SHA,'title':TITLE,
                  'format':'pdf','package_file':'sources/ja-muslim-web.pdf','metadata_path':'source.json',
                  'source_url_as_printed':META['web_edition']['source_url_as_printed'],'url_live_verified':False},
        'translator':{'name':None,'credited_names':[x['name'] for x in META['translation']['credited_translators']],
                      'attribution_scope':'named translators of volume one; individual occurrence assignment unverified',
                      'evidence':{'pdf_pages':[2,5,6],'source_metadata_path':'source.json','source_field':'translation.credited_translators'}},
        'translation_provenance':{'translation_origin':'human_translation','kind':'human_translator_credited','ai_translation':False,
                                  'evidence':{'pdf_pages':[2,5,6],'source_metadata_path':'source.json','basis':'named human translators and historical translation preface'},
                                  'human_translation_does_not_certify_web_transcription':True},
        'page':{'pdf':sorted({p['pdf_page'] for p in u['pieces']}),'printed':[s['printed_reference']],
                'printed_reference_scope':'section','printed_reference_line_id':s['printed_reference_line_id'],
                'printed_volume':s['printed_volume'],'printed_page_start':s['printed_start'],'printed_page_end':s['printed_end'],
                'exact_narration_print_pages':None,'sheet':None,'row':None},
        'references':{'arabic':None,'translation':None,'items':refs},
        'commentary':{'arabic':None,'translation':''.join(n['text_verbatim'] for n in commentaries) or None,'items':commentaries,
                      'inline_translator_explanations':'source parenthetical explanations inside Japanese translation retained; exhaustive separation pending'},
        'footnotes':footnotes,
        'grading':{'grade':None,'grader':None,'source':None,'scope':None,'status':'no_independently_verified_occurrence_grade',
                   'collection_membership':'supplied Japanese Sahih Muslim translation','collection_membership_is_not_scoped_grade_evidence':True},
        'ai_translation':False,
        'topic_tags':[],'source_structure_tags':tags,
        'editorial_tags':{'origin':'import_pipeline_not_publisher','values':[
            'source:'+SOURCE_ID,'language:ja','book:muslim','edition:'+EDITION,'volume:1','format:pdf',
            'method:embedded_pdf_text_pymupdf','translation:human_credited','ai_translation:false',
            'extraction:ai_assisted','review:pending_independent_pro','kind:'+record_type,
            'rights:pending','canonical_mapping:unverified','arabic:not_supplied']},
        'provenance':{'extraction_method':'embedded_pdf_text_pymupdf','ocr_used':False,'ai_assisted_extraction':True,
                      'ai_generated_translation':False,'source_sha256':SOURCE_SHA,'source_spans':spans(u['pieces']),
                      'source_line_ids':list(dict.fromkeys(p['line_id'] for p in u['pieces'])),
                      'boundary_evidence':u['start_reason'],'source_text_modifications':'none',
                      'source_span_offset_unit':'zero_based_unicode_codepoints_in_line_text_plus_LF',
                      'original_pdf_order_preserved':True},
        'review':{'status':'initial_extraction_targeted_boundary_repairs_full_independent_review_pending','issues':issues,
                  'full_character_visual_check':False,'release_status':'private_candidate','independent_pro_qc':'pending',
                  'release_eligible':False,'mechanical_validation_report':'reports/validation.json'},
        'rights':{'status':'not_assessed_for_publication','reuse_basis':None,'publication_authorized_by_this_import':False,
                  'source_conditions_path':'source.json'},
        'metadata_gaps':['independent_pro_publication_qc','complete_semantic_boundary_review','public_redistribution_basis',
                         'canonical_occurrence_mapping','full_arabic_narration','full_isnad_not_supplied',
                         'per_occurrence_translator_assignment','scoped_grading_evidence','publisher_topic_taxonomy_not_supplied'],
        'source_occurrence_group':{'id':u['id'],'basis':'individual source-position occurrence; repeated text retained'},
        'related_source_entries':related,'related_versions':[]
    }
    records.append(r);previous=r

# Preserve a continuous source account while exposing its explicit embedded chains.
record_map={r['id']:r for r in records}
composite_id=SOURCE_ID+'-p0121-l023-c000'
if composite_id in record_map:
    r=record_map[composite_id]
    r['embedded_transmission_attributions']=[
        {'source_spans':[p for p in r['provenance']['source_spans'] if p['line_id'] in ['p0122-l030','p0122-l031','p0122-l032','p0122-l033']],
         'role':'supplementary_named_chain_and_quoted_report_within_continuous_account',
         'canonical_occurrence_identity':None},
        {'source_spans':[p for p in r['provenance']['source_spans'] if p['line_id'] in ['p0122-l034','p0122-l035']],
         'role':'joint_attribution_for_continuation_of_the_account','canonical_occurrence_identity':None}]
    r['review']['issues'].append('composite_source_chain_attributions_pending_canonical_boundary_alignment')

# These are source-marker links, not moves of the source note text. The primary
# attribution remains at the note's physical position following a short variant.
physical_id=SOURCE_ID+'-p0151-l020-c000'
semantic_id=SOURCE_ID+'-p0150-l025-c000'
if physical_id in record_map and semantic_id in record_map:
    for n,marker_line in zip(record_map[physical_id]['footnotes'],['p0151-l004','p0151-l010']):
        n['semantic_target_record_ids']=[semantic_id]
        n['semantic_attachment_status']='source_marker_linked_in_targeted_review'
        n['semantic_marker_evidence']={'line_id':marker_line,'line_text_verbatim':BYLINE[marker_line]['text'],
                                     'source_label_note':'Literal source label 注l is preserved; its marker corresponds to 注1 in the report.' if marker_line=='p0151-l004' else None}
        record_map[semantic_id].setdefault('related_footnotes',[]).append({'note_id':n['note_id'],'physical_owner_record_id':physical_id,
                                                                       'relation':'explicit_source_note_marker','marker_line_id':marker_line})

# Preserve repeated text as separate occurrences and expose only exact-text relations.
hashgroups=collections.defaultdict(list)
for r in records:
    h=hashlib.sha256(r['text']['translation'].encode()).hexdigest();hashgroups[h].append(r)
for h,group in hashgroups.items():
    if len(group)>1:
        for r in group:
            r['related_versions']=[{'record_id':other['id'],'relation':'exact_extracted_translation_text',
                                    'basis_sha256':h,'canonical_equivalence_asserted':False} for other in group if other is not r]

edition=OUT/'bank'/EDITION_PATH
dump(OUT/'records.json',records)
(OUT/'records.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in records),encoding='utf8')
dump(OUT/'sections.json',SECTIONS)
dump(OUT/'footnotes.json',allnotes)
counts={'records':len(records),'record_types':dict(collections.Counter(r['record_type'] for r in records)),
        'sections':len(SECTIONS),'footnotes':len(allnotes),'section_notes':sum(len(s['notes']) for s in SECTIONS),
        'commentary_blocks':sum(len(r['commentary']['items']) for r in records),
        'records_with_narrator_attribution':sum(r['narrator']['name'] is not None for r in records),
        'records_with_embedded_arabic_fragments':sum(bool(r['embedded_arabic_fragments']) for r in records),
        'exact_translation_duplicate_groups':sum(len(g)>1 for g in hashgroups.values()),
        'occurrences_in_exact_translation_duplicate_groups':sum(len(g) for g in hashgroups.values() if len(g)>1),
        'source_pages':580,'raw_source_lines':len(LINES),'ai_translation_false_records':len(records)}
dump(OUT/'counts.json',counts)
print(json.dumps(counts,ensure_ascii=False,indent=2))

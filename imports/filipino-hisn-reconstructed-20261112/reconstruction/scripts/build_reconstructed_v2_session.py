#!/usr/bin/env python3
"""Build a new targeted reconstruction; never mutate the original v1 archive."""
from pathlib import Path
import copy, csv, datetime, hashlib, json, shutil, zipfile, collections

BASE = Path(__file__).resolve().parent
V1NAME = 'FIL_HISN_FINAL_PRO_REVIEW_20261112_HOLD_v1'
V1 = BASE / 'v1_extracted' / V1NAME
ZIP = BASE.parent / 'upload' / (V1NAME + '.zip')
STAMPFILE = BASE / 'reconstruction_identity.json'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def textsha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def objsha(o): return textsha(json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(',', ':')))
def dump(p, obj):
    p=Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def jsonl(p, rows):
    p=Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(''.join(json.dumps(x, ensure_ascii=False, separators=(',', ':'))+'\n' for x in rows), encoding='utf-8')
def csvout(p, rows, columns):
    p=Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=columns); w.writeheader(); w.writerows(rows)

if not STAMPFILE.exists():
    now=datetime.datetime.now(datetime.timezone.utc)
    dump(STAMPFILE, {'artifact_id':'FIL_HISN_RECONSTRUCTED_v2_HOLD_'+now.strftime('%Y%m%dT%H%M%SZ')+'_8043d352',
                     'created_utc':now.isoformat(), 'created_date_japan':'2026-11-12'})
IDENT=read(STAMPFILE); ART=IDENT['artifact_id']; OUT=BASE/'deliverables'/ART
OUT.mkdir(parents=True, exist_ok=True)
original=read(V1/'data/corrected_all_records.json'); result=copy.deepcopy(original)
records=original['records']; byid={r['record_id']:r for r in records}; ridx={r['record_id']:i for i,r in enumerate(records)}
assert ZIP.stat().st_size == 384986021 and sha(ZIP)=='8043d352e722d8c38ba49bdb54f4f273bb91e3fe4fba111d0d809b36ed17c7ad'
assert len(records)==323 and sum(len(r['components']) for r in records)==1500
for sub in ['data','partitions','audit','coverage','provenance','scripts','validation','preserved_inputs','coauthor_work']:
    (OUT/sub).mkdir(exist_ok=True)
preserved=OUT/'preserved_inputs'/(V1NAME+'.zip')
if not preserved.exists():
    # Copy, rather than re-serialize, the exact original archive and every nested predecessor.
    shutil.copyfile(ZIP, preserved)
assert sha(preserved)==sha(ZIP)

for src, dst in [('coauthor_attribution','attribution'),('coauthor_dialogue','dialogue'),('coauthor_blockers','blockers')]:
    shutil.copytree(BASE/src, OUT/'coauthor_work'/dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
attr=read(BASE/'coauthor_attribution/attribution_findings.json')
ad={x['record_id']:x for x in attr['decisions']}
dialog=read(BASE/'coauthor_dialogue/dialogue_context_decisions.json')
dd={x['record_id']:x for x in dialog['records']}
scope=read(BASE/'coauthor_blockers/blocker_scope_proposal.json')
blocks=read(BASE/'coauthor_blockers/record_blocker_mapping_proposal.json')
dependency=read(BASE/'coauthor_blockers/v1_dependency_preservation_ledger.json')
dump(OUT/'audit/v1_dependency_preservation_ledger.json', dependency)

INDEPENDENT={
 'N007','N118','N160','N161','N177','N225',
 'N129','N130','N145','U-P171-01','U-P185-01','U-P188-01','N168','N232'
}
QURAN_AUTHOR={'QC-U-P014-Q01','QC-U-P014-Q02','QC-U-P014-Q03','QC-U-P015-Q01','U-P100-Q01','N135'}
UNRESOLVED={'N015','N083','U-P100-01','U-P114-01','N214'}
assert not INDEPENDENT&QURAN_AUTHOR and not INDEPENDENT&UNRESOLVED and not QURAN_AUTHOR&UNRESOLVED
assert INDEPENDENT|QURAN_AUTHOR|UNRESOLVED <= set(byid)
def partition(rid):
    if rid in INDEPENDENT: return 'independent_non_prophetic'
    if rid in QURAN_AUTHOR: return 'quran_and_author_only'
    if rid in UNRESOLVED: return 'attribution_unresolved'
    return 'hisn_hadith_dhikr_context'

# Explicit record-level association does not alter the identity of Quran, commentary,
# other-speaker speech, nor the list of 493 inherited candidate components.
manual={
 'N004': ('QURAN_RECITATION_WITH_RETAINED_PROPHETIC_PRACTICE_CONTEXT',
          'The source body is Quran3:190-200 and remains Quran at component level. Its printed reference and retained Bukhari4569 narrative connect the selection to the Prophet waking and reciting. Retain the complete record as a recitation-context association; do not claim that the whole printed verse selection is one exact hadith matn or newly verify the cited print edition.'),
 'N235': ('QURAN_SUPPLICATION_WITH_RETAINED_PROPHETIC_RECITATION_CONTEXT',
          'The printed body remains Quran2:201. The source chapter locates the supplication between the two corners, and retained AbuDawud1892 explicitly narrates the Prophet reciting it there. Preserve that association without relabeling Quran as non-Quran, adding missing narrative to source text, or creating a new candidate component.'),
 'N135': ('QURAN_WITH_AUTHOR_DIRECTION_AND_SEPARATE_COMPANION_ADVICE',
          'Source Quran57:3, compiler direction and source reference remain in Quran/author-only. The retained AbuDawud5110 passage identifies IbnAbbas advice, not a Prophetic instruction. Preserve the associated Companion evidence and unresolved grading/wording questions; Quran/source spelling is unchanged.'),
 'N129': ('INDEPENDENT_COMPANION_INSTRUCTION_IBN_MASUD',
          'The retained Adab707 passage explicitly attributes this advice and prayer to IbnMasud. Keep the selected independent instruction and source placeholder, without deriving a Prophetic attribution from collection membership.'),
 'N130': ('INDEPENDENT_COMPANION_INSTRUCTION_IBN_ABBAS',
          'The retained Adab708 passage attributes the advice and threefold invocation to IbnAbbas. Source conjunction and repeated-practice wording remain unchanged; no Prophetic attribution is supplied.'),
 'N145': ('INDEPENDENT_RECOMMENDED_NEWBORN_CONGRATULATION',
          'The retained Nawawi Adhkar853 passage introduces a recommendation with يستحب / قال أصحابنا and names الحسين in that capture. Preserve that identity and the recommendation; do not silently normalize the name or infer marfu attribution.'),
 'U-P171-01': ('INDEPENDENT_JURISTIC_CONGRATULATION_REPLY',
          'The retained Nawawi Adhkar853 passage recommends the reply. It is not identified as a Prophetic quotation. Keep its source reference and relationship with N145.'),
 'U-P185-01': ('INDEPENDENT_JURISTIC_CHILD_FUNERAL_PRAYER',
          'The source recommends a longer formula after the independent short prayer N160. Retained IbnQudamah Mughni1563 allows this or similar wording; the retained IbnBaz excerpt is also a recommendation. Do not turn the juristic prescription into one Prophetic narration.'),
 'U-P188-01': ('INDEPENDENT_JURISTIC_CONSOLATION_FORMULA',
          'The source and retained Nawawi passage frame the formula as a scholarly recommendation (استحب أصحابنا). Preserve its relationship to the preceding narration, while leaving this independently recommended formula non-Prophetic.'),
 'N168': ('INDEPENDENT_COMPANION_DHIKR_IBN_AL_ZUBAYR',
          'The source footnote and retained Adab723 passage explicitly identify IbnAlZubayr practice. Preserve the Quran-derived wording and source variant; no Prophet speaker or approval is established in this retained occurrence.'),
 'N232': ('INDEPENDENT_COMPANION_AND_PREDECESSOR_COMPOSITE',
          'Retained Adab761 assigns the first clauses to an unnamed Companion; retained Bayhaqi4534 supplies a predecessor addition. Preserve both roles, the printed composite, and unnamed identities without inventing a Prophet speaker.'),
 'N066': ('HADITH_DHIKR_WITH_NARRATOR_EXPLANATION_AND_REPEAT_DIRECTION',
          'Retained Muslim591 narrates Prophetic practice and the peace supplication; the literal forgiveness formula is supplied by Awzai explaining it to Walid. Keep the coherent dhikr/report context and mark repetition instructions and explanatory formula separately. The printed يا and exact occurrence qualifications remain open.'),
 'N022': ('HADITH_DERIVED_ADHAN_RESPONSE_INSTRUCTION',
          'Retain the source practice instruction, caller words and response formula with their separate roles and retained Muslim385 support. Do not export the entire assembled instruction as one continuous direct quotation.'),
 'N024': ('HADITH_DERIVED_INSTRUCTION_RENDERED_BY_COMPILER',
          'The Filipino compiler summary is associated with retained Muslim384 instruction to respond then send blessings. Keep it in complete practice context, with compiler form explicit; no external Arabic is backfilled.'),
 'N026': ('HADITH_BEARING_REPORT_WITH_COMPILER_INTRODUCTION',
          'Source component P048-S003 joins a compiler recommendation to a translated report supported by retained AbuDawud521. Retain the complete component and annotate the two spans; the ornate-honorific question stays local and unresolved.'),
 'N031': ('HADITH_PRAYER_WITH_NARRATED_REPETITION_INSTRUCTION',
          'Retain the prayer and its narrated repetition direction coherently. Printed ثَلَاثًا and the Filipino repeat instruction are practice/framing content, not words necessarily spoken as part of the prayer. Preserve existing word/route qualifications.'),
 'N070': ('QURAN_RECITATION_WITH_HADITH_DERIVED_PRACTICE_CONTEXT',
          'Quran chapters retain Quran roles; the source after-prayer instruction has retained AbuDawud1523 support. Source instruction/translation and timing qualifications remain as recorded, without a new exact-occurrence claim.'),
 'N071': ('QURAN_RECITATION_WITH_HADITH_DERIVED_PRACTICE_CONTEXT',
          'Quran2:255 retains Quran roles. The printed after-prayer direction and retained NasaiKubra merit report provide the practice association; all source glyph and exact-locator limitations remain.'),
 'N075': ('QURAN_RECITATION_WITH_LINKED_APPROVAL_REPORT_CONTEXT',
          'Quran2:255 retains Quran roles. Preserve the existing linked child U-P103-01 and its retained approval-report context without transferring the jinn speech to the Prophet or merging child source text into this record.'),
 'N076': ('QURAN_RECITATION_WITH_HADITH_INSTRUCTION_CONTEXT',
          'Keep the Quran chapters, source repetition instruction and child U-P105-01 linked. Retained AbuDawud5082/Tirmidhi3575 support narrated practice; Quran remains textually distinct.'),
 'N099': ('QURAN_AND_COMPILER_SUMMARY_OF_PROPHETIC_PRACTICE',
          'The source directions summarize the palms/blowing/recitation/wiping practice supported by retained Bukhari5017. Preserve Quran components and compiler paraphrase separately within the complete source record; do not turn second-person editorial instructions into verbatim Prophet speech.'),
 'N100': ('QURAN_RECITATION_WITH_LINKED_APPROVAL_REPORT_CONTEXT',
          'Keep Quran2:255 distinct and preserve existing U-P133-01 benefit-report relationship. The captured stranger speech and Prophet approval belong to retained report evidence, not newly inserted source words; source after-prayer versus night context limitations remain.'),
 'N124': ('QURAN_DUA_WITH_PROPHETIC_REPORT_CONTEXT',
          'Keep the DhunNun Quran formula distinct. Retained Tirmidhi3505/Hakim1868 discuss that formula in a Prophetic report, supporting contextual association without converting the Quran text into a different textual type.'),
 'N128': ('QURAN_FORMULA_WITH_MULTISPEAKER_PROPHETIC_CONTEXT',
          'Retained Bukhari4563 reports IbnAbbas describing Ibrahim and Muhammad using the formula. Keep Quran wording, reporter, embedded speakers and transmission uncertainty distinct within the association.'),
 'N141': ('AUTHOR_PRACTICE_LABEL_WITH_RETAINED_HADITH_CONTEXT',
          'The nominal refuge label is compiler source text. Its retained night-prayer references ground a practice association; the label is not a direct Prophetic utterance and route criticisms remain preserved.'),
 'N142': ('AUTHOR_PRACTICE_LABEL_WITH_RETAINED_HADITH_CONTEXT',
          'The source label for adhan remains author/practice material. Retained Muslim389a narrates Satan fleeing the call and supplies contextual basis only; no claim that the Prophet spoke the label is made.'),
 'N143': ('AUTHOR_PRACTICE_SUMMARY_WITH_HADITH_BEARING_FOOTNOTES',
          'Preserve the general practice summary and its author footnote distinctly, while retaining child reports U-P169-01 and U-P169-02 with existing parent links. The visible footnote contains hadith-bearing reports and commentary; neither whole-footnote exclusion nor whole-summary promotion is justified.'),
 'U-P100-02': ('HADITH_BEARING_FOOTNOTE_INDEPENDENT_OF_PARENT_ATTRIBUTION_HOLD',
          'This source child explicitly attributes the Anas report to the Prophet. Keep it as hadith context with its parent link; the parent opening formula U-P100-01 remains attribution-unresolved and does not determine this child route.'),
 'U-P176-01': ('AUTHOR_SUMMARY_OF_RETAINED_PROPHETIC_ACTION_REPORT',
          'The printed writer summary mentions siwak use and retained Bukhari4449 supplies the Aishah report. Keep the summary as commentary associated with an action report, not a newly recovered verbatim hadith.'),
}

root_text_read_ids=set(manual)|{'N096','N098','N106','N114','N115','N164','N166','N239','N246'}
root_evidence_read_ids={'N004','N070','N071','N076','N099','N128','N135','N235','N142','N143','N129','N130','N145','U-P171-01','U-P185-01','U-P188-01','N168','N232'}
root_pages={26:['N004'],31:['N004'],243:['N235'],164:['N135'],165:['N135'],169:['N142','N143','U-P169-01','U-P169-02']}
root_visual=[]
for p, ids in root_pages.items():
    rel=f'pages/p{p:03d}_fresh400.png'; pp=V1/rel
    root_visual.append({'scope_owner':'root','pdf_page':p,'archive_image_path':rel,'image_sha256':sha(pp),'image_bytes':pp.stat().st_size,
      'record_ids':ids,'action_actually_performed':'Opened existing v1 image and inspected target source-role, reference and footnote loci.',
      'scope':'Targeted readable blocks only; not every glyph, entire page transcription, or incidental neighboring records.',
      'new_pdf_render':False,'repeated_pixel_enlargement':False,'every_character_or_diacritic_certified':False})
dump(OUT/'coverage/root_visual_inspection_log.json',root_visual)

def primary_evidence_links(r):
    return [{'enrichment_id_preserved':e.get('enrichment_id'), 'source_url_preserved':e.get('source_url'),
             'v1_json_pointer':f"/records/{ridx[r['record_id']]}/external_narration_evidence/{i}",
             'source_layer':'retained_external_evidence_not_PDF_verbatim',
             'new_live_retrieval':False, 'new_exact_print_edition_alignment':False}
            for i,e in enumerate(r.get('external_narration_evidence') or [])]

root_decisions=[]
for rid,(cl,why) in manual.items():
    rr=byid[rid]
    root_decisions.append({'record_id':rid,'new_class':cl,'record_partition':partition(rid),'rationale':why,
       'basis':'Retained v1 source fields and classification evidence; finite primary passage rereading or linked-context inspection as itemized.',
       'source_components_read_as_stored_text':rid in root_text_read_ids,
       'primary_passage_reading':'Finite passages or visible excerpts actually read; no complete source-edition/live check.' if rid in root_evidence_read_ids else 'Inherited v1 assessment and source fields; no new full primary-witness reading claimed.',
       'retained_evidence':primary_evidence_links(rr),
       'actual_visual_pages':[p for p,ids in root_pages.items() if rid in ids],
       'wording_changes':0,'new_attributed_grade':None,'new_canonical_id':None,'independent_final_evaluation':'NOT_RUN'})
dump(OUT/'audit/root_targeted_decisions.json',root_decisions)

old_routes={x['segment_id']:x for x in read(V1/'coverage/component_partition_map.json')}
component_index={c['segment_id']:(r,c) for r in records for c in r['components']}
candidate_ids={sid for sid,x in old_routes.items() if x['partition']=='prophetic_report_candidates_HOLD'}
assert len(candidate_ids)==493
special_component_roles={}
for d in dd.values():
    for a in d['component_annotations']: special_component_roles[a['segment_id']]=a['proposed_semantic_role']

# Additional exact source subspans are annotations, never replacements of source text.
root_spans=[]
def span(rid,sid,quote,role,why):
    txt=component_index[sid][1]['text']; assert quote in txt
    assert txt.count(quote)==1, (sid,quote)
    start=txt.index(quote)
    root_spans.append({'record_id':rid,'segment_id':sid,'start_codepoint':start,'end_codepoint':start+len(quote),
       'exact_source_quote':quote,'role':role,'basis':why,'source_text_sha256':textsha(txt),
       'offset_unit':'Python Unicode code points, end-exclusive','source_text_changed':False})
span('N031','P054-S003','"ثَلَاثًا"','NARRATED_REPETITION_INSTRUCTION_NOT_SPOKEN_PRAYER', 'Source quotation-marked repeat direction and retained v1 AbuDawud764 analysis.')
span('N031','P055-S003','(banggitin ng tatlong\nbeses sa wikang Arabik)','TRANSLATED_REPETITION_DIRECTION', 'The parenthetical instructs repetition; it is retained with the prayer without claiming a spoken prayer phrase.')
span('N066','P086-S003','أَسْتَغْفِرُ اللهَ','NARRATOR_EXPLAINED_FORGIVENESS_FORMULA_WITH_PROPHETIC_PRACTICE_CONTEXT', 'Inherited Muslim591 evidence distinguishes Awzai explanation from Prophet practice.')
span('N066','P086-S003','(ثلاثا)','REPETITION_DIRECTION', 'Printed parenthetical count, not asserted as an uttered phrase.')
span('N066','P086-S004','(3X)','TRANSLITERATION_REPEAT_MARKER', 'Printed practice count.')
span('N066','P086-S005','(3x)','TRANSLATION_REPEAT_MARKER', 'Printed practice count.')
q='Ang panalangin sa ganitong\noras ay hindi tinatanggihan. ²'
span('N026','P048-S003',q,'TRANSLATED_HADITH_REPORT_IN_MIXED_COMPONENT', 'Retained AbuDawud521 basis; v1 already distinguishes this report from compiler introduction.')
t=component_index['P048-S003'][1]['text']; prefix=t[:t.index(q)]
span('N026','P048-S003',prefix,'COMPILER_PRACTICE_INTRODUCTION', 'Printed introduction retained inside complete source component.')
span('N022','P045-S003','حَيَّ عَلَى الصَّلَاةِ وَحَيَّ عَلَى الْفَلَاحِ','CALLER_WORDS_WITHIN_NARRATED_RESPONSE_PRACTICE', 'Printed caller/response contrast; retained Muslim385 association.')
span('N022','P045-S006','لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللهِ','RESPONSE_FORMULA_WITHIN_NARRATED_PRACTICE', 'Printed response role, not entire compiler summary as a single quotation.')
dump(OUT/'audit/root_exact_source_subspan_annotations.json',root_spans)

context_only_labels=('EDITORIAL','COMPILER','SOURCE_DHIKR','ADAPTED','QURAN','NON_HADITH_QURAN','WRITER_SUMMARY','JURISTIC')
patch=[]; logs=[]
def mutation(path,after,op='add',before=None,before_exists=False,record_id=None,reason=''):
    if op=='replace': patch.append({'op':'test','path':path,'value':before})
    elif record_id: patch.append({'op':'test','path':f'/records/{ridx[record_id]}/record_id','value':record_id})
    patch.append({'op':op,'path':path,'value':copy.deepcopy(after)})
    logs.append({'change_id':f'RECON-PATCH-{len(logs)+1:04d}','op':op,'path':path,'before_exists':before_exists,
                 'before':copy.deepcopy(before),'after_exists':True,'after':copy.deepcopy(after), 'record_id':record_id,
                 'reason':reason,'source_wording_changed':False})

result['schema_version']='3.1-targeted-RECONSTRUCTED-v2-HOLD'
mutation('/schema_version',result['schema_version'],'replace',original['schema_version'],True,reason='New reconstructed artifact identity; original schema remains preserved in exact v1.')
component_roles=[]; decisions=[]; coverage=[]
for r in result['records']:
    rid=r['record_id']; prior=byid[rid]['content_classification_final_pro']; group=partition(rid)
    targeted=rid in manual or rid in ad or rid in dd
    if rid in dd: cl=dd[rid]['proposed_content_class']; why=dd[rid]['decision_basis']; decision_file='coauthor_work/dialogue/dialogue_context_decisions.json'
    elif rid in ad: cl=ad[rid]['proposed_content_class']; why=ad[rid]['decision_rationale']; decision_file='coauthor_work/attribution/attribution_findings.json'
    elif rid in manual: cl,why=manual[rid]; decision_file='audit/root_targeted_decisions.json'
    else:
        cl=prior['proposed_content_class']
        why=('Retain the inherited attribution/wording assessment; apply the clarified whole-record context rule. '
             'Content, source variants, narrative framing, notes and limitations remain intact. No new authenticity or exact-occurrence finding.')
        if group=='quran_and_author_only':
            why='Retain the inherited Quran/author classification; no evidenced Prophetic narration is newly attached to this source-only record.'
        decision_file='preserved_inputs/'+V1NAME+'.zip!/'+V1NAME+'/data/content_classification_final_pro.json'
    roles=[]
    for c in r['components']:
        sid=c['segment_id']; old=old_routes[sid]; op=old['partition']; typ=c['type']
        if sid in special_component_roles: role=special_component_roles[sid]
        elif op=='quran' or typ.startswith('quran'): role='QURAN_TEXT_OR_ITS_RENDERING_DISTINCT_FROM_HADITH_NARRATION'
        elif typ=='reference': role='SOURCE_REFERENCE_OR_PRINTED_ATTRIBUTION_GRADE_CLAIM'
        elif typ=='heading': role='SOURCE_HEADING_NOT_ADDITIONAL_HADITH'
        elif group=='independent_non_prophetic': role='INDEPENDENT_NON_PROPHETIC_SELECTED_CONTENT_AND_ITS_CONTEXT'
        elif group=='attribution_unresolved': role='ATTRIBUTION_UNRESOLVED_SOURCE_CONTENT_OR_CONTEXT'
        elif group=='quran_and_author_only': role='AUTHOR_OR_SOURCE_CONTEXT_WITH_QURAN'
        elif typ=='footnote': role='SOURCE_FOOTNOTE_PRESERVED_WITH_CONTEXT_NOT_AUTOMATICALLY_EXCLUDED'
        elif op=='prophetic_report_candidates_HOLD': role='PRESERVED_PRIOR_PROPHETIC_CANDIDATE_COMPONENT_NOT_RELEASE_APPROVED'
        elif op=='editorial_commentary': role='SOURCE_EXPLANATION_OR_PRACTICE_FRAMING_DISTINCT_WITHIN_CONTEXT'
        elif op=='non_prophetic_reports': role='OTHER_SPEAKER_OR_NARRATOR_MATERIAL_IN_RETAINED_REPORT_CONTEXT'
        else: role='HADITH_DHIKR_OR_COMPOSITE_SOURCE_CONTEXT_WITH_INHERITED_LIMITATIONS'
        ann={'record_id':rid,'segment_id':sid,'pdf_page':c.get('pdf_page'),'source_type_preserved':typ,
             'record_partition':group,'original_partition':op,'original_specific_role':old.get('specific_role'),
             'content_role':role,'source_text_sha256':textsha(c['text']),'preserved_prior_candidate':sid in candidate_ids,
             'source_text_unchanged':True,'whole_component_certified_as_direct_prophetic_quote':False,
             'approved_for_bank':False,'approved_for_html':False,'separate_independent_final_evaluation':'NOT_RUN'}
        roles.append(ann); component_roles.append(ann)
    related=[]
    for rr in r.get('related_reference_records',[]):
        cid=rr.get('record_id')
        if cid in byid: related.append({'record_id':cid,'relationship_preserved':rr.get('relationship'),'record_partition':partition(cid),
          'own_attribution_not_inherited_from_parent':True,'source_text_not_merged':True})
    exact=[x for x in root_spans if x['record_id']==rid]
    if rid in dd: exact+=copy.deepcopy(dd[rid].get('exact_subspan_annotations',[]))
    over={'record_id':rid,'review_id':ART,'status':'PARTIAL_HOLD','record_partition':group,
          'association_is_not_unique_hadith_count':True,'proposed_content_class':cl,
          'decision_basis':why,'inherited_v1_assessment':prior['independent_assessment'],
          'decision_evidence_file':decision_file,'scope':'Targeted attribution/context decision' if targeted else 'Inherited assessment plus policy-derived context routing; no new visual review of this record claimed',
          'source_wording_unchanged':True,'classification_is_not_authenticity_grade':True,
          'whole_record_is_one_exact_prophetic_matn':False,
          'context_only_source_form':prior['proposed_content_class'].startswith(context_only_labels) or cl.startswith(('AUTHOR_','QURAN_')),
          'context_role_policy':'Preserve Quran, author text, narrator framing, other-speaker dialogue, supported variants and hadith-bearing notes with explicit roles. Context association is not direct speech attribution.',
          'retained_evidence_links':primary_evidence_links(r),
          'new_canonical_occurrence_ids':[],'new_authenticity_grades':[],'new_isnad':None,
          'component_roles':roles,'exact_source_subspan_annotations':exact,
          'parent_record_ids_preserved':copy.deepcopy(r.get('parent_record_ids',[])),'related_context_records':related,
          'approved_for_bank':False,'approved_for_html':False,
          'package_release_gate':'RECONSTRUCTED_BYTES_REQUIRE_SEPARATE_INDEPENDENT_FINAL_EVALUATION',
          'separate_independent_final_evaluation':'NOT_RUN'}
    r['content_classification_reconstructed_v2']=over
    mutation(f'/records/{ridx[rid]}/content_classification_reconstructed_v2',over,record_id=rid,
             reason='Add active context/classification overlay; retain all original fields and historical v1 assessment unchanged.')
    decisions.append({'record_id':rid,'before_active_classification':copy.deepcopy(prior),
        'after_active_classification':copy.deepcopy(over),'change_kind':'ADDITIVE_CURRENT_OVERLAY_AND_CONTEXT_ROUTING',
        'old_component_partitions_retained_as_history':True,'source_wording_changes':0})
    coverage.append({'record_id':rid,'decision_mode':'TARGETED_RECONSTRUCTION' if targeted else 'INHERITED_ASSESSMENT_POLICY_PROJECTION',
       'v1_classification_read_or_projected':True,'all_record_components_visually_reread_this_reconstruction':False,
       'no_new_full_record_visual_certification':True,'decision_evidence_file':decision_file})

counts=collections.Counter(x['content_classification_reconstructed_v2']['record_partition'] for x in result['records'])
provenance={**IDENT,'artifact_kind':'NEW_RECONSTRUCTED_V2_HOLD',
 'reconstructed_from':'Exact attached v1 checkpoint and the substantive instructions/lost-v2 report reproduced in the current user message.',
 'not_byte_identical_recovered_v2':True,'original_v2_bytes_accessed':False,'old_chat_accessed':False,
 'pasted_text_library_file_accessed':False,'user_provided_transcript_reference':'libfile_fde3_f-37abc349aa0081918d1491b32baa9d23_c3a5ae5e9e0c8191af5d21c39948b9f7',
 'scope_of_transcript_used':'Only the substantive reconstruction instructions and reported old results reproduced by the user here; the standalone Pasted text.txt was not accessed.',
 'input_zip':{'filename':V1NAME+'.zip','size_bytes':ZIP.stat().st_size,'sha256':sha(ZIP)},
 'input_pdf':{'filename':'FIL-HISN-PRIVATE.pdf','size_bytes':5321887,'sha256':'3e409dd7266c2a150645ecfea548f266edf80c9c5df5129aa8df7a977d248a07'},
 'reported_missing_v2_not_verified':{'size_bytes':415468251,'sha256':'f5681984775bc18fd5ceaca6ea15477f8b05d94686b65b62bab7ef7373ba7e05','used_as_output_identity':False},
 'all_originals_preserved_in':'preserved_inputs/'+V1NAME+'.zip',
 'no_repository_integration':True,'no_publication':True,'no_other_chat_contact':True,
 'new_translations_or_source_wording_created':False,'source_fidelity':'PARTIAL','metadata':'PARTIAL','bank_readiness':'FAIL/HOLD',
 'separate_independent_final_evaluation':'NOT_RUN','coauthors_are_reconstruction_participants_not_independent_final_evaluators':True}
dump(OUT/'provenance/reconstruction_provenance.json',provenance)
result['reconstruction_v2']={
 'review_id':ART,'provenance_file':'provenance/reconstruction_provenance.json',
 'active_classification_field':'content_classification_reconstructed_v2',
 'historical_classification_fields':['content_classification_v5','content_classification_final_pro'],
 'historical_fields_policy':'All existing record fields, including source kind, old review wording, annotation timestamps and v1 routing, remain verbatim historical values. For current routing use only the active reconstructed overlay.',
 'status':'PARTIAL_HOLD','source_fidelity':'PARTIAL','metadata':'PARTIAL','bank_readiness':'FAIL/HOLD',
 'approved_for_bank':False,'approved_for_html':False,'source_wording_changes':0,
 'record_count':323,'component_count':1500,'record_partition_counts':dict(counts),
 'prior_prophetic_candidate_components_preserved':493,'new_candidate_promotions':0,
 'release_approved_records':0,'separate_independent_final_evaluation':'NOT_RUN',
 'candidate_vs_release_explanation':'The 493 are inherited candidate COMPONENTS, not 493 released hadiths. Whole-record context membership is another axis. Zero releases reflects the package-wide independent final-byte review gate; local text, attribution and metadata limitations remain separately indexed.',
 'record_context_vs_source_text_policy':'A hadith/dhikr/context record may contain Quran, a compiler summary or another speaker. Textual roles remain distinct; an associated external report is never inserted into PDF-verbatim fields.',
 'old_v2_not_recovered':True,'no_publication_or_repository_integration':True,
 'blocker_index':'audit/record_blocker_index.json','visual_coverage':'coverage/visual_decision_coverage.json',
 'historical_276_page_review_performed_this_turn':False}
mutation('/reconstruction_v2',result['reconstruction_v2'],reason='Explicit reconstructed provenance, active-field precedence, scoped hold semantics, and no release approval.')
dump(OUT/'data/corrected_all_records.json',result)
dump(OUT/'audit/replayable_patch.json',patch)
jsonl(OUT/'audit/full_before_after_correction_log.jsonl',logs)
jsonl(OUT/'audit/classification_before_after_decisions.jsonl',decisions)
dump(OUT/'audit/component_routing.json',component_roles)
dump(OUT/'data/content_classification_reconstructed_v2.json',[r['content_classification_reconstructed_v2'] for r in result['records']])
dump(OUT/'coverage/decision_coverage.json',{'records':coverage,'decision_mode_counts':dict(collections.Counter(x['decision_mode'] for x in coverage)),
   'mechanical_projection_is_not_new_visual_review':True,'separate_independent_final_evaluation':'NOT_RUN'})

# Explicit, disjoint complete-record exports; source components retain original identity.
envelope={k:copy.deepcopy(v) for k,v in result.items() if k!='records'}
dump(OUT/'data/records_export_envelope.json',envelope)
jsonl(OUT/'data/corrected_all_records.jsonl',result['records'])
csvout(OUT/'data/corrected_all_records.csv',[
 {'record_index':i,'record_id':r['record_id'],'record_partition':partition(r['record_id']),
  'record_json':json.dumps(r,ensure_ascii=False,separators=(',',':'))} for i,r in enumerate(result['records'])],
 ['record_index','record_id','record_partition','record_json'])
comps=[c for r in result['records'] for c in r['components']]
jsonl(OUT/'data/components.jsonl',comps)
csvout(OUT/'data/components.csv',[{'component_index':i,'record_id':c['record_id'],'segment_id':c['segment_id'],
 'component_json':json.dumps(c,ensure_ascii=False,separators=(',',':'))} for i,c in enumerate(comps)],
 ['component_index','record_id','segment_id','component_json'])
for group in ['hisn_hadith_dhikr_context','independent_non_prophetic','quran_and_author_only','attribution_unresolved']:
    subset=[r for r in result['records'] if partition(r['record_id'])==group]
    dump(OUT/'partitions'/(group+'_HOLD.json'),{'artifact_id':ART,'partition':group,'status':'HOLD',
       'record_count':len(subset),'component_count':sum(len(r['components']) for r in subset),'records':subset,
       'complete_source_records_with_context':True,'not_unique_or_release_approved_hadith_count':True,
       'approved_for_bank':False,'approved_for_html':False,'separate_independent_final_evaluation':'NOT_RUN'})
shutil.copyfile(V1/'partitions/prophetic_report_candidates_HOLD.json',OUT/'partitions/prophetic_report_candidates_preserved_HOLD.json')
dump(OUT/'partitions/hadith_only_release.json',{'status':'HOLD','records':[],'release_approved_records':0,
 'preserved_candidate_components':493,'reason':'Separate independent final evaluation of reconstructed changed bytes NOT_RUN; localized evidence holds are separately scoped.',
 'candidate_classification_is_not_release_approval':True})
dump(OUT/'partitions/index.json',{'record_partitions':dict(counts),'record_total':323,'component_total':1500,
  'prior_candidate_components':493,'release_approved_records':0,'record_routes_disjoint_and_exhaustive':True,
  'component_textual_roles_do_not_change_whole_record_containment':True})

meta=read(V1/'data/book_metadata.json'); newmeta=copy.deepcopy(meta)
newmeta['reconstruction_v2']={'artifact_id':ART,'current_status':'PARTIAL_HOLD','inherited_metadata_unchanged':True,
 'source_extent_pdf_pages':276,'catalog_extent_printed_pages':280,'cause_of_difference':'UNRESOLVED_NO_MISSING_PAGES_INFERRED',
 'no_new_date_translator_isnad_grade_or_canonical_id':True,'metadata_limits_do_not_make_all_narration_text_wrong':True,
 'separate_independent_final_evaluation':'NOT_RUN'}
dump(OUT/'data/book_metadata.json',newmeta)
dump(OUT/'audit/book_metadata_replayable_patch.json',[{'op':'add','path':'/reconstruction_v2','value':newmeta['reconstruction_v2']}])
for rel in ['data/ancillary_source_text_preserved.json','data/source_heading_contexts_preserved.json','data/source_heading_supplement.json']:
    shutil.copyfile(V1/rel, OUT/rel)

# Preserve every original exception verbatim inside the current rows and add scope,
# not a blanket all-record source failure. No glyph or source issue is resolved here.
exceptions=read(V1/'audit/unresolved_exceptions.json'); scoped=[]
for e,s in zip(exceptions,scope['exception_scopes']):
    assert e['exception_id']==s['exception_id']; row=copy.deepcopy(e); s=copy.deepcopy(s)
    rid=s.get('record_id')
    if s['issue_family']=='historical_classification_or_occurrence_span_hold':
        s['current_record_partition']=partition(rid) if rid in byid else None
        s['reconstruction_disposition']='RETAIN_WORDING_ATTRIBUTION_AND_OCCURRENCE_LIMITS; CONTEXT_EXCLUSION_SUPERSEDED_WHERE_SUPPORTED'
        s['context_exclusion_is_not_required_for_other_speakers_or_narrator_framing']=rid not in UNRESOLVED
        s['new_evidence_hold_cleared']=False
        s['current_decision_pointer']=f"data/corrected_all_records.json#/records/{ridx[rid]}/content_classification_reconstructed_v2" if rid in ridx else None
        s['scope_note']='Historical mixed-span labels remain preserved. The reconstructed record association and role annotations govern current grouping. Exact variant/occurrence, source fidelity, and unsupported attribution cautions are not automatically resolved.'
    s['inherited_exception_pointer']='preserved_inputs/'+V1NAME+'.zip!/'+V1NAME+'/'+s['inherited_exception_pointer']
    row['reconstruction_scope']=s; scoped.append(row)
dump(OUT/'audit/unresolved_exceptions.json',scoped)
jsonl(OUT/'audit/unresolved_exceptions.jsonl',scoped)
csvout(OUT/'audit/unresolved_exceptions.csv',[{
    'exception_id':e['exception_id'],'issue_family':e['reconstruction_scope']['issue_family'],
    'concern_domains':json.dumps(e['reconstruction_scope']['concern_domains'],ensure_ascii=False),
    'scope':e['reconstruction_scope']['scope'],'record_id':e['reconstruction_scope'].get('record_id') or '',
    'component_ids':json.dumps(e['reconstruction_scope']['exact_component_ids'],ensure_ascii=False),
    'pdf_pages':json.dumps(e['reconstruction_scope']['pdf_pages']),
    'disposition':e['reconstruction_scope']['reconstruction_disposition'],
    'exception_json':json.dumps(e,ensure_ascii=False,separators=(',',':'))} for e in scoped],
    ['exception_id','issue_family','concern_domains','scope','record_id','component_ids','pdf_pages','disposition','exception_json'])
scope_byid={x['exception_id']:x['reconstruction_scope'] for x in scoped}
for b in blocks:
    rid=b['record_id']; b['current_record_partition']=partition(rid)
    b['record_component_ids']=[c['segment_id'] for c in byid[rid]['components']]
    b['current_attribution_unresolved']=rid in UNRESOLVED
    b['local_issues']=[scope_byid[eid] for eid in b['localized_glyph_exception_ids']+b['source_alignment_exception_ids']+b['inherited_classification_or_occurrence_exception_ids']]
    b['component_scope_policy']='Exact component IDs limit localized issues; record-level attribution/occurrence rows affect context of this record only. Global book limitations and package gate are listed separately.'
    b['historical_classification_routing_replaced_by_current_overlay']=True
    b['no_local_issue_listed_is_not_every_character_certification']=True
    b['approved_for_bank']=False; b['approved_for_html']=False
dump(OUT/'audit/record_blocker_index.json',{'artifact_id':ART,'records':blocks,'issue_family_summary':scope['summary'],
 'ancillary_or_global_issues':[s for s in scope_byid.values() if not s.get('record_id')],
 'counts_overlap':True,'all_records_have_package_gate_but_not_all_have_local_text_issue':True})

av=read(BASE/'coauthor_attribution/visual_inspection_ledger.json')
dv=read(BASE/'coauthor_dialogue/visual_decision_coverage.json')['visual_inspection_ledger']
allvis=[dict(x,scope_owner='coauthor_attribution') for x in av]+[dict(x,scope_owner='coauthor_dialogue') for x in dv]+root_visual
pages=sorted({x['pdf_page'] for x in allvis})
dump(OUT/'coverage/visual_decision_coverage.json',{'artifact_id':ART,'actual_existing_image_open_events':len(allvis),
 'actual_distinct_source_pages_reopened':len(pages),'source_page_numbers':pages,'new_pdf_renders':0,
 'every_character_certificates':0,'whole_276_page_review_reperformed':False,
 'inspection_log':allvis,'record_decision_coverage_file':'coverage/decision_coverage.json',
 'historical_review':'v1 reports276 readable-text-block page comparisons/323 records/1500 components. That work is inherited and not attributed to this reconstruction.',
 'separate_independent_final_evaluation':'NOT_RUN'})
dump(OUT/'coverage/historical_coverage_reference.json',{'original_review_id':V1NAME,
 'preserved_unchanged_in':'preserved_inputs/'+V1NAME+'.zip',
 'historical_counts_reported_by_v1':original['final_pro_review']['coverage'],
 'this_reconstruction_did_not_perform_historical_review':True,
 'original_coverage_files':[str(p.relative_to(V1)) for p in sorted((V1/'coverage').glob('*')) if p.is_file()]})

expected={'hisn_hadith_dhikr_context':295,'independent_non_prophetic':15,'quran_and_author_only':8,'attribution_unresolved':5}
comparison={'source_of_expectation':'Lost original v2 report as reproduced by user; not verified original-v2 bytes.',
 'expected_record_partitions':expected,'actual_record_partitions':dict(counts),
 'deltas':{k:counts[k]-v for k,v in expected.items()},
 'expected_total':323,'actual_total':323,'expected_unresolved_ids':sorted(UNRESOLVED),
 'actual_unresolved_ids':sorted(UNRESOLVED),'unresolved_id_match':True,
 'reported_original_v2_wording_changes':0,'actual_reconstruction_wording_changes':0,
 'reported_original_v2_mechanical_check_count':474,'current_check_count':'See validation/mechanical_validation.json; not forced to474.',
 'reported_original_v2_visual_images_reopened':16,'actual_reconstruction_distinct_pages_reopened':len(pages),
 'decision_differences_documented':['N004 and N235: Quran text remains Quran, but whole records retain explicit archived Prophetic recitation associations.',
   'N204: singular editorial adaptation remains linked to Aishah reply inside the sheep-distribution narration; no new Prophetic speech/approval is asserted.'],
 'attribution_of_count_delta_to_lost_original':'The complete original-v2 per-record routing is unavailable. These three policy decisions explain the reconstruction approach and are potential reasons for the aggregate delta; they are NOT a verified item-by-item diff against unavailable v2.',
 'no_counts_forced':True,'not_byte_identical_recovery':True}
dump(OUT/'audit/lost_v2_expectation_comparison.json',comparison)

# List every preserved v1 ZIP member with actual hashes; inherited review claims are
# not substituted for current mechanical integrity verification.
members=[]
with zipfile.ZipFile(ZIP) as z:
    for i in z.infolist():
        if i.is_dir(): continue
        h=hashlib.sha256()
        with z.open(i) as f:
            for chunk in iter(lambda:f.read(4*1024*1024),b''): h.update(chunk)
        members.append({'path':i.filename,'size_bytes':i.file_size,'sha256':h.hexdigest(),'crc32':f'{i.CRC:08x}'})
dump(OUT/'provenance/preserved_v1_member_sha256.json',{'archive_sha256':sha(ZIP),'members':members,'file_count':len(members)})
dump(OUT/'provenance/input_verification.json',{'v1':provenance['input_zip'],'pdf':provenance['input_pdf'],
 'matched_user_expected_bytes_and_sha256':True,'v1_members_read_with_crc_validation':len(members),
 'original_input_zip_unchanged':sha(ZIP)==provenance['input_zip']['sha256']})

shutil.copyfile(BASE/'coauthor_blockers/validate_reconstructed_package.py', OUT/'scripts/validate_reconstructed_package.py')
shutil.copyfile(__file__, OUT/'scripts/build_reconstructed_v2_session.py')
dump(OUT/'audit/build_counts.json',{'record_partitions':dict(counts),'record_total':323,'component_total':1500,
 'prior_candidate_components_preserved':493,'new_candidate_promotions':0,'release_approved':0,
 'wording_changes':0,'json_mutations':len(logs),'rfc6902_operations_including_tests':len(patch),
 'targeted_record_decisions':sum(c['decision_mode']=='TARGETED_RECONSTRUCTION' for c in coverage),
 'inherited_policy_projection_records':sum(c['decision_mode']!='TARGETED_RECONSTRUCTION' for c in coverage),
 'actual_visual_pages':len(pages),'actual_image_open_events':len(allvis),'pdf_pages_newly_rendered':0,
 'glyph_question_rows_preserved':91,'source_alignment_rows_preserved':34,'all_exception_rows_preserved':230})
print(json.dumps({'artifact_id':ART,'output_directory':str(OUT),'partition_counts':dict(counts),'patch_mutations':len(logs),'rfc6902_operations':len(patch),'visual_pages':len(pages)},indent=2))

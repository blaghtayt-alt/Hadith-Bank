from pathlib import Path
import json, hashlib, datetime

BASE = Path('/workspace/scratch/d183b7a47e4b/reconstruction/v1_extracted/FIL_HISN_FINAL_PRO_REVIEW_20261112_HOLD_v1')
OUT = Path(__file__).parent
records = {r['record_id']: r for r in json.loads((BASE/'data/corrected_all_records.json').read_text())['records']}

def sha(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()

def quoted(file, pointer, quote, scope):
    return {'source_file': file, 'json_pointer_or_locus': pointer,
            'verbatim_anchor': quote, 'scope': scope, 'new_live_retrieval': False}

E = 'inputs/FIL_HISN_QC_v5_REVIEW_PACKAGE.zip!/'
configs = {
 'N007': {
  'route': 'independent_non_prophetic_HOLD',
  'content_class': 'INDEPENDENT_COMPANION_CUSTOM_GREETING_REPORTED_BY_ABU_NADRA',
  'speaker': 'Unspecified speaker in the greeting said to a Companion; Abu Nadra is the reporter, not an identified speaker of the greeting.',
  'reason': 'The selected greeting is the appended custom report introduced by Abu Nadra after a distinct Prophetic clothing supplication. The captured witness does not say that the Prophet said or approved this particular greeting. Preserve its collection context and distinguish the selected independent formula; do not transfer the preceding Prophetic attribution to it.',
  'pages': [33],
  'evidence': [quoted(E+'evidence/early/sources/sunnah_com_abudawud_4020.json','/arabic/0/text','قَالَ أَبُو نَضْرَةَ فَكَانَ أَصْحَابُ النَّبِيِّ','Appended custom-report transition; entire retained passage was read, including preceding Prophetic clause.'), quoted('data/corrected_all_records.json','N007/P033-S010','¹. Abu Dawud 4/41. Tingnan ang Sahih Abi Dawud 2/760.','Printed source reference, visually inspected on p33; exact edition equivalence remains unverified.')]
 },
 'N118': {
  'route': 'independent_non_prophetic_HOLD',
  'content_class': 'INDEPENDENT_COMPANION_QUNUT_UMAR',
  'speaker': 'Umar, as printed in the Filipino source footnote and the retained Bayhaqi occurrence.',
  'reason': 'The Filipino footnote attributes this qunut to Umar. The retained Bayhaqi passage reports hearing Umar recite it. Its chain assessment is a separate matter from who speaks. No Prophetic attribution is added.',
  'pages': [151],
  'evidence': [quoted('data/corrected_all_records.json','N118/p151-r004','sa mga kasabihan ni Umar.','Visible ending of the source footnote.'), quoted(E+'qc_v5/reviews/middle_a/evidence/reused_primary/V3-EXT-N118-bayhaqi_sunan-3187.json','/external_arabic_verbatim','صليت خلف عمر بن الخطاب رضي الله عنه صلاة الصبح، فسمعته يقول','Umar is the reciter. Retained source-specific display3187 is not newly verified against the printed edition.')]
 },
 'N160': {
  'route': 'independent_non_prophetic_HOLD',
  'content_class': 'INDEPENDENT_COMPANION_FUNERAL_DUA_ABU_HURAYRA',
  'speaker': 'Abu Hurayra in the retained Muwatta occurrence.',
  'reason': 'The p185 formula is matched by the retained Muwatta report in which Said ibn al-Musayyab hears Abu Hurayra pray over a child. The selected clause is not raised to the Prophet in this evidence. The neighboring long compiler-recommended prayer remains a separate linked record and is not merged into this attribution.',
  'pages': [185],
  'evidence': [quoted(E+'qc_v5/reviews/middle_b/evidence/V5-MB-REUSE-V3-EXT-N160-malik_muwatta-776.json','/external_arabic_verbatim','صَلَّيْتُ وَرَاءَ أَبِي هُرَيْرَةَ عَلَى صَبِيٍّ','Explicit observed reciter; retained passage continues with the matching prayer.'), quoted('data/corrected_all_records.json','N160/p185-r003','اللَّهُمَّ أَعِذْهُ مِنْ عَذَابِ الْقَبْرِ','Readable formula and adjacent separate recommendation visually inspected; no fine-character certificate.')]
 },
 'N161': {
  'route': 'independent_non_prophetic_HOLD',
  'content_class': 'INDEPENDENT_SUCCESSOR_FUNERAL_DUA_AL_HASAN_AL_BASRI',
  'speaker': 'Al-Hasan al-Basri, successor; not a Companion.',
  'reason': 'The printed footnote names Al-Hasan (Al-Basri). The retained Ayni passage quotes and identifies al-Hasan al-Basri. Keep the successor attribution and the prayer together. The Filipino wording issue concerning isanasaulo is not corrected or conflated with attribution.',
  'pages': [187],
  'evidence': [quoted('data/corrected_all_records.json','N161/p187-r010','Kalimitan ang ginagawa ni Al-Hasan (Al-Basri)','Visible source footnote attribution.'), quoted(E+'qc_v5/reviews/middle_b/evidence/V5-MB-REUSE-V3-EXT-N161-ayni_umdat_alqari-mainId394052.json','/external_arabic_verbatim','الحسن هو البصري','Explicit identification in retained commentary, read together with its quoted chapter statement.')]
 },
 'N177': {
  'route': 'independent_non_prophetic_HOLD',
  'content_class': 'INDEPENDENT_COMPANION_IFTAR_DUA_ABDULLAH_IBN_AMR',
  'speaker': 'Abdullah ibn Amr, as printed in the footnote and appended report.',
  'reason': 'The source footnote calls this Abdullah bin Amr\'s prayer. Ibn Majah1753 contains a preceding Prophetic teaching about a fasting person\'s supplication, then a distinct report of Abdullah ibn Amr\'s own formula. Preserve both roles in external context; the preceding Prophetic teaching does not make the selected appended formula the Prophet\'s words.',
  'pages': [198],
  'evidence': [quoted('data/corrected_all_records.json','N177/p198-r009','mula sa dalangin ni Abdullah bin Amr.','Printed attribution visually inspected.'), quoted(E+'evidence/middle/source_evidence.json','/sources/82/selected_arabic_evidence','قَالَ ابْنُ أَبِي مُلَيْكَةَ سَمِعْتُ عَبْدَ اللَّهِ بْنَ عَمْرٍو يَقُولُ إِذَا أَفْطَرَ','Distinct appended Companion formula after the Prophetic premise; complete selected passage read.')]
 },
 'N225': {
  'route': 'independent_non_prophetic_HOLD',
  'content_class': 'INDEPENDENT_COMPANION_SAYING_AMMAR',
  'speaker': 'Ammar, as explicitly printed and retained in the Bukhari chapter quotation.',
  'reason': 'The printed footnote attributes the virtues to Ammar and the retained chapter quotation says وقال عمار. Keep this source attribution. Historical commentary claims about hukm-marfu or other raised routes do not establish the exact printed occurrence as a direct Prophetic saying, and no grade is assigned here.',
  'pages': [236],
  'evidence': [quoted('data/corrected_all_records.json','N225/p236-r005','kasamahan na si ‘Ammar.','Visible printed attribution.'), quoted(E+'evidence/late/bukhari_iman_ammar_chapter.json','/arabic_lines/1','وَقَالَ عَمَّارٌ:','Explicit Companion chapter quotation; no numbered following hadith is substituted.')]
 },
 'N015': {
  'route': 'attribution_unresolved_HOLD',
  'content_class': 'DHIKR_WITH_DISPUTED_RAISED_VERSUS_STOPPED_ATTRIBUTION',
  'speaker': None,
  'reason': 'The retained Nasai10019 passage displays a raised route and the compiler\'s correction that the correct route is stopped. This is a route-specific attribution conflict, not merely a weak grade. Preserve the dhikr as devotional/report material with unresolved attribution; do not label it definitively non-hadith or certify direct Prophetic wording.',
  'pages': [37],
  'evidence': [quoted('data/corrected_all_records.json','N015/P037-S008','An-Nasa’i, ‘Amal al-Yawm wal-Lailah, p. 173.','Printed reference inspected; no canonical/edition equivalence newly assigned.'), quoted(E+'evidence/early/sources/islamweb_nasai_kubra_10019.json','/arabic/1/text','هَذَا خَطَأٌ ، وَالصَّوَابُ مَوْقُوفٌ','Compiler explicitly critiques attribution of the preceding raised route.')]
 },
 'N083': {
  'route': 'attribution_unresolved_HOLD',
  'content_class': 'DHIKR_WITH_PRINTED_MARFU_CLAIM_AND_DISTINCT_STOPPED_WITNESS',
  'speaker': None,
  'reason': 'The printed linked footnote claims marfu attribution, while the retained Abu Dawud occurrence stops at Abu al-Darda. A separate retained Ibn al-Qayyim quotation uses qualified reported Prophetic attribution without a chain. Preserve these distinct witnesses and the Quran-derived formula; the exact cited occurrence remains unresolved. This disposition is not based on the site\'s grade alone.',
  'pages': [114],
  'evidence': [quoted('data/corrected_all_records.json','U-P114-01/p114-r010','Ang mga-ulat na ito ay pinaniniwalaang galing sa\nPropeta ﷺ --Marfu’.','Printed marfu claim visually inspected with its parent formula.'), quoted(E+'evidence/early/sources/sunnah_com_abudawud_5081.json','/arabic/0/text','عَنْ أَبِي الدَّرْدَاءِ رضى الله عنه قَالَ','Stopped attribution in this particular retained occurrence.'), quoted(E+'evidence/early/sources/islamweb_zad_2_342.json','/arabic/1/text','ويذكر عنه صلى الله عليه وسلم أنه قال','Qualified raised report in a separate compilation; no chain or exact printed occurrence identity supplied.')]
 },
 'U-P100-01': {
  'route': 'attribution_unresolved_HOLD',
  'content_class': 'UNATTRIBUTED_OPENING_PRAISE_AND_SALAWAT_FORMULA',
  'speaker': None,
  'reason': 'The visible opening formula supplies no speaker attribution. Its footnote begins a different explicitly Prophetic report about sitting with people remembering Allah. Preserve that child U-P100-02 as hadith-bearing context and retain the parent relation; it does not establish this opening formula as Prophetic wording. No compiler authorship or unsupported attribution is invented.',
  'pages': [100],
  'evidence': [quoted('data/corrected_all_records.json','U-P100-01/p100-r005','الْحَمْدُ لِلَّهِ وَحْدَهُ، وَالصَّلَاةُ وَالسَّلَامُ عَلَى مَنْ لَا نَبِي بَعْدُهُ.','Opening formula in source, visually inspected in its immediate heading context.'), quoted('data/corrected_all_records.json','U-P100-02/p100-r009','Sinabi ni Anas ؓ na narinig niyang sinabi ng Propeta ﷺ:','Separate hadith-bearing footnote introduction, visually inspected on p100. Child continuation on p101 read as stored text only; no p101 visual claim.')]
 },
 'U-P114-01': {
  'route': 'attribution_unresolved_HOLD',
  'content_class': 'LINKED_REWARD_REPORT_WITH_UNRESOLVED_RAISED_ATTRIBUTION',
  'speaker': None,
  'reason': 'Retain the parent link to N083. The printed reward and marfu claim exceed what the stopped AbuDawud5081 witness establishes; the qualified Ibn al-Qayyim quotation supplies a related variant but does not establish exact occurrence equivalence. Keep attribution and source translation/alignment limitations separate from authenticity grading.',
  'pages': [114],
  'evidence': [quoted('data/corrected_all_records.json','U-P114-01/p114-r009','anuman ang kanyang gustuhin dito sa\nMundo at kabilang daigdig.','Printed reward wording visually inspected and retained verbatim.'), quoted(E+'evidence/early/sources/islamweb_zad_2_342.json','/arabic/1/text','كفاه الله ما أهمه من أمر الدنيا والآخرة','Related concern/world-and-hereafter wording; not verification of the unrestricted wishes translation.')]
 },
 'N214': {
  'route': 'attribution_unresolved_HOLD',
  'content_class': 'COMPANION_REPORTED_COLLECTIVE_DHIKR_WITH_PROPHETIC_CONTEXT_UNRESOLVED',
  'speaker': 'Jabir reports collective conduct; Prophetic participation/approval for this exact captured occurrence is not established here.',
  'reason': 'The source and retained Bukhari2993 passage give Jabir\'s first-person-plural report of takbir/tasbih while travelling. A Companion\'s narration is not automatically non-hadith. The finite capture does not itself resolve whether the selected collective conduct is anchored to Prophetic practice or approval. Move out of a definitive independent non-hadith conclusion into attribution HOLD pending the missing context; preserve all instructional expansions within the intact record, distinctly annotated.',
  'pages': [227],
  'evidence': [quoted('data/corrected_all_records.json','N214/p227-r004','قَالَ جَابِر رَضِيَ اللَّهُ عَنْهُ: كُنَّا إِذَا صَعِدْنَا كَبَّرْنَا،\nوَإِذَا نَزَلْنَا سَبَّحْنَا.','Visible source report; source also expands takbir/tasbih in translation.'), quoted(E+'evidence/late/sunnah.com_bukhari_2993.json','/arabic_lines/3','كُنَّا إِذَا صَعِدْنَا كَبَّرْنَا، وَإِذَا نَزَلْنَا سَبَّحْنَا','Finite retained witness supplies the same collective conduct, without explicit Prophetic context.')]
 }
}

findings=[]
for rid, cfg in configs.items():
    r=records[rid]
    components=[]
    for c in r['components']:
        role=('source_reference' if c['type']=='reference' else
              'contextual_instruction' if c['type']=='commentary' else
              'source_narration_or_report' if c['type'] in ('narration','footnote') else
              'formula_or_report_text')
        if rid=='N214' and c['segment_id'] in ['p227-r006','p227-r007','p227-r008','p227-r010','p227-r011','p227-r012']:
            role='source_explanatory_dhikr_expansion_inside_intact_report'
        components.append({'segment_id':c['segment_id'],'source_type':c['type'],'pdf_page':c['pdf_page'],
                           'text_sha256':hashlib.sha256(c['text'].encode()).hexdigest(),
                           'proposed_context_role':role,'source_text_unchanged':True})
    findings.append({'record_id':rid,'decision_kind':'COAUTHOR_TARGETED_RECONSTRUCTION',
                     'prior_content_class':r['content_classification_final_pro']['proposed_content_class'],
                     'proposed_record_partition':cfg['route'],'proposed_content_class':cfg['content_class'],
                     'attribution_statement':cfg['speaker'],'decision_rationale':cfg['reason'],
                     'evidence':cfg['evidence'],'actual_visual_pages_reopened':cfg['pages'],
                     'record_source_sha256_preserved':r['record_source_sha256'],
                     'components':components,'parent_record_ids_preserved':r['parent_record_ids'],
                     'related_reference_records_preserved':r['related_reference_records'],
                     'classification_is_not_authenticity_grade':True,
                     'new_grade':None,'new_isnad':None,'new_canonical_occurrence_id':None,
                     'source_wording_changes':0,'approved_for_bank':False,'approved_for_html':False,
                     'further_separate_independent_final_evaluation':'NOT_RUN'})

visual_notes = {
33: ('N007', 'Selected translation and its first footnote; next numbered item remains distinct. No attribution of N007 to the Prophet is printed here.'),
37: ('N015', 'Continuation of N015 translation and first source footnote. Arabic formula on p36 was read from the record, not visually reopened.'),
100: ('U-P100-01;U-P100-02', 'Opening praise/salawat and beginning of distinct Anas/Prophet footnote. The following-page continuation was read only as stored text.'),
114: ('N083;U-P114-01', 'Sevenfold formula, instructions, translation and linked footnote including printed marfu claim and unrestricted wishes rendering.'),
151: ('N118', 'Source translation and footnote explicitly ending with attribution to Umar; preceding Arabic page150 not visually reopened.'),
185: ('N160', 'Short child-funeral formula and immediate transition to a different longer recommendation; no fine-diacritic certification.'),
187: ('N161', 'Formula, translation, and al-Hasan al-Basri footnote/source reference.'),
198: ('N177', 'Formula, translation, and footnote explicitly naming Abdullah bin Amr as the supplicant.'),
227: ('N214', 'Jabir collective-conduct report, translation with formula expansions, and second reference footnote.'),
236: ('N225', 'Translation and first footnote identifying Ammar; following numbered N226 kept distinct.')
}
ledger=[]
for p,(ids,scope) in visual_notes.items():
    rel=f'pages/p{p:03d}_fresh400.png'
    ledger.append({'pdf_page':p,'retained_image_path':rel,'image_sha256':sha(BASE/rel),
                   'image_bytes':(BASE/rel).stat().st_size,'record_ids':ids.split(';'),
                   'action':'ACTUALLY_OPENED_AND_VISUALLY_INSPECTED_EXISTING_IMAGE',
                   'inspection_scope':scope,'new_render':False,'new_crop':False,
                   'whole_page_character_review':False,'every_character_or_diacritic_certified':False,
                   'historical_review_reperformed':False})

report={
 'artifact_type':'COAUTHOR_TARGETED_ATTRIBUTION_RECONSTRUCTION',
 'scope_record_ids':list(configs),
 'reconstructed_from':'Exact v1 archive and current user-supplied reconstruction instructions; no original v2 bytes inspected.',
 'scope_record_count':len(findings),'actual_existing_images_visually_inspected':len(ledger),
 'newly_rendered_pages':0,'source_wording_changes':0,
 'proposed_partition_counts_within_this_scope':{'independent_non_prophetic_HOLD':6,'attribution_unresolved_HOLD':5},
 'prior_v2_claim_comparison':'The six specifically named independent cases and five specifically named unresolved cases are supported with stated limitations. This is not confirmation of full-package partition totals or original-v2 byte identity.',
 'coverage_limits':'Targeted readable loci and selected retained Arabic witness passages only. Historical all276-page review is inherited, not newly performed. No fresh web retrieval or authenticity review.',
 'separate_independent_final_evaluation':'NOT_RUN',
 'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'decisions':findings
}
(OUT/'attribution_findings.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'visual_inspection_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(OUT/'decision_coverage.json').write_text(json.dumps({
 'record_ids_decision_reassessed':list(configs),
 'additional_linked_record_text_read':['U-P100-02'],
 'record_count_decision_reassessed':len(configs),
 'components_in_scope':sum(len(records[r]['components']) for r in configs),
 'images_actually_inspected':len(ledger),
 'record_source_hash_and_component_text_hash_inventory':'attribution_findings.json',
 'mode':'RECONSTRUCTION_COAUTHORING_NOT_INDEPENDENT_FINAL_REVIEW',
 'inherited_primary_capture_files_copied_byte_for_byte':9,
 'additional_primary_capture_selection':'retained_evidence/N177_source_evidence_selected.json; source JSON pointer and source-member SHA256 recorded',
 'new_words_or_attribution_inserted_into_source_fields':False
},ensure_ascii=False,indent=2)+'\n')
outputs=[p for p in OUT.rglob('*') if p.is_file() and p.name!='output_sha256_manifest.json']
(OUT/'output_sha256_manifest.json').write_text(json.dumps([{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(outputs)],ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'findings':len(findings),'components_in_scope':sum(len(records[r]['components']) for r in configs),'images':len(ledger),'output':str(OUT/'attribution_findings.json')}))

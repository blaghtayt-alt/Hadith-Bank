#!/usr/bin/env python3
"""Build the Bukhari content-screening audit from the reviewed candidate ledger.

This preserves the mechanical scan snapshot, records manual contextual decisions,
and binds those decisions to the final integration-file hashes. It is not an
independent authenticity check and does not change any integration record.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, re, unicodedata

BASE = Path(__file__).resolve().parent
FILES = ['hadith_only_primary_records.jsonl', 'variant_records.jsonl', 'explicit_hadith_quotation_records.jsonl']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def norm(text):
    text = ''.join(c for c in (text or '') if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', text.translate(str.maketrans({'ي':'ی','ى':'ی','ك':'ک','\u200c':' '})))

rows, inputs = [], []
for name in FILES:
    data = [json.loads(line) for line in (BASE/name).read_text().splitlines()]
    rows.extend(data)
    inputs.append({'file': name, 'sha256': sha(BASE/name), 'records': len(data)})
by_id = {r['id']:r for r in rows}
assert len(rows) == len(by_id) == 2627
candidates = json.loads((BASE/'hadith_content_screen_candidates.json').read_text())
groups = defaultdict(list)
for c in candidates:
    r = by_id[c['id']]
    assert norm(c['matched_normalized']) in norm(r['text'].get(c['language'])), c['id']
    groups[c['id']].append(c)
assert len(candidates) == 108 and len(groups) == 79

def evidence(rid, include_headings=False):
    r=by_id[rid]
    ev={k:r.get(k) for k in ['id','record_type','content_kind','source_filename','source_volume','source_local_number','source_sequence_position','text','references']}
    ev['source_locator'] = r.get('source_locator') or {'part':'word/document.xml','zero_based_body_paragraphs': r.get('source_paragraphs')}
    if include_headings: ev['source_headings'] = r.get('source_headings',[])
    return ev

findings = [
 {'finding_id':'BKH-CONTEXT-001',
  'kind':'source_context_warning',
  'is_explicit_shia_doctrine':False,
  'record':evidence('fa-faiz-al-bari-v6-p00506',True),
  'exact_permission_quote':'«برای شما اجازه داده شده است که متعه کنید، پس متعه کنید»',
  'assessment':'The narration reports permission for temporary marriage. Its own source chapter explicitly states the final prohibition. The six-volume upload also contains an explicit prohibition narration from Ali. Presenting only the permission excerpt without its source heading may give a misleading impression of the edition’s position; this is not evidence of a Shia interpolation.',
  'related_prohibition_record':evidence('fa-faiz-al-bari-v5-p01085',True),
  'action':'Preserve the exact narration and chapter metadata. Do not omit, rewrite, or label it as Shia on this evidence.'},
]
assert findings[0]['exact_permission_quote'] in by_id['fa-faiz-al-bari-v6-p00506']['text']['translation']
for number, rid in enumerate(['fa-faiz-al-bari-v5-fn324-p2-q001','fa-faiz-al-bari-v6-fn353-p2-q001'],1):
    r=by_id[rid]
    findings.append({'finding_id':f'BKH-SOURCE-GRADE-00{number}',
                     'kind':'source_stated_weak_isnad',
                     'is_explicit_shia_doctrine':False,
                     'record':evidence(rid),
                     'grade_as_stated_by_source':r['grade'],
                     'assessment':'The uploaded commentary explicitly grades the chain of this quoted report as weak. This grading is preserved as scoped source metadata and has not been independently authenticated. Its presence in a commentary on Bukhari does not make it a canonical Bukhari narration or give it a blanket sahih grade.',
                     'action':'Retain the exact quoted excerpt with its source-stated weak-chain metadata, and report the warning separately from ideology screening.'})

shared=[
 ('fa-faiz-al-bari-v6-p02274','twelve_rulers','The text says twelve rulers, all from Quraysh; it does not name twelve imams or assert their infallibility or divine designation.'),
 ('fa-faiz-al-bari-v6-p01943','divine_protection','The maxim that the protected person is the one God protects is not an assertion about the infallibility of specific Shia imams.'),
 ('fa-faiz-al-bari-v4-p02089','jesus_and_prayer_leader','The text describes Jesus returning and a prayer leader from the community. It does not specify a Shia doctrinal identification.'),
 ('fa-faiz-al-bari-v5-p01454','succession_conversation','This is a historical conversation involving Abbas and Ali about asking the Prophet regarding succession. It does not itself assert a divinely appointed infallible line of imams.'),
 ('fa-faiz-al-bari-v5-fn225-p0-q001','companion_speech','This speech is attributed to Ali, not to the Prophet. It is retained as a companion_report. The surrounding excluded commentary argues against a designation claim.'),
 ('fa-faiz-al-bari-v5-p01437','family_report','A report about Fatimah being the first of the Prophet’s family to follow him in death is not on its own an explicitly Shia doctrinal assertion.'),
 ('fa-faiz-al-bari-v5-p01007','geographic_name','The matched Ghadir refers to Ghadir al-Ashtat in the travel narrative. A place-name match is not a Ghadir Khumm doctrinal assertion.'),
 ('fa-faiz-al-bari-v4-p01310','ordinary_adjective','The Arabic phrase هاديا مهديا uses a word meaning guided; the match does not assert an eschatological Mahdi doctrine.'),
 ('fa-faiz-al-bari-v3-p00973','hajj_tamattu','The mutah/tamattu terminology is in a Hajj narrative, not a temporary-marriage permission.'),
 ('fa-faiz-al-bari-v3-p00988','hajj_tamattu','The mutah/tamattu terminology is in a Hajj narrative, not a temporary-marriage permission.'),
]
shared_findings=[]
for rid,kind,reason in shared:
    assert rid in by_id, rid
    shared_findings.append({'kind':kind,'record':evidence(rid),'assessment':reason,'is_explicit_shia_doctrine':False})

special = {x['record']['id']: x['finding_id'] for x in findings}
shared_map = {x['record']['id']:x for x in shared_findings}
reviewed=[]
for rid, hits in groups.items():
    cats=sorted(set(x['category'] for x in hits))
    decision={'id':rid,'matched_categories':cats,'matched_context_count':len(hits),
              'explicit_shia_doctrine_identified':False,
              'review_status':'matched_contexts_reviewed',
              'assessment':'No explicitly Shia-specific doctrinal assertion identified in the reviewed matched contexts.'}
    if rid in special: decision['related_finding']=special[rid]
    if rid in shared_map: decision['assessment']=shared_map[rid]['assessment']
    if cats==['explicit_sect_or_theology']:
        decision['assessment']='Substring false positive: normalized تقیه occurs within another Arabic word (such as عاتقيه, يرتقيه, or أعتقيها), not a doctrinal taqiyyah assertion.'
    reviewed.append(decision)

out={
 'schema':'hadith-content-screening-audit/v1',
 'source_family':'Persian Faiz al-Bari, six uploaded DOCX volumes',
 'final_integration_inputs':inputs,
 'integration_record_count':len(rows),
 'record_type_counts':dict(Counter(r['record_type'] for r in rows)),
 'scope':'All final primary, unnumbered-variant and ancillary-excerpt Arabic and Persian text fields were mechanically scanned. All 108 resulting localized matches in 79 distinct records were contextually reviewed. Source chapters and relevant excluded commentary were consulted where they resolve the matched topic.',
 'mechanical_candidate_ledger':{'file':'hadith_content_screen_candidates.json','sha256':sha(BASE/'hadith_content_screen_candidates.json'),'candidate_match_count':len(candidates),'distinct_record_count':len(groups),'all_matches_revalidated_against_final_text':True},
 'screened_topic_families':['explicit sect or doctrinal identifiers','succession and infallibility terminology','family virtues, Mahdi, twelve rulers and Ghadir terms','temporary marriage and Hajj tamattu terms','possible curse/companion combinations'],
 'confirmed_explicit_shia_specific_assertions_identified':0,
 'records_omitted_or_rewritten_for_ideology':0,
 'limitations':['This is a targeted semantic screening of machine-selected matches, not a claim of line-by-line theological certification of every sentence.','Keyword screening can miss expressions that do not use the selected terms.','Printed canonical references and hadith grades were not independently authenticated.','Persian language, origin, Ali or Ahl al-Bayt virtues, family-inclusive blessings, Mahdi references and twelve-rulers wording alone do not establish Shia-specific doctrine.'],
 'findings_inside_integrated_narrations_or_excerpts':findings,
 'reviewed_shared_material_and_false_positive_examples':shared_findings,
 'candidate_record_decisions':reviewed,
 'common_false_positive_classes':['تقیه within unrelated Arabic words','خم within زخم, تخم, ضخم, jars, or bending','علی matching parts of عليه honorifics','prayer leadership described as امامت','twelve people, months, animals, or troop numbers','العنز or العنب matching broad curse patterns','narrators named Ibn Umar or Ibn Amr narrating general curses, rather than a curse directed at those narrators'],
 'separate_excluded_commentary_review':{'file':'doctrinal_review.json','sha256':sha(BASE/'doctrinal_review.json'),'commentary_prose_in_integrated_reader':False,'note':'The excluded commentary discusses some Shia positions and disputes them; these source discussions are kept separate from findings in the extracted narration text.'},
 'user_warning_policy':'Report concrete context and source-grade findings with exact citations/locators. Do not convert shared religious material, unfamiliar Persian wording, or keyword matches into sect accusations.'
}
(BASE/'hadith_content_screening.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'output':'hadith_content_screening.json','records_screened':len(rows),'matches_reviewed':len(candidates),'distinct_records_reviewed':len(groups),'confirmed_explicit_shia_specific_assertions_identified':0,'context_or_grade_findings':len(findings)},ensure_ascii=False))

"""Record the root reviewer's completed original-field readings before candidate construction."""
from pathlib import Path
import datetime, gzip, hashlib, json, shutil, sys

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
INPUT = WORK / 'phase16-checkpoint5589-input-partitions/root-nasai22-ibnmajah3'
EVIDENCE = WORK / 'phase15-successor-acquisition-monitor/held-evidence'
PIN = '5589a3ffc3b43c3324ae26f2b6c4d33152834456'
sys.path.insert(0, str(WORK / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer

NOTES = {
 'ibnmajah:2355': ('Muhammad ibn Yahya reports his own grandfather Munqidh, the injury, damaged speech, continued trading and repeated deception, then the actual visit and Prophetic instruction. Preserve the three-day option and both keep/return alternatives without repairing source spelling.', 'The terminal Urdu footnote pointer is context; every narrated circumstance and condition remains.'),
 'ibnmajah:2360': ('Retain Ibn Khalda and companions visiting Abu Hurayra over a bankrupt companion and the actually reported Prophetic judgment, both death/bankruptcy alternatives and the condition that the exact goods remain. The parenthetic Medina-judge biography is source context, not part of this reported event.', 'The Urdu Medina-judge biography is likewise contextual. Keep the explicit goods-in-their-original-state condition and all event actors.'),
 'ibnmajah:2370': ('Retain the reported judgment based on one witness and an oath. The parenthetic claimant identifies whose oath is required and is substantive, not a disposable synonym.', 'The Urdu claimant role in parentheses is equally material to the judgment and remains.'),
 'nasai:2300': ('Preserve Hamza\'s continuous fasting practice in the Prophet\'s time, his actual travel question and both affirmative and negative options in the reply.', 'The complete Urdu field independently supplies both alternatives and its own framing; no wording is copied across languages.'),
 'nasai:2301': ('Retain the statement of habitual fasting, the travel question and both supplied alternatives in the answer, preserving the printed Hindi spellings.', 'The complete Urdu question and its two-option answer remain under the printed attribution.'),
 'nasai:2303': ('Retain Hamza\'s capacity to fast, the specific question about sin if he fasts, the concession and both taking it/choosing to fast alternatives.', 'The parenthetic if-I-fast condition is the actual question\'s scope and must remain. Preserve both ensuing alternatives and the stated concession.'),
 'nasai:2305': ('The Hindi reply is terse and grammatically damaged: keep exactly its supplied fast/do-not-fast words. Do not insert Urdu\'s fuller repeated condition or conjunction.', 'Urdu supplies the fuller two-choice construction in its own field; retain it independently without harmonizing the Hindi.'),
 'nasai:2310': ('Preserve the collective travel account, some fasting and others not, and both directions of non-reproach. This is reported practice, not an invented direct Prophetic utterance.', 'Retain the two complementary negative clauses and the narrator\'s actual collective perspective.'),
 'nasai:2311': ('Retain the finite shared journey with the Prophet and the stated split between fasting and not fasting; no absent reason or additional ruling is supplied.', 'The short Urdu field is a complete practice report, with both group alternatives intact.'),
 'nasai:2314': ('Preserve the journey, fasting until Usfan, the water-filled vessel, visible daytime drinking, remaining without a fast until Mecca and the Ramadan conquest. The parenthetic water is the supplied drinking object and remains. Distinguish Ibn Abbas\'s concluding option as a second same-family companion statement, not direct Prophetic speech.', 'The Urdu water qualifier likewise supplies the object. Keep the full sequence and separate Ibn Abbas\'s own concluding choice from the described Prophetic practice, without changing either.'),
 'nasai:2322': ('Retain both visits, the food question, absent food and fasting declaration, the gift/hidden portion/preference, the bring-it command, prior intention, actual eating and the charity analogy. The food object and voluntary-charity scope in parentheses are material. The parenthetic but-I-will-eat is an explanatory preview already followed by actual eating and stays context.', 'Retain the same actually supplied Urdu narrative and material food/voluntary qualifiers. The Hays footnote pointer and the outside-quotation but-I-will-eat parenthesis are context; neither is promoted into the quoted answer.'),
 'nasai:2323': ('Preserve both encounters, food inquiry, fasting declaration, gift and actual eating, Aisha\'s surprise/question and the full answer. Retain the exclusions for Ramadan and its makeup, the voluntary-fast wording and voluntary-charity parenthesis, and both giving/withholding outcomes.', 'Keep the independently supplied Urdu clauses, exclusions and voluntary analogy in full. Only the terminal footnote marker is apparatus.'),
 'nasai:2325': ('Keep the visit, gift and allocation of a share, fasting declaration and subsequent breaking of the fast. The parenthetic also specifies inclusion in the allocation and remains.', 'The Urdu also qualifier likewise belongs to the reported allocation and is retained.'),
 'nasai:2327': ('Preserve the food inquiry, negative answer and fasting declaration. The parenthetic food object determines what was requested and remains.', 'Retain the material food-object parenthesis and the full reported exchange in Urdu.'),
 'nasai:2330': ('Retain both visits, the first question/negative reply and fasting declaration, the Hays gift and the later statement of breaking despite prior intention. Only the parenthetic a-kind-of-food definition of Hays is lexical context.', 'Urdu contains no corresponding parenthetic definition. Keep its complete own exchange and intention qualification; do not insert the Hindi gloss.'),
 'nasai:2336': ('Ibn Umar transmits Hafsa\'s own finite statement about resolving the intention before dawn. Preserve the condition and classify it as a companion saying; this field does not attribute it directly to the Prophet.', 'The Urdu statement is likewise explicitly Hafsa\'s, with the before-dawn condition intact and no upgraded attribution.'),
 'nasai:2348': ('Preserve each of Aisha\'s three I-do-not-know qualifications about a whole Quran in a night, prayer through the night until morning and a whole fasting month other than Ramadan. Do not convert limited knowledge into an unqualified never assertion.', 'Keep all three independent Urdu knowledge limitations, their full-time scopes and the Ramadan exception.'),
 'nasai:2349': ('Retain Ibn Shaqiq\'s actual inquiry and Aisha\'s alternating fasting/nonfasting account, both we-would-say expectations, the Medina-arrival boundary and Ramadan exception. The parenthetic continually changes the expectation and remains. The parenthetic not-fasting merely glosses iftar and is lexical context.', 'The Urdu continually qualifier remains substantive; its parenthetic not-fasting gloss of iftar stays context. Preserve every temporal limit, observer qualification and exception.'),
 'nasai:2354': ('Keep the comparison with other months and the full-or-most-of-Shaban alternative exactly; do not choose one reading or reconcile another report.', 'The Urdu full-or-most uncertainty is equally part of the supplied report and remains.'),
 'nasai:2357': ('Retain Usama\'s observation/question and the complete answer about the month between Rajab and Ramadan, neglect, presentation of deeds and the speaker\'s wish to be fasting.', 'Retain the complete own Urdu explanation and motive, with no imported date or doctrinal elaboration.'),
 'nasai:2358': ('Retain both apparently continuous practice patterns and their observer qualifications, the exception of two days, both whether-they-fall-within-the-pattern branches, the question naming Monday/Thursday and the explanation about deeds. The parenthetic then-it-is-fine is the supplied first conditional consequence and remains.', 'The Urdu conditional consequence in parentheses remains for the same reason. Preserve all actual conditions, both named days and the concluding motive.'),
 'nasai:2369': ('Retain all three instructions to Abu Hurayra: the two Duha units, not sleeping without Witr and three fasting days per month. Preserve source wording without adding details from another version.', 'The full Urdu three-part instruction and its negation/number/time scopes remain.'),
 'nasai:2370': ('Retain the question about Ashura, Ibn Abbas\'s I-do-not-know limitation and the actual exception identifying Ramadan and Ashura. The inline namely supplies the material exceptions and remains despite the source\'s awkward day/month wording.', 'The Urdu knowledge qualification and explicit Ramadan/Ashura exceptions are preserved exactly. Do not smooth the awkward singular-day/month wording or create a direct Prophetic statement.'),
 'nasai:2378': ('Two supplied pieces remain in one report family: the finite opening that the Prophet was informed of Abdullah\'s repeated fasting, and Ata\'s qualified recollection transmitted by Ibn Jurayj. The whole-hadith omission pointer stays context. Retain Ata\'s uncertainty about the wording and the actual finite always-fasting quotation with unresolved internal pronouns; do not fill the absent middle or assign its final speaker by inference. Parenthetic fasts merely gloss siyam and stay context.', 'The independently supplied Urdu first event and Ata memory qualification are retained as ordered components in the same family. Leave the whole-hadith pointer and repeated lexical siyam glosses in context; preserve both remembered wording and admitted uncertainty.'),
 'nasai:2379': ('Retain the anonymous person\'s reported unbroken fasting and the actual reply that he neither fasted nor broke his fast. Keep the anonymous identity and both negated clauses without interpreting them into replacement wording.', 'Preserve the complete Urdu question and paired negative answer without assigning an identity to the unnamed person.')
}

def sha(b): return hashlib.sha256(b).hexdigest()
def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): assert path.read_bytes() == data, path
    else: path.write_bytes(data)

raw = (INPUT / 'full-hi-ur-reading-input-50.jsonl').read_bytes()
cohort = (INPUT / 'cohort.jsonl').read_bytes()
assert sha(raw) == '04674cc0fcd2ef51c9aca6ac552f168633b02b5e1505badce02c01ecc705a896'
assert sha(cohort) == 'c9af6dfbbee05702c2d1fe518e8a008d1a3c5e609c95dccf7b5ec09f4bf4a754'
rows = [json.loads(x) for x in cohort.splitlines()]
originals = [json.loads(x) for x in raw.splitlines()]
assert len(rows) == len(NOTES) == 25 and len(originals) == 50
source_rows = {'deenhindi-'+r['collection']+':'+r['number']:r for r in rows}
manifest = json.loads((EVIDENCE/'evidence-manifest.json').read_bytes())
entries = json.loads((EVIDENCE/'held-state-entries.json').read_bytes())
assert manifest['saved_head'] == PIN
for identity, saved in source_rows.items():
    entry = entries[identity.removeprefix('deenhindi-')]
    for d in [saved['snapshot'], entry['parsed']]:
        b = (EVIDENCE/'sources'/d['path']).read_bytes(); authority = manifest['files'][d['path']]
        assert sha(b) == authority.get('stored_sha256', authority['sha256'])
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest() == authority['git_blob_sha1']
        plain = importer.checked_bytes(EVIDENCE/'sources', d)
        if d == saved['snapshot']:
            source, reference = importer.parse_record(plain, saved['collection'], saved['number'])
            assert source == saved['source_record'] and reference == saved['source_reference_verbatim']
        else:
            parsed = json.loads(plain)
            for key in ['collection','number','source_record','source_reference_verbatim','snapshot']:
                assert parsed[key] == saved[key]
fields = []
for f in originals:
    key = f['occurrence_id'].removeprefix('deenhindi-'); text = f['text']
    assert text == source_rows[f['occurrence_id']]['source_record'][f['source_field']]
    assert sha(text.encode()) == f['text_sha256']
    note = NOTES[key][0] + (' ' + NOTES[key][1] if f['language']=='ur' else '')
    fields.append({'id':f['occurrence_id'], 'language':f['language'], 'source_field':f['source_field'],
        'text':text, 'sha256':sha(text.encode()), 'characters':len(text), 'utf8_bytes':len(text.encode()),
        'complete_field_read':True, 'reading_note':note})
assert (sum(f['characters'] for f in fields),sum(f['utf8_bytes'] for f in fields)) == (17084,36958)
receipt = {'source_commit':PIN, 'reviewer':'/root',
    'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'all_full_fields_read_before_candidate_creation':True, 'candidate_inspected':False,
    'complete_fields':50, 'characters':17084, 'utf8_bytes':36958,
    'source_files_rehashed':50, 'source_raw_reparses_exact':25,
    'prepared_reading_input_sha256':sha(raw), 'cohort_sha256':sha(cohort),
    'field_scope':'All25 Hindi and25 Urdu original fields actually read in full. No other sibling-language reading is claimed. Every parent has a supplied finite report; no source-only parent is proposed.',
    'fields':fields, 'independent_pro_qc':'not_performed'}
target = ROOT/'source-first-complete-reading.json'
assert not target.exists(), 'Do not replace a frozen reading receipt.'
put(target,(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
for src,dst in [('cohort.jsonl','cohort.jsonl'),('full-hi-ur-reading-input-50.jsonl','full-hi-ur-reading-input-50.jsonl')]:
    put(ROOT/'input'/dst,(INPUT/src).read_bytes())
put(ROOT/'source-verification.json',(INPUT/'source-verification.json').read_bytes())
print(json.dumps({'receipt_sha256':sha(target.read_bytes()),'fields':50,'characters':17084,'utf8_bytes':36958,'source_files_rehashed':50,'exact_reparses':25,'candidate_created':False}))

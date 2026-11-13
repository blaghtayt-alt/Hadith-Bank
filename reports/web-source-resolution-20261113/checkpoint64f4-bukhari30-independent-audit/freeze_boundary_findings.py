"""Freeze complete66-field independent inspection and ten exact context moves."""
import copy, gzip, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIMARY = ROOT.parent / 'phase23-checkpoint64f4-bukhari30-review'
sha = lambda b: hashlib.sha256(b).hexdigest()
canon = lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
enc = lambda v: (json.dumps(v, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
mp = PRIMARY / 'delivery-manifest-v1.json'
assert sha(mp.read_bytes()) == '98355c7137fb76a49d6fafe206c101d39a844d84f8806d13744d51f13affa6db'
manifest = json.loads(mp.read_bytes())
ACTIVE = 'imports/web-deenhindi-20261112/reviews/source-review-checkpoint64f4-bukhari30-20261113.json.gz'
entry = next(f for f in manifest['files'] if f['path'] == ACTIVE)
active = Path(entry['local_path']).read_bytes()
assert sha(active) == entry['sha256'] == '7a8b51bfb7112971ef04613efae7fabfa9a87fa87da820b9bf659081cff25c3f'
ledger = json.loads(gzip.decompress(active)); decisions = {r['id']:r for r in ledger['records']}
input_bytes = (ROOT/'input/full-field-reading-input-66.jsonl').read_bytes()
assert sha(input_bytes) == 'cf95a77e5b8c68e2609cbbd54b882c262ef3e9d55f49f4460e6e1a88ee289562'
originals = [json.loads(x) for x in input_bytes.splitlines()]
first = (ROOT/'complete-independent-source-first-readings.json').read_bytes()
assert sha(first) == 'da0ae55af31743029a6e6fead8edf08edc678ea63c42b2e93e4cbd7415ec3cc2'
initial = {(f['occurrence_id'],f['language']):f['independent_source_first_note'] for f in json.loads(first)['fields']}
adjudication_path = ROOT.parent/'phase23-bukhari2737-2763-independent-scope-adjudication/independent-complete-original-role-adjudication.json'
adjudication = adjudication_path.read_bytes()
assert sha(adjudication) == '7937df3d88852ebf5eb0dc6b43b81dd6a7d42e15d6c8bca97347113821cd9fcc'
copied = ROOT/'input/root-complete-original-role-adjudication.json'
assert not copied.exists(); copied.write_bytes(adjudication)

CUTS = {
 ('bukhari:2709','hi'):[(1675,1744)], ('bukhari:2709','ur'):[(1524,1579)],
 ('bukhari:2718','hi'):[(2825,2914),(2937,3019)],
 ('bukhari:2718','ur'):[(2568,2648),(2668,2741)],
 ('bukhari:2737','hi'):[(1101,1252)], ('bukhari:2737','ur'):[(991,1132)],
 ('bukhari:2763','hi'):[(1501,1761)], ('bukhari:2763','ur'):[(1405,1658)],
}
RATIONALES = {
 'bukhari:2709':'The selected Asr/attendance wording describes what a version mentions; it supplies no own arrival predicate. Keep it as attributed transmission context, alongside the omitted-person/laughter and final Dhuhr comparison. The actual finite thirty-wasq father-debt clause remains selected. This does not harmonize either time or amount.',
 'bukhari:2718':'The one-uqiya-of-gold clarification and two-hundred-dirham description are nominal version labels, unlike the actual bought/permission/condition predicates printed in the other retained variants. Preserve both labels visibly as transmission context; retain every finite purchase, riding condition, source circumstance and the complete I-think four-uqiya material uncertainty. Do not choose a price.',
 'bukhari:2737':'Ibn Awn’s named mention/reply frame establishes who voiced the appended steward qualification, but its role is to explain the cited hadith’s stewardship rule. Under the owner side-explanation exclusion it remains attributed legal context. Keep the entire actual Umar/Ibn Umar consultation/endowment report. This is not a blanket rejection of Successor sayings, legal content or named scholarly encounters.',
 'bukhari:2763':'The final narrator-said analogy is an explicitly appended legal explanation after the actual Urwah/Aisha question and Aisha’s own interpretations. Preserve its unnamed attribution as context rather than admitting the side explanation. All preceding actual verse excerpts, supplied renderings, attributed Aisha interpretation and meaningful predicates/conditions remain selected.',
}
REFINEMENTS = {
 'bukhari:2739':'My initial source-first note allowed the family-linked reporter frame. On exact comparison, the primary’s narrower Amr ibn Harith frame is sound: static brother-in-law/Juwayriya biography is source context, while the actual named reporter and all inventory predicates/exceptions remain. No narrative participant or event is lost.',
 'bukhari:2742':'My initial note treated the no-current-need-for-a-will parenthesis as interpretation. On complete source/candidate comparison, it is a finite negative advice predicate supplied within the actual rendered reply, rather than a separately introduced compiler appendix. I accept retaining it alongside the actual expenditure predicate, morsel-charity predicate, time and recipient scope. The distinct alias apposition remains context.',
 'bukhari:2746':'My initial note called the parenthetic assailant clause redundant. In its actual identification-question sequence, it identifies the selected assailant after alternative candidates. I accept the primary’s retention as participant linkage, while preserving the Hindi’s missing reporter and all original defects.',
 'bukhari:2748':'My initial note treated the final leaving-the-world parenthesis as a gloss. The source actually supplies a finite death predicate within the answer’s health/death contrast. I accept its retention with the material wealth-desire and spending/fear conditions; this does not make dictionary or compiler labels eligible.',
}
findings, inspections, plan = [], [], []
for row in originals:
    oid, lang, text = row['occurrence_id'], row['language'], row['text']
    short = oid.removeprefix('deenhindi-'); key = (short,lang)
    field = next(f for f in decisions[oid]['field_reviews'] if f['language'] == lang)
    assert field['reviewed'] and sha(text.encode()) == field['text_sha256']
    spans = copy.deepcopy(field['spans'])
    old_mask = {p for s in spans for p in range(s['start'],s['end'])}
    for s in spans: assert sha(text[s['start']:s['end']].encode()) == s['sha256']
    removed = set()
    for a,b in CUTS.get(key,[]):
        matches = [s for s in spans if (s['start'],s['end']) == (a,b)]
        assert len(matches) == 1 and set(range(a,b)) <= old_mask
        span = matches[0]; spans.remove(span); removed.update(range(a,b))
        findings.append({'occurrence_id':oid,'language':lang,'kind':'move_source_side_explanation_or_nominal_version_apparatus_to_context',
            'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode()),
            'source_text_sha256':row['text_sha256'],'source_record_sha256':row['source_record_sha256'],
            'currently_selected_intersection':[[a,b]],'removed_component':{k:v for k,v in span.items() if k not in ('start','end','sha256','reason')},
            'removed_characters':b-a,'removed_utf8_bytes':len(text[a:b].encode()),'rationale':RATIONALES[short],
            'root_independent_role_adjudication_sha256':sha(adjudication) if short in ('bukhari:2737','bukhari:2763') else None})
    new_mask = {p for s in spans for p in range(s['start'],s['end'])}
    assert old_mask-new_mask == removed and not new_mask-old_mask
    plan.append({'occurrence_id':oid,'language':lang,'source_text_sha256':row['text_sha256'],
        'before_field_definition_sha256':sha(canon(field)),
        'expected_spans':[{k:v for k,v in s.items() if k!='reason'} for s in spans],
        'expected_added_positions':[],'expected_removed_positions':sorted(removed),
        'required_note_refinement':bool(removed)})
    inspections.append({'occurrence_id':oid,'language':lang,'source_text_sha256':row['text_sha256'],
        'complete_original_field_read':True,'complete_candidate_masks_and_voices_compared':True,
        'result':'bounded_context_amendment_requested' if removed else 'accepted',
        'source_first_note':initial[oid,lang],
        'final_assessment':RATIONALES.get(short) if removed else REFINEMENTS.get(short,'All exact selected/context boundaries and actual component voices are accepted against the complete own source reading, with no absent words, identities or sibling text filled.'),
        'selected_before':[{**{k:v for k,v in s.items() if k!='reason'},'text':text[s['start']:s['end']]} for s in field['spans']]})
assert len(inspections) == len(plan) == 66 and len(findings) == 10
assert sum(f['removed_characters'] for f in findings) == 1253
payload = {'schema':'hadith-bank-independent-complete-candidate-inspection-v1',
    'status':'complete_inspection_with_ten_bounded_context_moves',
    'primary_manifest':{'path':str(mp),'sha256':sha(mp.read_bytes())},'active_path':ACTIVE,'active_sha256':sha(active),
    'own_source_first_receipt_sha256':sha(first),
    'own_source_proof_sha256':'3825e8023755f5af135fab8c87719b1ea5b040b6232e00f6aab9af97be32d04d',
    'root_source_only_role_adjudication':{'path':str(copied),'sha256':sha(adjudication),'additional_cohort_reading_credit':0},
    'coverage':{'parents':30,'complete_fields':66,'characters':47492,'utf8_bytes':100674},
    'requested_changes':findings,'all_complete_field_inspections':inspections,
    'explicit_refinements_to_immutable_initial_notes':REFINEMENTS,
    'change_limits':{'changed_fields':8,'changed_parents':4,'whole_selected_ranges_to_context':10,
        'removed_characters':1253,'removed_utf8_bytes':sum(f['removed_utf8_bytes'] for f in findings),
        'added_source_positions':0,'other_reviewed_fields_exact':58,'unread_fields_exact':84,
        'other_complete_field_definitions_exact':142,'other_whole_parents_exact':26,
        'retained_component_type_speaker_family_and_position_labels_exact':True,
        'parent_disposition_changes':0,'additional_reading_credit':0},
    'instructions':'Preserve every v1 payload and the original complete-source notes. Only these exact currently selected intersections move to context. Transparently refine eight affected reasons and the four affected parent review explanations and derived inventories where required, without changing actual parent/source metadata. Retained spans, types, speakers, component/family IDs and all142 other complete field definitions remain exact. Final native/source gate awaits the versioned candidate; this is not publication.'}
for name,value in [('independent-boundary-findings-v1.json',payload),('accepted-reviewed-field-plan-v1.json',
        {'schema_version':1,'primary_manifest_sha256':sha(mp.read_bytes()),'active_sha256':sha(active),'fields':plan})]:
    p=ROOT/name; assert not p.exists(); p.write_bytes(enc(value));print(name,sha(p.read_bytes()),p.stat().st_size)
print(json.dumps(payload['change_limits'],sort_keys=True))

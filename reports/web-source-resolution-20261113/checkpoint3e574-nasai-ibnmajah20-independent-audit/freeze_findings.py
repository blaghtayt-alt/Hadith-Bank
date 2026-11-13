"""Bind all forty inspected candidate fields and the two source-based findings."""
from pathlib import Path
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent
OWNER = HERE.parent / 'phase19-checkpoint3e574-nasai-ibnmajah20-review'
MANIFEST_SHA = 'fda319d9c0c9a2bf0b6f7a98cdb32e5ae1bce7684a89fe4b7fcfc98e4cdb856a'
ACTIVE_SHA = 'ecaa9e8e077b2a55e64288e6b10adb63af69f3c64b56d4fddd32eaa1542316e1'


def sha(b): return hashlib.sha256(b).hexdigest()
def enc(v): return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


manifest_raw=(OWNER/'delivery-manifest-v1.json').read_bytes()
assert sha(manifest_raw)==MANIFEST_SHA
manifest=json.loads(manifest_raw)
for binding in manifest['files']:
    raw=Path(binding['local_path']).read_bytes()
    assert sha(raw)==binding['sha256'] and len(raw)==binding['bytes']
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==binding['git_blob_sha1']
active=next(b for b in manifest['files'] if '/source-review-' in b['path'])
active_raw=Path(active['local_path']).read_bytes();assert sha(active_raw)==ACTIVE_SHA
ledger=json.loads(gzip.decompress(active_raw))
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,(HERE/'input/cohort.jsonl').read_bytes().splitlines())}
initial_raw=(HERE/'complete-independent-source-first-readings.json').read_bytes()
assert sha(initial_raw)=='088d0cf7ca63c5c4daecfa21dc2ef7823d9f95e096f650674b76785a2b333f08'
initial=json.loads(initial_raw)
notes={(r['occurrence_id'],r['language']):r for r in initial['fields']}
checked=[]
for record in ledger['records']:
    for field in record['field_reviews']:
        if not field['reviewed']:continue
        key=(record['id'],field['language'])
        source=sources[record['id']]['source_record'][field['source_field']]
        assert sha(source.encode())==field['text_sha256']==notes[key]['text_sha256']
        gaps=[];cursor=0
        for span in field['spans']:
            if cursor<span['start']:gaps.append({'start':cursor,'end':span['start'],'text':source[cursor:span['start']]})
            assert sha(source[span['start']:span['end']].encode())==span['sha256']
            cursor=span['end']
        if cursor<len(source):gaps.append({'start':cursor,'end':len(source),'text':source[cursor:]})
        result='amend_named_exegetical_component' if record['id']=='deenhindi-nasai:2492' else 'narrow_unasserted_eyewitness_type' if record['id']=='deenhindi-nasai:2540' else 'accept_exact_boundaries_and_voices'
        checked.append({'id':record['id'],'language':field['language'],'source_record_sha256':record['source_record_sha256'],
            'source_field_sha256':field['text_sha256'],'complete_field_characters':len(source),
            'initial_source_first_note':notes[key]['source_first_note'],'candidate_field_decision':field,
            'candidate_context_gaps':gaps,'independent_result':result})
assert len(checked)==40
findings=[]
for language,end in [('hi',276),('ur',257)]:
    row=sources['deenhindi-nasai:2492'];field={'hi':'translationHindi','ur':'translationUrdu'}[language]
    text=row['source_record'][field]
    locators=[]
    if language=='ur':
        literal='( البقرہ: ۲۶۷ )';a=text.index(literal);locators=[{'start':a,'end':a+len(literal),'text':literal}]
    findings.append({'id':'deenhindi-nasai:2492','language':language,'source_field_sha256':sha(text.encode()),
        'requested_change':'restore_attributed_exegesis_as_separate_named_interpreter_component',
        'opening_interval':[0,end],'opening_text':text[:end],'retain_as_context':locators,
        'actual_speaker':'Abu Umama as named in this own source field, relayed to Ibn Shihab; no external identity or biographical status is inferred.',
        'recommended_type':'attributed_exegetical_statement',
        'reason':'The source explicitly reports that the named speaker told Ibn Shihab about this quoted verse and identifies two particular date varieties as its referent. That is a finite transmitted exegetical application, not a dictionary synonym of khabith. Preserve the actual verse and supplied rendering inside that distinct saying, with the existing Prophet prohibition separately attributed afterward. The Urdu verse locator alone remains reference apparatus; no canonical mapping is added.',
        'parent_disposition_or_field_reading_change':False})
for language in ['hi','ur']:
    row=next(r for r in ledger['records'] if r['id']=='deenhindi-nasai:2540')
    field=next(f for f in row['field_reviews'] if f['language']==language)
    assert all(s['report_type']=='witnessed_speech_and_prophetic_statement' for s in field['spans'])
    findings.append({'id':row['id'],'language':language,'source_field_sha256':field['text_sha256'],
        'requested_change':'narrow_report_type_without_any_boundary_change',
        'old_report_type':'witnessed_speech_and_prophetic_statement',
        'recommended_report_type':'reported_speech_and_prophetic_statement',
        'reason':'Abdullah ibn Amr reports that when the Prophet conquered Mecca he stood and spoke. Neither own field says Abdullah personally saw, heard or attended this scene. Preserve the supplied transmitter and statement, but do not add eyewitness status. Nasai2532 is different because its own we-arrived-and-saw wording explicitly supports a witnessed report.',
        'exact_all_source_positions_speakers_and_families_to_preserve':True,
        'parent_disposition_or_field_reading_change':False})
report={'schema':'independent-complete-field-boundary-findings-v1','status':'AMENDMENT_REQUESTED',
    'source_checkpoint':'3e574b9e7e4dd7cf8bc23232249004a18692c61c',
    'primary_manifest_sha256':MANIFEST_SHA,'primary_active_sha256':ACTIVE_SHA,
    'independent_complete_source_first_receipt_sha256':sha(initial_raw),
    'independent_source_verification_sha256':sha((HERE/'independent-source-verification.json').read_bytes()),
    'complete_fields_independently_read_and_compared':40,'characters_read':10697,'utf8_bytes_read':21245,
    'findings':findings,'unchanged_parent_dispositions':20,'unchanged_reading_scope':True,
    'initial_note_refinements':[{'id':'deenhindi-nasai:2500','languages':['hi','ur'],
        'initial_view':'The fitr parenthetic alias could be treated as explanatory context.',
        'final_source_based_view':'Retain this particular category qualifier. Ramadan zakat alone does not express the exact fitr-payment identity, and the source parenthesis supplies that material subject scope. This is different from a redundant dictionary synonym. All participant/amount wording and the distinct later determination stay literal.',
        'initial_notes_rewritten':False}],
    'all_candidate_field_checks':checked,'candidate_or_source_mutations':0,
    'no_independent_authenticity_or_pro_qc_claim':True}
path=HERE/'independent-boundary-findings-v1.json';raw=enc(report)
assert not path.exists()
path.write_bytes(raw)
print(json.dumps({'path':str(path),'sha256':sha(raw),'bytes':len(raw),'findings':len(findings)}))

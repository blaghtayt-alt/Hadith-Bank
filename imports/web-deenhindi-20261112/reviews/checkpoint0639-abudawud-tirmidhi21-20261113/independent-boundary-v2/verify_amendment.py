"""Verify only the three agreed literal cuts and one orphan separator move."""
from pathlib import Path
import copy, gzip, hashlib, json, shutil

ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'publish'; NEW=ROOT/'publish-v2'
PREFIX='imports/web-deenhindi-20261112/reviews/checkpoint0639-abudawud-tirmidhi21-20261113'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpoint0639-abudawud-tirmidhi21-20261113.json.gz'
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
OLD_HASH='b03ba173957857ac7acf9b0eaa4375151f4320fa212cda765a7d10a1036f4410'
NEW_HASH='b4735dc63110fd87e92205140a305fee5164f26eafe8b09bddcbca7643a13e34'
MANIFEST_HASH='cb1f293fc0d21c128a3cf18ba7b432e6630cebb92a81f47db27b91b5de693166'
EXPECTED={
 ('deenhindi-abudawud:2233','hi'):[(260,271,'(बारीरा को)','Repeated pronoun expansion of already explicit Barira.')],
 ('deenhindi-abudawud:2233','ur'):[(223,235,'( بریرہ کو )','Repeated pronoun expansion of already explicit Barira.')],
 ('deenhindi-abudawud:2253','ur'):[(993,994,' ','Orphan single separator between the existing verse-locator context and the newly cut continuation pointer.'),
                                   (994,1000,'آخر تک','Pointer to omitted verse continuation, not actual recitation.')],
}

def main():
    manifest=(ROOT/'delivery-manifest.json').read_bytes(); assert sha(manifest)==MANIFEST_HASH
    for item in json.loads(manifest)['files']:
        b=(OLD/item['path']).read_bytes()
        assert len(b)==item['bytes'] and sha(b)==item['sha256'] and git(b)==item['git_blob_sha1']
    old_bytes=(OLD/ACTIVE).read_bytes();new_bytes=(NEW/ACTIVE).read_bytes()
    assert sha(old_bytes)==OLD_HASH and sha(new_bytes)==NEW_HASH
    old=json.loads(gzip.decompress(old_bytes));new=json.loads(gzip.decompress(new_bytes))
    assert old['source_ledger_path']==new['source_ledger_path']
    assert (OLD/old['source_ledger_path']).read_bytes()==(NEW/new['source_ledger_path']).read_bytes()
    for key in set(old)-{'records','manual_decision_files'}: assert old[key]==new[key],key
    rows={r['collection']+':'+r['number']:r for r in map(json.loads,gzip.decompress((OLD/old['source_ledger_path']).read_bytes()).splitlines())}
    assert len(old['records'])==len(new['records'])==21
    changes=[]; unchanged=0
    for before,after in zip(old['records'],new['records'],strict=True):
        assert before['id']==after['id'] and before['decision']==after['decision']=='register'
        for key in set(before)-{'field_reviews'}:assert before[key]==after[key],(before['id'],key)
        for left,right in zip(before['field_reviews'],after['field_reviews'],strict=True):
            binding=(before['id'],left['language']);assert left['language']==right['language']
            if binding not in EXPECTED:
                assert left==right,binding;unchanged+=1;continue
            for key in set(left)-{'spans'}:assert left[key]==right[key],(binding,key)
            text=rows[before['id'].removeprefix('deenhindi-')]['source_record'][left['source_field']]
            old_positions={i for span in left['spans'] for i in range(span['start'],span['end'])}
            new_positions={i for span in right['spans'] for i in range(span['start'],span['end'])}
            assert new_positions <= old_positions
            expected_positions=set();cuts=[]
            for start,end,literal,reason in EXPECTED[binding]:
                assert text[start:end]==literal
                expected_positions.update(range(start,end))
                cuts.append({'start':start,'end':end,'text':literal,'sha256':sha(literal.encode()),
                             'characters':len(literal),'utf8_bytes':len(literal.encode()),'reason':reason})
            assert old_positions-new_positions==expected_positions,(binding,sorted(old_positions-new_positions))
            for span in right['spans']:
                matches=[s for s in left['spans'] if s['start']<=span['start']<span['end']<=s['end']]
                assert len(matches)==1
                for key in set(span)-{'start','end','sha256'}:assert span[key]==matches[0][key],(binding,key)
            changes.append({'id':binding[0],'language':binding[1],'source_text_sha256':sha(text.encode()),
                            'before_field_sha256':sha(enc(left)),'after_field_sha256':sha(enc(right)),
                            'before_spans':left['spans'],'after_spans':right['spans'],'moved_to_context':cuts,
                            'newly_admitted_positions':0,'attribution_and_family_metadata_unchanged':True})
    assert len(changes)==3 and unchanged==39
    evidence=NEW/PREFIX/'independent-boundary-v2';evidence.mkdir(parents=True,exist_ok=True)
    retained=[]
    for target,data in [('active-before-v1.json.gz',old_bytes),('delivery-manifest-before-v1.json',manifest),
                        ('manual_readings-before-v1.py',(ROOT/'manual_readings.py').read_bytes()),
                        ('manual-abudawud-before-v1.json',(ROOT/'manual-abudawud.json').read_bytes())]:
        (evidence/target).write_bytes(data)
        retained.append({'path':str((evidence/target).relative_to(NEW)),'bytes':len(data),'sha256':sha(data),'git_blob_sha1':git(data)})
    report={'schema':'hadith-bank-exact-independent-boundary-amendment-v1','result':'PASS',
      'source_checkpoint':'0639af7fd15786284b4c413fced77e38eec8825a',
      'before_active_sha256':OLD_HASH,'after_active_sha256':NEW_HASH,'before_manifest_sha256':MANIFEST_HASH,
      'source_baseline_unchanged':True,'parent_decisions_unchanged':21,'explicit_field_reviews_unchanged':39,
      'explicit_field_reviews_amended':3,'unread_source_context_slots_unchanged':63,
      'literal_context_cuts':3,'orphan_whitespace_characters_moved_to_context':1,
      'characters_moved_to_context':sum(c['characters'] for x in changes for c in x['moved_to_context']),
      'utf8_bytes_moved_to_context':sum(c['utf8_bytes'] for x in changes for c in x['moved_to_context']),
      'newly_admitted_positions':0,'all_source_words_and_metadata_preserved':True,
      'all_unmodified_component_types_speakers_and_families_preserved':True,
      'frozen_v1_package_file_hashes_rechecked':True,'changes':changes,'preserved_before_evidence':retained,
      'native_validation_path':PREFIX+'/validation.json','source_http_requests':0,'github_writes':0,
      'formal_independent_pro_certification':False}
    (evidence/'exact-amendment.json').write_bytes(enc(report))
    shutil.copyfile(Path(__file__),evidence/'verify_amendment.py')
    print(json.dumps({'result':'PASS','changed_fields':3,'unchanged_fields':39,
                      'characters_moved_to_context':report['characters_moved_to_context'],
                      'utf8_bytes_moved_to_context':report['utf8_bytes_moved_to_context'],
                      'report_sha256':sha(enc(report))},indent=2))

if __name__=='__main__':main()

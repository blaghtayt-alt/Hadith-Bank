"""Independent native/source and final exact-boundary audit; writes isolated files only."""
from pathlib import Path
import argparse,collections,copy,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
OWNER=WORK/'phase18-checkpointbd4a-nasai-ibnmajah23-review'
CENTRAL=WORK/'phase16-successor-acquisition-monitor/held-evidence'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpointbd4a-nasai-ibnmajah23-20261113.json.gz'
PIN='bd4a75695d3c695e98bf8efa5ce07764ac5e2633'
READING_SHA='90d8cb83116f17a3a0ac5d006dec3cf642a4608f1d4d2323eea1459c4cf9a7ad'
FINDING_SHA='a4190628144c9eef5e1bb98987f03efa05d021bb36f0fba98a055746bdd729f7'
FIELDS={'ar':'textArabic','hi':'translationHindi','ur':'translationUrdu','ur-Latn':'translationUrduRoman','en':'translationEnglish'}
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):
    b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def bind(p):
    b=p.read_bytes();return {'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
def leaves(v):
    if isinstance(v,dict):return sum(leaves(x) for x in v.values())
    if isinstance(v,list):return sum(leaves(x) for x in v)
    return 1
def equal(a,b):assert a==b;return leaves(a)
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,('Frozen output differs',str(p))
    else:p.write_bytes(b)

def audit(manifest_name,manifest_sha,active_sha,final):
    reading_path=ROOT/'complete-independent-source-first-readings.json'
    assert sha(reading_path.read_bytes())==READING_SHA
    reading=read(reading_path);assert not reading['candidate_viewed'] and not reading['author_semantic_notes_viewed']
    read_fields={(r['occurrence_id'],r['language']):r for r in reading['fields']};assert len(read_fields)==49
    findings_path=ROOT/'independent-boundary-findings-v1.json';assert sha(findings_path.read_bytes())==FINDING_SHA
    findings=read(findings_path);inspected={(r['id'],r['language']):r for r in findings['all_fields_inspected']}
    assert set(inspected)==set(read_fields)
    corrections={(r['id'],r['language']):r for r in findings['requested_changes']}
    assert len(corrections)==2
    source_rows=list(map(json.loads,(ROOT/'input/cohort.jsonl').read_bytes().splitlines()))
    source_by={'deenhindi-'+r['collection']+':'+r['number']:r for r in source_rows}
    assert len(source_by)==len(source_rows)==23
    central_by={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,(CENTRAL/'held-source-records.jsonl').read_bytes().splitlines())}
    assert all(central_by[k]==v for k,v in source_by.items())
    manifest_path=OWNER/manifest_name;assert sha(manifest_path.read_bytes())==manifest_sha
    manifest=read(manifest_path);repo=ROOT/'validation'/('final' if final else 'v1-preflight')
    owner_bindings=[]
    for item in manifest['files']:
        relative=Path(item['path']);assert not relative.is_absolute() and '..' not in relative.parts
        local=Path(item['local_path']);assert local.is_file() and not local.is_symlink() and local.resolve().is_relative_to(OWNER)
        b=bind(local);assert b['sha256']==item['sha256'] and b['bytes']==item['bytes'] and b['git_blob_sha1']==item['git_blob_sha1']
        put(repo/relative,local.read_bytes());owner_bindings.append({'path':item['path'],'owner_path':str(local),**b})
    assert len(owner_bindings)==len({x['path'] for x in owner_bindings})
    active_path=repo/ACTIVE;assert sha(active_path.read_bytes())==active_sha
    active=read(active_path);baseline=repo/active['source_ledger_path']
    assert sha(baseline.read_bytes())==active['source_ledger_sha256']
    assert list(map(json.loads,gzip.decompress(baseline.read_bytes()).splitlines()))==source_rows
    decisions={r['id']:r for r in active['records']};assert len(decisions)==len(active['records'])==23 and set(decisions)==set(source_by)
    old=read(OWNER/'publish'/ACTIVE);old_by={r['id']:r for r in old['records']}
    assert sha((OWNER/'publish'/ACTIVE).read_bytes())=='3b430498bcef0f5934dcd3157fc55e2a8da11aaab72fa39ae1b1d3c3e77509c8'
    authority=read(CENTRAL/'evidence-manifest.json');assert authority['saved_head']==PIN
    state=read(CENTRAL/'held-state-entries.json')
    engine=SourceReviews(repo,'deenhindi');counts=collections.Counter();metadata=collections.Counter()
    field_proof=[];source_proof=[];surgical=[];unchanged_fields=0;unchanged_parents=0
    for ident,saved in source_by.items():
        d=decisions[ident];entry=state[saved['collection']+':'+saved['number']]
        assert entry['parsed']['path']==saved['parsed_path']
        for descriptor in [saved['snapshot'],entry['parsed']]:
            plain=importer.checked_bytes(CENTRAL/'sources',descriptor)
            path=CENTRAL/'sources'/descriptor['path'];given=authority['files'][descriptor['path']];b=bind(path)
            assert b['sha256']==given['sha256'] and b['git_blob_sha1']==given['git_blob_sha1'] and b['bytes']==given['bytes']
            source_proof.append({'id':ident,'path':descriptor['path'],**b,'plain_sha256':sha(plain),'plain_bytes':len(plain)})
        parsed=json.loads(importer.checked_bytes(CENTRAL/'sources',entry['parsed']))
        for k in ['collection','number','source_record','source_reference_verbatim','snapshot']:assert parsed[k]==saved[k]
        assert parsed['classification']==saved.get('intake_classification',saved['classification'])
        obj,ref=importer.parse_record(importer.checked_bytes(CENTRAL/'sources',saved['snapshot']),saved['collection'],saved['number'])
        assert obj==saved['source_record'] and ref==saved['source_reference_verbatim']
        assert d['source_record_sha256']==sha(importer.json_bytes(obj)) and d['source_reference_verbatim']==ref
        assert d['source_snapshot']==saved['snapshot'] and d['collection']==saved['collection'] and d['number']==saved['number']
        original=importer.canonical_record(saved);revised,action=engine.apply(copy.deepcopy(original),saved=saved)
        assert action==d['decision']==('exclude' if ident=='deenhindi-nasai:2412' else 'register');counts[action]+=1
        for k,v in original.items():
            if k not in ['text','language_versions','review','content_kind','extraction']:metadata['parent']+=equal(v,revised[k])
        fields={f['language']:f for f in d['field_reviews']};old_fields={f['language']:f for f in old_by[ident]['field_reviews']}
        assert len(fields)==len(d['field_reviews'])==5 and set(fields)==set(FIELDS)
        assert len(original['language_versions'])==len(revised['language_versions'])==5
        if final:
            assert {k:v for k,v in d.items() if k not in ['field_reviews','reason']}=={k:v for k,v in old_by[ident].items() if k not in ['field_reviews','reason']}
            if ident!='deenhindi-nasai:2387':assert d==old_by[ident];unchanged_parents+=1
        for before,after in zip(original['language_versions'],revised['language_versions']):
            lang=before['language'];key=(ident,lang);f=fields[lang];text=obj[FIELDS[lang]]
            assert isinstance(text,str) and text and before['text']==text
            assert f['source_field']==FIELDS[lang] and f['text_sha256']==sha(text.encode()) and f['text_chars']==len(text)
            reviewed=key in read_fields;assert f['reviewed'] is reviewed
            assert f['chars_reviewed']==(len(text) if reviewed else 0) and f['bytes_reviewed']==(len(text.encode()) if reviewed else 0)
            selected=[False]*len(text);spans=f['spans'];cursor=0
            for s in spans:
                a,b=s['start'],s['end'];assert cursor<=a<b<=len(text) and sha(text[a:b].encode())==s['sha256']
                assert not any(selected[a:b]);selected[a:b]=[True]*(b-a);cursor=b
                assert s['speaker'].strip() and s['report_type'].strip() and s['component_id'] and s['source_report_family_id']
            counts['selected_spans']+=len(spans)
            if reviewed:
                r=read_fields[key];assert r['text_sha256']==sha(text.encode()) and r['characters']==len(text) and r['utf8_bytes']==len(text.encode())
                counts['complete_fields_read']+=1;counts['characters_read']+=len(text);counts['utf8_bytes_read']+=len(text.encode())
                counts['admitted_fields' if spans else 'read_context_fields']+=1
                prior=inspected[key];expected=[False]*len(text)
                accepted_spans=[]
                for p in prior['candidate_partition']:
                    if p['kind']!='selected':continue
                    expected[p['start']:p['end']]=[True]*(p['end']-p['start'])
                    accepted_spans.append({k:v for k,v in p.items() if k not in ['kind','text']})
                if final and key in corrections:
                    cut=corrections[key];a,b=cut['start'],cut['end'];expected[a:b]=[False]*(b-a)
                    accepted_spans=[s for s in accepted_spans if not (s['start']==a and s['end']==b)]
                assert selected==expected,(key,'unapproved selection change')
                expected_labels=[{k:s[k] for k in ['start','end','sha256','component_id','source_report_family_id','report_type','speaker']} for s in accepted_spans]
                actual_labels=[{k:s[k] for k in ['start','end','sha256','component_id','source_report_family_id','report_type','speaker']} for s in spans]
                assert actual_labels==expected_labels,(key,'unapproved voice, boundary or family change')
            else:
                assert not spans and after['text'] is None;counts['unread_fields']+=1
            if final:
                old_f=old_fields[lang]
                if key not in corrections:assert old_f==f;unchanged_fields+=1
                else:
                    assert old_f!=f
                    for k in ['language_version_id','language','source_field','text_sha256','text_chars','reviewed','chars_reviewed','bytes_reviewed','review_method','review_scope']:
                        assert old_f[k]==f[k]
                    surgical.append({'id':ident,'language':lang,'before_field_sha256':sha(enc(old_f)),
                        'after_field_sha256':sha(enc(f)),'exact_requested_cut':corrections[key]})
            assert (after['text'] or '')==''.join(text[s['start']:s['end']] for s in spans)
            pieces=[(s['start'],s['end'],text[s['start']:s['end']]) for s in spans]
            pieces += [(c['source_span'][0],c['source_span'][1],c['text']) for c in after.get('comments',[]) if c.get('source_span') is not None]
            cursor=0
            for a,b,t in sorted(pieces):assert a==cursor and text[a:b]==t;cursor=b
            assert cursor==len(text) and ''.join(t for a,b,t in sorted(pieces))==text;counts['partitions']+=1
            for k,v in before.items():
                if k not in ['text','scope','source','comments']:metadata['language']+=equal(v,after[k])
            for k,v in before['source'].items():metadata['source']+=equal(v,after['source'][k])
            for i,c in enumerate(before.get('comments',[])):
                for k,v in c.items():metadata['previous_comments']+=equal(v,after['comments'][i][k])
            field_proof.append({'id':ident,'language':lang,'source_field_sha256':sha(text.encode()),
                'characters':len(text),'utf8_bytes':len(text.encode()),'complete_own_field_read':reviewed,
                'selected_mask_sha256':sha(bytes(selected)),'selected_spans':spans,'lossless_partition_pass':True})
        if ident=='deenhindi-nasai:2412':assert all(f['reviewed'] and not f['spans'] for f in fields.values())
    engine.finish()
    assert (counts['register'],counts['exclude'],counts['partitions'])==(22,1,115)
    assert (counts['complete_fields_read'],counts['characters_read'],counts['utf8_bytes_read'])==(49,29579,61743)
    assert (counts['admitted_fields'],counts['read_context_fields'],counts['unread_fields'])==(44,5,66)
    assert len(source_proof)==46 and len(field_proof)==115
    if final:assert unchanged_fields==113 and unchanged_parents==22 and len(surgical)==2
    for item in owner_bindings:assert bind(Path(item['owner_path']))['sha256']==item['sha256']
    assert sha(manifest_path.read_bytes())==manifest_sha
    report={'schema':'hadith-bank-independent-reading-native-audit-v1','status':'PASS' if final else 'NATIVE_SOURCE_PASS_EXACT_TWO_FIELD_SEMANTIC_AMENDMENT_PENDING',
        'source_checkpoint':PIN,'candidate_manifest_path':manifest_name,'candidate_manifest_sha256':manifest_sha,
        'active_ledger_path':ACTIVE,'active_ledger_sha256':active_sha,'baseline_path':active['source_ledger_path'],
        'baseline_sha256':active['source_ledger_sha256'],'frozen_candidate_files_checked':len(owner_bindings),
        'source_first_receipt_sha256':READING_SHA,'independent_findings_sha256':FINDING_SHA,
        'counts':dict(counts),'metadata_leaf_equalities':dict(metadata),'metadata_leaf_equalities_total':sum(metadata.values()),
        'all_complete_source_records_and_references_equal':True,'source_files_reopened':46,'raw_reparses':23,
        'all_stored_plain_git_blob_hashes_pass':True,'source_parser_sha256':sha(Path(importer.__file__).read_bytes()),
        'source_review_engine_sha256':engine.engine_sha256,'observed_script_changes':0,
        'all_independently_accepted_span_positions_types_voices_families_exact':True,
        'surgical_final_amendment':{'required_cuts':2,'characters':130,'utf8_bytes':276,
            'unchanged_other_field_definitions':unchanged_fields if final else None,
            'unchanged_whole_parent_records':unchanged_parents if final else None,'fields':surgical},
        'all_owner_and_source_inputs_unchanged':True,'native_apply_and_finish_pass':True,
        'source_requests':0,'github_writes':0,'independent_pro_qc':'not_performed',
        'limitations':'This exact candidate and preserved source packet only. No authenticity certification, legal advice, canonical identity repair or live deployment claim.'}
    suffix='final' if final else 'v1-preflight'
    put(ROOT/('native-source-audit-'+suffix+'.json'),enc(report))
    put(ROOT/('field-and-source-proof-'+suffix+'.json.gz'),gzip.compress(enc({'fields':field_proof,'source_files':source_proof,'owner_bindings':owner_bindings}),mtime=0))
    print(json.dumps({'status':report['status'],'report':bind(ROOT/('native-source-audit-'+suffix+'.json')),
        'counts':dict(counts),'metadata_leaf_equalities_total':sum(metadata.values())}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--manifest-sha',required=True);p.add_argument('--active-sha',required=True);p.add_argument('--final',action='store_true');a=p.parse_args()
    audit(a.manifest,a.manifest_sha,a.active_sha,a.final)

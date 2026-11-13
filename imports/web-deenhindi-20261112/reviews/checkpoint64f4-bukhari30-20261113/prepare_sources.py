"""Reopen the exact assigned30 saved source pairs before semantic decisions."""
from pathlib import Path
import collections,hashlib,json,sys
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
EVIDENCE=WORK/'phase22-successor-acquisition-monitor/complete-held-evidence'
PIN='64f4ed50ed6026855237a5d547a86dd03e73f804'
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b
    else:p.write_bytes(b)
def read(p):return json.loads(p.read_bytes())

baseline=(ROOT/'input/cohort.jsonl').read_bytes()
reading=(ROOT/'input/full-hi-ur-reading-input-60.jsonl').read_bytes()
manifest_raw=(ROOT/'input/input-delivery-manifest.json').read_bytes()
assert sha(baseline)=='84374e54f524510e249fb59e39907c21b22b5ea10507fdc98ef0547963fe9c4a'
assert sha(reading)=='60a8a6e96d8a60e2bd3308dfe9bb2b6ce0cb91191754747f5b3aa1de63750084'
assert sha(manifest_raw)=='b25b208fd6702ffab10c5f848c6d243fe86365b45d5cc2372dfc959822094232'
manifest=json.loads(manifest_raw)
assert manifest['source_commit']==PIN and manifest['file_count']==64
for row in manifest['files']:
    data=Path(row['local_path']).read_bytes()
    assert len(data)==row['bytes'] and sha(data)==row['sha256'] and git(data)==row['git_blob_sha1']
rows=list(map(json.loads,baseline.splitlines()))
fields=list(map(json.loads,reading.splitlines()))
assert len(rows)==30 and len(fields)==60
assert collections.Counter(r['collection'] for r in rows)=={'bukhari':30}
lookup={(r['occurrence_id'],r['language']):r for r in fields}
assert len(lookup)==60
assert all(not r['complete_own_field_read'] and r['source_commit']==PIN for r in fields)
authority=read(EVIDENCE/'evidence-manifest.json')
entries=read(EVIDENCE/'held-state-entries.json')
assert authority['saved_head']==PIN
proofs=[]
for saved in rows:
    key=saved['collection']+':'+saved['number'];ident='deenhindi-'+key
    entry=entries[key]
    assert entry['parsed']['path']==saved['parsed_path']
    evidence=[]
    for kind,descriptor in [('raw',saved['snapshot']),('parsed',entry['parsed'])]:
        path=EVIDENCE/'sources'/descriptor['path'];data=path.read_bytes()
        expected=authority['files'][descriptor['path']]
        assert len(data)==expected['bytes'] and sha(data)==expected['sha256'] and git(data)==expected['git_blob_sha1']
        plain=importer.checked_bytes(EVIDENCE/'sources',descriptor)
        assert sha(plain)==descriptor['sha256']
        put(ROOT/'sources'/descriptor['path'],data)
        if kind=='raw':
            source,reference=importer.parse_record(plain,saved['collection'],saved['number'])
            assert source==saved['source_record'] and reference==saved['source_reference_verbatim']
        else:
            parsed=json.loads(plain)
            for name in ['collection','number','source_record','source_reference_verbatim','snapshot']:
                assert parsed[name]==saved[name]
            assert parsed['classification']==saved.get('intake_classification',saved['classification'])
        evidence.append({'kind':kind,'path':descriptor['path'],'stored_bytes':len(data),
            'stored_sha256':sha(data),'git_blob_sha1':git(data),'plain_bytes':len(plain),'plain_sha256':sha(plain)})
    for language in ['hi','ur']:
        item=lookup[(ident,language)];text=saved['source_record'][importer.LANGUAGE_FIELDS[language]]
        assert item['text']==text and item['text_sha256']==sha(text.encode())
        assert item['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))
        assert len(text)==item['characters'] and len(text.encode())==item['utf8_bytes']
    proofs.append({'id':ident,'source_record_sha256':sha(importer.json_bytes(saved['source_record'])),
        'source_reference_verbatim':saved['source_reference_verbatim'],'files':evidence,
        'raw_reparse_and_saved_parsed_object_equal':True})
assert sum(r['characters'] for r in fields)==45364 and sum(r['utf8_bytes'] for r in fields)==97929
selection={'schema':'fixed-primary-source-selection-v1','source_commit':PIN,
    'scope':'The fixed30 Bukhari new occurrences from the frozen disjoint102-entry saved-source packet.',
    'ids':['deenhindi-'+r['collection']+':'+r['number'] for r in rows],
    'source_baseline_sha256':sha(baseline),'reading_input_sha256':sha(reading),
    'input_manifest_sha256':sha(manifest_raw),'hi_ur_fields':60,'characters':45364,'utf8_bytes':97929,
    'semantic_reading_claimed_at_preparation':False,'source_site_requests':0,'github_writes':0}
proof={'schema':'primary-saved-source-provenance-check-v1','status':'PASS','source_commit':PIN,
    'cohort_sha256':sha(baseline),'input_manifest_sha256':sha(manifest_raw),
    'source_evidence_manifest_sha256':sha((EVIDENCE/'evidence-manifest.json').read_bytes()),
    'source_files_reopened':60,'complete_raw_reparses':30,
    'no_source_object_or_reference_change':True,'current_parser_sha256':sha(Path(importer.__file__).read_bytes()),
    'semantic_fields_read_by_verifier':0,'records':proofs}
put(ROOT/'input/selection.json',enc(selection));put(ROOT/'input/own-source-verification.json',enc(proof))
print(json.dumps({'selection_sha256':sha(enc(selection)),'source_verification_sha256':sha(enc(proof)),
    'occurrences':30,'files':60,'raw_reparses':30,'planned_hi_ur_fields':60},indent=2))

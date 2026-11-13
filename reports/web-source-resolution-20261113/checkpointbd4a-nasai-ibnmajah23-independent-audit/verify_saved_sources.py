"""Independent saved-source hash and parser replay for the exact root23 packet."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
EVIDENCE=WORK/'phase16-successor-acquisition-monitor/held-evidence'
PIN='bd4a75695d3c695e98bf8efa5ce07764ac5e2633'
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):return json.loads(p.read_bytes())

baseline=(ROOT/'input/cohort.jsonl').read_bytes()
assert sha(baseline)=='e215153fe6a482802e61087a97201a6faf76dd973ec9cca5c1def72515b9abcd'
rows=list(map(json.loads,baseline.splitlines()))
originals=(ROOT/'input/full-hi-ur-reading-input-46.jsonl').read_bytes()
extra=(ROOT/'input/additional-nasai2412-originals.jsonl').read_bytes()
assert sha(originals)=='f5f423c97289b1edf937ec9314dd954224aa4f79b532dd374519d246b8636a3f'
assert sha(extra)=='a2036f3de875c0b2ddefcc172bcc00a9367ac923afd72186970954d5916b941b'
fields=list(map(json.loads,originals.splitlines()))+list(map(json.loads,extra.splitlines()))
assert len(rows)==23 and len(fields)==49
lookup={(r['occurrence_id'],r['language']):r for r in fields};assert len(lookup)==49
authority=read(EVIDENCE/'evidence-manifest.json');entries=read(EVIDENCE/'held-state-entries.json')
assert authority['saved_head']==PIN
proofs=[];checked_fields=[]
for saved in rows:
    key=saved['collection']+':'+saved['number'];ident='deenhindi-'+key
    entry=entries[key];assert entry['parsed']['path']==saved['parsed_path']
    evidence=[]
    for kind,descriptor in [('raw',saved['snapshot']),('parsed',entry['parsed'])]:
        path=EVIDENCE/'sources'/descriptor['path'];data=path.read_bytes();expected=authority['files'][descriptor['path']]
        assert len(data)==expected['bytes'] and sha(data)==expected['sha256'] and git(data)==expected['git_blob_sha1']
        plain=importer.checked_bytes(EVIDENCE/'sources',descriptor);assert sha(plain)==descriptor['sha256']
        if kind=='raw':
            source,reference=importer.parse_record(plain,saved['collection'],saved['number'])
            assert source==saved['source_record'] and reference==saved['source_reference_verbatim']
        else:
            parsed=json.loads(plain)
            for name in ['collection','number','source_record','source_reference_verbatim','snapshot']:
                assert parsed[name]==saved[name]
            assert parsed['classification']==saved.get('intake_classification',saved['classification'])
        evidence.append({'kind':kind,'path':descriptor['path'],'stored_bytes':len(data),'stored_sha256':sha(data),
            'git_blob_sha1':git(data),'plain_bytes':len(plain),'plain_sha256':sha(plain)})
    for (identity,language),item in lookup.items():
        if identity!=ident:continue
        text=saved['source_record'][importer.LANGUAGE_FIELDS[language]]
        assert item['text']==text and item['text_sha256']==sha(text.encode())
        if 'source_record_sha256' in item:
            assert item['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))
        assert len(text)==item['characters'] and len(text.encode())==item['utf8_bytes']
        checked_fields.append({'id':ident,'language':language,'sha256':sha(text.encode()),
            'characters':len(text),'utf8_bytes':len(text.encode())})
    proofs.append({'id':ident,'source_record_sha256':sha(importer.json_bytes(saved['source_record'])),
        'source_reference_verbatim':saved['source_reference_verbatim'],'files':evidence,
        'raw_reparse_and_saved_parsed_object_equal':True})
assert len(checked_fields)==49 and sum(r['characters'] for r in checked_fields)==29579 and sum(r['utf8_bytes'] for r in checked_fields)==61743
proof={'schema':'independent-saved-source-provenance-check-v1','status':'PASS','source_commit':PIN,
    'cohort_sha256':sha(baseline),'originals_sha256':sha(originals),'additional_originals_sha256':sha(extra),
    'source_evidence_manifest_sha256':sha((EVIDENCE/'evidence-manifest.json').read_bytes()),
    'source_files_reopened':46,'complete_raw_reparses':23,'no_source_object_or_reference_change':True,
    'current_parser_sha256':sha(Path(importer.__file__).read_bytes()),'records':proofs,'checked_reading_fields':checked_fields,
    'source_requests':0,'github_writes':0,'semantic_reading_claimed_by_parser':False}
p=ROOT/'independent-source-verification.json';data=enc(proof)
if p.exists():assert p.read_bytes()==data
else:p.write_bytes(data)
print(json.dumps({'status':'PASS','path':str(p),'bytes':len(data),'sha256':sha(data),'files':46,'reparses':23}))

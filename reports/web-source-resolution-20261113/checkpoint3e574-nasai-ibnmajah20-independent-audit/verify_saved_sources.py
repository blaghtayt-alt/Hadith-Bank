"""Independent saved-source hash and parser replay for the exact root20 packet."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
EVIDENCE=WORK/'phase18-successor-acquisition-monitor/held-evidence'
PIN='3e574b9e7e4dd7cf8bc23232249004a18692c61c'
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):return json.loads(p.read_bytes())

baseline=(ROOT/'input/cohort.jsonl').read_bytes()
assert sha(baseline)=='0c794e514bcbebcda174dab501a3139963bda68b636a5a3b1049db0ce93f9a15'
rows=list(map(json.loads,baseline.splitlines()))
originals=(ROOT/'input/full-hi-ur-reading-input-40.jsonl').read_bytes()
assert sha(originals)=='bda781923e040e3941516f296430f726147ad1faf4ed03e6c4986d86939ce316'
fields=list(map(json.loads,originals.splitlines()))
assert len(rows)==20 and len(fields)==40
lookup={(r['occurrence_id'],r['language']):r for r in fields};assert len(lookup)==40
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
assert len(checked_fields)==40 and sum(r['characters'] for r in checked_fields)==10697 and sum(r['utf8_bytes'] for r in checked_fields)==21245
proof={'schema':'independent-saved-source-provenance-check-v1','status':'PASS','source_commit':PIN,
    'cohort_sha256':sha(baseline),'originals_sha256':sha(originals),
    'source_evidence_manifest_sha256':sha((EVIDENCE/'evidence-manifest.json').read_bytes()),
    'source_files_reopened':40,'complete_raw_reparses':20,'no_source_object_or_reference_change':True,
    'current_parser_sha256':sha(Path(importer.__file__).read_bytes()),'records':proofs,'checked_reading_fields':checked_fields,
    'source_requests':0,'github_writes':0,'semantic_reading_claimed_by_parser':False}
p=ROOT/'independent-source-verification.json';data=enc(proof)
if p.exists():assert p.read_bytes()==data
else:p.write_bytes(data)
print(json.dumps({'status':'PASS','path':str(p),'bytes':len(data),'sha256':sha(data),'files':40,'reparses':20}))

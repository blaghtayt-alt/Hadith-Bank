"""Freeze only six agreed scope restorations and two qualified speaker descriptions."""
from pathlib import Path
import gzip,hashlib,json
HERE=Path(__file__).resolve().parent
EVID=Path('imports/web-deenhindi-20261112/reviews/checkpoint17cd-bukhari-ibnmajah22-20261113')
ACTIVE=Path('imports/web-deenhindi-20261112/reviews/source-review-checkpoint17cd-bukhari-ibnmajah22-20261113.json.gz')
PEER=HERE.parent/'phase22-checkpoint17cd-bukhari-ibnmajah22-independent-audit'
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def binding(b):return {'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,('Immutable v2 output differs',str(p))
    else:p.write_bytes(b)
def fieldmap(r):return {f['language']:f for f in r['field_reviews']}
def mask(f):return {i for s in f['spans'] for i in range(s['start'],s['end'])}
def attributes(f):return {i:{k:v for k,v in s.items() if k not in ['start','end','sha256','reason']} for s in f['spans'] for i in range(s['start'],s['end'])}
v1raw=(HERE/'delivery-manifest-v1.json').read_bytes()
assert sha(v1raw)=='95967f1f4950735e7b1b03188911367c39dfaf8b1eb590af23148fb470581ff3'
v1=json.loads(v1raw);draft=json.loads((HERE/'candidate-delivery-manifest-v2.json').read_bytes())
for manifest in [v1,draft]:
    for r in manifest['files']:
        b=Path(r['local_path']).read_bytes();assert binding(b)=={k:r[k] for k in ['bytes','sha256','git_blob_sha1']}
findings=(PEER/'independent-boundary-findings-v1.json').read_bytes()
planraw=(PEER/'accepted-reviewed-field-plan-v1.json').read_bytes()
assert sha(findings)=='fb24b7bf48b3ae07b1cd79a4f96871f94d94f8ebfab6e9ead90dedb42b710303'
assert sha(planraw)=='4ade18cd65ca10054e4e6befdf70424f331ddb68cf915324f22c5eef811877c6'
plan={(r['occurrence_id'],r['language']):r for r in json.loads(planraw)['fields']};assert len(plan)==44
before_raw=(HERE/'publish-v1'/ACTIVE).read_bytes();after_raw=(HERE/'candidate-v2'/ACTIVE).read_bytes()
assert sha(before_raw)=='e1c976355261853f38ee258aaade04f3ff332743b0790fdf43937f900dacf705'
before={r['id']:r for r in json.loads(gzip.decompress(before_raw))['records']}
after={r['id']:r for r in json.loads(gzip.decompress(after_raw))['records']}
source={'deenhindi-'+r['collection']+':'+r['number']:r['source_record'] for r in map(json.loads,(HERE/'input/cohort.jsonl').read_bytes().splitlines())}
assert set(before)==set(after)==set(source) and len(before)==22
requested={
 ('deenhindi-bukhari:2647','hi'):(222,230,'(घर में)'),('deenhindi-bukhari:2647','ur'):(195,206,'( گھر میں )'),
 ('deenhindi-bukhari:2681','hi'):(370,405,'(मुहम्मद (सल्लल्लाहु अलैहि वसल्लम))'),('deenhindi-bukhari:2681','ur'):(320,347,'( محمد صلی اللہ علیہ وسلم )'),
 ('deenhindi-bukhari:2698','hi'):(263,274,'(क़ुरैश से)'),('deenhindi-bukhari:2698','ur'):(229,240,'( قریش سے )'),
}
speaker_only={('deenhindi-bukhari:2693','hi'),('deenhindi-bukhari:2693','ur')}
affected=set(requested)|speaker_only;parents={i for i,l in affected}
changes=[];unchanged_fields=0;unchanged_parents=0;plan_checks=0
for ident,old in before.items():
    new=after[ident]
    stable=lambda r:{k:v for k,v in r.items() if k not in ['field_reviews','reason']}
    assert stable(old)==stable(new)
    if ident not in parents:assert old==new;unchanged_parents+=1
    a,b=fieldmap(old),fieldmap(new);assert set(a)==set(b)
    for language,f in a.items():
        key=(ident,language);g=b[language]
        if key in plan:
            pure=lambda s:{k:v for k,v in s.items() if k!='reason'}
            assert [pure(s) for s in g['spans']]==plan[key]['expected_spans'],(key,'exact independent span/voice plan')
            plan_checks+=1
        if key not in affected:assert f==g;unchanged_fields+=1;continue
        stable_field=lambda x:{k:v for k,v in x.items() if k not in ['spans','reason']}
        assert stable_field(f)==stable_field(g)
        oldattrs,newattrs=attributes(f),attributes(g)
        item={'id':ident,'language':language,'before_field_sha256':sha(enc(f)),'after_field_sha256':sha(enc(g))}
        if key in requested:
            start,end,literal=requested[key];text=source[ident][f['source_field']]
            assert text[start:end]==literal
            assert mask(g)-mask(f)==set(range(start,end)) and not mask(f)-mask(g)
            assert all(newattrs[i]==v for i,v in oldattrs.items())
            assert len({json.dumps(newattrs[i],sort_keys=True) for i in range(start,end)})==1
            assert newattrs[start]==newattrs[start-1]==newattrs[end]
            item.update(kind='exact_source_scope_restoration',start=start,end=end,text=literal,
                text_sha256=sha(literal.encode()),characters_restored=end-start,utf8_bytes_restored=len(literal.encode()),
                all_previously_selected_positions_and_attribution_values_exact=True)
        else:
            assert mask(g)==mask(f)
            for i,v in oldattrs.items():assert {k:x for k,x in newattrs[i].items() if k!='speaker'}=={k:x for k,x in v.items() if k!='speaker'}
            assert all(newattrs[i]['speaker']==plan[key]['expected_spans'][0]['speaker'] for i in oldattrs)
            item.update(kind='source_local_honorific_pronoun_qualification',characters_restored=0,utf8_bytes_restored=0,
                source_positions_types_components_and_families_exact=True,final_speaker=plan[key]['expected_spans'][0]['speaker'])
        changes.append(item)
assert len(changes)==8 and unchanged_fields==102 and unchanged_parents==18 and plan_checks==44
assert sum(r['characters_restored'] for r in changes)==103 and sum(r['utf8_bytes_restored'] for r in changes)==216
summary=draft['summary'];assert summary==v1['summary']
out=HERE/'publish-v2';archive=EVID/'independent-boundary-v2/before-v1'
for r in draft['files']:
    if r['path']==str(EVID/'package-file-manifest.json'):continue
    put(out/r['path'],Path(r['local_path']).read_bytes())
for r in v1['files']:put(out/archive/'payload'/r['path'],Path(r['local_path']).read_bytes())
put(out/archive/'delivery-manifest-v1.json',v1raw)
receipt={'schema':'hadith-bank-source-scope-and-attribution-refinement-v2','status':'PASS',
 'source_checkpoint':'17cd396eb858a29162505d545aad556ac73ce9ce','previous_manifest_sha256':sha(v1raw),
 'previous_active_sha256':sha(before_raw),'final_active_sha256':sha(after_raw),'independent_findings_sha256':sha(findings),
 'independent_complete_field_plan_sha256':sha(planraw),'all44_reviewed_fields_match_exact_peer_span_voice_plan':True,
 'exact_changes':changes,'scope_restoration_fields':6,'speaker_description_only_fields':2,
 'characters_restored':103,'utf8_bytes_restored':216,'characters_removed':0,
 'unchanged_other_field_definitions':102,'unchanged_whole_parents':18,
 'parent_source_and_dispositions_unchanged':True,'all_types_components_families_and_prior_selected_positions_exact':True,
 'initial_complete_source_first_receipt_unchanged':True,'initial_notes_and_all_v1_payloads_preserved':True,
 'v1_payload_files_archived':len(v1['files']),'v1_manifest_archived':True,
 'final_native_summary':summary,'final_independent_gate_pending':True,
 'reason':'Actual arrival location, the otherwise-pronominal subject and treaty counterparty carry meaningful source scope. Restore only their six exact literals. Separately qualify2693’s speaker descriptions to the locally supplied honorific pronoun without adding an explicit name. All initial broader-context judgments remain immutable historical evidence.',
 'new_language_reading_credit':0,'github_writes':0,'source_http_requests':0}
put(out/EVID/'independent-boundary-v2/amendment-receipt.json',enc(receipt))
put(out/EVID/'independent-boundary-v2/independent-boundary-findings-v1.json',findings)
put(out/EVID/'independent-boundary-v2/accepted-reviewed-field-plan-v1.json',planraw)
put(out/EVID/'independent-boundary-v2/package_v2.py',Path(__file__).read_bytes())
def record(p,local=False):
    r={'path':p.relative_to(out).as_posix(),**binding(p.read_bytes())}
    if local:r.update(local_path=str(p),source_path=str(p))
    return r
portable=out/EVID/'package-file-manifest.json'
put(portable,enc({'schema':'hadith-bank-source-review-package-manifest-v2','source_checkpoint':receipt['source_checkpoint'],
 'active_ledger':str(ACTIVE),'summary':summary,'amendment':receipt,'manifest_excludes_its_own_recursive_hash':True,
 'files':[record(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=portable]}))
manifest={'schema':'hadith-bank-source-review-delivery-v2','output_root':str(out),'summary':summary,'amendment':receipt,
 'files':[record(p,True) for p in sorted(out.rglob('*')) if p.is_file()]}
manifest.update(total_files=len(manifest['files']),total_bytes=sum(r['bytes'] for r in manifest['files']))
put(HERE/'delivery-manifest-v2.json',enc(manifest));put(HERE/'amendment-receipt-v2.json',enc(receipt))
for r in v1['files']:assert binding(Path(r['local_path']).read_bytes())=={k:r[k] for k in ['bytes','sha256','git_blob_sha1']}
assert (HERE/'delivery-manifest-v1.json').read_bytes()==v1raw
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(manifest)),'active_sha256':sha(after_raw),
 'files':manifest['total_files'],'bytes':manifest['total_bytes'],'amendment_receipt_sha256':sha(enc(receipt)),
 'restored_characters':103,'restored_utf8_bytes':216,'unchanged_fields':102,'unchanged_parents':18}))

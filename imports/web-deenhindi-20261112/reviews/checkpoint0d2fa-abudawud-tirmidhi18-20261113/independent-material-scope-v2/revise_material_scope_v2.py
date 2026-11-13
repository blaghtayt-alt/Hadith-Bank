#!/usr/bin/env python3
"""Restore four independently agreed source scopes; preserve the entire frozen v1."""
from pathlib import Path
import copy,gzip,hashlib,json,pprint,subprocess,sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import manual_boundaries
PREFIX='imports/web-deenhindi-20261112/reviews/checkpoint0d2fa-abudawud-tirmidhi18-20261113'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpoint0d2fa-abudawud-tirmidhi18-20261113.json.gz'
OLD=ROOT/'publish-v1';OUT=ROOT/'publish-v2';REV=PREFIX+'/independent-material-scope-v2'
AUDIT=ROOT.parent/'phase21-checkpoint0d2fa-mixed18-independent-audit'
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

def put(path,data):
    p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

def positions(field):
    return {i for s in field['spans'] for i in range(s['start'],s['end'])}

def label(field,index):
    return {k:v for k,v in next(s for s in field['spans'] if s['start']<=index<s['end']).items() if k not in ('start','end','sha256')}

def main():
    assert not OUT.exists() and not (ROOT/'delivery-manifest-v2.json').exists()
    mb=(ROOT/'delivery-manifest-v1.json').read_bytes()
    assert sha(mb)=='e3514907ac9d889dc4bb58a8a47386eb535d0e6307bc837f56ae2aae263793f2'
    manifest=json.loads(mb);assert len(manifest['files'])==24
    for f in manifest['files']:
        b=(OLD/f['path']).read_bytes();assert sha(b)==f['sha256'] and len(b)==f['bytes']
        put(REV+'/before-v1/payload/'+f['path'],b)
    put(REV+'/before-v1/delivery-manifest-v1.json',mb)
    for name,expected in [('independent-boundary-findings-v1.json','35d288b9721d0a4b2cdfe269c85a4b8b49d02e073815a4ec84b0bf95cb819dae'),('accepted-reviewed-field-plan.json','e109842aa48355de57b48e18e86d150cd8936357b33a7e484472f3de6d393fff')]:
        b=(AUDIT/name).read_bytes();assert sha(b)==expected;put(REV+'/'+name,b)
    findings=json.loads((OUT/REV/'independent-boundary-findings-v1.json').read_bytes())
    plan=json.loads((OUT/REV/'accepted-reviewed-field-plan.json').read_bytes())
    changes={}
    for f in findings['findings']:changes.setdefault((f['id'].removeprefix('deenhindi-'),f['language']),[]).append(f)
    assert len(changes)==3 and sum(len(v) for v in changes.values())==4
    assert sum(f['characters'] for v in changes.values() for f in v)==62
    assert sum(f['utf8_bytes'] for v in changes.values() for f in v)==114
    sources={r['collection']+':'+r['number']:r for r in map(json.loads,(ROOT/'input/cohort.jsonl').read_bytes().splitlines())}
    records=copy.deepcopy(manual_boundaries.records)
    refinements={
        ('tirmidhi:2549','ur'):(
            "The repeated lower-rank-object label and 'we (Paradise people)' identification are explanatory aliases.",
            "The lower-rank recipient label and the Paradise-inhabitant identification materially specify the local participant referents and remain within the existing transmitted account. They are preserved as this source's rendering, without declaring their parenthetical wording verbatim Prophetic speech."),
        ('tirmidhi:2551','hi'):(
            "The Fajr/Maghrib parenthesis is a prayer-name explanation of the already printed times.",
            "The Fajr/Maghrib parenthesis materially restricts the supplied prayer scope and remains as the source's rendering. Preserve its exact names and after-setting wording alongside the verse's before-setting wording, without claiming the parenthesis is verbatim Prophetic speech or substituting a different prayer."),
        ('tirmidhi:2551','ur'):(
            "Keep the verse and translation as recitation content, while the prayer-name gloss, numbered footnote and final grading remain context.",
            "Keep the actual verse and translation as recitation content and the Fajr/Maghrib names as material source-rendered prayer scope. Only the numbered footnote and final grading remain context. The after-setting wording and the verse's before-setting wording stay exact; no external harmonization or verbatim attribution of the parenthesis is implied."),
    }
    for row in records:
        for language,field in row['fields'].items():
            key=(row['key'],language)
            if key not in changes:continue
            text=sources[row['key']]['source_record'][{'hi':'translationHindi','ur':'translationUrdu'}[language]]
            removed=[]
            for change in changes[key]:
                assert sha(text.encode())==change['source_text_sha256']
                assert text[change['start']:change['end']]==change['text']
                assert sha(change['text'].encode())==change['sha256']
                cuts=[c for c in field['omit_source_context'] if c['text']==change['text']]
                assert len(cuts)==1 and cuts[0]['expected_count']==1;removed.append(cuts[0])
            field['omit_source_context']=[c for c in field['omit_source_context'] if c not in removed]
            assert not field['omit_source_context']
            before,after=refinements[key];assert field['reason'].count(before)==1
            field['reason']=field['reason'].replace(before,after)
            field['reason']+=' V2 explicit reconsideration: the initial narrower selection treated these supplied scopes as dispensable explanation. Complete independent comparison established their material participant or prayer scope; the exact earlier selection and reasons remain archived, while all existing component, speaker, type and report-family identities remain unchanged.'
    (ROOT/'manual_boundaries_v2.py').write_text('"""Four exact material-scope restorations; the immutable first reading remains archived."""\nrecords = '+pprint.pformat(records,width=110,sort_dicts=False)+'\n',encoding='utf-8')
    compiler=(ROOT/'compile_review.py').read_text().replace('from manual_boundaries import records as instructions','from manual_boundaries_v2 import records as instructions').replace("OUT=ROOT/'publish-v1'","OUT=ROOT/'publish-v2'").replace('delivery-manifest-v1.json','delivery-manifest-v2.json')
    compiler=compiler.replace("for n in ('source_first_notes.py','manual_boundaries.py','compile_review.py'):put(PREFIX+'/'+n,(ROOT/n).read_bytes())","for target,source in (('source_first_notes.py','source_first_notes.py'),('manual_boundaries.py','manual_boundaries_v2.py'),('compile_review.py','compile_review_v2.py')):put(PREFIX+'/'+target,(ROOT/source).read_bytes())")
    compiler=compiler.replace('Initial primary16register/2source-only','Version2 primary16register/2source-only after four independently agreed material source-scope restorations')
    (ROOT/'compile_review_v2.py').write_text(compiler)
    subprocess.run([sys.executable,str(ROOT/'compile_review_v2.py')],check=True)
    before=json.loads(gzip.decompress((OLD/ACTIVE).read_bytes()));after=json.loads(gzip.decompress((OUT/ACTIVE).read_bytes()))
    oldrows={r['id']:r for r in before['records']};newrows={r['id']:r for r in after['records']};assert oldrows.keys()==newrows.keys()
    expected={(f['id'],f['language']):f for f in plan['reviewed_fields']}
    unchanged_fields=unchanged_parents=restored=prior_selected=0;proof=[]
    for rid,a in oldrows.items():
        b=newrows[rid];assert {k:v for k,v in a.items() if k!='field_reviews'}=={k:v for k,v in b.items() if k!='field_reviews'}
        if a==b:unchanged_parents+=1
        for old,new in zip(a['field_reviews'],b['field_reviews'],strict=True):
            key=(rid,new['language']);assert new['spans']==expected[key]['expected_spans']
            assert new['text_sha256']==old['text_sha256']==expected[key]['source_text_sha256']
            prior_selected+=len(positions(old));cuts=changes.get((rid.removeprefix('deenhindi-'),new['language']))
            if cuts:
                assert {k:v for k,v in old.items() if k not in ('spans','reason')}=={k:v for k,v in new.items() if k not in ('spans','reason')}
                assert positions(old)<=positions(new)
                assert positions(new)-positions(old)=={i for c in cuts for i in range(c['start'],c['end'])}
                for i in positions(old):assert label(old,i)==label(new,i)
                oldlabels={json.dumps(label(old,i),sort_keys=True) for i in positions(old)}
                assert {json.dumps(label(new,i),sort_keys=True) for i in positions(new)}==oldlabels
                restored+=len(positions(new)-positions(old))
                proof.append({'id':rid,'language':new['language'],'before_reason':old['reason'],'after_reason':new['reason'],'all_prior_selected_positions_and_component_type_speaker_family_exact':True})
            else:assert old==new;unchanged_fields+=1
    assert (unchanged_fields,unchanged_parents,restored,prior_selected)==(45,16,62,10433)
    assert before['source_ledger_sha256']==after['source_ledger_sha256']
    assert sha((ROOT/'complete-source-first-readings.json').read_bytes())=='d06cabecb168dc8dadf5342a93fe53721e803c5b289b7157b66d8b3df0360410'
    assert sha((ROOT/'source_first_notes.py').read_bytes())=='f1ba3f34012e73e385e4bc57eba658f97862d641dae9254591a393b59ffb72df'
    for f in manifest['files']:assert (OLD/f['path']).read_bytes()==(OUT/REV/'before-v1/payload'/f['path']).read_bytes()
    receipt={'schema':'hadith-bank-material-source-scope-amendment-v2','result':'PASS','source_checkpoint':after['source_checkpoint'],'before_manifest_sha256':sha(mb),'before_active_sha256':sha((OLD/ACTIVE).read_bytes()),'after_active_sha256':sha((OUT/ACTIVE).read_bytes()),'exact_restorations':findings['findings'],'changed_reasons':proof,'restored_ranges':4,'changed_reviewed_fields':3,'restored_characters':62,'restored_utf8_bytes':114,'selected_characters_moved_to_context':0,'isolated_whitespace_changes':0,'all10433_prior_selected_positions_and_component_type_speaker_family_exact':True,'final_selected_characters':10495,'final_selected_spans':46,'unchanged_reviewed_fields':45,'unchanged_whole_parents':16,'unchanged_unread_nonempty_slots':42,'parent_dispositions_unchanged':{'register':16,'source_only':2},'all48_final_fields_match_root_accepted_plan':True,'all24_v1_payloads_and_manifest_archived_and_rehashed':True,'initial_notes_and_source_first_receipt_unchanged':True,'source_http_requests':0,'github_writes':0,'canonical_identity_fills':0,'independent_pro_qc':'not_performed','final_independent_hash_bound_gate':'pending_parent'}
    put(REV+'/amendment-receipt.json',enc(receipt));put(REV+'/revise_material_scope_v2.py',Path(__file__).read_bytes())
    packaging=(ROOT/'package_review.py').read_text().replace("OUT=ROOT/'publish-v1'","OUT=ROOT/'publish-v2'").replace('delivery-manifest-v1.json','delivery-manifest-v2.json').replace('boundary-view-v1.json','boundary-view-v2.json').replace('672e1b32189c64a5739c7fbce5bb61615986aeb7739ed7d9b8a626baed46019d',sha((OUT/ACTIVE).read_bytes()))
    retained={
        ('tirmidhi:2549','ur','( ادنیٰ مرتبے والے کو )'):'Material lower-rank recipient referent for the garment/reaction pronouns, preserved as source-rendered narrative scope in the existing account, not claimed as verbatim Prophetic wording.',
        ('tirmidhi:2549','ur','( جنتی )'):'Material Paradise-inhabitant identification of the first-person plural, distinguishing the account participants from the current reception-dialogue speakers.',
        ('tirmidhi:2551','hi','(फ़ज्र और मग़रिब)'):'Material source-rendered prayer scope. Preserve the printed Fajr/Maghrib and after-setting wording alongside the later before-setting verse without external correction or a verbatim parenthesis claim.',
        ('tirmidhi:2551','ur','( فجر اور مغرب )'):'Material source-rendered prayer scope. Preserve the exact Fajr/Maghrib and time-wording difference; no replacement prayer or historical-verbatim parenthesis claim.',
    }
    packaging=packaging.replace('\ndef main():','\nRETAINED.update('+repr(retained)+')\n\ndef main():',1)
    packaging=packaging.replace("counts['narrative_qualifications_or_recitations']==3","counts['narrative_qualifications_or_recitations']==7").replace("cuts['literal_omissions']==9","cuts['literal_omissions']==5").replace("'literal_context_cuts_inside_components':9","'literal_context_cuts_inside_components':5")
    packaging=packaging.replace("report={\n", "report={\n        'revision':'v2 after four exact independently agreed material-scope restorations; original source-first reading history remains unchanged',\n        'amendment_receipt_path':PREFIX+'/independent-material-scope-v2/amendment-receipt.json',\n",1)
    packaging=packaging.replace("prayer-name explanation and grade/footnote apparatus stay context.","the supplied Fajr/Maghrib names remain selected as material source-rendered scope, while grade/footnote apparatus stays context. The names are not claimed as verbatim historical Prophetic wording.")
    packaging=packaging.replace("its no-truly-inferior-rank qualification remains.","its no-truly-inferior-rank qualification and the exact lower-rank/inhabitant participant referents remain.")
    (ROOT/'package_review_v2.py').write_text(packaging)
    subprocess.run([sys.executable,str(ROOT/'package_review_v2.py')],check=True)
    print(json.dumps({'amendment_receipt_sha256':sha((OUT/REV/'amendment-receipt.json').read_bytes()),'unchanged_fields':unchanged_fields,'unchanged_whole_parents':unchanged_parents,'restored_characters':restored,'selected_characters':prior_selected+restored}))

if __name__=='__main__':main()

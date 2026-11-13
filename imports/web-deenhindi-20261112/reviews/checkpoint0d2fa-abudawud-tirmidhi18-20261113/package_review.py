#!/usr/bin/env python3
"""Freeze the explicitly read18-parent package after exact native/source validation."""
import collections,gzip,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'publish-v2'
COHORT='checkpoint0d2fa-abudawud-tirmidhi18-20261113'
PREFIX='imports/web-deenhindi-20261112/reviews/'+COHORT
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-'+COHORT+'.json.gz'
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(path,b):
    p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    return {'path':path,'bytes':len(b),'sha256':sha(b),'git_blob_sha1':blob(b)}

RETAINED={
 ('abudawud:2578','ur','( دوبارہ )'):'Actual repetition/sequence qualification of the second narrated race, not a lexical definition.',
 ('tirmidhi:2549','ur','( حالانکہ حقیقت میں اس میں سے کوئی بھی کم مرتبے والا نہیں ہو گا )'):'Substantive limitation of the reported rank comparison: no inhabitant is truly inferior. This actual narrative qualification remains source-rendered.',
 ('tirmidhi:2551','hi','(सूरज निकलने से पहले और सूरज डूबने से पहले अपने रब की तस्बीह तारीफ़ के साथ बयान करो)'):'Complete source translation of the explicitly recited verse. This is actual quotation/recitation content, not a locator label or detached lexical gloss.',
}

RETAINED.update({('tirmidhi:2549', 'ur', '( ادنیٰ مرتبے والے کو )'): 'Material lower-rank recipient referent for the garment/reaction pronouns, preserved as source-rendered narrative scope in the existing account, not claimed as verbatim Prophetic wording.', ('tirmidhi:2549', 'ur', '( جنتی )'): 'Material Paradise-inhabitant identification of the first-person plural, distinguishing the account participants from the current reception-dialogue speakers.', ('tirmidhi:2551', 'hi', '(फ़ज्र और मग़रिब)'): 'Material source-rendered prayer scope. Preserve the printed Fajr/Maghrib and after-setting wording alongside the later before-setting verse without external correction or a verbatim parenthesis claim.', ('tirmidhi:2551', 'ur', '( فجر اور مغرب )'): 'Material source-rendered prayer scope. Preserve the exact Fajr/Maghrib and time-wording difference; no replacement prayer or historical-verbatim parenthesis claim.'})

def main():
    assert not (ROOT/'delivery-manifest-v2.json').exists()
    raw=(OUT/ACTIVE).read_bytes()
    assert sha(raw)=='96703552593953aef526f234822cd8dbfce0d6460c5d194cbd2fa03127d3e756'
    doc=json.loads(gzip.decompress(raw));v=json.loads((OUT/PREFIX/'validation.json').read_bytes());t=v['totals']
    assert t['source_occurrences']==18 and t['register']==16 and t['exclude']==2
    assert (t['complete_fields_read'],t['admitted_language_fields'],t['read_context_fields'],t['unread_context_fields'])==(48,38,10,42)
    fields=json.loads(gzip.decompress((OUT/PREFIX/'complete-field-readings-and-boundaries.json.gz').read_bytes()))['fields']
    assert len(fields)==48
    items=[];used=set();counts=collections.Counter();view=[];separators=[]
    for f in fields:
        text=f['text'];mask={i for s in f['selected_spans'] for i in range(s['start'],s['end'])}
        assert all(s['text'].strip() and '؎' not in s['text'] for s in f['selected_spans'])
        for c in f['retained_context']:
            if not c['text'].strip():
                separators.append({'id':f['occurrence_id'],'language':f['language'],'start':c['start'],'end':c['end'],'text':c['text'],'sha256':sha(c['text'].encode()),'reason':'Isolated separator between individually excluded source apparatus spans; retained as context rather than a whitespace-only quotation.'})
        for m in re.finditer(r'\([^()]*\)',text):
            if not set(range(m.start(),m.end()))<=mask:continue
            literal=m.group();key=(f['occurrence_id'].removeprefix('deenhindi-'),f['language'],literal)
            if key in RETAINED:
                reason=RETAINED[key];category='individually_read_narrative_qualification_or_recitation';used.add(key);counts['narrative_qualifications_or_recitations']+=1
            else:
                assert re.fullmatch(r'\((?:सल्लल्लाहु|रज़ियल्लाहु|रज़ियल्लाहु|रदि अल्लाहु|रदी अल्लाहु|रज़ि अल्लाहु|\s*صلی اللہ|Radi Allahu|Sallallahu|ﷺ)[^()]*\)',literal),(key,literal)
                reason='Exact printed source honorific, read and preserved without normalization.';category='source_honorific';counts['honorifics']+=1
            items.append({'id':f['occurrence_id'],'language':f['language'],'field_sha256':f['text_sha256'],'start':m.start(),'end':m.end(),'text':literal,'sha256':sha(literal.encode()),'category':category,'reason':reason})
        view.append({'id':f['occurrence_id'],'language':f['language'],'text':text,'reason':f['actual_field_review']['reason'],'selected_spans':f['selected_spans'],'retained_context':f['retained_context']})
    assert used==set(RETAINED) and counts['narrative_qualifications_or_recitations']==7
    cuts=json.loads((OUT/PREFIX/'explicit-source-apparatus-context.json').read_bytes())
    assert cuts['literal_omissions']==5
    # The one separator between the ghutti gloss and the footnote is represented
    # inside their contiguous native context interval, with exact literal proof.
    separator_field=next(f for f in fields if f['occurrence_id']=='deenhindi-abudawud:2563' and f['language']=='ur')
    separator_start=separator_field['text'].index('( گھٹی )')+len('( گھٹی )')
    assert separator_field['text'][separator_start:separator_start+1]==' '
    assert not any(s['start']<=separator_start<s['end'] for s in separator_field['selected_spans'])
    separators.append({'id':separator_field['occurrence_id'],'language':'ur','start':separator_start,'end':separator_start+1,'text':' ','sha256':sha(b' '),'reason':'The isolated separator between the explicitly cut ghutti synonym and footnote marker remains within their contiguous context interval.'})
    put(PREFIX+'/retained-source-parentheses.json',enc({'scope':'Individually authored reasons for every non-honorific selected parenthesis; an inventory of completed readings, not an automatic admission rule.','counts':dict(counts),'items':items,'selected_footnote_markers':0,'selected_explicit_verse_locator_labels':0,'isolated_context_separators':separators}))
    (ROOT/'boundary-view-v2.json').write_bytes(enc(view))
    original=(ROOT/'input/full-field-reading-input-48.jsonl').read_bytes()
    assert sha(original)=='d5fab447f9bcae574117b2d8f1eb976a382a88f6f2b657a70aa7bdc445dea7fb'
    put(PREFIX+'/original-full-field-reading-input-48.jsonl.gz',gzip.compress(original,mtime=0))
    put(PREFIX+'/original-source-verification.json',(ROOT/'input/source-verification.json').read_bytes())
    put(PREFIX+'/freeze_source_first.py',(ROOT/'freeze_source_first.py').read_bytes())
    report={
        'revision':'v2 after four exact independently agreed material-scope restorations; original source-first reading history remains unchanged',
        'amendment_receipt_path':PREFIX+'/independent-material-scope-v2/amendment-receipt.json',
        'schema':'hadith-bank-source-bound-primary-review-v1','result':'PASS',
        'source_commit':doc['source_checkpoint'],
        'cohort':'Exactly18 new0d2fa occurrences:12 AbuDawud and6 Tirmidhi, disjoint from the other three assigned new86 groups.',
        'source_worker_run_id':43466109189,'artifact_id':14061659376,
        'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(raw),
        'source_baseline_path':doc['source_ledger_path'],'source_baseline_sha256':doc['source_ledger_sha256'],
        'source_first_receipt_sha256':'d06cabecb168dc8dadf5342a93fe53721e803c5b289b7157b66d8b3df0360410',
        'source_first_notes_sha256':'f1ba3f34012e73e385e4bc57eba658f97862d641dae9254591a393b59ffb72df',
        'actual_readings':{'full_fields':48,'characters':13826,'utf8_bytes':27038,'admitted':38,'reviewed_context_only':10,'unread_siblings':42,'empty_siblings':0},
        'dispositions':{'registered':16,'source_only':2,'unresolved':0},
        'source_only_ids':['deenhindi-abudawud:2582','deenhindi-abudawud:2617'],
        'native_validation':v,'literal_context_cuts_inside_components':5,
        'retained_parentheses':dict(counts),'isolated_context_separator_characters':1,
        'source_files_reopened':36,'exact_raw_reparses':18,
        'scope_qualifications':[
            'Abu2582 is a term-domain explanation in every own language; Abu2617 is a place-name correction. All ten nonempty fields were read before preserving these two parents as source-only.',
            'Abu2563 preserves the main newborn/branding observation and Hisham’s explicitly uncertain finite ear-location variant in separate components of one family. Hindi’s missing observation link is not completed from Urdu.',
            'Abu2610 admits independently read prohibitions in all five fields. Malik’s explicit causal conjecture and Hindi’s damaged unassigned explanatory tail remain context; no speaker is imported into Hindi.',
            'The short Nafi-to-Ibn-Umar frame remains coherent attribution; only the long Arabic prefatory multi-step route is excluded. This final source-bound choice is explicitly recorded as a refinement of the initial notes.',
            'T2549 Hindi remains its own condensed account with the full recipient-linked Said frame. Urdu preserves the actual reception wish/question separately from the longer transmitted account; its no-truly-inferior-rank qualification and the exact lower-rank/inhabitant participant referents remain.',
            'T2551 retains actual recitation and its complete source translation. The source’s time wording and Maghrib gloss are not corrected or harmonized; the supplied Fajr/Maghrib names remain selected as material source-rendered scope, while grade/footnote apparatus stays context. The names are not claimed as verbatim historical Prophetic wording.',
            'T2565 admits only the actual finite hadith fragment independently present inside each field’s exegesis. Ultimate speaker and complete parent identity remain unknown; the verse, listening explanation and route remain context.',
            'T2619 admits its finite anonymous reported clause while retaining the A’mash/previous-chain pointer as context. Familiar wording is not used to supply a canonical identity or Prophetic speaker.',
            'All original words, defects, references, names, grades, scripts and raw/parsed bytes remain unchanged. Unread siblings are complete context and are not claimed as reviewed.',
        ],
        'peer_notes_inspected_before_primary_freeze':False,'source_http_requests':0,'github_writes':0,'shared_engine_changes':0,
        'independent_pro_qc':'not_performed','certified_release_eligible':False,
        'limitations':'Primary complete own-field review and local SourceReviews apply/finish, saved-source reparse and lossless metadata/partition validation. Independent second reading, combined repository export and actual reader/deployment remain separate gates.',
    }
    put('reports/web-source-resolution-20261113/checkpoint0d2fa-abudawud-tirmidhi18-primary-review.json',enc(report))
    put(PREFIX+'/package_review.py',Path(__file__).read_bytes())
    def inventory(local=False):
        files=[]
        for p in sorted(OUT.rglob('*')):
            if p.is_file() and (local or p.relative_to(OUT).as_posix()!=PREFIX+'/portable-manifest.json'):
                b=p.read_bytes();f={'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':blob(b)}
                if local:f['local_path']=str(p)
                files.append(f)
        return files
    files=inventory()
    put(PREFIX+'/portable-manifest.json',enc({'schema':'hadith-bank-portable-review-package-v1','source_commit':doc['source_checkpoint'],'active_ledger_sha256':sha(raw),'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}))
    files=inventory(True)
    manifest={'schema':'hadith-bank-source-review-delivery-v1','source_commit':doc['source_checkpoint'],'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(raw),'source_baseline_sha256':doc['source_ledger_sha256'],'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}
    mb=enc(manifest);(ROOT/'delivery-manifest-v2.json').write_bytes(mb)
    print(json.dumps({'status':'FROZEN','manifest_sha256':sha(mb),'active_ledger_sha256':sha(raw),'files':len(files),'bytes':manifest['total_bytes'],'dispositions':report['dispositions'],'actual_readings':report['actual_readings'],'retained_parentheses':dict(counts)},indent=2))

if __name__=='__main__':main()

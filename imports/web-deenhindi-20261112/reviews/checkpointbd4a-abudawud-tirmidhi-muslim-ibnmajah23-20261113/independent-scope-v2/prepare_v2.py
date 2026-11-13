#!/usr/bin/env python3
"""Apply seven independently reviewed scope restorations; retain frozen v1."""
import copy, hashlib, importlib.util, json, pprint, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import manual_boundaries
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
BEFORE=ROOT/'publish-v1';OUT=ROOT/'publish-v2'
PREFIX='imports/web-deenhindi-20261112/reviews/checkpointbd4a-abudawud-tirmidhi-muslim-ibnmajah23-20261113'
REVISION=PREFIX+'/independent-scope-v2'
AUDIT=ROOT.parent/'phase18-checkpointbd4a-abudawud-tirmidhi-muslim-ibnmajah23-independent-audit'
RESTORE={
 ('tirmidhi:2382','ur'):['( قرآن سیکھنے سے )'],
 ('tirmidhi:2434','hi'):['(उम्मत-ए-मुहम्मदी)','(दाख़िल होने में)'],
 ('tirmidhi:2434','ur'):['( امت محمد )','( داخل ہونے میں )'],
 ('ibnmajah:2449','hi'):['(नक़द)'],
 ('ibnmajah:2449','ur'):['( نقد )'],
}
REASONS={
 ('tirmidhi:2382','ur'):"Read all 4,533 characters. Preserve the full Shufayya/Abu Hurayrah setting, repeated fainting, three judgment dialogues and final knee gesture in its own report family. The source-supplied Quran-learning parenthesis supplies the actual object of the reported intention and remains as a source-rendered qualification; this does not assert that its brackets are literal historical speech. After the compiler introduction, Walid/Abu Uthman/Ukbah report Shufayya notifying Muawiyah; Alaa describes Muawiyah's response, crying, recovery and Quran recitation. Preserve those distinct actual voices in their separate reception family. The explicit Hud locator and final compiler grading remain context; actual Arabic recitation and Urdu rendering remain selected. This v2 scope refinement replaces the initial explanatory-gloss treatment, preserved verbatim in the v1 archive.",
 ('tirmidhi:2434','hi'):"Read all 5,410 characters of the meat setting and intercession narrative. The nested speakers and final first-person Messenger account remain within the supplied report, without inferred canonical occurrences. Preserve the source's repeated supplication, source-qualified beneficiary group and entry action, explicit return-to-Messenger attribution, and defective gate-leaf/geographic wording. The friend definition, Abu Hayyan pointer to an unprinted three-falsehood list and final compiler material remain context. V2 restores the two beneficiary/entry qualifications after independent complete reading; the initial gloss treatment remains in the immutable v1 evidence.",
 ('tirmidhi:2434','ur'):"Read all 5,061 Urdu characters independently. Preserve every supplied intercession dialogue, request/refusal, repeated community supplication, gate-distance alternatives and explicit return-to-Messenger attribution. The source-qualified beneficiary group and entry action are actual narrative scope and remain. The Khalil definition, Abu Hayyan pointer to an unprinted list, final footnote and compiler tail remain context. Preserve the distinct Urdu Basra spelling and all source honorifics without normalization. V2 restores only the two independently identified scope qualifications; the initial gloss treatment is retained as history.",
 ('ibnmajah:2449','hi'):"Rafi reports the prohibitions and three categories who may cultivate: own land, given land, and paid lease. Retain the printed gift-or-loan alternatives and cash-payment qualification as source-supplied transaction scope, without choosing or canonically resolving either grant mode. V2 restores the exact cash-payment qualification after independent reading; the former lexical-gloss interpretation remains archived rather than silently rewritten.",
 ('ibnmajah:2449','ur'):"Read all Urdu prohibitions and three cultivating categories. Retain the printed gift-or-loan alternatives and cash-payment qualification as source-supplied transaction scope, without choosing a grant mode or filling external wording. V2 restores the exact cash-payment qualification after independent reading; the initial lexical-gloss interpretation remains verbatim in the v1 history.",
}

def main():
 assert not OUT.exists() and not (ROOT/'delivery-manifest-v2.json').exists()
 mbytes=(ROOT/'delivery-manifest-v1.json').read_bytes();assert sha(mbytes)=='8d66fd9f9373f513cf06d31c42ff8128e5c55f38e8f228da9f61bba0b8806a64'
 manifest=json.loads(mbytes)
 for f in manifest['files']:
  b=(BEFORE/f['path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256']
  dest=OUT/REVISION/'before-v1/payload'/f['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 (OUT/REVISION/'before-v1/delivery-manifest-v1.json').write_bytes(mbytes)
 for name,expected in [('independent-boundary-findings-v1.json','9b52c350b7eda0e5bee536f5f50d66db5a1bebe0de5d6a0398d5f661eda12420'),('accepted-reviewed-field-plan.json','a1833a7fd1190de7f65b98560dc3d26f2dfcb3b5bd00e7ad0158b2254b9a5184')]:
  b=(AUDIT/name).read_bytes();assert sha(b)==expected;(OUT/REVISION/name).write_bytes(b)
 records=copy.deepcopy(manual_boundaries.records);changes=[]
 for row in records:
  for lang,field in row['fields'].items():
   key=(row['key'],lang)
   if key not in RESTORE:continue
   old=copy.deepcopy(field);cuts=field.get('omit_source_context',[])
   assert all(sum(c['text']==text for c in cuts)==1 for text in RESTORE[key])
   field['omit_source_context']=[c for c in cuts if c['text'] not in RESTORE[key]]
   field['reason']=REASONS[key]
   assert {k:v for k,v in field.items() if k not in ('omit_source_context','reason')}=={k:v for k,v in old.items() if k not in ('omit_source_context','reason')}
   changes.append({'id':'deenhindi-'+row['key'],'language':lang,'restored_literals':RESTORE[key],'initial_reason':old['reason'],'current_reason':field['reason']})
 assert len(changes)==5
 (ROOT/'manual_boundaries_v2.py').write_text('"""Versioned seven-scope restoration rules; original readings are retained."""\nrecords = '+pprint.pformat(records,width=110,sort_dicts=False)+'\n',encoding='utf-8')
 script=(ROOT/'compile_review.py').read_text()
 script=script.replace('from manual_boundaries import records as instructions','from manual_boundaries_v2 import records as instructions').replace("OUT=ROOT/'publish-v1'","OUT=ROOT/'publish-v2'").replace("delivery-manifest-v1.json","delivery-manifest-v2.json")
 script=script.replace("for n in ('source_first_notes.py','manual_boundaries.py','compile_review.py'):put(PREFIX+'/'+n,(ROOT/n).read_bytes())", "for target,source in (('source_first_notes.py','source_first_notes.py'),('manual_boundaries.py','manual_boundaries_v2.py'),('compile_review.py','compile_review_v2.py')):put(PREFIX+'/'+target,(ROOT/source).read_bytes())")
 script=script.replace('Initial primary20register/3source-only','Version2 primary20register/3source-only after seven independently assessed source-scope restorations')
 (ROOT/'compile_review_v2.py').write_text(script)
 (ROOT/'amendment-input-v2.json').write_bytes(enc({'source_checkpoint':'bd4a75695d3c695e98bf8efa5ce07764ac5e2633','changes':changes,'prior_manifest_sha256':sha(mbytes),'exact_restored_spans':7,'restored_characters':96,'restored_utf8_bytes':192,'unchanged_parent_dispositions':True,'changed_field_reasons_are_explicit_reconsiderations':True,'original_source_first_notes_unchanged':True}))
 print(json.dumps({'prepared_fields':len(changes),'restored_spans':7,'archived_v1_files':len(manifest['files'])}))

if __name__=='__main__':main()

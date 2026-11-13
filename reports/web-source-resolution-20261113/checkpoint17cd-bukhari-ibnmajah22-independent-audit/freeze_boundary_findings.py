"""Freeze the actual independent44-field candidate inspection; no primary edits."""
import copy,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PRIMARY=ROOT.parent/'phase22-checkpoint17cd-bukhari-ibnmajah22-review'
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
mp=PRIMARY/'delivery-manifest-v1.json'
assert sha(mp.read_bytes())=='95967f1f4950735e7b1b03188911367c39dfaf8b1eb590af23148fb470581ff3'
man=json.loads(mp.read_bytes())
ap='imports/web-deenhindi-20261112/reviews/source-review-checkpoint17cd-bukhari-ibnmajah22-20261113.json.gz'
ae=next(x for x in man['files'] if x['path']==ap)
ab=Path(ae['local_path']).read_bytes();assert sha(ab)==ae['sha256']
ledger=json.loads(gzip.decompress(ab));byid={x['id']:x for x in ledger['records']}
orig=[json.loads(x) for x in (ROOT/'input/full-hi-ur-reading-input-44.jsonl').read_text().splitlines()]
assert sha((ROOT/'complete-independent-source-first-readings.json').read_bytes())=='77f1c3afb7025d99cccba3f4dfd766dc1be3513bef6e42504000273203485917'
RESTORES={
 ('bukhari:2647','hi'):(222,230,'(घर में)'),('bukhari:2647','ur'):(195,206,'( گھر میں )'),
 ('bukhari:2681','hi'):(370,405,'(मुहम्मद (सल्लल्लाहु अलैहि वसल्लम))'),('bukhari:2681','ur'):(320,347,'( محمد صلی اللہ علیہ وسلم )'),
 ('bukhari:2698','hi'):(263,274,'(क़ुरैश से)'),('bukhari:2698','ur'):(229,240,'( قریش سے )'),
}
SPEAKERS={
 ('bukhari:2693','hi'):'Sahl reports the Quba dispute and the proposal attributed locally to आप (सल्लल्लाहु अलैहि वसल्लम); this field supplies that honorific pronoun rather than an explicit personal name.',
 ('bukhari:2693','ur'):'Sahl reports the Quba dispute and the proposal attributed locally to آپ صلی اللہ علیہ وسلم; this field supplies that honorific pronoun rather than an explicit personal name.',
}
ASSESSMENTS={
 'bukhari:2633':'Both full camel/charity/gift/milking dialogues and the final conditional remain. The zakat word is a lexical apposition and the earlier route is context; no actual reply or condition is lost.',
 'bukhari:2641':'Both fields preserve the coherent final Abdullah ibn Utba hearing frame and Umar\u2019s full own public statement, including all outward/inner and good/bad distinctions. This is not direct Prophet speech.',
 'bukhari:2642':'Both finite funeral episodes and the final testimony predicate are retained. The removed block expressly discusses equivalent wording/transmitter formula doubt, rather than doubt about whether the episode occurred. No absent Paradise/Hell object is filled.',
 'bukhari:2647':'Request the house-location restoration in each field: at-my-place does not explicitly supply the house destination of the arrival. Accept the duplicate anticipatory milk-brother apposition as context because Aisha\u2019s actual spoken relationship claim remains, along with both route contexts.',
 'bukhari:2648':'The Urwah episode and Aisha\u2019s later own report are separately attributed in the same source family. No woman\u2019s name or retroactive Aisha source link is invented.',
 'bukhari:2659':'Both coherent Uqbah reports retain the marriage-domain and remaining-marriage predicates, repeated approaches and supplied reason. Equivalent transmission formulas stay context, and the earlier departure is not silently asserted to be a completed divorce.',
 'bukhari:2675':'Both field-specific market reports, actual supplied verse/translation and later Companion assessment remain under their own voices. The Hindi duplicated price assertion, missing contrary-price predicate and printed spelling defects are preserved, without importing Urdu\u2019s contrary statement.',
 'bukhari:2681':'Request the Muhammad subject designation in each field: the rest of the local field supplies only the pronoun for the person whose commands are being described. Keep the whole speech as Heraclius\u2019s retrospective report/assessment, not direct Prophet speech.',
 'bukhari:2683':'The post-death arrival/announcement and Jabir\u2019s actual promise claim/payment are separate components in one family. All three five-hundred payments and both announcement alternatives remain; the biographical Bahrain-agent title can stay context.',
 'bukhari:2685':'Ibn Abbas\u2019s own admonition, oath, negative questions and through-your-Prophet mediation remain. Short lexical/group appositions are context. The malformed Urdu opening parenthesis is narrowly bounded so the actual question predicate is not swallowed.',
 'bukhari:2693':'All source positions are supported. Request only speaker-description qualification: each field designates the proposer by an honorific pronoun, without an explicit personal name. Preserve the report type, component and family, and do not add or change any source word.',
 'bukhari:2694':'The main numbered Aisha interpretation is an actually attributed Companion saying. Its supplied verse/rendering is the subject of interpretation, not an invented recitation event. The attribution-predicate and maintenance-domain parentheses are correctly retained.',
 'bukhari:2698':'Request restoration of the stated Quraysh counterparty in both fields; the later broader mushrikin label does not repeat that specific participant group. Next-year/three-day conditions and full negotiation remain. The final pupils\u2019 technical-term dialogue is lexical teaching apparatus and correctly stays context.',
 'bukhari:2700':'Accept all actual three conditions, their stated count, asymmetric obligations and the conversion/captivity and agreement-compliance qualifiers. Refinement of my initial notes: the parenthetic1/2/3 display labels can remain context because the explicit three-count, every condition and their order remain selected. This does not permit trimming an actual quantity or scope qualifier.',
 'ibnmajah:2612':'Both the delegation episode and later repeatedly reported Ashath saying remain, with the latter in its own family and own Companion voice. Unlike an explicitly introduced compiler legal explanation, this is the supplied participant\u2019s own narrated habitual conditional statement. No punishment is asserted to have occurred.',
 'ibnmajah:2622':'All actual story/dialogue scope is preserved, including finite rhetorical complements, moral qualifications, sinful-town circumstance, Urdu-only mercy consequence and adjudication/measurement/movement clauses. Later Abu Rafi and Hasan continuations retain qualified actual transmitters and no invented ultimate/eyewitness link. Only the multistep middle route and two Urdu footnote markers are context.',
 'ibnmajah:2633':'Both complete responsibility predicates remain. The different own-language aqilah definitions are lexical context, including Urdu\u2019s additional killer wording, with no harmonization.',
 'ibnmajah:2636':'The not-at-the-joint injury condition, request, blessing and explicit non-qisas conclusion remain. Urdu\u2019s blood-money synonym alone is lexical context.',
 'ibnmajah:2640':'The consultation, Mughirah\u2019s actual witness statement and Umar\u2019s witness demand/supporting testimony are distinct qualified components of one family. Both slave alternatives remain; only the Urdu footnote marker is context.',
 'ibnmajah:2641':'Ibn Abbas\u2019s consultation account and Haml\u2019s own two-wife testimony/decisions stay distinct. Both deaths and the slave-or-maid alternatives remain. Repeated janin definitions and the Urdu footnote glyph are context.',
 'ibnmajah:2647':'Both source statements preserve wajib, the inheritance-residue limit, the if-killed condition and actual final agencies. The asabah definition alone is lexical context; no current-law conclusion is asserted.',
 'ibnmajah:2648':'Both printed victim/killer party labels and finite inheritance claim/reply remain. The damaged Hindi actor bridge is explicitly qualified, with no Urdu restoration. The paternal-relatives definition is context; the source dialogue/wording is otherwise exact.',
}
findings=[];inspection=[];plan=[]
semantic=lambda s:{k:v for k,v in s.items() if k not in ('start','end','sha256','reason')}
for row in orig:
 oid=row['occurrence_id']; short=oid.removeprefix('deenhindi-');lang=row['language'];key=(short,lang);t=row['text']
 f=next(x for x in byid[oid]['field_reviews'] if x['language']==lang)
 assert f['reviewed'] and sha(t.encode())==f['text_sha256']
 spans=copy.deepcopy(f['spans']);oldmask=set()
 for s in spans:
  assert sha(t[s['start']:s['end']].encode())==s['sha256'];oldmask.update(range(s['start'],s['end']))
 if key in RESTORES:
  a,b,literal=RESTORES[key];assert t[a:b]==literal and not oldmask.intersection(range(a,b))
  before=next(s for s in spans if s['end']==a);after=next(s for s in spans if s['start']==b)
  assert semantic(before)==semantic(after)
  before['end']=after['end'];before['sha256']=sha(t[before['start']:before['end']].encode());spans.remove(after)
  findings.append({'occurrence_id':oid,'language':lang,'kind':'restore_actual_source_scope','start':a,'end':b,'text':literal,'sha256':sha(literal.encode()),'source_text_sha256':row['text_sha256'],'rationale':ASSESSMENTS[short],'preserve_component_metadata':semantic(before),'expected_added_characters':b-a,'expected_added_utf8_bytes':len(literal.encode())})
 if key in SPEAKERS:
  old={s['speaker'] for s in spans};assert len(old)==1
  for s in spans:s['speaker']=SPEAKERS[key]
  findings.append({'occurrence_id':oid,'language':lang,'kind':'honorific_pronoun_description_qualification_only','source_text_sha256':row['text_sha256'],'old_speaker':old.pop(),'new_speaker':SPEAKERS[key],'rationale':ASSESSMENTS[short],'source_mask_change':False,'report_type_component_family_change':False})
 newmask={p for s in spans for p in range(s['start'],s['end'])}
 assert not oldmask-newmask
 plan.append({'occurrence_id':oid,'language':lang,'source_text_sha256':row['text_sha256'],'before_field_definition_sha256':sha(canon(f)),'expected_spans':[{k:v for k,v in s.items() if k!='reason'} for s in spans],'expected_added_positions':sorted(newmask-oldmask),'expected_removed_positions':[],'required_note_refinement':key in RESTORES or key in SPEAKERS})
 inspection.append({'occurrence_id':oid,'language':lang,'source_text_sha256':row['text_sha256'],'complete_field_read':True,'complete_candidate_boundaries_and_voices_compared':True,'result':'narrow_amendment_requested' if key in RESTORES or key in SPEAKERS else 'accepted','rationale':ASSESSMENTS[short],'selected_before':[{**{k:v for k,v in s.items() if k!='reason'},'text':t[s['start']:s['end']]} for s in f['spans']]})
assert len(inspection)==44 and len(findings)==8
payload={'schema_version':1,'status':'complete_independent_candidate_inspection_with_bounded_amendments','primary_manifest':{'path':str(mp),'sha256':sha(mp.read_bytes())},'active_path':ap,'active_sha256':sha(ab),'own_source_first_receipt_sha256':'77f1c3afb7025d99cccba3f4dfd766dc1be3513bef6e42504000273203485917','own_source_proof_sha256':'d8264c6714aaf0388170830562a3f88d248b86e006341921b169e472a9c72292','coverage':{'complete_fields':44,'characters':30058,'utf8_bytes':65003,'parents':22,'parent_disposition_changes':0},'requested_changes':findings,'all_complete_field_inspections':inspection,'refinement_to_immutable_initial_notes':{'bukhari2700':'The three parenthetic enumeration labels can remain visible context as display apparatus; its actual count of three, complete conditions, narrative scope qualifiers and ordering remain selected. No other initial scope judgment is silently changed.'},'change_limits':{'restored_ranges':6,'restored_characters':sum(b-a for a,b,t in RESTORES.values()),'restored_utf8_bytes':sum(len(t.encode()) for a,b,t in RESTORES.values()),'removed_positions':0,'metadata_only_fields':2,'changed_fields_total':8,'other_reviewed_fields_exact':36,'unread_fields_exact':66,'other_whole_parents_exact':18,'existing_component_type_family_identities_preserved':True},'instructions':'Preserve all v1 payloads and initial readings; transparently refine changed reasons/speakers and regenerate dependent inventories and receipts. No source words, metadata, references, source snapshots or other fields may change.'}
for name,obj in [('independent-boundary-findings-v1.json',payload),('accepted-reviewed-field-plan-v1.json',{'schema_version':1,'primary_manifest_sha256':sha(mp.read_bytes()),'active_sha256':sha(ab),'fields':plan})]:
 p=ROOT/name;assert not p.exists();p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');print(name,sha(p.read_bytes()),p.stat().st_size)
print(json.dumps(payload['change_limits'],ensure_ascii=False))

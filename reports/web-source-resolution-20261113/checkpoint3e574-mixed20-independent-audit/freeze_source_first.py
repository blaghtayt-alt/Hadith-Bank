"""Freeze root's complete independent40-field pass before any primary candidate."""
from pathlib import Path
import datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
INPUT=WORK/'phase19-checkpoint3e574-input-partitions/deployment-abudawud4-tirmidhi11-bukhari2-ibnmajah3'
EVID=WORK/'phase18-successor-acquisition-monitor/held-evidence'
PIN='3e574b9e7e4dd7cf8bc23232249004a18692c61c'
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
NOTES={
 'abudawud:2492':'Keep the actual sleep/waking scene, the source-named Umm Haram/Rumaysa washing her own head, her question about laughing at her hair and the supplied negative answer. Hindi lacks an intact transition into the abridgement note; retain the actual no reply and leave the more-or-less/same-hadith pointer in context. Urdu likewise has a complete scene and then an omitted-body pointer. The appended compiler\'s milk-sister biography and Urdu footnote markers are context. Do not replace the source name or reconstruct a familiar sea-expedition continuation.',
 'abudawud:2521':'The unnamed uncle of Hasna bint Muawiya asks who is in Paradise. Keep every category actually supplied in each field and the parenthetic underage qualification of children, which materially limits scope. Urdu additionally names martyrs, which Hindi omits: do not insert that category into Hindi or identify the uncle from memory.',
 'abudawud:2527':'Keep Yala\'s age/lack of a servant, recruitment for service and a share, the worker\'s uncertainty about shares, fixed-pay request whether or not there is a share, all three-dinar statements, later spoils/doubt and the actual supplied consultation/reply. Preserve the reply\'s restriction to this person and this expedition and its world/hereafter scope; do not generalize it into a present-day wage rule.',
 'abudawud:2535':'Retain the actual Ibn Zagh/Abdullah ibn Hawala encounter frame and the reported walking expedition, empty-handed return, observed distress and three-part supplication. Preserve the additive also parenthesis, all inability/preference reasons, hand-on-head-or-nape uncertainty, the source\'s Syria/caliphate condition, and the exact hand/head proximity comparison. The parenthetic time-of-appearance clause makes the listed events\' nearness temporal and remains material scope. Do not choose the bodily-location alternative or map the condition to a modern political event.',
 'tirmidhi:2464':'Abd al-Rahman ibn Awf makes his own retrospective contrast: patience under hardship with the Prophet and inability to endure prosperity afterward. Keep both temporal contexts and the negation in his voice; do not relabel it as the Prophet\'s words. Urdu compiler grade and pointer remain context.',
 'tirmidhi:2469':'Keep Aisha\'s actual description of the leather pillow, resting on it and date-bark filling. The bed/bedding parenthesis is an object gloss, not an explicit OR alternative, and remains lexical context. Do not silently replace the printed pillow with another object from a parallel. Urdu grade and pointer are apparatus.',
 'tirmidhi:2471':'Keep Aisha\'s own household observation, the one-month-at-a-time unlit hearth and the dates-and-water-only sustenance. Retain the family identity and temporal/only qualifiers without turning them into an unlimited universal claim. The Urdu appended compiler grade is context.',
 'tirmidhi:2473':'Retain Ali\'s complete cold-day account: worn/stinking skin garment, cutting/tying, hunger, the conditional statement about food at the Prophet\'s house, search, the source-described Jewish gardener, wall opening, address, one-date-per-bucket agreement, entering and work, handful stopping point, eating, two-or-three sips and return to the mosque where he found the Prophet. Do not add a subsequent conversation, food-sharing act or identify the unnamed employer. The conditional food statement and imprecise sip count remain. Urdu grade/pointer are context.',
 'tirmidhi:2474':'Keep the actual one-occasion hunger and the Prophet giving each companion only one date. Both per-person quantity and only qualification remain; the Urdu appended grade is context.',
 'tirmidhi:2475':'Keep Jabir\'s300-person expedition, carrying provisions, exhaustion, one-date shares, the unnamed interlocutor\'s question, appreciation after even that ended, seaside fish and18 days of eating to satiety. Do not name the fish or supply an explicit answer introducer absent at the source join. The Urdu compiler grade, extra-route note and more-complete-Malik pointer are context rather than additional body.',
 'tirmidhi:2479':'Keep Abu Musa\'s address to his son and his conditional recollection of the rainy occasion with the Prophet and sheep-like smell. Hindi\'s English sheep parenthesis only glosses the existing animal word. The compiler\'s appended authenticity statement and wool-clothing explanation are context in both fields; do not admit the explanation as a new report or assign the speech to the Prophet.',
 'tirmidhi:2480':'The complete source supplies Abu Hamza\'s actual dialogue with Ibrahim al-Nakhai: the building statement, question about a necessary house and the neither-reward-nor-sin answer. This is a standalone substantive successor statement/dialogue, not a lexical definition or an appended compiler explanation of another report. Retain its own voice and all necessity/negation qualifications, without upgrading it to a Prophetic saying.',
 'tirmidhi:2485':'Keep Abdullah ibn Salam\'s actual Medina-arrival observation, the three repeated arrival calls, his stated purpose and personal face assessment, then the supplied first-speech claim and every instruction/promise. Retain the night/others-sleeping condition and distinguish the witness\'s assessment from the Prophet\'s actual quoted words. Urdu pointer and compiler grade are context.',
 'tirmidhi:2502':'Retain Aisha\'s mimicking episode, the first refusal-even-for-money reply, her Safiyya remark, the actual hand gesture and final conditional sea-water comparison. Hindi\'s other-wife parenthesis materially supplies the stated relationship, and its whole hand-gesture parenthesis reports an actual finite action: retain both as source rendering. Urdu actually states the gesture and qualifies the inferred short-stature intention; preserve that inference marker rather than inventing literal spoken wording. Do not expand Safiyya\'s identity beyond the supplied relationship/name. Urdu footnote marker is context.',
 'tirmidhi:2516':'Keep Ibn Abbas riding behind on the stated day, the boy address, the commands and all request/help conditions, the paired collective-benefit/harm limits and the lifted-pens/dried-pages ending. The parenthetic of-destiny phrase specifies the domain of the pages and remains a source-rendered qualification. Do not drop either negation or one of the parallel cases. Compiler grade and Urdu pointer are context.',
 'bukhari:2535':'The opening transmission chain is source context. Retain the actual attributed prohibition of both selling and gifting wala, without defining the technical term externally or inventing further legal conditions. Keep Ibn Umar\'s reported voice distinct from the preceding transmitters.',
 'bukhari:2536':'Retain the actual first-person purchase of Barira, the owners\' retained-wala condition, consultation/reply, freeing, later choice concerning her husband, her conditional refusal even for unspecified gifts and separation. Both parenthetic after-freedom/in-their-favor clauses are material contractual and temporal scope and must remain. Hindi has a damaged/abbreviated chain, prints the female narrator\'s name as ऐसा, and loses the explicit wala/link at the reply join; preserve and annotate those defects without inserting Urdu\'s missing chain or words. Urdu explicitly names Aisha and supplies its own full reply. The actual chain portions are context, and the different embedded speakers are not flattened into one Prophetic quotation.',
 'ibnmajah:2499':'Keep the undivided-property condition and the joint boundary-marking/separate-roads termination condition exactly. Do not substitute the different conditions of another occurrence. Urdu terminal pointer is context.',
 'ibnmajah:2513':'Keep the unnamed person\'s mudabbar act, no-other-property condition, the Prophet\'s actual sale and the source-named purchaser. Hindi omits Urdu\'s Banu Adi phrase and has a damaged final join/name spelling; do not fill or silently repair it. No unnamed owner identity or extra emancipation conditions are supplied.',
 'ibnmajah:2523':'Keep Abu Dharr\'s actual question about the best person to free and both conjunctive criteria in the reply: most liked by the owners and highest in price. Do not turn the AND into a choice or add a modern transaction instruction. Urdu pointer is context.'
}
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,p
 else:p.write_bytes(b)
cb=(INPUT/'cohort.jsonl').read_bytes();assert sha(cb)=='0dca769d84f5e54031d1e6245dae9376a488de9ca30dc83a09bcf800f2c1f342'
ib=(INPUT/'full-hi-ur-reading-input-40.jsonl').read_bytes();assert sha(ib)=='d6d8fa72362675713ca2e762ac71af2fef987ab61f4c4e5d6fbcc416c0793368'
sources={r['collection']+':'+r['number']:r for r in map(json.loads,cb.splitlines())};assert len(sources)==20 and sources.keys()==NOTES.keys()
entries=json.loads((EVID/'held-state-entries.json').read_bytes());manifest=json.loads((EVID/'evidence-manifest.json').read_bytes());assert manifest['saved_head']==PIN
proof=[]
for key,r in sources.items():
 files=[]
 for kind,d in [('raw',r['snapshot']),('parsed',entries[key]['parsed'])]:
  b=(EVID/'sources'/d['path']).read_bytes();a=manifest['files'][d['path']]
  g=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert sha(b)==a.get('stored_sha256',a['sha256']) and g==a['git_blob_sha1']
  plain=importer.checked_bytes(EVID/'sources',d)
  if kind=='raw':
   obj,ref=importer.parse_record(plain,r['collection'],r['number']);assert obj==r['source_record'] and ref==r['source_reference_verbatim']
  else:
   expected={k:r[k] for k in ['schema','collection','number','snapshot','source_reference_verbatim','source_record']};expected['classification']=r['intake_classification']
   assert json.loads(plain)==expected and plain==importer.json_bytes(expected)
  files.append({'kind':kind,'path':d['path'],'stored_bytes':len(b),'stored_sha256':sha(b),'git_blob_sha1':g,'plain_sha256':sha(plain)})
 proof.append({'id':'deenhindi-'+key,'files':files,'full_raw_reparse_exact':True})
fields=[]
for f in map(json.loads,ib.splitlines()):
 key=f['collection']+':'+f['number'];text=f['text'];assert text==sources[key]['source_record'][f['source_field']] and sha(text.encode())==f['text_sha256']
 fields.append({'id':f['occurrence_id'],'language':f['language'],'source_field':f['source_field'],'text':text,'sha256':sha(text.encode()),'characters':len(text),'utf8_bytes':len(text.encode()),'complete_field_read':True,'independent_reading_note':NOTES[key]})
assert len(fields)==40 and sum(f['characters'] for f in fields)==17859 and sum(f['utf8_bytes'] for f in fields)==38456
receipt={'schema':'hadith-bank-complete-independent-source-first-reading-v1','reviewer':'/root','source_commit':PIN,'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_or_primary_notes_inspected':False,'all_fields_read_in_full_before_candidate_access':True,'input_sha256':sha(ib),'complete_fields':40,'characters':17859,'utf8_bytes':38456,'source_only_proposed_ids':[],'proposed_finite_report_occurrences':20,'fields':fields,'coverage_note':'All40 complete original Hindi/Urdu fields were actually read before any candidate or primary notes. Each occurrence has finite supplied content in these fields, including actual successor dialogue under its own voice. No other sibling-language reading is claimed.','independent_pro_qc':'not_performed'}
target=ROOT/'complete-independent-source-first-readings.json';assert not target.exists();put(target,enc(receipt))
put(ROOT/'independent-source-verification.json',enc({'status':'PASS','source_commit':PIN,'records':proof,'source_files_verified':40,'full_raw_reparses_exact':20,'new_semantic_approvals_from_hashing':0}))
put(ROOT/'input/full-hi-ur-reading-input-40.jsonl',ib)
print(json.dumps({'source_first_sha256':sha(target.read_bytes()),'source_verification_sha256':sha((ROOT/'independent-source-verification.json').read_bytes()),'complete_fields':40,'characters':17859,'utf8_bytes':38456,'candidate_inspected':False},indent=2))

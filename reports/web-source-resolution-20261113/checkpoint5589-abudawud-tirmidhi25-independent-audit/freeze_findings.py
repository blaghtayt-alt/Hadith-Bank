"""Bind the independent original-field decisions to exact V1 masks and requested corrections."""
from pathlib import Path
import copy,gzip,hashlib,json
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
own=ROOT/'complete-independent-source-first-readings.json';assert sha(own.read_bytes())=='9c43db15281646afead594e6e9e313ec32f5c0ce9521134c660968ee3c898af4'
mp=WORK/'phase16-checkpoint5589-abudawud-tirmidhi25-review/delivery-manifest-v1.json';assert sha(mp.read_bytes())=='4e82a1b13b65c21c8d31034e79439e11b1353aea1ca27d6510513aa2308668ec'
m=json.loads(mp.read_bytes());f=next(f for f in m['files'] if '/reviews/source-review-' in f['path']);p=Path(f.get('local_path',f.get('source_path')));assert sha(p.read_bytes())=='b2f5305335c2a896ea850a2ef79b7f6b878a6f6f72e5301972c256cd1d8296af'
v1=json.loads(gzip.decompress(p.read_bytes()));read=json.loads(own.read_bytes());original={(f['occurrence_id'],f['language']):f for f in read['fields']}
all_sources={'deenhindi-'+s['collection']+':'+s['number']:s for s in map(json.loads,(WORK/'phase15-successor-acquisition-monitor/next-review-cohort/held-source-records.jsonl').read_bytes().splitlines())}
FIELDS={'ar':'textArabic','en':'translationEnglish','hi':'translationHindi','ur':'translationUrdu','ur-Latn':'translationUrduRoman'}
plan=[];findings=[]
for r in v1['records']:
    parent={'id':r['id'],'decision':'exclude' if r['id'] in ['deenhindi-abudawud:2330','deenhindi-abudawud:2331'] else r['decision'],'fields':[]}
    explicit={f['language']:f for f in r['field_reviews']}
    for lang,field_name in FIELDS.items():
        present=lang in explicit
        f=explicit.get(lang,{'language':lang,'source_field':field_name,'text_sha256':sha(all_sources[r['id']]['source_record'][field_name].encode()),'reviewed':False,'spans':[]})
        item={'language':f['language'],'source_field':f['source_field'],'source_text_sha256':f['text_sha256'],
              'reviewed':f['reviewed'],'accepted_positions':[[s['start'],s['end']] for s in f['spans']],
              'v1_field_sha256':sha(enc(f)) if present else None,'v1_field_decision_explicit':present,'allowed_semantic_change':False}
        if r['id'] in ['deenhindi-abudawud:2330','deenhindi-abudawud:2331']:
            assert (r['id'],f['language']) in original
            item.update(reviewed=True,accepted_positions=[],allowed_semantic_change=True,
                reason='All five fields independently read: chain-framed lexical definition of sirrahu only, not a substantive numbered report. Preserve as source context.')
        elif r['id']=='deenhindi-abudawud:2306' and f['language'] in ['hi','ur']:
            cutoff=1395 if f['language']=='hi' else 1260
            item['accepted_positions']=[[s['start'],min(s['end'],cutoff)] for s in f['spans'] if s['start']<cutoff]
            item.update(allowed_semantic_change=True,reason='Appended Ibn Shihab juristic exposition is legal commentary about the preceding narrative. Keep the entire actual Subayah report before it, with existing biography/lexical gaps unchanged.')
            t=original[r['id'],f['language']]['text'];findings.append({'id':r['id'],'language':f['language'],'action':'move_appended_legal_exposition_to_context','start':cutoff,'end':len(t),'text':t[cutoff:]})
        elif r['id']=='deenhindi-tirmidhi:2363' and f['language'] in ['hi','ur']:
            a,b=(82,90) if f['language']=='hi' else (66,76)
            item['accepted_positions']=[[0,180 if f['language']=='hi' else 173]]
            item.update(allowed_semantic_change=True,reason='Retain the printed or-table alternative as source-qualified object scope; do not choose an object by assuming it is merely a glossary synonym.')
            t=original[r['id'],f['language']]['text'];findings.append({'id':r['id'],'language':f['language'],'action':'restore_supplied_object_alternative','start':a,'end':b,'text':t[a:b]})
        parent['fields'].append(item)
    plan.append(parent)
assert sum(f['allowed_semantic_change'] for r in plan for f in r['fields'])==14
report={'status':'REQUIRES_NARROW_V2','source_commit':'5589a3ffc3b43c3324ae26f2b6c4d33152834456','own_source_first_sha256':sha(own.read_bytes()),'candidate_v1_manifest_sha256':sha(mp.read_bytes()),'candidate_v1_active_sha256':sha(p.read_bytes()),'complete_independent_fields_read':59,'actual_characters':25470,'actual_utf8_bytes':52806,
    'source_only_reclassifications':[{'id':identity,'all_five_fields_read':True,'reason':'Every supplied language contains a word definition and transmission/lexical discussion. AGENTS excludes explanatory material even when it has a provider number.'} for identity in ['deenhindi-abudawud:2330','deenhindi-abudawud:2331']],
    'exact_span_findings':findings,'expected_final_counts':{'register':22,'source_only':3,'read_fields':59,'admitted_fields':44,'read_context_fields':15,'unread_context_fields':66},
    'unchanged_whole_parents_expected':21,'unchanged_field_slots_expected':111,'unchanged_existing_explicit_field_decisions_expected':45,
    'transparent_refinement_of_initial_notes':[{'id':'deenhindi-abudawud:2310','language':'ur','initial_concern':'The parenthetic greatest-sin-is-that formula repeats the preceding question.','final_judgment':'Retain it: it is a finite ranking predicate within the supplied answer, not a lexical definition. This refinement follows rereading of the complete source in its answer context, not an automatic keep-all-parentheses rule.'}],
    'other_boundary_voice_decisions':'All other50 Hindi/Urdu boundaries and the all-five Tirmidhi2296 source-only case were compared with the full original fields. Preserve the actual finite dialogue/practice/recollection, their conditions and speaker qualifiers, source corruption and all existing compiler/gloss cuts. No other change is requested.',
    'independent_pro_qc':'not_performed'}
for n,d in [('independent-boundary-findings-v1.json',report),('accepted-final-field-plan.json',{'source_commit':report['source_commit'],'rows':plan})]:
    target=ROOT/n;assert not target.exists();target.write_bytes(enc(d));print(n,sha(target.read_bytes()))

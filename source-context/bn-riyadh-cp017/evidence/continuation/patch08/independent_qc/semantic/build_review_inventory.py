"""Serialize only passages actually read by the independent semantic reviewer.

Selection statements below are a record of completed manual reading, not an
algorithm that awards semantic review credit to all matching rows.
"""
from pathlib import Path
import json, collections, re
import qc_tools as q

GROUPS=[]
OBS={}
DISPLAYED={(r['source_volume'],r['pdf_page']) for r in q.rows(q.OUT/'actual_image_observations.jsonl')}

def add(group_id, branch, selected, note, context=None, pages=()):
    selected=list(selected)
    GROUPS.append({'group_id':group_id,'branch':branch,'selection_method':'documented purposive risk-based sample; not random or statistically representative',
                   'decision_ids':[r['decision_id'] for r in selected], 'row_count':len(selected),
                   'manual_observation':note,'source_context':context,
                   'pdf_pages_actually_displayed':[p for p in pages if (selected[0]['source_volume'],p) in DISPLAYED] if selected else [],
                   'manual_review_scope':'Every selected row text and assigned role read; contextual source and images only as stated.'})
    for r in selected:
        key=(branch,r['decision_id'])
        if key not in OBS:
            OBS[key]={'branch':branch,'author_file':f'patches/patch08/{branch}/semantic_decisions.jsonl',
                      'author_file_sha256':q.sha(q.PATCH/branch/'semantic_decisions.jsonl'),
                      'decision_id':r['decision_id'],'source_volume':r['source_volume'],'story':r['story'],
                      'cp_start':r['cp_start'],'cp_end':r['cp_end'],'text_verbatim':r['text_verbatim'],
                      'role_reviewed':r['after_role'],'manual_semantic_read':True,
                      'lexical_row':any(c.isalnum() for c in r['text_verbatim']),
                      'review_groups':[], 'manual_observations':[], 'verdict':'supported_in_reviewed_context'}
        OBS[key]['review_groups'].append(group_id);OBS[key]['manual_observations'].append(note)

def gap(i, branch, note):
    g=q.GAPS[i-1]
    rr=[r for r in q.DECISIONS[branch] if r['source_volume']==g['source_volume'] and r['story']==g['story'] and g['cp_start']<=r['cp_start']<g['cp_end']]
    add(f'inventory-gap-{i:04}',branch,rr,note,{'source_volume':g['source_volume'],'story':g['story'],'cp_start':g['cp_start'],'cp_end':g['cp_end'],'entire_inventory_gap_read':True},g.get('pdf_pages',[]))

add('all-uncertainty-qualifications','semantic_review',q.DECISIONS['semantic_review'],
    'All 28 additive qualification spans were read against their source-case context. Retention of an unprinted endpoint, unnamed speaker or contradictory bilingual attribution is appropriate; no conjectured repair is supplied.')
add('all-header-field-spans','header_story_review',q.DECISIONS['header_story_review'],
    'Word PAGE field instructions, cached results and controls are distinguished. Cached field results are not assertions of every rendered page number.')
add('all-tail-and-cover-spans','tail_review',q.DECISIONS['tail_review'],
    'Preface closing belongs to the author; cover title, volume/language labels, author/editor/translator credits, printed years and hyperlink-field object are source apparatus. A grading-editor credit does not verify a report grade.')

for i,n in {
1:'Preface invocation and heading lead into author prose; Quran quotations, translations, references and return to preface are separated.',
5:'Umar transmission frame, translated Prophetic intention/hijra teaching, Bengali parenthetic explanations and anchor remain distinct.',
9:'Tabuk narrative and speech are separated; Sahih Bukhari is a collection title. The following report locator and transmitter frame are not quotation.',
22:'Sad bequest questions and Prophetic responses alternate explicitly. Inline biography and Bengali explanatory parentheses remain outside the speech text roles.',
27:'Abu Bakra question is distinct from the Prophetic answer; the following congregational-prayer report introduces, but does not yet include, the nested angels utterance.'}.items():gap(i,'semantics_v1_early',n)
gap(71,'semantics_v1_early_b','Boy/monk story: outer Prophetic storytelling is distinct from the monk, healed courtier, king and boy dialogue. Speaker cues and intervening narrative do not flatten those inner voices.')
gap(302,'semantics_v1_early_c','Reports97–103 distinguish Divine speech, ordinary Prophetic teaching, Aisha question and practice narration, the100 parallel-report notice, hypothetical regret words and prescribed response; Bengali insertions remain separate.')
for i,n in {
422:'Chapter bridge and reports189–191: narrator frames, Prophetic teachings, Bengali explanatory phrases and Ubadah pledge account remain distinct.',
498:'Long Zubayr debt account: Abdullah narration and the successive statements/questions of Zubayr, Hakim, Abdullah ibn Jafar, Muawiya and purchasers are participant speech; not Prophetic quotations.',
977:'Parent-duty question and Prophetic answer are separated; Aisha jealousy account returns to narration before her comment and the Prophetic reply.',
613:'The numbered list belongs to the Prophetic quotation. The old continuation role is defective; corrected through the independently reviewed exact-offset replay.'}.items():gap(i,'semantics_v1_middle',n)
for i,n in {
1371:'Hakim conclusion is narrator prose, followed by collection reference and Bengali scene introduction.',
1545:'Aqra statement is participant speech; the kissing scene and the subsequent Prophetic cue remain narrative. The honorific does not change the voice.',
1558:'Prophetic instruction, embedded supplication transliteration, Bengali meaning, collection names, chain quality and Hakim-attributed grade are distinct source claims.',
1564:'Visit and crying are reported actions leading into a speech cue; this gap does not itself contain the following quotation.',
1577:'Narrative introduction has two printed Bengali explanatory insertions. The original broad role requires the qualified additive five-part correction.'}.items():gap(i,'semantics_v1_late_and_notes',n)
for i,n in {
2083:'Abu Burda/Ibn Umar question and father-to-Prophet transmission layers are preserved. Next report separates Abu Dawud reference from the source-claimed sound chain and chapter heading.',
2085:'Sad scene and three prostrations are reported actions; subsequent first-person explanation is Prophetic speech. Repeated Bengali paradise insertions are separated.',
2102:'Reports1186–1191 distinguish Prophetic instructions from Aisha narrated practice, Bengali explanatory phrases, collection references and claimed chain grades.'}.items():gap(i,'semantics_v2_gaps',n)

fn=q.DECISIONS['semantics_v1_late_and_notes']
add('footnote-discussion-and-grading-spans','semantics_v1_late_and_notes',
    [r for r in fn if r['story']=='footnote' and r['after_role'] not in ['source_bibliographic_references','footnote_marker_or_separator']],
    'Every one of the 49 nonbibliographic/nonseparator footnote additions was read, with 18 complete surrounding source-note contexts. Source-attributed grading, named scholarly criticism, wording/variant discussion and Quran reference are distinguished; note169 antecedent remains unresolved.',
    {'context_file':'sampled_footnote_contexts.json','complete_source_note_contexts_read':18},[149,232])
add('bibliographic-footnote-sample','semantics_v1_late_and_notes',
    [r for r in fn if r['story']=='footnote' and ((r['source_volume']==1 and 1138848<=r['cp_start']<1139300) or (r['source_volume']==2 and 991758<=r['cp_start']<992600))],
    'Collection names and numerals are bibliographic references, including Sahih in the Bukhari title; the explicit wording attribution is separately labeled. No cited collection is itself promoted to independent grade verification.')

refparents=[7197,7200,7245,7249,7254,7260,7277,7317,7472,7496,7517,7554,7559,7573,7594,8669]
for n in refparents:
    p=q.PARENT_DECISIONS[n-1]
    rr=[r for r in q.DECISIONS['reference_refinement'] if r['source_volume']==p['source_volume'] and r['story']==p['story'] and p['cp_start']<=r['cp_start']<p['cp_end']]
    note='Exact parent and complete replacement partition read. Collection, wording attribution, source-claimed grade, explanation, anchor or punctuation boundaries are semantically supported.'
    if n in [7554,7559,7573,7594]:note='The date-eating/fighting narrative is not a collection reference. The named or unnamed participant action and, where present, Umayr own speech are separated from the final Muslim attribution and anchor; PDF289–291 corroborates the actor and quotation layers.'
    add(f'reference-parent-{n:05}','reference_refinement',rr,note,{'parent_ledger_1_based_row':n,'source_volume':p['source_volume'],'story':p['story'],'cp_start':p['cp_start'],'cp_end':p['cp_end']},[289,290,291] if n in [7554,7559,7573,7594] else [])

for h,a,b,pg,note in [
    (802,973204,978423,[863,864,865,866,867],'Sahl recollection contains a fighter, two disputants, Prophetic reply and Abu Darda/Sahl exchange. The Arabic father/Bishr chain and Bengali explicit Qays return remain language-specific and uncertain.'),
    (854,1016296,1017934,[904,905],'Tufayl and Ibn Umar market dialogue is Companion/participant discourse; the dash aside about Tufayl is narration, not Prophetic speech.'),
    (888,1041462,1042143,[929],'The Jews hoped-for response is distinct from the actual Prophetic response. The Bengali source grade must be split from collection names; the parenthetic response circumstance also receives a qualified insertion split.'),
    (893,1044293,1044971,[931,932],'The questioner and the repeated Prophetic yes/no answers alternate correctly. Bengali Hasan is a source grade, not just part of a collection reference; corrected additively.'),
    (901,1049203,1051183,[937,938,939],'Outer Prophetic report introduces the Divine-servant dialogue; Divine speech and servant questions retain distinct inner voices. Inherited narrower speech spans were also checked in source context.')]:
    for br in ['semantics_broad_v1_root','semantics_broad_v1']:
        rr=[r for r in q.DECISIONS[br] if r['source_volume']==1 and r['story']=='main' and a<=r['cp_start']<b]
        if rr:add(f'numbered-report-{h}-{br}',br,rr,note,{'source_volume':1,'story':'main','cp_start':a,'cp_end':b},pg)
for n in [5352,5479,24360,24624,24702]:
    rr=[r for r in q.DECISIONS['semantics_broad_v1'] if f'parent-{n:05}-' in r['decision_id']]
    add(f'broad-parent-{n:05}','semantics_broad_v1',rr,
        'Complete selected parent context and all replacement rows read: preserve the narrator/participant/Prophetic distinction, source parenthetical explanations and references. In the greetings and sneezing accounts, quoted greeting/praise formulas are not flattened into a new narrator voice.',
        {'source_volume':1,'story':'main','cp_start':min(r['cp_start'] for r in rr),'cp_end':max(r['cp_end'] for r in rr)})

# These finite queues were fully adjudicated manually after automatic selection.
for filename,idkey in [('narration_closing_quote_adjudications.json','decision_id'),('parenthetical_narration_adjudications.json','decision_id'),('parenthetical_attribution_adjudications.json','decision_id')]:
    queue=json.loads((q.OUT/filename).read_text())
    for br in q.BRANCHES:
        ids={r[idkey] for r in queue if r['branch']==br}
        if ids:add(filename[:-5]+'-'+br,br,[r for r in q.DECISIONS[br] if r['decision_id'] in ids],
                   'Finite candidate-set follow-up; see the named adjudication file for the exact observation and any required correction. Queue filtering alone receives no manual credit.',{'adjudication_file':filename})
replay=q.rows(q.OUT/'middle_offset_replay_adjudications.jsonl')
ids={r['old_decision_id'] for r in replay}
add('all-53-exact-offset-replay-targets','semantics_v1_middle',[r for r in q.DECISIONS['semantics_v1_middle'] if r['decision_id'] in ids],
    'All 53 candidate targets and proposed partitions were read independently: 52 lexical voice corrections accepted, plus one blank-only structural normalization. Every change is explained in middle_offset_replay_adjudications.jsonl.',{'adjudication_file':'middle_offset_replay_adjudications.jsonl'})

# Corrections are appended only after their final source and partition recheck.
checks=q.OUT/'final_correction_recheck.json'
if checks.exists():
    c=json.loads(checks.read_text())
    if c.get('status')=='pass':
        assert c['semantic_decisions_sha256']==q.sha(q.PATCH/'qc_corrections/semantic_decisions.jsonl')
        add('all-final-additive-correction-spans','qc_corrections',q.DECISIONS['qc_corrections'],
            'Final replacements match the manually accepted partitions, exact source bytes and qualified overlay targets. Corrected current status has been checked; see final_correction_recheck.json.')

correction_targets={r['before_decision']['decision_id'] for r in q.rows(q.PATCH/'qc_corrections/semantic_correction_overlay.jsonl')}
for r in OBS.values():
    if r['decision_id'] in correction_targets:r['verdict']='original_interpretation_corrected_additively; historical_row_retained'

ordered=sorted(OBS.values(),key=lambda r:(r['branch'],r['source_volume'],r['story'],r['cp_start'],r['decision_id']))
(q.OUT/'span_observations.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in ordered))
(q.OUT/'sampling_inventory.json').write_text(json.dumps({'groups':GROUPS,'not_statistical_sample':True,'manual_row_count':len(ordered),'lexical_manual_rows':sum(r['lexical_row'] for r in ordered),'branches':dict(collections.Counter(r['branch'] for r in ordered))},ensure_ascii=False,indent=2))
print(json.dumps({'groups':len(GROUPS),'manual_rows':len(ordered),'lexical_rows':sum(r['lexical_row'] for r in ordered),'branches':dict(collections.Counter(r['branch'] for r in ordered))},ensure_ascii=False))

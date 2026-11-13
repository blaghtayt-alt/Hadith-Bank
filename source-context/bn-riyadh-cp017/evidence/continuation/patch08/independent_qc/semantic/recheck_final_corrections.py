from pathlib import Path
import json, hashlib, collections
import qc_tools as q

manifest=q.PATCH/'REVIEW_CANDIDATE.json'
cand=json.loads(manifest.read_text()); stage=Path(cand['stage'])
integration=stage/'continuation/integration'
ledger=integration/'semantic_interval_decisions.jsonl'
rawlines=ledger.read_bytes().splitlines(keepends=True)
ledgerrows=[json.loads(l) for l in rawlines]
ledgerhash=q.sha(ledger)
status=q.rows(integration/'semantic_current_status_index.jsonl')
statusby={r['ledger_1_based_row']:r for r in status}
new=q.rows(q.PATCH/'qc_corrections/semantic_decisions.jsonl')
newby={r['decision_id']:r for r in new}
neword={r['decision_id']:n for n,r in enumerate(ledgerrows,1) if r['decision_id'] in newby}
overlays=q.rows(q.PATCH/'qc_corrections/semantic_correction_overlay.jsonl')
replay={r['old_decision_id']:r for r in q.rows(q.OUT/'middle_offset_replay_adjudications.jsonl')}
parenthetical=[]
for f in ['parenthetical_narration_adjudications.json','parenthetical_attribution_adjudications.json']:
    parenthetical += [r for r in json.loads((q.OUT/f).read_text()) if r['verdict'].startswith('split_')]
expected_parentheticals=collections.defaultdict(list)
for r in parenthetical:expected_parentheticals[r['decision_id']].append((r['cp_start'],r['cp_end']))
prefixes={n:hashlib.sha256(b''.join(rawlines[:n])).hexdigest() for n in {o['before_ledger_row_count'] for o in overlays}}
errors=[];observations=[];replacedord=set();replacementord=set()
for o in overlays:
    old=o['before_decision'];oid=old['decision_id'];ordinal=o['before_ledger_1_based_row']
    old_errors=[]
    if prefixes[o['before_ledger_row_count']]!=o['before_ledger_sha256']:old_errors.append('before ledger prefix SHA mismatch')
    if ledgerrows[ordinal-1]!=old:old_errors.append('historical before row changed')
    children=sorted([newby[i] for i in o['replacement_decision_ids']],key=lambda r:r['cp_start'])
    if children[0]['cp_start']!=old['cp_start'] or children[-1]['cp_end']!=old['cp_end'] or any(a['cp_end']!=b['cp_start'] for a,b in zip(children,children[1:])):old_errors.append('replacement partition gap/overlap')
    if ''.join(r['text_verbatim'] for r in children)!=old['text_verbatim']:old_errors.append('replacement text differs')
    for r in children:
        if q.source(r['source_volume'],r['story'],r['cp_start'],r['cp_end'])!=r['text_verbatim']:old_errors.append('source CP mismatch')
        st=statusby[neword[r['decision_id']]]
        if st['ledger_sha256']!=ledgerhash or st['decision_id']!=r['decision_id'] or st['current_interpretation_active'] is not True:old_errors.append('replacement current status inactive/wrong binding')
        replacementord.add(neword[r['decision_id']])
    st=statusby[ordinal]
    if st['ledger_sha256']!=ledgerhash or st['current_interpretation_active'] is not False or st['historical_row_suppressed'] is not False:old_errors.append('old row status incorrect')
    if set(st['superseded_by_patch08_decision_ids'])!=set(o['replacement_decision_ids']):old_errors.append('status replacement IDs mismatch')
    if oid in replay:
        expected=replay[oid]['proposed_exact_partition']
        if len(expected)!=len(children):old_errors.append('replay accepted partition length mismatch')
        for a,b in zip(expected,children):
            role='source_structural_control_or_separator' if not any(c.isalnum() for c in old['text_verbatim']) else a['role_after']
            if (a['cp_start'],a['cp_end'],a['text_verbatim'],role)!=(b['cp_start'],b['cp_end'],b['text_verbatim'],b['after_role']):old_errors.append('replay accepted partition mismatch')
        category='exact_offset_voice_repair' if any(c.isalnum() for c in old['text_verbatim']) else 'blank_only_normalization'
    elif oid in expected_parentheticals:
        target=set(expected_parentheticals[oid]); actual={(r['cp_start'],r['cp_end']) for r in children if 'parenthetical' in r['after_role']}
        if target!=actual:old_errors.append('accepted parenthetical boundary mismatch')
        for r in children:
            if (r['cp_start'],r['cp_end']) not in target and r['after_role']!=old['after_role']:old_errors.append('unapproved surrounding role change')
        category='parenthetical_boundary_refinement'
    elif oid in ['p08-root-broad-05283-02-00','p08-root-broad-05306-01-00']:
        grades=[r for r in children if r['after_role']=='source_claimed_grade_not_independently_verified']
        expected=(1042129,1042139,'হাসান সহীহ') if '05283' in oid else (1044960,1044965,'হাসান')
        if len(grades)!=1 or (grades[0]['cp_start'],grades[0]['cp_end'],grades[0]['text_verbatim'])!=expected:old_errors.append('accepted grade boundary mismatch')
        category='collection_grade_separation'
    else:old_errors.append('unreviewed correction target');category='unknown'
    replacedord.add(ordinal)
    observations.append({'overlay_id':o['overlay_id'],'old_decision_id':oid,'old_ledger_ordinal':ordinal,'category':category,'source_volume':old['source_volume'],'story':old['story'],'cp_start':old['cp_start'],'cp_end':old['cp_end'],'replacement_decision_ids':o['replacement_decision_ids'],'manual_semantic_acceptance_from':'targeted source reading and corresponding independent adjudication files','exact_source_partition_verified':not old_errors,'historical_row_retained_and_current_interpretation_inactive':not old_errors,'all_replacements_currently_active':not old_errors,'errors':old_errors})
    errors += [{'overlay_id':o['overlay_id'],'error':e} for e in old_errors]

atoms_seen=set();bad_old=[]
for r in q.rows(integration/'current_source_semantic_segments.jsonl'):
    ords=set(r['all_active_semantic_row_ordinals'])
    if ords & replacedord:bad_old.append(r['source_segment_id'])
    atoms_seen |= ords & replacementord
if bad_old:errors.append({'kind':'superseded row active in atom','count':len(bad_old)})
if atoms_seen!=replacementord:errors.append({'kind':'replacement absent from atomic view','ordinals':sorted(replacementord-atoms_seen)})

report={'status':'pass' if not errors else 'fail','candidate_revision':cand['candidate_revision'],'review_candidate_sha256':q.sha(manifest),'stage':str(stage),'semantic_ledger_sha256':ledgerhash,'semantic_ledger_rows':len(ledgerrows),'semantic_decisions_sha256':q.sha(q.PATCH/'qc_corrections/semantic_decisions.jsonl'),'correction_overlay_sha256':q.sha(q.PATCH/'qc_corrections/semantic_correction_overlay.jsonl'),'overlays_reviewed':len(overlays),'replacement_spans_reviewed':len(new),'categories':dict(collections.Counter(r['category'] for r in observations)),'bound_prefix_ledgers':prefixes,'current_status_index_sha256':q.sha(integration/'semantic_current_status_index.jsonl'),'current_source_semantic_segments_sha256':q.sha(integration/'current_source_semantic_segments.jsonl'),'all_superseded_target_interpretations_inactive':not bad_old,'all_replacements_represented_in_current_atoms':atoms_seen==replacementord,'errors':errors,'observations':observations,'mechanical_vs_manual':'The role judgments were manually made in the stated source contexts. This script checks exact application, bytes, bounds and qualified current states; these checks create no additional manual review credit.'}
(q.OUT/'final_correction_recheck.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['observations','mechanical_vs_manual']},ensure_ascii=False,indent=2))

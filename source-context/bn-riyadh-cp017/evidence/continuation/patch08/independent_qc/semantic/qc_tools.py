"""Read-only candidate inspection helpers and independently computed engineering evidence.

Mechanical checks in this file confer no manual semantic-review credit.
"""
from pathlib import Path
import json, hashlib, sys, collections

ROOT = Path('/workspace/scratch/9965d2d3679f')
PARENT = ROOT/'work/cp016_parent/bn_riyadh_20261113_v2_cp016_patch07'
PATCH = ROOT/'patches/patch08'
OUT = PATCH/'independent_qc/semantic'
BRANCHES = ['semantic_review', 'semantics_v1_early', 'semantics_v1_early_b',
            'semantics_v1_early_c', 'semantics_v1_middle',
            'semantics_v1_late_and_notes', 'semantics_v2_gaps',
            'reference_refinement', 'header_story_review',
            'semantics_broad_v1_root', 'semantics_broad_v1', 'root_scope_review',
            'tail_review', 'qc_corrections']

def rows(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

SOURCES={v:json.loads((PARENT/f'source_exports/v{v:02}/doc_all_stories.json').read_text()) for v in [1,2]}
GAPS=rows(PATCH/'semantic_gap_inventory.jsonl')
DECISIONS={b:rows(PATCH/b/'semantic_decisions.jsonl') for b in BRANCHES}
PARENT_DECISIONS=rows(PARENT/'continuation/integration/semantic_interval_decisions.jsonl')

def source(v, story, a, b):
    s=SOURCES[v][story]
    return s['text'][a-s['cp_start']:b-s['cp_start']]

def show_gap(i, branches=None):
    g=GAPS[i-1]
    print('\nGAP',i,'V',g['source_volume'],g['story'],g['cp_start'],g['cp_end'],'PDF',g.get('pdf_pages'))
    print('SOURCE:',g['text_verbatim'].replace('\r','\n'))
    print('DECISIONS:')
    for b,rr in DECISIONS.items():
        if branches is not None and b not in branches: continue
        for r in rr:
            if r['source_volume']==g['source_volume'] and r['story']==g['story'] and r['cp_start']<g['cp_end'] and r['cp_end']>g['cp_start']:
                print(b,r['decision_id'],r['cp_start'],r['cp_end'],r['after_role'],repr(r['text_verbatim']))

def show_range(v, story, a, b, branches=None):
    print('\nSOURCE',v,story,a,b,repr(source(v,story,a,b)))
    for branch,rr in DECISIONS.items():
        if branches is not None and branch not in branches: continue
        for r in rr:
            if r['source_volume']==v and r['story']==story and r['cp_start']<b and r['cp_end']>a:
                print(branch,r['decision_id'],r['cp_start'],r['cp_end'],r['after_role'],repr(r['text_verbatim']))

def automatic_checks():
    results=[]
    ids=collections.defaultdict(list)
    for b,rr in DECISIONS.items():
        errors=[]
        for n,r in enumerate(rr,1):
            ids[r['decision_id']].append((b,n))
            st=SOURCES[r['source_volume']][r['story']]
            if not st['cp_start']<=r['cp_start']<r['cp_end']<=st['cp_end']:errors.append({'row':n,'kind':'source_bounds'})
            if source(r['source_volume'],r['story'],r['cp_start'],r['cp_end'])!=r['text_verbatim']:errors.append({'row':n,'kind':'exact_source_mismatch'})
            if r.get('source_text_changed') or r.get('source_wording_modified'):errors.append({'row':n,'kind':'source_changed_assertion'})
            if r.get('verified_grade') is not None or r.get('canonical_identity') is not None:errors.append({'row':n,'kind':'unexpected_verified_claim'})
        results.append({'branch':b,'file':str((PATCH/b/'semantic_decisions.jsonl').relative_to(ROOT)), 'sha256':sha(PATCH/b/'semantic_decisions.jsonl'),'rows':len(rr),'checks':'Exact source/global CP bounds/source immutability/canonical-claim fields','errors':errors,'manual_semantic_credit':0})
    ledger=PARENT/'continuation/integration/semantic_interval_decisions.jsonl'
    unc=PARENT/'continuation/integration/semantic_uncertainties.jsonl'
    uu=rows(unc)
    hashes={'semantic_interval_decision':sha(ledger),'semantic_uncertainty':sha(unc)}
    overlay_errors=[]
    for n,r in enumerate(rows(PATCH/'semantic_review/semantic_review_status_overlay.jsonl'),1):
        target=(PARENT_DECISIONS if r['target_kind']=='semantic_interval_decision' else uu)[r['target_ledger_1_based_row']-1]
        if r['target_ledger_sha256']!=hashes[r['target_kind']]:overlay_errors.append([n,'ledger_sha'])
        if r['target_id']!=target.get('decision_id',target.get('uncertainty_id')):overlay_errors.append([n,'ordinal_id'])
        if r.get('suppress_original_row'):overlay_errors.append([n,'suppression'])
        if r['target_kind']=='semantic_interval_decision' and r.get('old_role')!=r.get('new_role'):overlay_errors.append([n,'role_mutation'])
        if any(d not in ids for d in r['additive_decision_ids']):overlay_errors.append([n,'missing_additive_id'])
    ref_errors=[]
    refby={r['decision_id']:r for r in DECISIONS['reference_refinement']}
    for n,r in enumerate(rows(PATCH/'reference_refinement/semantic_correction_overlay.jsonl'),1):
        p=PARENT_DECISIONS[r['parent_ledger_1_based_row']-1]
        if r['parent_ledger_sha256']!=hashes['semantic_interval_decision']:ref_errors.append([n,'ledger_sha'])
        if r['parent_decision_id']!=p['decision_id']:ref_errors.append([n,'ordinal_id'])
        children=sorted([refby[x] for x in r['replacement_decision_ids']],key=lambda d:d['cp_start'])
        if children[0]['cp_start']!=p['cp_start'] or children[-1]['cp_end']!=p['cp_end'] or any(a['cp_end']!=b['cp_start'] for a,b in zip(children,children[1:])):ref_errors.append([n,'partition'])
        if ''.join(c['text_verbatim'] for c in children)!=p['text_verbatim']:ref_errors.append([n,'replacement_text'])
    report={'mechanical_only':True,'manual_semantic_review_credit':0,'branches':results,'cross_branch_duplicate_new_ids':{k:v for k,v in ids.items() if len(v)>1},'status_overlays':{'rows':79,'errors':overlay_errors},'reference_overlays':{'rows':207,'errors':ref_errors}}
    (OUT/'mechanical_semantic_input_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({'new_rows':sum(x['rows'] for x in results),'exact_source_errors':sum(len(x['errors']) for x in results),'duplicate_new_ids':len(report['cross_branch_duplicate_new_ids']),'status_overlay_errors':overlay_errors,'reference_overlay_errors':ref_errors},ensure_ascii=False))

if __name__=='__main__':
    if sys.argv[1]=='checks':automatic_checks()
    elif sys.argv[1]=='gaps':
        for n in sys.argv[2:]:show_gap(int(n))
    elif sys.argv[1]=='range':show_range(int(sys.argv[2]),sys.argv[3],int(sys.argv[4]),int(sys.argv[5]))

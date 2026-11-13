from pathlib import Path
import json, collections, datetime
import qc_tools as q

cor=json.loads((q.OUT/'final_correction_recheck.json').read_text())
assert cor['status']=='pass'
mechanical=json.loads((q.OUT/'mechanical_semantic_input_checks.json').read_text())
sample=json.loads((q.OUT/'sampling_inventory.json').read_text())
spans=q.rows(q.OUT/'span_observations.jsonl')
cases=q.rows(q.OUT/'case_observations.jsonl')
images=q.rows(q.OUT/'actual_image_observations.jsonl')
unc=json.loads((q.OUT/'uncertainty_current_state_check.json').read_text())
assert len(cases)==32 and all(r['author_disposition_supported'] for r in cases)
assert all(r['displayed'] for r in images)
assert not any(b['errors'] for b in mechanical['branches'])
stage=Path(cor['stage']);integ=stage/'continuation/integration'
now=datetime.datetime.now(datetime.timezone.utc).isoformat()

inputs=[]
def inp(p,scope):
    p=Path(p)
    inputs.append({'path':str(p.relative_to(q.ROOT)),'bytes':p.stat().st_size,'sha256':q.sha(p),'actual_review_scope':scope})
for v in [1,2]:
    inp(q.PARENT/f'originals/bn_riyadh_{v:02}.pdf','Targeted visual semantic inspection only on pages recorded in actual_image_observations.jsonl; not all pages or characters.')
    inp(q.PARENT/f'source_exports/v{v:02}/doc_all_stories.json','Every new decision mechanically checked against exact global-CP source slices. Manual reading restricted to recorded sampled spans, source-case contexts and corrective contexts.')
inp(q.PARENT/'continuation/integration/semantic_interval_decisions.jsonl','Mechanically checked qualified original row/ordinal identities and overlay targets; selected inherited narrower spans and 16 reference parents manually read.')
inp(q.PARENT/'continuation/integration/semantic_uncertainties.jsonl','All 22 inherited uncertainty cases independently reviewed in their exact source context; target identity checked mechanically.')
inp(q.PATCH/'semantic_gap_inventory.jsonl','Used to select and locate 19 complete manually read gap samples; no manual credit for other inventory rows.')
for b in q.BRANCHES:
    inp(q.PATCH/b/'semantic_decisions.jsonl',f"Every row source/CP checked mechanically. {sample['branches'].get(b,0)} rows manually read; exact IDs in span_observations.jsonl.")
for p in sorted({r['reviewed_author_file'] for r in cases}):inp(q.ROOT/p,'All cases from this author file are independently adjudicated in case_observations.jsonl; source limitations are retained.')
for p,scope in [
 ('semantic_review/semantic_review_status_overlay.jsonl','All 79 qualified target bindings and additive decision links checked mechanically; source semantic dispositions assessed through 32 case reviews.'),
 ('reference_refinement/semantic_correction_overlay.jsonl','All 207 parent SHA/ordinal identities and exact replacement partitions mechanically checked; 16 parents manually reviewed.'),
 ('qc_corrections/semantic_correction_overlay.jsonl','All 63 overlays independently checked for exact approved correction application, preserved historical rows and current deactivation/activation.'),
 ('semantics_v1_middle/review_writer.py','Manually inspected the standard/manual_quotes/add offset serialization path to understand the observed systematic defect; no author code was changed by this reviewer.'),
 ('qc_corrections/middle_offset_replay/REPLAY_SUMMARY.json','Read replay scope and claimed causal isolation; semantic acceptance did not rely on replay alone.'),
 ('qc_corrections/middle_offset_replay/candidate_corrections.jsonl','All 53 old rows and proposed exact partitions manually read and source/CP checked; 52 lexical changes accepted and one blank normalized.'),
 ('REVIEW_CANDIDATE.json','Binds candidate revision 4; semantic-related files used below were rehashed directly.')]:inp(q.PATCH/p,scope)
for f,scope in [
 ('semantic_interval_decisions.jsonl','All 63 exact historical correction targets and all 139 final replacements matched by SHA-qualified ordinal; entire ledger read mechanically, not semantically.'),
 ('semantic_current_status_index.jsonl','All corrected targets inactive, historical rows retained, all 139 replacements active; qualified current SHA/ordinal checks.'),
 ('current_source_semantic_segments.jsonl','All corrected target/replacement current participation checked mechanically; 106 equal-width multiple-label atoms counted without asserting universal semantic equivalence.'),
 ('semantic_uncertainties.jsonl','All 32 retained source-limited uncertainty IDs and source dispositions reconciled to independent case observations.'),
 ('semantic_uncertainty_current_status.jsonl','All 32 independently reviewed cases remain unresolved and investigation-complete.')]:inp(integ/f,scope)
for r in images:inp(q.ROOT/r['path'],'Actually displayed independent PDF render; targeted semantic issue and local page context inspected. No full-page character-review credit.')
(q.OUT/'reviewed_inputs.json').write_text(json.dumps({'created_utc':now,'reviewer':'independent semantic QC agent','candidate_revision':4,'input_count':len(inputs),'files':inputs,'reviewed_prior_ledger_prefix_bindings':cor['bound_prefix_ledgers'],'note':'Hash binding is not a claim that every byte was manually interpreted. The actual review scope is explicit per file.'},ensure_ascii=False,indent=2))

counts={b['branch']:b['rows'] for b in mechanical['branches']}
original_total=sum(counts.values())-counts['qc_corrections'];manual_original=len(spans)-counts['qc_corrections']
by_story=collections.defaultdict(list)
for r in spans:by_story[r['source_volume'],r['story']].append((r['cp_start'],r['cp_end']))
union={}
for key,intervals in by_story.items():
    merged=[]
    for a,b in sorted(intervals):
        if merged and a<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],b)
        else:merged.append([a,b])
    union[f'v{key[0]:02}:{key[1]}']={'source_CP':sum(b-a for a,b in merged),'merged_spans':len(merged)}
image_pages={f'v{v:02}':sorted(r['pdf_page'] for r in images if r['source_volume']==v) for v in [1,2]}
branch_scope=[{'branch':b,'new_rows_mechanically_checked':n,'rows_manually_read':sample['branches'].get(b,0),'rows_not_manually_read':n-sample['branches'].get(b,0)} for b,n in counts.items()]
report={
 'status':'pass_after_corrections_with_explicit_scope_limitations','created_utc':now,'candidate_revision':4,
 'candidate_manifest_sha256':cor['review_candidate_sha256'],'candidate_semantic_ledger_sha256':cor['semantic_ledger_sha256'],
 'semantic_ledger_rows':cor['semantic_ledger_rows'], 'independent_reviewer_modified_author_files':False,
 'manual_scope':{'original_new_rows_read':manual_original,'original_new_rows_total':original_total,'final_correction_rows_read':139,'all_selected_rows_read':len(spans),'lexical_selected_rows':sample['lexical_manual_rows'],'nonlexical_selected_rows':len(spans)-sample['lexical_manual_rows'],'original_new_rows_not_manually_read':original_total-manual_original,'complete_gap_samples':19,'reference_parents_sampled':16,'reference_replacement_rows_sampled':43,'footnote_discussion_spans_read':49,'complete_footnote_contexts_read':18,'uncertainty_cases_read':32,'inherited_uncertainty_cases':22,'new_uncertainty_cases':10,'pdf_pages_actually_displayed':len(images),'pdf_total_pages':2054,'pdf_pages_not_displayed':2054-len(images),'displayed_page_numbers':image_pages,'selected_row_CP_union':union,'selected_row_CP_union_total':sum(r['source_CP'] for r in union.values()),'selection':'purposive risk-based; not a statistical estimate'},
 'mechanical_scope':{'all_new_decision_rows':sum(counts.values()),'source_CP_errors':0,'duplicate_new_decision_ids':0,'status_overlays_checked':79,'reference_replacement_overlays_checked':207,'correction_overlays_checked':63,'manual_credit_from_mechanical_checks':0},
 'findings':{'incorrect_lexical_speaker_rows_fixed':52,'parenthetical_boundary_targets_refined':8,'parenthetical_insertions_separated':10,'collection_grade_conflations_fixed':2,'blank_only_target_normalized':1,'historical_targets_retained':63,'additive_replacement_spans':139,'open_implementation_findings_in_defined_scope':0,'source_limited_uncertainties_retained':32,'source_limited_uncertainties_resolved':0},
 'final_correction_application':{'status':'pass','all63_old_interpretations_inactive':True,'all139_replacements_active_and_in_current_atoms':True,'source_bytes_changed':0},
 'current_multiple_equal_width_role_label_atoms':106,
 'limitations':['This is not an exhaustive independent reread of 2,054 PDF pages or every new semantic span.','15,887 original new decision rows were not manually reread; they received exact-source/CP checks and author review only.','97 PDF pages were displayed for targeted semantic passages; no new full-page character-review credit is claimed.','The 52 lexical offset repairs were all read in exact source context; only representative corrective pages were image-inspected.','External canonical narrator identities, hadith grades, collection editions and theological interpretations were not independently authenticated.','Qualified historical multi-label authorities remain; this report does not collapse or equate all 106 equal-width label combinations.','Full candidate integrity, reconstruction, record preservation and package publication are handled by separate reviewers.'],
 'branch_scope':branch_scope,
 'evidence_files':['reviewed_inputs.json','case_observations.jsonl','span_observations.jsonl','sampling_inventory.json','actual_image_observations.jsonl','sampled_footnote_contexts.json','parenthetical_narration_adjudications.json','parenthetical_attribution_adjudications.json','narration_closing_quote_adjudications.json','middle_offset_replay_adjudications.jsonl','mechanical_semantic_input_checks.json','final_correction_recheck.json','uncertainty_current_state_check.json','multiple_current_leaf_labels.json']}
(q.OUT/'REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))

lines=[
 '# Independent semantic QC — patch08',
 '',
 '**Result: pass after corrections, within the independently reviewed scope described below.** Candidate revision 4 has no remaining implementation finding from this review. All 32 source-limited semantic uncertainties remain unresolved; completing their investigation does not supply information missing from the source.',
 '',
 '## Candidate and independence',
 '',
 f'This review binds candidate manifest SHA-256 `{cor["review_candidate_sha256"]}` and the 43,543-row semantic ledger SHA-256 `{cor["semantic_ledger_sha256"]}`. The reviewer used the immutable parent PDF files and global-CP DOC story exports, displayed independently rendered page images, and read the selected source passages afresh. The author branches were not edited by this reviewer. The author applied the findings through qualified additive overlays, which were then independently rechecked.',
 '',
 'The PDF sources contain 1,023 and 1,031 pages. Exact source text was read with CR and embedded controls preserved; CP offsets were evaluated against each story’s global start. Source spelling, printed contradictions and incomplete punctuation were not silently repaired.',
 '',
 '## What was manually reviewed',
 '',
 f'The manual ledger sample comprises **{manual_original} of {original_total:,} original new rows**, plus **all 139 final correction rows**: **{len(spans):,} rows in total**, including {sample["lexical_manual_rows"]} lexical rows and {len(spans)-sample["lexical_manual_rows"]} nonlexical rows. Their exact source intervals cover 51,944 unique CP. Context read around them is recorded separately and is not used to inflate the ledger-row count. The 65 documented groups are purposive checks of specific semantic risks, not a random sample or an estimate of the error rate in the remainder.',
 '',
 '- All 22 inherited uncertainty cases and all 10 newly reported cases were independently investigated against the targeted source images and DOC context. All 28 additive uncertainty qualification spans were read.',
 '- Nineteen complete inventory gaps were read: 1, 5, 9, 22, 27, 71, 302, 422, 498, 613, 977, 1371, 1545, 1558, 1564, 1577, 2083, 2085 and 2102. These cover preface/Quran boundaries, numbered reports, nested dialogue, report variants, narrated practice, explanations and grades.',
 '- The long Sahl report 802 was followed through its fighter, disputants, Prophetic response, Abu Darda and Sahl layers. Reports 854, 888, 893 and 901 were checked for Companion dialogue, anticipated versus actual responses, repeated question/answer turns and the Divine–servant dialogue. Five additional broad parents 5352, 5479, 24360, 24624 and 24702 were read completely in context.',
 '- Sixteen reference parents, comprising 43 replacement rows, were read. Parents 7554, 7559, 7573 and 7594 were checked against the actual date-eating/fighting reports on V2 pages 289–291. Their action and participant-speech text must not be treated as a collection reference.',
 '- All 49 nonbibliographic/nonseparator additions in the late/footnote branch were read, together with 18 complete surrounding source-note contexts. Additional bibliographic examples distinguish a collection title containing Sahih from a source-claimed chain grade.',
 '- All 11 header-field rows and all 19 tail/cover rows were read. Field instructions and cached page numbers, publication credits and a grading-editor credit are apparatus rather than report authenticity conclusions.',
 '',
 f'**{len(images)} unique PDF pages were actually displayed.** Every page is listed in `actual_image_observations.jsonl`, with the render hash and targeted inspection scope. Preparing a render did not earn review credit. These were semantic inspections of relevant passages and local context, not 97 new full-page character reviews.',
 '',
 '## Findings and verified corrections',
 '',
 '| Finding class | Historical targets | Corrective result |',
 '|---|---:|---|',
 '| Collection reference included a Bengali grade |2|Hasan/Sahih claims separated from Abu Dawud/Tirmidhi references, delimiters, anchor and controls.|',
 '| Bengali explanatory insertion remained inside a broad narration/attribution cue |8|Ten printed insertions separated, while surrounding narrative and attribution wording remain intact.|',
 '| Quoted lexical text reverted to narration at a misplaced offset |52|39 Bengali Prophetic, 8 Arabic Prophetic and 5 Bengali participant-speech rows corrected.|',
 '| Blank-only row affected by the same offset path |1|The one space receives a structural role; no speaker claim is attached to it.|',
 '',
 'The first two grade/reference findings were in h888 and h893. A focused grade-term scan of new main-story reference/collection labels distinguished these genuine claims from Sahih appearing in a collection title. The findings were checked against the printed source, not accepted merely because a keyword matched.',
 '',
 'The parenthesis follow-up first inspected all 18 matches in the newly added narration/scene/reporter label family. It separated actual explanatory insertions from named narrator cues, list ordinals and honorifics. Extending the same check to explicit attribution/introduction label variants produced eight further relevant main-story candidates after collection/reference metadata and already-qualified uncertainty labels were excluded. Five required additional insertion boundaries; the other three were correctly labeled honorifics or a translation-introduction cue. The two finite adjudication files record every decision. The source wording for the Jibril-report “third” qualification is not treated as a third named speaker.',
 '',
 'The list-number example in h243 also exposed a separate voice error. A focused closing-quote scan produced 44 candidates; 36 were confirmed Prophetic-speech continuations incorrectly labeled as narration. The remaining eight were valid inner speech, narrated practice, or narration after only closing punctuation. The author traced the defect to helper-generated suffix anchors: a trailing whitespace suffix could be located at an earlier internal space. An isolated replay using exact integer offsets identified 53 affected old rows, including fragments without closing quotation marks and Arabic text. **Every proposed changed partition was independently read**; replay by itself was not treated as semantic proof. All 36 manually detected closing-quote errors are included in that causal set.',
 '',
 'The final application contains 63 SHA-and-ordinal-qualified overlays and 139 exact replacement spans. Recheck verified each historical before-row, each bound prior-ledger prefix, every replacement CP slice and complete partition, and the final status/atomic views. All 63 superseded interpretations are inactive; all historical rows remain present; all 139 replacements are active and represented in the current atoms. The source text is unchanged. Detailed results are in `final_correction_recheck.json`.',
 '',
 '## Source limitations retained',
 '',
 'All 32 case decisions support retention. They concern unprinted quote/parenthesis endpoints, unnamed speakers or gloss suppliers, pronominal assessment subjects, and source-internal Arabic/Bengali attribution differences. The review does not select an external canonical identity to make the languages agree. Examples include h1616 Arabic linkage versus the Bengali named narrator; h1798 Abu Bakra/Abu Hurayra; h987 Abu Hurayra/Abu Abdullah; h990 Ibn Amr/Ibn Umar; and the h802 father/Bishr versus explicit Bengali Qays layer. The Sufyan transition and note 169 Ibn Hajar antecedent remain localized uncertainties.',
 '',
 'The current uncertainty status view contains exactly the 32 independently reviewed IDs, all investigation-complete and none resolved. The retained qualified alternatives must remain available to downstream users. There are also 106 current atoms with more than one equal-width qualified leaf label. Their strings and identities were checked, and the source-limited combinations were reviewed through the case work; this report does not assert that every label pair is universally interchangeable.',
 '',
 '## Mechanical checks, separate from manual semantic reading',
 '',
 'Every one of the 16,976 new rows, including 139 corrections, was checked for exact immutable source text and valid global-CP bounds. There were zero source mismatches, zero duplicate new decision IDs and zero unexpected source-mutation/verified-grade/canonical-identity assertions in the checked fields. All 79 investigation-status overlays and 207 reference-refinement overlays were checked for qualified target identity and exact additive partition/link consistency. The 63 final correction overlays received the additional integrated-status check described above. These checks receive **zero manual semantic-review credit**.',
 '',
 'The full candidate reconstruction, record preservation, all-source-unit partition and package checks belong to the separate engineering review. This semantic report does not substitute an automated exact-text pass for source interpretation.',
 '',
 '## Exact remaining scope',
 '',
 '**15,887 original new decision rows were not independently reread manually.** They received exact-source/CP checks and the author’s review. **1,957 PDF pages were not independently displayed by this reviewer.** Many displayed pages were examined only for their targeted passages. No claim is made of an exhaustive independent reread of 2,054 pages, every new semantic span, or every inherited semantic row.',
 '',
 'No external canonical narrator identification, independent hadith grading or source-edition reconciliation was performed. These are source-faithful classifications and explicitly attributed source claims. The 32 retained ambiguities remain limitations of the supplied source, not unfinished coding corrections.',
 '',
 '| Author branch | New rows checked mechanically | Rows manually read | Rows not manually read |',
 '|---|---:|---:|---:|']
for b in branch_scope:lines.append(f"|{b['branch']}|{b['new_rows_mechanically_checked']:,}|{b['rows_manually_read']:,}|{b['rows_not_manually_read']:,}|")
lines += ['', 'The zero-row root_scope_review branch contributes the Sufyan uncertainty rather than new decision rows. Its source issue is included in the 32-case review.', '', '## Actually displayed page inventory', '']
for v,pgs in image_pages.items():lines.append(f"- **{v}:** "+', '.join(map(str,pgs))+'.')
lines += ['', '## Case-by-case independent observations', '']
for r in cases:
    lines += [f"### {r['qc_case_id']} — {r['uncertainty_id']}", '', f"Volume {r['source_volume']}; displayed source pages: "+', '.join(map(str,r['pdf_pages_actually_displayed']))+'.', '', r['manual_observation'], '', '**Disposition:** retain the source-limited uncertainty.', '']
lines += ['## Evidence and handoff', '', 'The complete source-bound observations are in `case_observations.jsonl` and `span_observations.jsonl`. `sampling_inventory.json` lists every selected row and group; `reviewed_inputs.json` binds every actually used source/author file and displayed render with its review scope. The finite follow-up queues, adjudications and final corrective recheck are retained for reproduction and audit. This pass is complete for that defined scope.']
# Preserve exact hashes, identifiers and source observations in the Markdown output.
text='\n'.join(lines)+'\n'
(q.OUT/'REPORT.md').write_text(text)
handoff={'status':report['status'],'candidate_revision':4,'review_candidate_sha256':cor['review_candidate_sha256'],'semantic_ledger_sha256':cor['semantic_ledger_sha256'],'open_findings_in_defined_scope':0,'retained_source_uncertainties':32,'manual_original_new_rows':manual_original,'manual_correction_rows':139,'manual_rows_total':len(spans),'actual_targeted_PDF_pages':len(images),'unreviewed_original_new_rows':original_total-manual_original,'unviewed_PDF_pages':2054-len(images),'all63_corrections_integrated_and_rechecked':True,'full_independent_reread_claim':False,'author_files_modified':False,'reports':{'json':'REPORT.json','markdown':'REPORT.md','inputs':'reviewed_inputs.json','cases':'case_observations.jsonl','spans':'span_observations.jsonl','correction_recheck':'final_correction_recheck.json'},'report_json_sha256':q.sha(q.OUT/'REPORT.json'),'report_markdown_sha256':q.sha(q.OUT/'REPORT.md'),'reviewed_inputs_sha256':q.sha(q.OUT/'reviewed_inputs.json')}
(q.OUT/'HANDOFF.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2))
print(json.dumps(handoff,ensure_ascii=False,indent=2))

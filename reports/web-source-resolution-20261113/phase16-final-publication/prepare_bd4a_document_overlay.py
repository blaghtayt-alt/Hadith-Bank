"""Version the already frozen status document with the newly verified source checkpoint."""
from pathlib import Path
import difflib,hashlib,json
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
before=ROOT/'document-update.md';b=before.read_bytes();assert sha(b)=='be1e4a3d30da206c37252add250a14e0081117d7f948aa29f2a5a8da94132158'
progress_path=WORK/'phase16-successor-acquisition-monitor/saved-checkpoint/progress.json'
progress_bytes=progress_path.read_bytes();assert sha(progress_bytes)=='1d2dab7f60271117a828d24cea046023cd59725ecd1ce015d649a1be5d0a862c'
p=json.loads(progress_bytes)
assert (p['imported_count'],p['registered_hadith_count'],p['non_narration_source_entries'],p['classification_pending_count'],p['pending_fetch_count'])==(16664,16321,151,192,19726)
assert p['blocked'] is False and p['errors_count']==0
state=(WORK/'phase16-successor-acquisition-monitor/saved-checkpoint/state.json').read_bytes()
assert len(state)==12991459 and sha(state)=='ab088c36fc4e4e44f9252067cbe34343226fb5479136a9b473d491ba63f2d34f'
assert git(state)=='9580caaa0587797cbda69646e66bf2e1330858cb'
assert len(json.loads(state)['imported'])==16664
section='''### Later verified acquisition checkpointbd4a

The ordinary source workflow then completed run
[`43450869489`](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43450869489)
and saved
[`bd4a75695d3c695e98bf8efa5ce07764ac5e2633`](https://github.com/blaghtayt-alt/Hadith-Bank/commit/bd4a75695d3c695e98bf8efa5ce07764ac5e2633)
on top of the concurrent PR15 merge. Its exact saved export records **16,664
fetched,16,321 registered,151 source-only,192 held and19,726 ordinary unfetched
occurrences**, with zero current errors and no access block.

The495 newly fetched occurrences comprise403 registered and92 newly held.
The earlier117 review decisions were consumed by this saved export. Its192
held rows consist of the **unchanged100 reviewed in this checkpoint plus92 new
occurrences**; their source objects and immutable descriptors were compared
before publication. The new92 are disjoint from the full preceding217-held set
and the15,672 imported occurrences in the complete0639 baseline.

| Fixedbd4a source data | Fetched | Registered | Source-only | Held | Unfetched |
| --- | ---: | ---: | ---: | ---: | ---: |
| Actual saved export | 16,664 | 16,321 | 151 | 192 | 19,726 |
| Derived application of these100 reviewed decisions | 16,664 | 16,417 | 155 | 92 | 19,726 |

The second row remains a derived projection until a subsequent saved export
consumes this publication. The92 next-review source occurrences are eight Abu
Dawud,22 Bukhari,ten Ibn Majah,27 Muslim,16 Nasai and nine Tirmidhi. Their source
verification is complete; no linguistic admission is claimed for them here.

The bounded artifact now includes the exact complete saved state through the
published gzip repair: **2,115,157 compressed bytes expand to12,991,459 exact
original bytes**, matching the state file's Git blob atbd4a. The audit checks all
384 raw/parsed files and192 raw reparses, preserves every15,672 baseline source
descriptor and all1,000 historical error-attempt lists/consumed attempts. This
is a fullbd4a-to0639 history comparison; the unavailable complete5589
intermediate state is not falsely claimed as compared. The original compressed
and decompressed hashes, size bounds, Git path bindings and complete next92
partition are recorded in the
[bd4a acquisition audit package](../reports/web-source-resolution-20261113/phase16-bd4a-full-acquisition-audit-delivery-manifest.json).

'''
for a,z in {'checkpointbd4a':'checkpoint bd4a','fetched,16,321':'fetched, 16,321','registered,151':'registered, 151','source-only,192':'source-only, 192','and19,726':'and 19,726','The495':'The 495','comprise403':'comprise 403','and92':'and 92','earlier117':'earlier 117','Its192':'Its 192','unchanged100':'unchanged 100','plus92':'plus 92','new92':'new 92','preceding217-held':'preceding 217-held','the15,672':'the 15,672','complete0639':'complete 0639','Fixedbd4a':'Fixed bd4a','these100':'these 100','The92':'The 92','Dawud,22':'Dawud, 22','Majah,27':'Majah, 27','Muslim,16':'Muslim, 16','to12,991,459':'to 12,991,459','atbd4a':'at bd4a','and192':'and 192','every15,672':'every one of the 15,672','all1,000':'all 1,000','fullbd4a-to0639':'full bd4a-to0639','complete5589':'complete 5589','next92':'next 92'}.items():section=section.replace(a,z)
text=b.decode();anchor='### Original requested groups and remaining language work\n';assert text.count(anchor)==1
text=text.replace(anchor,section+anchor,1)
old='The published diagnostic-exporter repair includes exact\ncompressed saved-state bytes in future bounded artifacts while preserving all\nexisting size caps and source request budgets.'
new='The published diagnostic-exporter repair has now been exercised by the\ncompletedbd4a workflow, as recorded above. It preserves exact full-state bytes\ninside the existing artifact size caps without changing source request budgets.'
assert old in text;text=text.replace(old,new.replace('completedbd4a','completed bd4a'),1)
target=ROOT/'document-update-v2.md';assert not target.exists();target.write_text(text)
patch=''.join(difflib.unified_diff(b.decode().splitlines(True),text.splitlines(True),fromfile='document-update-v1.md',tofile='document-update-v2.md'))
(ROOT/'document-bd4a-overlay.patch').write_text(patch)
receipt={'schema':'hadith-bank-status-document-source-checkpoint-overlay-v1','before_sha256':sha(b),'before_bytes':len(b),'before_git_blob_sha1':git(b),'after_sha256':sha(target.read_bytes()),'after_bytes':len(target.read_bytes()),'after_git_blob_sha1':git(target.read_bytes()),'new_source_commit':'bd4a75695d3c695e98bf8efa5ce07764ac5e2633','source_progress_sha256':sha(progress_bytes),'complete_source_state_sha256':sha(state),'complete_source_state_git_blob_sha1':git(state),'patch_sha256':sha(patch.encode()),'reviewed_candidate_bytes_changed':False,'canonical_priority_queue_changed':False,'all_frozen_staging_files_unchanged_except_versioned_doc_overlay':True,'projection_is_not_a_saved_export':True,'publication_base_must_preserve_concurrent_merge_and_source_save':True}
(ROOT/'document-bd4a-overlay-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))

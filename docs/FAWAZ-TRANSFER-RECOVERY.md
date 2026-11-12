# Fawaz upload recovery and publication checks

## What failed

The saved continuation checkpoint records `written_full_export =
failed_no_space_left_on_device`. The incomplete local export therefore was not
a GitHub rejection. The old workspaces subsequently became unavailable; counts
and hashes in a progress message could not recreate their missing file bodies.
See the original [interruption checkpoint](../reports/fawaz-import-review/continuation-20261113/interruption-checkpoint.json)
on recovery commit `4ac2abc81816210bb3028134d83f87fa5f037c4b`.

The existing [remote execution record](REMOTE-WORKFLOW.md) also identifies large
encoded file transfers and verbose tool output exhausting conversation context.
A more recent recursive directory request returned `Transport closed`, while
smaller directory requests worked. That transport error contained no GitHub
HTTP status. It does not establish a GitHub rate limit or a rejected file size.

The current execution environment can read the public repository with Git, but
an authenticated push dry-run returned `fatal: unable to get password from
user`. The connected GitHub tool can write blobs. Read access and write
authentication are therefore handled separately; credentials are not copied
between environments.

GitHub rate limits must be diagnosed from the actual HTTP response and rate
headers. The documented REST rate-limit responses are 403 or 429; retry timing
must respect `Retry-After` or the reset information. Splitting data into many
small commits can itself increase request pressure. A 128 KB transfer chunk is
not GitHub's general file-size limit. See [REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
and [large-file limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

## The delivery path

1. Read the existing pinned source files directly with Git. Verify their stored
   and expanded hashes. Reuse source and recovery blobs already in this
   repository rather than sending their bodies through the conversation.
2. Upload changed code, small review manifests and new compressed review
   evidence using the authenticated GitHub connector. Pass bytes between tools
   without printing them. Check each returned Git blob SHA against the local
   byte-derived SHA, and save the successful acknowledgements locally.
3. Construct one additive Git tree and commit from the recorded base revision.
   Use a dedicated continuation branch and an expected-head update. Refresh
   remote state before publication and retain unrelated concurrent work.
4. Let GitHub Actions generate the canonical Fawaz materials from the saved
   original sources and review decisions. The generated material files are not
   repeatedly uploaded through the conversation.
5. Run exact source, preservation and selected-review projection checks before
   building or deploying the reader. Save bounded diagnostic artifacts even
   when a gate fails. Normal test or source failures stop publication.

The immutable original publication baseline is commit
`ca5f3f18e682376ce2c91e5f97f4b0d7e24eb4c6`: 36,464 provider occurrences,
29,911 registered occurrences, 6,553 held occurrences and 31 edition files.
The baseline is audited from its actual Git objects; its fingerprints do not
need another multi-megabyte upload.

## Reproducible inputs and interruption recovery

`catalog/fawaz-reviewed-spans.json` retains the original published decisions.
`catalog/fawaz-review-inputs.json` pins the recovered catalog, the phase archive
and any subsequently reviewed batches by stored and expanded size/hash.
`scripts/fawaz_review_inputs.py` assembles them without changing their decisions,
and rejects conflicting/repeated identities, changed baseline decisions,
unsafe archive members and damaged input bytes.

The recovered inputs originally contained 4,014 newly positive provider IDs.
That is an input recovery count, not a claim that the later 6,331-addition
checkpoint or a 36,242-record deployment was recovered. Subsequent source
reviews are separate, additive files with their actual field-level coverage.
The written progress and final source audit determine the eventual published
counts; a number from a chat is never used as an inclusion target.

Use [the reviewed refresh entry point](FAWAZ-REVIEWED-REFRESH.md) for the complete
export procedure. It checks disk space, works in a staging directory, preserves
the original checkout until validation succeeds, and rolls back ordinary
installation failures. An interrupted installation retains a marker and journal
that must be inspected before resuming; an uncertain write is not blindly
repeated. The full provider inventory remains accounted for, including empty
source fields and non-narration context.

These controls verify data transfer and source preservation. They do not claim
new translation, independent certification, authenticity grading or rights
clearance.

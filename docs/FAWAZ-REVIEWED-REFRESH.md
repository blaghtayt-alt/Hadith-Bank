# Rebuild the saved Fawaz reviews before reader publication

`scripts/refresh_fawaz_reviewed.py` performs a gated, offline export of the exact
saved decisions referenced by `catalog/fawaz-review-inputs.json`. It is a no-op
when that supplemental manifest is absent. The normal source download queue,
new review decisions, translations, and reader publication remain separate.

## Workflow integration

The reader build should run this command after its unit tests and before
`scripts/refresh_bank.py`:

```bash
python scripts/refresh_fawaz_reviewed.py --root .
python scripts/refresh_bank.py --root .
```

Use the existing logged-task wrapper when running manually or when detailed CI
logs need a durable job record. The refresh entry point also writes bounded
status events and full audits beneath `.work/fawaz-reviewed-refresh/run-*`.

The checkout must already contain Git objects for the immutable published
baseline `ca5f3f18e682376ce2c91e5f97f4b0d7e24eb4c6`, including its blobs. A normal
GitHub Actions checkout with `fetch-depth: 0` provides the history. The entry
point performs no fetch and disables Git's implicit fetching of missing blobs.
It restores only Fawaz materials/imports/catalog/reports plus `AGENTS.md` to a
temporary directory and verifies the complete baseline source inventory before
deriving a local fingerprint snapshot. No baseline fingerprints need to be
uploaded through the application or added to the repository.

For an already source-validated local checkpoint, both explicit arguments are
required:

```bash
python scripts/refresh_fawaz_reviewed.py --root . \
  --baseline-snapshot /absolute/path/baseline.json.gz \
  --baseline-snapshot-sha256 VERIFIED_STORED_SHA256
```

The supplied file must name that exact baseline commit and provider revision,
with 36,464 provider IDs, 29,911 registered occurrences, 6,553 held occurrences,
and all 31 edition inputs. Its caller-supplied stored SHA-256 is mandatory.

The workflow must let any nonzero refresh exit stop the reader build, generated
commit, artifact upload, and deployment. Do not apply `continue-on-error` or an
unconditional deployment condition to this gate. Include the resulting
`materials/fawaz-*` and `imports/web-fawaz-20261112/{classification,held,progress.json,source-integrity-validation.json}`
in the existing generated-output synchronization commit. Preserve the normal
reader, catalog, search, concurrent-import, and expected-head checks.

## What is checked

Before export, all compressed review archives and their expanded content are
verified by the review-input loader, the unchanged baseline decisions are
checked, all 31 pinned edition inputs must be present, and free disk space is
checked for the temporary source and generated output. The job holds the
existing Fawaz importer lock and runs only its `export_only` path.

The new export is written to a private staging root. The source audit checks
the exact upstream bytes, numbering, quotations, notes, language ownership,
source reports, and the complete provider ledger. The preservation comparison
requires every original provider ID and registered language quotation to remain
unchanged. A second gate requires every saved positive review to appear under
its own provider ID and own language, with its exact selected spans, excluded
notes, report groups, speaker/type metadata and context status. The registered
ID set must equal the baseline registrations plus those saved positive IDs; an
unreviewed additional promotion is rejected.

Only after all gates pass are importer-owned material directories, held and
classification ledgers, progress and the compact integrity report installed.
Unknown files in a Fawaz material directory or any symlink input stop the run.
Other material families, raw sources and review evidence are not replacement
targets. Ordinary installation errors roll back the original directories. An
uncatchable interruption leaves `.work/fawaz-reviewed-install.json`, the job
journal and rollback bytes for inspection; another refresh refuses to proceed
until that interrupted installation has been resolved. A failed CI gate cannot
publish the partially installed checkout.

These checks establish source fidelity and execution completeness. They do not
assert new translation, authenticity assessment, independent certification or
rights clearance.

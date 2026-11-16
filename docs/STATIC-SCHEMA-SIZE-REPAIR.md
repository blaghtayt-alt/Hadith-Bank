# Static occurrence metadata size repair

PR26 adds2,050 source occurrences across six reviewed source registrations.
Its complete build43856451091 passed software and pre-build reader/discovery
fixtures, then stopped at963,050,749bytes against the unchanged950,000,000-byte
publication budget. No replacement site was staged; later checks were skipped.

The generator now omits two optional duplicate current-page `url` properties
from an exact generated occurrence graph. The absolute HTML canonical link
remains. The occurrence `@id` uses `#occurrence`, checked against its original
canonical URL. Source prose, edition URL, citations, occurrence identifier,
source downloads, HTML body and every other graph field remain unchanged.
Restoring the three declared serialization changes must reproduce the original
graph exactly. Other graphs and the nonindexable404 page are untouched.

Four new portable tests and18existing discovery regressions pass. All2,050
new source pages have exact before/after bytes outside JSON-LD. Root checked
16actual desktop/mobile paired cases without JavaScript. A separate existing
reviewer independently passed the22tests, eight actual page pairs, seven real
guard cases and the complete failed-CI inventory calculation; no new defect.
The reviewer did not rerun Root's entire2,050-page or browser proof.

Independent result archive:21,781bytes; SHA-256
`341ba3559821049d143e7cdd4dcbe5c1b9880b98d1de494dad8ba96ef5068bce`.
Exact reviewed production SHA-256:
`b80cd37d960ee4230165564bc03ed9f9136fa743a46c91f1031459845ca75a8e`.

The40,832occurrence-page inventory projects15,304,527bytes saved, giving
947,746,222bytes and2,253,778bytes headroom. These are arithmetic projections,
not a fresh complete build. The repaired exact commit must pass the full corpus,
sitemap, static DOM, reader, accessibility and performance workflow before any
deployment claim. Canonical sources and all existing source qualifications stay
unchanged; no counterpart, translation or authenticity certification is added.

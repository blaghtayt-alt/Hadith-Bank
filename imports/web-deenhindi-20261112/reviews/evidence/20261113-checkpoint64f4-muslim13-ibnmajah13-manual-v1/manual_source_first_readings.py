"""Immutable original-field notes, accumulated before any candidate authorship."""
import importlib
NOTES={}
for number in range(1,7):
    module=importlib.import_module(f'source_first_batch{number:02d}')
    for key,languages in module.READINGS.items():
        for language,note in languages.items():
            identity=('deenhindi-'+key,language)
            assert identity not in NOTES
            NOTES[identity]=note
assert len(NOTES)==55

"""Read-only aggregation of the three immutable complete-source reading batches."""
from source_first_batch01 import NOTES as FIRST
from source_first_batch02 import NOTES as SECOND
from source_first_batch03 import NOTES as THIRD

assert not (set(FIRST)&set(SECOND) or set(FIRST)&set(THIRD) or set(SECOND)&set(THIRD))
NOTES={('deenhindi-'+key,language):note
       for batch in (FIRST,SECOND,THIRD)
       for key,fields in batch.items()
       for language,note in fields.items()}
assert len(NOTES)==36

"""Search explicit collection/number pairs without joining unrelated references.

The parser recognizes search clauses, not source bibliography. Only structured
reference objects (or clearly scoped collection-number fields) create matches.
"""
import re
import unicodedata
from functools import lru_cache
from counterpart_display import counterpart_source_data


COLLECTION_ALIASES = [
    ('bukhari', r'(?:(?:sahih|ṣaḥīḥ|صحيح|صحیح)\s+)?(?:al[-\s]*)?(?:bukhari|bukhārī|bukhary|البخاري|بخاري|بخاری)'),
    ('muslim', r'(?:(?:sahih|ṣaḥīḥ|صحيح|صحیح)\s+)?(?:muslim|مسلم)'),
    ('abu-dawud', r'(?:(?:sunan|سنن)\s+)?(?:(?:abu|abi|abū|abī)[-\s]*(?:dawud|dawood|dāwūd)|(?:أبو|أبي|ابو|ابي)\s*داود)'),
    ('tirmidhi', r'(?:(?:jami[ʿ’\x27]?|jāmi[ʿ’\x27]?|sunan|جامع|سنن)\s+)?(?:(?:al|at)[-\s]*)?(?:tirmidhi|tirmizi|tirmidhī|الترمذي|ترمذي)'),
    ('nasai', r'(?:(?:sunan|سنن)\s+)?(?:al[-\s]*)?(?:nasai|nasa[’\x27]?i|nasā[’\x27]?ī|النسائي|نسائي)|السنن\s+الصغرى\s+للنسائي'),
    ('nasai-kubra', r'(?:(?:al[-\s]*)?sunan[-\s]+(?:al[-\s]*)?kubra(?:\s+by\s+(?:al[-\s]*)?(?:nasai|nasa[’\x27]?i))?|nasai[-\s]+kubra|السنن\s+الكبرى\s+للنسائي|سنن\s+النسائي\s+الكبرى)'),
    ('ibn-majah', r'(?:(?:sunan|سنن)\s+)?(?:ibn|ابن)[-\s]*(?:majah|maja|mājah|ماجه|ماجة)'),
    ('malik', r'(?:muwatta(?:\s+malik)?|muwaṭṭa[ʾ’\x27]?(?:\s+mālik)?|موطأ(?:\s+مالك)?|الموطأ|malik)'),
    ('ahmad', r'(?:(?:musnad|مسند)\s+)?(?:الإمام\s+)?(?:ahmad|ahmed|aḥmad|أحمد|احمد)(?:\s+بن\s+حنبل)?'),
    ('darimi', r'(?:(?:sunan|musnad|سنن|مسند)\s+)?(?:al[-\s]*)?(?:darimi|dārimī|الدارمي|دارمي)'),
    ('ibn-hibban', r'(?:(?:sahih|صحيح)\s+)?(?:ibn|ابن)[-\s]*(?:hibban|ḥibbān|حبان)'),
    ('ibn-khuzaymah', r'(?:(?:sahih|صحيح)\s+)?(?:ibn|ابن)[-\s]*(?:khuzaymah|khuzaimah|khuzayma|خزيمة)'),
    ('hakim', r'(?:(?:al[-\s]*)?(?:hakim|ḥākim|mustadrak(?:\s+by\s+(?:al[-\s]*)?hakim)?)|الحاكم|المستدرك(?:\s+على\s+الصحيحين)?(?:\s+للحاكم)?)'),
    ('tabarani', r'(?:al[-\s]*)?(?:tabarani|ṭabarānī|الطبراني|طبراني)'),
    ('tabarani-kabir', r'(?:(?:al[-\s]*)?mu[ʿ’\x27]?jam[-\s]+(?:al[-\s]*)?kabir(?:\s+by\s+(?:al[-\s]*)?tabarani)?|tabarani[-\s]+kabir|المعجم\s+الكبير(?:\s+للطبراني)?)'),
    ('tabarani-awsat', r'(?:(?:al[-\s]*)?mu[ʿ’\x27]?jam[-\s]+(?:al[-\s]*)?awsat(?:\s+by\s+(?:al[-\s]*)?tabarani)?|tabarani[-\s]+awsat|المعجم\s+الأوسط(?:\s+للطبراني)?)'),
    ('tabarani-saghir', r'(?:(?:al[-\s]*)?mu[ʿ’\x27]?jam[-\s]+(?:al[-\s]*)?saghir(?:\s+by\s+(?:al[-\s]*)?tabarani)?|tabarani[-\s]+saghir|المعجم\s+الصغير(?:\s+للطبراني)?)'),
    ('adab-al-mufrad', r'(?:al[-\s]*)?adab[-\s]+(?:al[-\s]*)?mufrad|(?:الأدب|الادب)\s+المفرد(?:\s+للبخاري)?'),
    ('riyad-as-salihin', r'riyad[h]?[-\s]+(?:as[-\s]*|al[-\s]*)?salihin|رياض\s+الصالحين(?:\s+من\s+كلام\s+سيد\s+المرسلين)?'),
    ('hisn-al-muslim', r'hisn[-\s]+(?:al[-\s]*)?muslim|حصن\s+المسلم'),
    ('mishkat-al-masabih', r'mishkat[-\s]+(?:al[-\s]*)?masabih|مشكاة\s+المصابيح'),
]
KEY_ALIASES = {'al-nasai': 'nasai', 'riyadh-al-salihin': 'riyad-as-salihin',
               'riyad-al-salihin': 'riyad-as-salihin', 'riyadh-as-salihin': 'riyad-as-salihin'}
_KEYS = {key for key, _ in COLLECTION_ALIASES}
_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
_PERSIAN = str.maketrans({'\u064a': '\u06cc', '\u0643': '\u06a9', '\u200c': '', '\u200d': ''})
_SEPARATOR = r'[\s:：,،#№.()\[\]-]*'
_LABEL = r'(?:(?:no\.?|number|hadith|hadīth|رقم|حديث|حدیث)\s*[.:#№-]?\s*)?'
_NUMBER = r'([0-9]+[a-z]?)(?![0-9a-z]|\s*[/\\:–—-]\s*[0-9])'
_BAD_SCOPE = re.compile(r'commentary|context|unresolved|volume|page', re.I)
_BAD_NUMBERING = re.compile(r'volume|page|unresolved|source_entry|provider|sequence|part|column|not_canonical|abridg(?:e)?ment|within_source_named_book', re.I)


def normalized(value):
    value = unicodedata.normalize('NFKC', str(value)).casefold().translate(_DIGITS).translate(_PERSIAN)
    return ''.join(c for c in value if c != '\u0640' and not
                   (unicodedata.category(c).startswith('M') and 'ARABIC' in unicodedata.name(c, ''))).strip()


# Compile against the same search alphabet as queries and reference names.
# Keep the published alias definitions unchanged for browser/CLI parity.
_NORMALIZED_ALIASES = [(key, normalized(alias)) for key, alias in COLLECTION_ALIASES]
_PATTERNS = [(key, re.compile(r'(?<!\w)(?:' + alias + ')' + _SEPARATOR + _LABEL + _NUMBER, re.I))
             for key, alias in _NORMALIZED_ALIASES]


def number_key(value):
    if type(value) not in (str, int):
        return None
    number = normalized(value)
    if not re.fullmatch(r'[0-9]+[a-z]?', number):
        return None
    return re.sub(r'^0+(?=[0-9])', '', number)


def collection_key(value):
    if not isinstance(value, str):
        return None
    value = normalized(value)
    return _collection_key(value)


@lru_cache(maxsize=512)
def _collection_key(value):
    value = KEY_ALIASES.get(value, value)
    if value in _KEYS:
        return value
    matches = {key for key, alias in _NORMALIZED_ALIASES if re.fullmatch('(?:' + alias + ')', value, re.I)}
    return next(iter(matches)) if len(matches) == 1 else None


def _reference_eligible(reference):
    if not isinstance(reference, dict):
        return False
    scope = ' '.join(str(reference.get(field) or '') for field in ('scope', 'citation_scope'))
    if _BAD_SCOPE.search(scope):
        return False
    numbering = ' '.join(str(reference.get(field) or '') for field in ('numbering_scheme', 'numbering_scope'))
    return not (reference.get('numbering_system') or
                reference.get('sequence_is_hadith_number') is False or _BAD_NUMBERING.search(numbering))


def reference_pair(reference):
    if not _reference_eligible(reference):
        return None
    keys = {collection_key(reference.get(field)) for field in ('book_key', 'collection', 'collection_ar')}
    keys.discard(None)
    number = number_key(reference.get('number'))
    if len(keys) != 1 or number is None:
        return None
    return (next(iter(keys)), number)


def reference_pairs(reference, *, printed=False):
    """Read explicit same-item citation numbers, never local/raw cross-references."""
    if not _reference_eligible(reference):
        return set()
    if reference.get('field') == 'citations_as_printed':
        children = reference.get('value')
        return set().union(*(reference_pairs(item, printed=True) for item in children)) if isinstance(children, list) else set()

    def supplied_scalar(value):
        return isinstance(value, str) and bool(value) or type(value) in (int, float)

    if supplied_scalar(reference.get('number')):
        numbers = [reference['number']]
    elif isinstance(reference.get('numbers'), list):
        numbers = reference['numbers']
    elif printed and supplied_scalar(reference.get('number_as_printed')):
        numbers = [reference['number_as_printed']]
    else:
        numbers = []
    pairs = set()
    for number in numbers:
        pair = reference_pair({**reference, 'number': number})
        if pair:
            pairs.add(pair)
    return pairs


def has_noncanonical_numbering(number):
    if not isinstance(number, dict):
        return False
    scope = ' '.join(str(number.get(field) or '') for field in ('numbering_scope', 'numbering_scheme', 'status'))
    return (bool(number.get('numbering_system')) or
            number.get('sequence_is_hadith_number') is False or bool(_BAD_NUMBERING.search(scope)))


def record_citation_pairs(record):
    pairs = set()
    for version in record.get('language_versions') or []:
        if isinstance(version, dict):
            for reference in version.get('references') or []:
                pairs.update(reference_pairs(reference))
    for language in ('arabic', 'english'):
        item = counterpart_source_data(record, language)
        if item is None:
            continue
        references = item.get('references')
        for reference in references if isinstance(references, list) else []:
            pairs.update(reference_pairs(reference))
    references = record.get('references') or {}
    items = references.get('items') if isinstance(references, dict) else None
    for reference in items if isinstance(items, list) else []:
        pairs.update(reference_pairs(reference))
    number = record.get('number') or {}
    if isinstance(number, dict):
        # Source-part/column labels and provider IDs are not canonical numbers.
        if not has_noncanonical_numbering(number):
            key, value = collection_key(record.get('book_key')), number_key(number.get('in_book'))
            if key and value is not None:
                pairs.add((key, value))
    return pairs


def split_citation_query(query):
    """Accept an already search-normalized query; return pairs and other text."""
    matches = []
    for key, pattern in _PATTERNS:
        for match in pattern.finditer(query):
            matches.append((match.start(), match.end(), key, number_key(match.group(1))))
    # Prefer the full collection name over an alias nested within the name.
    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    accepted = []
    for item in matches:
        if item[3] is not None and not any(item[0] < previous[1] and previous[0] < item[1] for previous in accepted):
            accepted.append(item)
    if not accepted:
        return [], query
    remaining, previous = [], 0
    for start, end, _, _ in accepted:
        remaining.append(query[previous:start])
        previous = end
    remaining.append(query[previous:])
    text = ' '.join(remaining).strip(' \t\r\n,;،()[]{}')
    pairs = list(dict.fromkeys((key, number) for _, _, key, number in accepted))
    return pairs, text

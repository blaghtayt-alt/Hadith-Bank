"""Read explicit hadith numbers from compact publisher bibliography citations.

Numbers remain publisher-reported references, not independently aligned routes
or canonical editions. Publication years, volume/page locators, commentary
books, ranges, and prose are never promoted to individual hadith numbers.
"""
import re
import unicodedata


# Distinct works stay distinct: al-Nasa'i's Kubra is not his Sunan al-Sughra.
_BOOKS = (
    (('صحيح البخاري',), 'bukhari', 'Sahih al-Bukhari', 'صحيح البخاري'),
    (('صحيح مسلم',), 'muslim', 'Sahih Muslim', 'صحيح مسلم'),
    (('سنن أبي داود', 'سنن أبو داود'), 'abu-dawud', 'Sunan Abi Dawud', 'سنن أبي داود'),
    (('سنن الترمذي', 'جامع الترمذي'), 'tirmidhi', 'Jami al-Tirmidhi', 'جامع الترمذي'),
    (('سنن ابن ماجه',), 'ibn-majah', 'Sunan Ibn Majah', 'سنن ابن ماجه'),
    (('سنن النسائي', 'السنن الصغرى للنسائي'), 'nasai', "Sunan al-Nasa'i", 'سنن النسائي'),
    (('السنن الكبرى للنسائي',), 'nasai-kubra', "Al-Sunan al-Kubra by al-Nasa'i", 'السنن الكبرى للنسائي'),
    (('مسند أحمد', 'مسند الإمام أحمد', 'مسند الإمام أحمد بن حنبل'), 'ahmad', 'Musnad Ahmad', 'مسند أحمد'),
    (('موطأ مالك',), 'malik', 'Muwatta Malik', 'موطأ مالك'),
    (('سنن الدارمي', 'مسند الدارمي'), 'darimi', 'Sunan al-Darimi', 'سنن الدارمي'),
    (('صحيح ابن حبان',), 'ibn-hibban', 'Sahih Ibn Hibban', 'صحيح ابن حبان'),
    (('صحيح ابن خزيمة',), 'ibn-khuzaymah', 'Sahih Ibn Khuzaymah', 'صحيح ابن خزيمة'),
    (('المستدرك على الصحيحين للحاكم', 'المستدرك على الصحيحين', 'المستدرك للحاكم'),
     'hakim', 'Al-Mustadrak by al-Hakim', 'المستدرك على الصحيحين'),
    (('الأدب المفرد', 'الأدب المفرد للبخاري'), 'adab-al-mufrad', 'Al-Adab al-Mufrad', 'الأدب المفرد'),
    (('رياض الصالحين من كلام سيد المرسلين', 'رياض الصالحين'),
     'riyad-as-salihin', 'Riyad as-Salihin', 'رياض الصالحين'),
    (('المعجم الكبير للطبراني',), 'tabarani-kabir', 'Al-Mujam al-Kabir by al-Tabarani', 'المعجم الكبير للطبراني'),
    (('المعجم الأوسط للطبراني',), 'tabarani-awsat', 'Al-Mujam al-Awsat by al-Tabarani', 'المعجم الأوسط للطبراني'),
    (('المعجم الصغير للطبراني',), 'tabarani-saghir', 'Al-Mujam al-Saghir by al-Tabarani', 'المعجم الصغير للطبراني'),
)
_ALIASES = sorted(((alias, key, english, arabic)
                   for aliases, key, english, arabic in _BOOKS for alias in aliases),
                  key=lambda row: len(row[0]), reverse=True)
_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
_PREFIX = re.compile(r'^\s*(?:[-*•]\s*)?(?:[0-9]+\s*[-.)]\s*)?')
_SEPARATOR = re.compile(r'[\s,،.;؛:]*')
_NUMBERS = re.compile(r'[1-9][0-9]*(?:\s*[,،]\s*[1-9][0-9]*)*\Z')
_LOCATION = re.compile(r'(?:[0-9]+\s*/\s*[0-9]+|ص(?:فحة)?\.?\s*[0-9]+)'
                       r'(?:\s*[-–—,،]\s*[0-9]+)*\Z')


def _parse_form(value):
    value = unicodedata.normalize('NFKC', value).translate(_DIGITS)
    return ''.join(c for c in value if unicodedata.category(c) != 'Mn' and c != '\u0640')


def parse_provider_references(bibliography):
    """Return supported compact citations, keeping each original source line.

    Only leading parenthesized citation groups after a known collection title
    are scanned. Encountering an author, publisher, edition, or another title
    stops that line, preventing their later years/pages from becoming numbers.
    Number ranges are intentionally left in the preserved bibliography rather
    than expanded into inferred individual occurrences.
    """
    if not isinstance(bibliography, str):
        return []
    result, seen = [], set()
    for source_line in bibliography.splitlines():
        line = _PREFIX.sub('', _parse_form(source_line), count=1)
        matched = None
        for alias, key, english, arabic in _ALIASES:
            if not line.startswith(alias):
                continue
            suffix = line[len(alias):]
            if suffix and not (suffix[0].isspace() or suffix[0] in '(,،:'):
                continue
            matched = key, english, arabic, suffix
            break
        if matched is None:
            continue
        key, english, arabic, suffix = matched
        position = 0
        while True:
            position = _SEPARATOR.match(suffix, position).end()
            if position >= len(suffix) or suffix[position] != '(':
                break
            close = suffix.find(')', position + 1)
            if close < 0:
                break
            group = suffix[position + 1:close].strip()
            if _NUMBERS.fullmatch(group):
                numbers = re.split(r'\s*[,،]\s*', group)
            elif _LOCATION.fullmatch(group):
                numbers = []
            else:
                break
            for number in numbers:
                identity = (key, number, source_line)
                if identity in seen:
                    continue
                seen.add(identity)
                result.append({
                    'book_key': key, 'collection': english, 'collection_ar': arabic,
                    'number': number, 'numbering_scheme': 'publisher_bibliography',
                    'scope': 'publisher_entry', 'source_citation': source_line,
                })
            position = close + 1
    return result


def format_citation(reference, language='en'):
    """Format a parsed reference for display after its counterpart narration."""
    if language == 'ar':
        return '[' + reference['collection_ar'] + '، رقم ' + reference['number'] + ']'
    return '[' + reference['collection'] + ' no. ' + reference['number'] + ']'

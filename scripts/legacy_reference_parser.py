"""Parse explicitly written collection/number citations without resolving text identity.

Returned references describe what a supplied document cites.  They are not an
independent verification of a narration, numbering scheme, or Arabic alignment.
"""
import re
import unicodedata

COLLECTIONS = {
    'bukhari': ('Sahih al-Bukhari', r'(?:Ṣaḥīḥ\s+|Sahih\s+|صحیح\s+|صحيح\s+)?(?:al[-\s]*)?(?:Bukh[aā]r[iīy](?:y)?|Buxoriy|Бухорий|Бухари|بخاري|بخاری|البخاري|ブハーリー|ブハリ|布哈里|बुख़ारी|बुखारी)'),
    'muslim': ('Sahih Muslim', r'(?:Ṣaḥīḥ\s+|Sahih\s+|صحیح\s+|صحيح\s+)?(?:Muslim|Муслим|مسلم|ムスリム|穆斯林|मुस्लिम)'),
    'abu-dawud': ('Sunan Abi Dawud', r'(?:Sunan\s+|سنن\s+)?(?:Ab[uūīi][\s-]+D[aā][wv][uū][uū]?d|Abu\s+Dovud|Abu\s+Dawood|أبو داود|أبي داود|ابی داود|ابو\s?داوود|ابوداود|アブー[・＝]?ダーウード|アブー[・＝]?ダーウド|艾布[·・]?达伍德|अबी दाऊद|अबू दाऊद)'),
    'tirmidhi': ('Jami al-Tirmidhi', r'(?:J[aā]mi[ʿ’\x27]?\s+|Sunan\s+|جامع\s+|سنن\s+)?(?:al[-\s]*)?(?:Tirmi[dt]h?[iīy](?:y)?|Tirmizdi|Termiziy|Термизий|الترمذي|ترمذي|ترمذی|アッ[＝・]?ティルミズィー|ティルミズィー|提尔密济|铁尔密济|तिर्मिज़ी|तिर्मिजी)'),
    'ibn-majah': ('Sunan Ibn Majah', r'(?:Sunan\s+|سنن\s+)?(?:Ibn[\s-]*M[aāo]j(?:ah|a|o|ه)|Ибн Можа|ابن ماجه|ابن ماجة|ابن ماجہ|イブン[・＝]?マージャ|伊本[·・]?马哲|इब्न माजा|इब्न माजह)'),
    'nasai': ('Sunan al-Nasai', r'(?:Sunan\s+|سنن\s+)?(?:al[-\s]*)?(?:Nas[aā][ʾ’\x27]?[iīy]|Nasoiy|النسائي|نسائي|نسائی|アン[＝・]?ナサーイー|ナサーイー|奈萨仪|नसाई)'),
    'ahmad': ('Musnad Ahmad', r'(?:Musnad\s+|مسند\s+)?(?:Aḥmad|Ahmad|Ahmed|Aḥmed|Аҳмад|أحمد|احمد|アフマド|艾哈迈德|अहमद)'),
    'malik': ('Muwatta Malik', r'(?:al[-\s]*)?(?:Muwaṭṭa[ʾ’\x27]?\s*(?:M[aā]lik)?|Muwatta\s*(?:Malik)?|موطأ\s*(?:مالك)?|موطأ|ムワッタ)'),
    'darimi': ('Sunan al-Darimi', r'(?:Sunan\s+|سنن\s+)?(?:al[-\s]*)?(?:D[aā]rim[iīy]|الدارمي|دارمي|ダーリミー|达里米)'),
    'ibn-hibban': ('Sahih Ibn Hibban', r'(?:Ṣaḥīḥ\s+|Sahih\s+|صحيح\s+)?(?:Ibn[\s-]+[ḤH]ibb[aā]n|ابن حبان|イブン[・＝]?ヒッバーン)'),
    'hakim': ('Al-Mustadrak', r'(?:al[-\s]*)?(?:[ḤH][aā]kim|Ҳоким|Mustadrak|الحاكم|المستدرك|ハーキム|ムスタドラク)'),
    'tabarani': ('Al-Tabarani', r'(?:al[-\s]*)?(?:[ṬT]abar[aā]n[iī]|الطبراني|طبراني|タバラーニー)'),
}

_PUNCT = r'[\s\u3000:：,،#№.\[\]（）()【】』」»–—-]*'
_BIB_TITLE = r'(?:(?:tuyển tập|bộ|kalipunang)\s+(?:Sahih|Jami|Sunan)|[«『「](?:Саҳиҳ|Сунан|Жомеъ|Жоме|真正集|ジャーミウ|スナン)[»』」])'
_SEP = (r'(?:の?\s*[『「][^』」\n]{1,40}[』」])?' + _PUNCT +
        r'(?:' + _BIB_TITLE + _PUNCT + r')?' +
        r'(?:(?:had[iī]th|hadis|no\.?|number|حديث|حدیث|رقم|番号|हदीस|số|bilang)\s*[:：#№.]?\s*)?')
# Unicode decimal digits include mixed-width citations such as アフマド1４８1.
_NUMBER = r'\d+(?:[a-z])?(?:\s*[–—/-]\s*\d+(?:[a-z])?)?(?!\d)'
_PATTERNS = [(key, title, re.compile(alias + _SEP + '(' + _NUMBER + ')', re.I))
             for key, (title, alias) in COLLECTIONS.items()]


def ascii_number(value):
    return ''.join(str(unicodedata.digit(c)) if c.isdigit() else c for c in value).replace(' ', '')


def _nfc_with_offsets(text):
    """Match decomposed published spellings while retaining ORIGINAL offsets."""
    chars, starts, ends = [], [], []
    pos = 0
    while pos < len(text):
        end = pos + 1
        while end < len(text) and unicodedata.combining(text[end]):
            end += 1
        normalized = unicodedata.normalize('NFC', text[pos:end])
        chars.extend(normalized)
        starts.extend([pos] * len(normalized))
        ends.extend([end] * len(normalized))
        pos = end
    return ''.join(chars), starts, ends


def parse_references(text):
    """Return ordered {collection, collection_title, number, citation, start,end,scope}.

    Slashed locators are preserved but marked ambiguous, so callers must not turn
    them into an asserted canonical Hadith number. Repeated identical mentions
    retain only their first citation span in this particular supplied string.
    """
    if not isinstance(text, str):
        return []
    normalized, starts, ends = _nfc_with_offsets(text)
    found = []
    for key, title, pattern in _PATTERNS:
        for match in pattern.finditer(normalized):
            number = ascii_number(match.group(1))
            start, end = starts[match.start()], ends[match.end() - 1]
            tail = re.split(r'[。.;；\n]', text[end:end + 55], maxsplit=1)[0]
            variant = bool(re.search(r'異なる文言|別伝|different wording|parallel variant|wording differs|varian', tail, re.I))
            found.append({'collection': key, 'collection_title': title,
                          'number': number, 'citation': text[start:end],
                          'start': start, 'end': end,
                          'scope': 'parallel_variant_citation' if variant else 'source_citation',
                          'numbering_scheme': 'unresolved_volume_page_or_number' if '/' in number else 'as_cited_in_source',
                          'verification': 'transcribed_citation_not_independent_text_alignment'})
            # Consecutive explicitly listed numbers under one collection name.
            # This stops before prose, a named second book, and any new sentence.
            suffix = re.match(r'(?:\s*[,،]\s*\d+[a-z]?)+', normalized[match.end():])
            if suffix:
                for n in re.finditer(r'\d+[a-z]?', suffix.group(0)):
                    nend = ends[match.end() + n.end() - 1]
                    row = dict(found[-1], number=ascii_number(n.group(0)), citation=text[start:nend], end=nend)
                    found.append(row)
    found.sort(key=lambda row: (row['start'], -row['end']))
    result, seen = [], set()
    for row in found:
        key = (row['collection'], row['number'], row['scope'])
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def primary_reference(references):
    """Choose the first explicit non-variant, unambiguous cited number, if any."""
    return next((r for r in references if r.get('scope') != 'parallel_variant_citation'
                 and r.get('numbering_scheme') != 'unresolved_volume_page_or_number'), None)

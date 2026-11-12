"""Conservative language-local boundaries for pinned Fawaz source readings.

``split_source_reading(text, book, language)`` returns None when it supplies no
additional rule, so a caller can use its existing language-specific splitter.
Otherwise it returns ``quotation``, ``notes``, ``spans`` and ``pending_reason``.
Offsets are Python character offsets into the exact input string. Quotation
spans and complementary note spans partition that string without rewriting it.
Multiple quotation spans join only their original substrings, in source order;
they are explicitly marked as disjoint rather than a contiguous quotation.

A pending reading has no asserted quotation and retains the complete original
as source-context notes. It must not hold another language's independently
bounded reading or be presented as an empty/missing source translation. These
rules decide boundaries only, not Prophetic attribution or authenticity.
"""
from __future__ import annotations

import re


# Keep tatweel U+0640: this publisher also uses it as a visible dash delimiting
# compiler parentheticals. Removing it would erase the boundary evidence.
_MARKS = re.compile(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]')
_DIRECTION = '\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069'
_SPACING = '\\s' + _DIRECTION
_AR_PROPHET = re.compile(r'رسول\s+الله|(?:النبي|للنبي|نبيكم|نبينا)\b')
_AR_TRANSMISSION = re.compile(r'و?(?:حدثنا|حدثني|اخبرنا|اخبرني|انبانا|بلغني|سمعت)\b')
_AR_BUKHARI = re.compile(r'قال\s+(?:ابو\s+عبد\s*الله|البخاري)\b')
_AR_MALIK = re.compile(r'قال\s+(?:يحيي\s+قال\s+)?مالك\b')
_AR_TIRMIDHI = (
    ('named_compiler', re.compile(r'قال\s+ابو\s+عيسي\b')),
    ('source_assessment', re.compile(r'(?:و?قال\s+)?(?:هذا|وهذا)\s+حديث\s+(?:حسن|صحيح|غريب)\b')),
    ('parallel_reference_list', re.compile(r'(?:و?قال\s+)?وفي\s+الباب\s+عن\b')),
    ('compiler_parallel_report', re.compile(r'(?:و?قال\s+)?وقد\s+روي\s+هذا\s+الحديث\b')),
)
_EN_BUKHARI = re.compile(
    r"(?:Abu\s+['‘’`]?Abdullah(?:\s*\([^)]{0,60}\))?|(?:Al[- ]?)?Bukhari)\s+(?:said|says|added|explained)\b", re.I)
_EN_MALIK = re.compile(r'\bMalik\s+(?:said|commented|explained|added|was\s+asked|considered)\b', re.I)
_EN_ANAS_IBN_MALIK = re.compile(r'\bAnas\s+(?:(?:ibn|bin)\s+|b\.\s*)$', re.I)
_EN_ABUDAWUD = re.compile(r"Abu\s*D(?:a['’]?w[uū]d|a['’]?ud)\s+(?:said|says)\s*:?", re.I)
_EN_NARRATIVE_OPENING = re.compile(r'^\s*(?:Yahya|Ziyad|Malik)\s+related\s+to\s+me\b', re.I)
_EN_LEGAL_CONTEXT = re.compile(
    r'what\s+he\s+preferred|generally\s+agreed|was\s+asked\s+whether|'
    r'our\s+position|the\s+position\s+with\s+us|the\s+situation\s+with\s+us', re.I)
_UR_MALIK = re.compile(r'(?:امام\s+)?مالک(?:\s*\([^)]{0,60}\))?\s+'
    r'(?:(?:نے\s+)?(?:کہا|فرمایا)|کہتے(?:\s+ہیں)?|سے\s+(?:پوچھا|کہتے))')
_BN_MALIK = re.compile(r'(?:ইমাম\s+)?মালিক(?:\s*\([^)]{0,60}\))?\s*'
    r'(?:বলিয়াছেন|বলেছেন|বলিলেন|বললেন|বলেন)')
_BN_NAMES = {
    'abudawud': re.compile(r'আব[ূু]\s*দা[ঊউ]দ'),
    'tirmidhi': re.compile(r'আব[ূু]\s*[ঈই]সা'),
}
# Recognize cases already owned by the importer's Bengali splitter, so this
# supplemental guard does not replace its earlier, language-local decision.
_BN_EXISTING = {
    'abudawud': re.compile(r'(?:ইমাম\s+)?আব[ূু]\s*দা[ঊউ]দ\s*'
        r'(?:\([^)]{0,30}\)\s*)?(?:বলেন|বলেছেন|বললেন)'),
    'tirmidhi': re.compile(r'(?:ইমাম\s+)?আব[ূু]\s*[ঈই]সা\s*(?:\([^)]{0,30}\)\s*)?'
        r'(?:(?:বলেন|বলেছেন|বললেন|ৰলেন)|(?=[^।!?\n]{0,180}(?:হাসান|সহীহ|সহিহ|গরীব|গারীব|মুরসাল|সমালোচিত)[^।!?\n]{0,40}বলেছেন))'
        r'|আমি\s*\(আব[ূু]\s*[ঈই]সা\)|ইমাম\s+তিরমিযী\s+(?:বলেন|বলেছেন|বললেন)'
        r'|(?<=[।.!?])\s*[-—–]+\s*(?:সহীহ্?|সহিহ|হাসান|যঈফ|সনদ\s+সহীহ)(?=[\s।,;:])'),
}
_NAWAWI_CITATIONS = {
    'ar': re.compile(r'\b(?:رواه|رويناه)\b|\bحديث\s+(?:حسن|صحيح)\b'),
    'en': re.compile(r'\[(?:(?:Al-)?Bukhari|Muslim|At-Tirmidhi|An-Nasai|Abu Dawud|Imam an-Nawawi says:)'
        r'|\b(?:It was related|Related) by\b'
        r'|\bA (?:hasan(?: \(good\))?|good|sound) (?:hadeeth|hadith)\b', re.I),
    'bn': re.compile(r'\[(?:সহীহ্\s+আল-বুখারী|সহীহ্\s+মুসলিম|বুখারী|মুসলিম|তিরমিযী|'
        r'আবূ\s+দাউদ|ইবনে\s+মাজাহ্|হাদীসটি\s+হাসান|এ\s+হাদীসটি\s+হাসান|এটি\s+হচ্ছে\s+হাসান)'),
}
_NAWAWI_VARIANTS = {
    'ar': re.compile(r'وفي\s+رواية\s+(?:لمسلم|غير\s+الترمذي)\s*:'),
    'en': re.compile(r'In another version in Muslim it reads:|Another narration, other than that of Tirmidhi, reads:'),
    'bn': re.compile(r'মুসলিমের বর্ণনার ভাষা হলো এই যে,|তিরমিযী ছাড়া অন্য বর্ণনায় বলা হয়েছেঃ'),
}
_NAWAWI_SECOND_REPORT = {
    'ar': re.compile(r'وعن\s+وابصة\s+بن\s+معبد\b'),
    'en': re.compile(r'And on the authority of Wabisah bin Ma[’\']bad\b'),
    'bn': re.compile(r"ওয়াবেসা ইব্\u200cন মা'বাদ"),
}
_NAWAWI_COMPANION_COMMENT = {
    'ar': re.compile(r'وكان\s+ابن\s+عمر\s+رضي\s+الله\s+عنهما\s+يقول'),
    'en': re.compile(r'And Ibn Umar \(may Allah be pleased with him\) used to say'),
    'bn': re.compile(r'ইবনে উমার \(রাঃ\) বলতেন,'),
}


def _normalized(text):
    result, offsets = [], []
    replacements = str.maketrans('أإآىٱ', 'ااايا')
    for position, char in enumerate(text):
        if not _MARKS.fullmatch(char):
            result.append(char.translate(replacements))
            offsets.append(position)
    return ''.join(result), offsets


def _original_span(offsets, start, end, length):
    return [offsets[start], offsets[end] if end < len(offsets) else length]


def _partition(text, quotations, method, rule, pending_reason=None):
    quotations = [list(span) for span in quotations if span[0] < span[1]]
    notes, cursor = [], 0
    for start, end in quotations:
        if not 0 <= cursor <= start < end <= len(text):
            raise ValueError('Quotation spans must be ordered, disjoint original-text offsets')
        if cursor < start:
            notes.append([cursor, start])
        cursor = end
    if cursor < len(text):
        notes.append([cursor, len(text)])
    spans = {'quotation_spans': quotations, 'notes': notes,
        'method': method, 'rule': rule, 'offset_unit': 'python_unicode_character',
        'coverage': 'exact_original_text_partition', 'disjoint_quotation': len(quotations) > 1,
        'independent_attribution_assessment': False}
    if len(quotations) == 1:
        spans['quotation'] = quotations[0]
    elif not quotations:
        spans['quotation'] = [0, 0]
    return {'quotation': ''.join(text[start:end] for start, end in quotations),
            'notes': [text[start:end] for start, end in notes],
            'spans': spans, 'pending_reason': pending_reason}


def _pending(text, reason, rule):
    return _partition(text, [], 'unsegmented_source_context_v1', rule, reason)


def _whole(text, rule):
    return _partition(text, [[0, len(text)]], 'source_narration_context_preserved_v1', rule)


def _tail(text, boundary, rule):
    if not text[:boundary].strip():
        return _pending(text, 'compiler_material_precedes_established_narration', rule)
    # A source with a compiler cue inside an unclosed quotation needs a source
    # view, not a guessed punctuation repair or a manufactured complete matn.
    if text[:boundary].count('"') % 2:
        return _pending(text, 'compiler_cue_inside_unclosed_source_quotation', rule)
    return _partition(text, [[0, boundary]], 'literal_source_compiler_tail_v2', rule)


def _clause_boundary(text, boundary, *, allow_conjunction=False):
    prefix = text[:boundary]
    visible = prefix.rstrip(' \t\r\n' + _DIRECTION)
    if allow_conjunction and visible.endswith('و'):
        visible = visible[:-1].rstrip(' \t\r\n' + _DIRECTION)
        boundary = len(visible)
    return bool(visible and visible[-1] in '.!?؟۔।"”\')'), boundary


def _remove_glosses(text, original_spans, rule):
    quotation_spans, cursor = [], 0
    for start, end in sorted(original_spans):
        if cursor < start:
            quotation_spans.append([cursor, start])
        cursor = end
    if cursor < len(text):
        quotation_spans.append([cursor, len(text)])
    return _partition(text, quotation_spans, 'explicit_delimited_source_gloss_v1', rule)


def _arabic_bukhari(text, normalized, offsets):
    markers = list(_AR_BUKHARI.finditer(normalized))
    if not markers:
        return None
    # Source6119: an explicitly delimited narrator-name explanation, with the
    # original isnad resuming after its closing dash. No generic dash removal.
    gloss = re.compile(r'(?P<dash>[ـ\-–—])[' + _SPACING + r']*'
        r'قال\s+ابو\s+عبد\s*الله\s+اسمه\s+عبد\s+الله\s+بن\s+ابي\s+عتبة'
        r'[' + _SPACING + r']*(?P=dash)')
    gloss_matches = list(gloss.finditer(normalized))
    if gloss_matches:
        covered = [m for m in markers if any(g.start() <= m.start() < g.end() for g in gloss_matches)]
        if len(covered) != len(markers):
            return _pending(text, 'inline_gloss_and_additional_compiler_material', 'bukhari_delimited_name_gloss')
        ranges = [_original_span(offsets, m.start(), m.end(), len(text)) for m in gloss_matches]
        return _remove_glosses(text, ranges, 'bukhari_delimited_name_gloss')
    # Source313: the bracketed words introduce an alternative isnad. Keeping
    # that source-supplied chain context is different from deleting a gloss.
    alternate = re.compile(r'(?P<dash>[ـ\-–—])[' + _SPACING + r']*'
        r'قال\s+ابو\s+عبد\s*الله\s+او\s+هشام\s+بن\s+حسان\s+عن\s+حفصة'
        r'[^ـ\-–—]{0,100}(?P=dash)')
    if len(markers) == 1 and alternate.search(normalized):
        return _whole(text, 'bukhari_explicit_alternate_isnad_preserved')
    remaining = []
    for marker in markers:
        before, after = normalized[:marker.start()], normalized[marker.end():]
        # Sources89/2291/6341/7367 and similar: compiler introduces a chain.
        # This guard requires nearby transmission wording and no prior matn.
        if (marker.start() < 220 and not _AR_PROPHET.search(before) and '"' not in before
                and _AR_TRANSMISSION.search(after[:180])):
            continue
        remaining.append(marker)
    if not remaining:
        return _whole(text, 'bukhari_initial_or_alternate_chain_preserved')
    marker = remaining[0]
    boundary = offsets[marker.start()]
    safe, boundary = _clause_boundary(text, boundary, allow_conjunction=True)
    if not safe:
        return _pending(text, 'compiler_boundary_not_separate_from_source_narration', 'bukhari_named_compiler')
    return _tail(text, boundary, 'bukhari_named_compiler_after_complete_source_clause')


def _arabic_malik(text, normalized, offsets):
    markers = list(_AR_MALIK.finditer(normalized))
    if not markers:
        return None
    # Source13 names a different Malik, Abu Suhayl's father. It is not evidence
    # that the collection's compiler has started a comment.
    markers = [m for m in markers if not re.match(r'\s+والد\s+ابي\s+سهيل\b', normalized[m.end():])]
    if not markers:
        return _whole(text, 'named_narrator_malik_not_compiler')
    # Source244 explicitly qualifies whether the report is Prophetic. Source
    #1744 has a qualified recollection of the continuation. Do not trim either
    # into a stronger, complete or unqualified attribution.
    for marker in markers:
        after = normalized[marker.end():].lstrip(' \t\r\n' + _DIRECTION)
        if re.match(r'(?:لا\s+ادري|لا\s+احسبه|احسبه|اظنه)\b', after):
            return _pending(text, 'source_attribution_or_continuation_explicitly_qualified', 'malik_uncertain_narration_context')
    marker = markers[0]
    before, after = normalized[:marker.start()], normalized[marker.end():]
    # Do not reinterpret initial compiler speech or an inline name as a tail.
    if not before.strip(' \t\r\nو' + _DIRECTION) or not re.match(
            r'^[' + _SPACING + r']*(?:و?حدث(?:نا|ني)|و?اخبر(?:نا|ني)|و?روي|عن)\b', normalized):
        return _pending(text, 'source_compiler_discussion_or_initial_chain_needs_local_spans', 'malik_initial_context')
    # Source1851's unbracketed uqiya explanation is followed by a resumption of
    # the same first-person narration. A prefix-only split would discard it.
    if re.match(r'\s+والاوقية\s+اربعون\s+درهما\b', after):
        return _pending(text, 'unbracketed_inline_gloss_with_resumed_narration', 'malik_uqiya_context')
    # A second transmitted report after a compiler cue belongs to its own
    # bounded source span, not automatically to commentary or the first matn.
    if _AR_TRANSMISSION.search(after[:150]) or re.match(r'\s+(?:قال\s+)?(?:نافع|ابن\s+شهاب|هشام)\b', after):
        return _pending(text, 'compiler_cue_introduces_or_resumes_narrational_context', 'malik_following_narration')
    boundary = offsets[marker.start()]
    safe, boundary = _clause_boundary(text, boundary, allow_conjunction=True)
    if not safe:
        return _pending(text, 'compiler_boundary_not_separate_from_source_narration', 'malik_named_compiler')
    return _tail(text, boundary, 'malik_comment_after_complete_source_clause')


def _english(text, book):
    pattern = _EN_BUKHARI if book == 'bukhari' else _EN_MALIK
    markers = list(pattern.finditer(text))
    if book == 'malik':
        # Anas ibn/bin/b. Malik is an explicitly named narrator. His speech is
        # not a compiler boundary merely because the last name is shared.
        markers = [marker for marker in markers
                   if not _EN_ANAS_IBN_MALIK.search(text[:marker.start()])]
    if not markers:
        return None
    if book == 'malik':
        # Source1851 explicitly brackets this explanation and resumes the
        # narrator afterwards. Keep both narration spans and the exact gloss.
        gloss = re.compile(r'\(Malik explained that an uqiya was forty dirhams\.\)', re.I)
        glosses = list(gloss.finditer(text))
        if glosses and all(any(g.start() <= m.start() < g.end() for g in glosses) for m in markers):
            return _remove_glosses(text, [[m.start(), m.end()] for m in glosses], 'malik_explicit_parenthetical_uqiya_gloss')
        first = markers[0]
        if (not _EN_NARRATIVE_OPENING.match(text) or _EN_LEGAL_CONTEXT.search(text[:first.start()])
                or first.start() < 80):
            return _pending(text, 'mixed_compiler_discussion_requires_language_local_narration_spans', 'malik_english_source_context')
        if re.search(r'When\s+Allah\s+is\s+angry\s+with\s+a\s+slave', text[:first.start()], re.I):
            return _pending(text, 'source_attribution_or_continuation_explicitly_qualified', 'malik_english_qualified_continuation')
    first = markers[0]
    boundary = first.start()
    if boundary and text[boundary - 1] == '(':
        boundary -= 1
    safe, boundary = _clause_boundary(text, boundary)
    if not safe:
        return _pending(text, 'compiler_boundary_not_separate_from_source_narration', book + '_english_named_compiler')
    return _tail(text, boundary, book + '_english_named_compiler_after_complete_source_clause')


def _abudawud(text, language):
    if language == 'en':
        marker = _EN_ABUDAWUD.search(text)
        if marker is None:
            return None
        # Source5210: the compiler explicitly transmits the Prophetic
        # attribution. Cutting here would leave only the narrator heading.
        if (marker.start() < 200 and re.match(r'^\s*Narrated\b[^:]{1,160}:\s*$', text[:marker.start()], re.I)
                and re.search(r'\btraced\s+this\s+(?:tradition|hadith)\s+back\s+to\s+the\s+Prophet\b',
                              text[marker.end():marker.end() + 220], re.I)):
            return _whole(text, 'abudawud_compiler_transmitted_attribution_preserved')
        boundary = marker.start()
        if boundary and text[boundary - 1] in '([':
            boundary -= 1
        safe, boundary = _clause_boundary(text, boundary)
        if not safe:
            return _pending(text, 'compiler_boundary_not_separate_from_source_narration', 'abudawud_english_named_compiler')
        return _tail(text, boundary, 'abudawud_english_named_compiler_after_complete_source_clause')
    if language == 'ar':
        normalized, offsets = _normalized(text)
        # Source2306 gives Ibn Shihab's expressly personal ruling after the
        # narrated account. This literal opinion opening is not a general
        # rule that would delete Ibn Shihab from an isnad.
        marker = re.search(r'قال\s+ابن\s+شهاب\s+ولا\s+اري\s+باسا\s+ان\s+تتزوج\s+حين\s+وضعت\b', normalized)
        if marker is None:
            return None
        boundary = offsets[marker.start()]
        safe, boundary = _clause_boundary(text, boundary)
        if not safe:
            return _pending(text, 'scholarly_opinion_boundary_needs_source_review', 'abudawud_ibn_shihab_opinion')
        return _tail(text, boundary, 'abudawud_explicit_ibn_shihab_personal_opinion')
    return None


def _malik_other_language(text, language):
    pattern = _UR_MALIK if language == 'ur' else _BN_MALIK
    markers = list(pattern.finditer(text))
    if language == 'ur':
        # Anas ibn Malik and the father of Abu Suhayl are narrators, not this
        # collection's compiler. A shared name is not an editorial boundary.
        if re.match(r'^\s*مالک\s+بن\s+ابی\s+عامر\b', text) and not re.search(r'امام\s+مالک', text):
            return _whole(text, 'urdu_named_narrator_malik_not_compiler') if markers else None
        markers = [m for m in markers if not re.search(r'(?:بن|ابن)\s*$', text[max(0, m.start() - 20):m.start()])]
        fallback = re.search(r'امام\s+مالک\b', text)
    else:
        if re.search(r'পিতা\s+মালিক', text[:180]) and not re.search(r'ইমাম\s+মালিক', text):
            return _whole(text, 'bengali_named_narrator_malik_not_compiler') if markers else None
        markers = [m for m in markers if not re.search(r'(?:ইবন|ইবনে|বিন)\s*$', text[max(0, m.start() - 25):m.start()])]
        fallback = re.search(r'ইমাম\s+মালিক|মালিকের\s+মতে', text)
    if not markers:
        return _pending(text, 'visible_compiler_reference_has_no_supported_local_boundary',
                        'malik_' + language + '_compiler_reference') if fallback else None
    first = markers[0]
    after = text[first.end():]
    # These source-language qualifiers or transmission cues may introduce a
    # report, preserve uncertain attribution, or resume narration after a
    # comment. They are never resolved by borrowing Arabic/English offsets.
    uncertain = (re.search(r'معلوم\s+نہیں|علم\s+نہیں|گمان|خیال|مجھے\s+پہنچا|سے\s+روایت|رسول\s+اللہ|نبی', after[:240])
                 if language == 'ur' else
                 re.search(r'জানা\s+না[ইইঁ]|জানা\s+নেই|মনে\s+হয়|রেওয়ায়ত|রাসূল|রাসুল|নবী|উকিয়া', after[:260]))
    if uncertain:
        return _pending(text, 'compiler_cue_may_qualify_or_continue_source_narration', 'malik_' + language + '_qualified_context')
    before = text[:first.start()]
    if (first.start() < 80 or (language == 'bn' and re.fullmatch(r'\s*রেওয়ায়ত\s+[০-৯0-9]+[.।]?\s*', before))):
        return _pending(text, 'initial_compiler_or_isnad_context_needs_local_spans', 'malik_' + language + '_initial_context')
    safe, boundary = _clause_boundary(text, first.start())
    if not safe:
        return _pending(text, 'compiler_boundary_not_separate_from_source_narration', 'malik_' + language + '_named_compiler')
    return _tail(text, boundary, 'malik_' + language + '_comment_after_complete_source_clause')


def _bengali_residual_context(text, book):
    name = _BN_NAMES[book].search(text)
    if name is None:
        return None
    known = _BN_EXISTING[book].search(text)
    if known is not None and known.start() <= name.start():
        return None
    normalized, offsets = _normalized(text)
    arabic = re.search(r'قال\s+ابو\s+' + ('داود' if book == 'abudawud' else 'عيسي') + r'\b', normalized)
    if arabic is not None and offsets[arabic.start()] < name.start():
        return None
    # Source4356 has the publisher's literal spelling বরেন. It is an explicit
    # compiler statement after a complete sentence, not a normalized repair.
    if book == 'abudawud':
        spelling = re.search(r'(?:ইমাম\s+)?আব[ূু]\s*দা[ঊউ]দ\s*(?:\([^)]{0,30}\)\s*)?বরেন\b', text)
        if spelling is not None and spelling.start() <= name.start():
            safe, boundary = _clause_boundary(text, spelling.start())
            if safe:
                return _tail(text, boundary, 'bengali_literal_compiler_statement_spelling_variant')
    # Audited residuals include long footnote discussions (Abu Dawud229/821),
    # compiler-introduced isnads (978/981/2218/3781), and a different narrator's
    # kunyah (Tirmidhi3452). The visible name alone proves none of their matn
    # boundaries. Keep the complete language's source context available.
    return _pending(text, 'named_source_reference_requires_bengali_local_boundary_review',
                    book + '_bengali_residual_named_context')


def _nawawi(text, language):
    if language not in _NAWAWI_CITATIONS:
        return None
    normalized, offsets = _normalized(text) if language == 'ar' else (text, list(range(len(text))))

    def position(match):
        return offsets[match.start()]

    def citation_start(match):
        boundary = position(match)
        if boundary and text[boundary - 1] == '[':
            boundary -= 1
        bracketed = text[boundary:boundary + 1] == '['
        # Literal <br> separators are source markup next to the citation, not
        # part of the narration. Preserve them in the exact source note.
        separator = re.search(r'<br\s*/?>\s*$', text[:boundary], re.I)
        if separator:
            boundary = separator.start()
        return boundary, bracketed

    companion = _NAWAWI_COMPANION_COMMENT[language].search(normalized)
    if companion:
        boundary = position(companion)
        safe, boundary = _clause_boundary(text, boundary)
        if not safe:
            return _pending(text, 'companion_comment_boundary_requires_local_review', 'nawawi_companion_comment')
        return _partition(text, [[0, boundary]], 'literal_source_companion_comment_v1',
                          'nawawi_40_separately_attributed_companion_advice')

    citations = list(_NAWAWI_CITATIONS[language].finditer(normalized))
    if not citations:
        return None
    boundary, bracketed = citation_start(citations[0])
    if not text[:boundary].strip():
        return _pending(text, 'source_citation_precedes_established_narration', 'nawawi_source_citation')
    if not bracketed and not _clause_boundary(text, boundary)[0]:
        return _pending(text, 'source_citation_boundary_requires_local_review', 'nawawi_source_citation')

    second = _NAWAWI_SECOND_REPORT[language].search(normalized, citations[0].end())
    if second:
        # Entry27 already contains two distinct reports in this source unit.
        # Keep its internal citation and second isnad intact; do not join the
        # reports across a removed span or inflate it to two provider entries.
        final = next((match for match in citations if match.start() >= second.end()), None)
        if final is None:
            return _pending(text, 'multiple_reports_have_no_supported_final_boundary', 'nawawi_two_source_reports')
        ending, _ = citation_start(final)
        second_start = position(second)
        result = _partition(text, [[0, ending]], 'source_multiple_reports_preserved_v1',
                            'nawawi_27_two_separately_attributed_reports')
        reports = [[0, boundary], [second_start, ending]]
        result.update(source_report_count=2, source_report_boundaries=reports)
        result['spans'].update(source_report_count=2, source_report_boundaries=reports,
                              retained_internal_citation_spans=[[boundary, second_start]])
        return result

    variant = _NAWAWI_VARIANTS[language].search(normalized, citations[0].end())
    if variant:
        # Entries5/19 explicitly resume a source-labelled alternative wording.
        # Preserve that label and all variant text, including source defects;
        # only the intervening source citation/assessment becomes a note.
        beginning = position(variant)
        final = next((match for match in citations if match.start() >= variant.end()), None)
        ending = citation_start(final)[0] if final else len(text)
        return _partition(text, [[0, boundary], [beginning, ending]],
                          'source_labelled_variant_citation_partition_v1', 'nawawi_explicit_source_variant')

    # Some pinned readings have a missing opening quote or closing citation
    # bracket. Their independent source-citation boundary is still explicit;
    # retaining both exact partitions does not repair that punctuation.
    return _partition(text, [[0, boundary]], 'literal_source_citation_tail_v1', 'nawawi_own_language_citation')


def split_source_reading(text, book, language):
    """Return a supplemental exact-span result, or None for the caller's rules.

    Supported supplemental decisions concern Arabic Tirmidhi and Arabic/English
    Bukhari/Malik, narrow Abu Dawud source cases, and independently recognized
    Urdu/Bengali compiler contexts, and the Nawawi source's Arabic/English/
    Bengali citations and explicitly qualified report/variant structure. This
    function never transfers boundaries from one source language to another.
    """
    if not isinstance(text, str):
        raise TypeError('Source reading must be an exact source string')
    if not text:
        return None
    if book == 'nawawi':
        return _nawawi(text, language)
    if book == 'malik' and language in ('ur', 'bn'):
        return _malik_other_language(text, language)
    if language == 'bn' and book in _BN_NAMES:
        return _bengali_residual_context(text, book)
    if book == 'abudawud':
        return _abudawud(text, language)
    if language == 'en' and book in ('bukhari', 'malik'):
        return _english(text, book)
    if language != 'ar' or book not in ('bukhari', 'malik', 'tirmidhi'):
        return None
    normalized, offsets = _normalized(text)
    if book == 'bukhari':
        return _arabic_bukhari(text, normalized, offsets)
    if book == 'malik':
        return _arabic_malik(text, normalized, offsets)
    matches = [(m.start(), kind, m) for kind, pattern in _AR_TIRMIDHI
               if (m := pattern.search(normalized))]
    if not matches:
        return None
    _, kind, match = min(matches, key=lambda item: item[0])
    return _tail(text, offsets[match.start()], 'tirmidhi_' + kind)

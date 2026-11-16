"""Opt-in *presentation* of anchored source OCR uncertainty, never a source edit.

The independently pinned closed-application authority is separate from any
mutable record/projection. Every opted-in record must match the approved parent,
text-record ID, body digest, and complete annotation disposition map. Never
confuse a record's own digest with an independent attestation.
Source offsets are Unicode code points (not UTF-8 bytes or JS UTF-16 units).
This implementation does not assert review, release or publication eligibility.
"""
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from html import escape
import re

SCHEMA = 'source_uncertainty_projection.v1'
WARNING = '(OCR wasn’t clear)'
AUTHORITY_SHA256 = 'a67c25a06be950798a45050a52a68c0dd77a6bc73389a184953eeee011a2c895'
HEX = re.compile(r'[a-f0-9]{64}\Z')
IDENTITY = re.compile(r'[A-Za-z0-9][A-Za-z0-9:._-]{0,159}\Z')
MARKER = re.compile(r'⟦[^⟦⟧\r\n]{1,160}⟧')
KINDS = ('accepted_uncertain_reading', 'unfilled_source_gap', 'unreviewed_source_gap')
PROJECTION_FIELDS = {'schema', 'record_id', 'text_record_id', 'field', 'expected_body_sha256', 'annotations'}
ANNOTATION_FIELDS = {'issue_id', 'start', 'end', 'span_sha256', 'kind'}


def digest(value):
    try:
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
    except UnicodeEncodeError:
        _fail()


@lru_cache(maxsize=1)
def _approved_authority():
    """Build-code trust anchor, independent of material records and registry.

    Exact digest is pinned in this source module. The JSON is solely a closed
    owner-application allowlist: 14 parent/text IDs and 18 metadata tuples.
    Replacing either artifact requires an explicit code/trust review.
    """
    source = Path(__file__).with_name('source_uncertainty_authority.json')
    try:
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != AUTHORITY_SHA256:
            _fail()
        data = json.loads(raw)
        if data['schema'] != 'source_uncertainty_authority.v1' or len(data['bindings']) != 14:
            _fail()
        return data['bindings']
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        _fail()


def _well_formed(text):
    return isinstance(text, str) and all(not 0xD800 <= ord(c) <= 0xDFFF for c in text)


def _approved_binding(record_id, text, projection, sorted_annotations):
    """Do not treat a hash provided by the candidate as approval."""
    trusted = _approved_authority().get(record_id)
    if (trusted is None or projection['text_record_id'] != trusted['text_record_id'] or
            projection['expected_body_sha256'] != trusted['body_sha256'] or
            digest(text) != trusted['body_sha256'] or sorted_annotations != trusted['annotations']):
        _fail()


def _fail():
    raise ValueError('Invalid source-bound uncertainty projection; quotation withheld')


def checked_source_identity(record, projection):
    """Bind the independently approved text ID to its real caller identities.

    The parent record is checked by validated_parts. When the canonical row or
    normalized source carries a declared source text-record ID, do not let it
    disagree with the closed decision. No heuristic number/title identity join.
    """
    if not isinstance(record, dict) or not isinstance(projection, dict):
        _fail()
    expected = projection.get('text_record_id')
    source = record.get('source') or {}
    number = record.get('number') or {}
    if not isinstance(source, dict) or not isinstance(number, dict):
        _fail()
    declared = [number.get('source_entry_id'), source.get('source_text_record_id')]
    if 'original_metadata' in source:
        original = source['original_metadata']
        if not isinstance(original, dict):
            _fail()
        declared.append(original.get('source_text_record_id'))
    if any(item is not None and item != expected for item in declared):
        _fail()


def validated_parts(text, projection, *, record_id, expected_body_sha256=None, glyphs=None):
    """Return reversible ordered display parts; reject any unverifiable opt-in.

    ``expected_body_sha256`` when supplied MUST originate outside the supplied
    record/projection (e.g. the pinned independent source application receipt).
    """
    if (not _well_formed(text) or not _well_formed(record_id) or not record_id or
            not isinstance(projection, dict) or set(projection) != PROJECTION_FIELDS or
            projection['schema'] != SCHEMA or projection['record_id'] != record_id or
            not _well_formed(projection['text_record_id']) or not IDENTITY.fullmatch(projection['text_record_id']) or
            projection['field'] != 'text.translation' or
            not isinstance(projection['expected_body_sha256'], str) or
            not HEX.fullmatch(projection['expected_body_sha256']) or
            digest(text) != projection['expected_body_sha256'] or
            (expected_body_sha256 is not None and projection['expected_body_sha256'] != expected_body_sha256) or
            not isinstance(projection['annotations'], list) or not projection['annotations'] or
            glyphs):
        _fail()
    checked, seen = [], set()
    for note in projection['annotations']:
        if not isinstance(note, dict) or set(note) != ANNOTATION_FIELDS:
            _fail()
        start, end, issue, kind, span_hash = (note[k] for k in ('start', 'end', 'issue_id', 'kind', 'span_sha256'))
        if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text) or
                not _well_formed(issue) or not issue or len(issue) > 160 or issue in seen or
                kind not in KINDS or not isinstance(span_hash, str) or not HEX.fullmatch(span_hash) or
                digest(text[start:end]) != span_hash):
            _fail()
        seen.add(issue)
        if (kind.endswith('source_gap') and not MARKER.fullmatch(text[start:end]) or
                kind == 'accepted_uncertain_reading' and MARKER.search(text[start:end])):
            _fail()
        checked.append({'start': start, 'end': end, 'issue_id': issue, 'kind': kind})
    checked.sort(key=lambda n: (n['start'], n['end']))
    if any(a['end'] > b['start'] for a, b in zip(checked, checked[1:])):
        _fail()
    _approved_binding(record_id, text, projection, [
        {**note, 'span_sha256': digest(text[note['start']:note['end']])} for note in checked])
    # A marker of any shape in the original must not leak into a displayed quote.
    # The specific bracketed marker is retained unchanged in raw JSON/audit.
    for marker in re.finditer(r'⟦[^⟧]*⟧|⟦|⟧', text):
        if not any(n['start'] == marker.start() and n['end'] == marker.end() and
                   n['kind'].endswith('source_gap') for n in checked):
            _fail()
    parts, cursor = [], 0
    for n in checked:
        if cursor < n['start']:
            parts.append({'kind': 'quotation', 'start': cursor, 'end': n['start'], 'source_text': text[cursor:n['start']]})
        value = text[n['start']:n['end']]
        parts.append({**n, 'kind': 'gap' if n['kind'].endswith('source_gap') else 'quotation', 'source_text': value})
        parts.append({'kind': 'note', 'start': n['start'], 'end': n['end'], 'issue_id': n['issue_id'],
                      'text': WARNING, 'review_status': ('unreviewed' if n['kind'] == 'unreviewed_source_gap'
                                                       else 'owner_decision_applied')})
        cursor = n['end']
    if cursor < len(text):
        parts.append({'kind': 'quotation', 'start': cursor, 'end': len(text), 'source_text': text[cursor:]})
    if ''.join(part['source_text'] for part in parts if part['kind'] != 'note') != text:
        _fail()
    return parts


def exact_quotation(parts):
    """Return full quotation only if no source word is unavailable.

    Silently joining text across a gap can fabricate an adjacent word. Refuse
    incomplete quotations instead of suggesting that the copy is gap-free.
    """
    if any(p['kind'] == 'gap' for p in parts):
        raise ValueError('Cannot copy an incomplete source quotation with unresolved gaps')
    return ''.join(p['source_text'] for p in parts if p['kind'] == 'quotation')


def quotation_fragments(parts):
    """Visible narration chunks separated by source gaps; no OCR labels/IDs.

    Search positions must not bridge an unresolved source gap. Notes on
    accepted uncertain words do not separate otherwise contiguous quotations.
    """
    chunks = ['']
    for part in parts:
        if part['kind'] == 'quotation':
            chunks[-1] += part['source_text']
        elif part['kind'] == 'gap':
            chunks.append('')
        elif part['kind'] != 'note':
            _fail()
    return [value for value in chunks if value]


def exact_source_reconstruction(parts):
    """Audit-only reversibility. NOT a safe rendered or copied quotation."""
    return ''.join(p['source_text'] for p in parts if p['kind'] != 'note')


def source_parts_html(parts, *, language, direction='auto', line_breaks=False):
    """Source-bound display with every warning/gap outside ``.quotation``.

    Works as static HTML and embedded Markdown HTML; never use raw text inside
    attributes. Gap markers remain in an audited record, never in visual text.
    """
    if not isinstance(language, str) or not isinstance(direction, str) or direction not in ('auto', 'ltr', 'rtl'):
        _fail()
    result = ['<div class="source-reading" lang="' + escape(language, quote=True) +
              '" dir="' + direction + '">']
    for part in parts:
        start, end = part['start'], part['end']
        bound = f' data-source-start="{start}" data-source-end="{end}"'
        if part['kind'] == 'quotation':
            value = escape(part['source_text'])
            # Keep the original LF only: pre-wrap + <br> would double it.
            # line_breaks is retained for API compatibility with Markdown.
            result.append('<span class="quotation source-quote"' + bound + '>' + value + '</span>')
        elif part['kind'] == 'gap':
            result.append('<span class="source-gap" role="note"' + bound +
                          '>[Source gap: exact reading unavailable]</span>')
        elif part['kind'] == 'note':
            # The stable issue ID remains in the private projection, not in
            # render-source or casual copyable markup (some held IDs embed
            # the raw internal source-gap marker).
            result.append('<span class="source-uncertainty" role="note" data-issue-hash="' +
                          digest(part['issue_id']) + '"' + bound + '>' + WARNING + '</span>')
            if part['review_status'] == 'unreviewed':
                result.append('<span class="source-unreviewed" role="note">Separate unresolved hold</span>')
        else:
            _fail()
    result.append('</div>')
    return ''.join(result)

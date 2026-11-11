"""Resolve explicit publisher identities without guessing canonical hadith numbers.

An identity links a bank occurrence to a publisher entry. It does not certify
that its Arabic revision, full narration, or translation boundaries are equal.
Only primary/selected source fields are inspected; commentary and other cited
works cannot assign the identity of the current quotation.
"""
import re
from urllib.parse import parse_qs, urlsplit


_POSITIVE_ID = re.compile(r'[1-9][0-9]*\Z')
_PAGE = re.compile(r'/[A-Za-z]{2,3}(?:-[A-Za-z0-9]+)*/browse/hadith/([1-9][0-9]*)/?\Z')
_API = '/api/v1/hadeeths/one'
_SELECTED_URL_FIELDS = (
    ('sourceUrl',),
    ('publication', 'url'),
    ('source_binding', 'sourceURL'),
    ('selected_parent', 'sourceURL'),
    ('selected_parent', 'source_url'),
    ('selected_parent', 'url'),
    ('reference_register_entry', 'sourceURL'),
)


def _positive_id(value):
    # bool is an int subclass; provider IDs must not accept True as entry 1.
    if type(value) is int:
        return str(value) if value > 0 else None
    return value if isinstance(value, str) and _POSITIVE_ID.fullmatch(value) else None


def _at(value, path):
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _url_ids(value):
    if not isinstance(value, str):
        return []
    try:
        parts = urlsplit(value.strip())
        if (parts.scheme not in ('http', 'https') or parts.hostname != 'hadeethenc.com'
                or parts.username is not None or parts.password is not None
                or parts.port not in (None, 443 if parts.scheme == 'https' else 80)):
            return []
        page = _PAGE.fullmatch(parts.path)
        if page:
            return [page.group(1)]
        if parts.path.rstrip('/') != _API:
            return []
        # Repeated differing IDs are retained as a conflict, never first-wins.
        return [identifier for raw in parse_qs(parts.query).get('id', [])
                if (identifier := _positive_id(raw)) is not None]
    except (ValueError, UnicodeError):
        return []


def provider_identity(record):
    """Return a linked/conflict/absent HadeethEnc identity for a projected record.

    Raw registered-material records are also accepted: their source metadata
    becomes source.original_metadata in the generated projection. In either
    representation, the bank's generic provider_entry_id is trusted only when
    book_key is hadeethenc. For other books it may be a local lesson field ID.
    """
    evidence = {}

    def add(path, identifiers):
        for identifier in identifiers:
            if identifier is not None:
                evidence.setdefault(identifier, []).append('/' + '/'.join(path))

    if isinstance(record, dict):
        if record.get('book_key') == 'hadeethenc':
            for path in (('provider_entry_id',), ('number', 'source_entry_id')):
                add(path, [_positive_id(_at(record, path))])

        # These are the current source's primary locator fields, not references
        # nested in explanations or in an unrelated source's comparison text.
        for prefix in (('source',), ('source', 'original_metadata')):
            for key in ('url', 'record_url'):
                path = prefix + (key,)
                add(path, _url_ids(_at(record, path)))
            for suffix in _SELECTED_URL_FIELDS:
                path = prefix + ('historical_metadata',) + suffix
                add(path, _url_ids(_at(record, path)))

    candidates = sorted(evidence, key=int)
    status = 'linked' if len(candidates) == 1 else 'conflict' if candidates else 'absent'
    return {
        'provider': 'hadeethenc',
        'id': candidates[0] if status == 'linked' else None,
        'basis': sorted({path for paths in evidence.values() for path in paths}),
        'status': status,
        'candidates': candidates,
    }


def provider_id(record):
    """Return the unambiguous publisher entry ID, or None."""
    return provider_identity(record)['id']

"""Add source-preserving Arabic/English parallels from verified local exports.

The resolver never translates, replaces an occurrence, or joins by number alone.
Primary publisher IDs identify publisher versions; an ID inherited from a parent
document additionally requires quotation alignment. Other joins require unique
source-text alignment, with cited collection numbers used only as corroboration.
"""
from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sqlite3
import unicodedata

from counterpart_identity import provider_identity
from counterpart_references import parse_provider_references
from citation_search import reference_pair, reference_pairs
from reviewed_counterparts import ReviewedCounterpartResolver, MANIFEST as REVIEWED_MANIFEST
from counterpart_quality import apply_quality_policy, load_quality_policy

MANIFEST = 'sources/counterparts/hadeethenc/manifest.json'
SCHEMA = 'hadith-bank-counterpart-link-v1'
BOOK_NAMES = {
    'bukhari': ('Sahih al-Bukhari', 'صحيح البخاري'),
    'muslim': ('Sahih Muslim', 'صحيح مسلم'),
    'abu-dawud': ('Sunan Abi Dawud', 'سنن أبي داود'),
    'tirmidhi': ('Jami al-Tirmidhi', 'جامع الترمذي'),
    'nasai': ('Sunan al-Nasai', 'سنن النسائي'),
    'ibn-majah': ('Sunan Ibn Majah', 'سنن ابن ماجه'),
    'ahmad': ('Musnad Ahmad', 'مسند أحمد'),
    'malik': ('Muwatta Malik', 'موطأ مالك'),
    'darimi': ('Sunan al-Darimi', 'سنن الدارمي'),
    'ibn-hibban': ('Sahih Ibn Hibban', 'صحيح ابن حبان'),
    'riyadh-al-salihin': ('Riyadh al-Salihin', 'رياض الصالحين'),
    'riyad-as-salihin': ('Riyadh al-Salihin', 'رياض الصالحين'),
    'adab-al-mufrad': ('Al-Adab al-Mufrad', 'الأدب المفرد'),
    'hisn-al-muslim': ('Hisn al-Muslim', 'حصن المسلم'),
    'nawawi40': ('Nawawi Forty', 'الأربعون النووية'),
}
ALIASES = {'al-nasai': 'nasai', 'riyad-as-salihin': 'riyadh-al-salihin'}
ARABIC_LETTER_EQUIVALENTS = str.maketrans({'ک': 'ك', 'ی': 'ي'})


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def local(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('Unsafe counterpart source path')
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or path.as_posix() != relative or ':' in relative:
        raise ValueError('Unsafe counterpart source path: ' + relative)
    target = root
    for part in path.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError('Symlink counterpart source path: ' + relative)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('Counterpart source path escapes bank')
    return target


def normalize_quote(value):
    """Normalize only for matching; stored and displayed quotations stay exact."""
    value = unicodedata.normalize('NFKC', value or '').casefold()
    return ''.join(c for c in value if not c.isspace() and c != '\u0640'
                   and unicodedata.category(c)[0] not in ('P', 'M', 'Z')
                   and unicodedata.category(c) != 'Cf')


def normalize_arabic_quote(value):
    """Compare Arabic quotations across Persian keyboard letter variants only.

    This is a matching key, never a source-text correction. Alef maqsura,
    hamza-bearing letters and other distinct Arabic letters remain distinct.
    """
    return normalize_quote(value).translate(ARABIC_LETTER_EQUIVALENTS)


def quote_relation(quotation, full):
    left, right = normalize_quote(quotation), normalize_quote(full)
    if not left or not right:
        return None
    minimum = 16 if re.search(r'[\u3040-\u30ff\u3400-\u9fff]', quotation or '') else 32
    if len(left) < minimum:
        return None
    if left == right:
        return 'normalized_exact'
    if left in right:
        return 'source_excerpt'
    return None


def arabic_quote_relation(quotation, full, allow_target_excerpt=False):
    left, right = normalize_arabic_quote(quotation), normalize_arabic_quote(full)
    if len(left) < 32 or not right:
        return None
    if left == right:
        return 'normalized_exact'
    if left in right:
        return 'source_excerpt'
    # A longer selected entry can contain the provider's shorter narration.
    # Such reverse containment needs a substantive anchor and a shared explicit
    # collection reference; the caller supplies that occurrence-level support.
    if allow_target_excerpt and len(right) >= 64 and right in left:
        return 'target_excerpt'
    return None


def reference_key(reference):
    book = reference.get('book_key')
    number = reference.get('number')
    if not isinstance(book, str) or type(number) not in (str, int):
        return None
    number = ''.join(str(unicodedata.digit(c)) if c.isdigit() else c for c in str(number)).strip()
    if not re.fullmatch(r'[0-9]+[a-z]?', number):
        return None
    return ALIASES.get(book, book), number


def suffix_compatible_references(source, target):
    """Record a bare-number/suffixed-number pair without rewriting either.

    This is only corroboration for an independently aligned Arabic quotation.
    Two distinct suffixes are never treated as equivalent, and callers must not
    use a common number family to select a narration or a longer source entry.
    """
    pairs = []
    for left in sorted(source):
        for right in sorted(target):
            if left[0] != right[0] or left[1] == right[1]:
                continue
            if ((re.fullmatch(r'[0-9]+[a-z]', left[1]) and left[1][:-1] == right[1])
                    or (re.fullmatch(r'[0-9]+[a-z]', right[1]) and right[1][:-1] == left[1])):
                pairs.append({'source': list(left), 'target': list(right)})
    return pairs


def narration_reference_scope(reference):
    """Require narration identity metadata at both wrapper and child levels."""
    if not isinstance(reference, dict):
        return False
    metadata = ' '.join(str(reference.get(field) or '') for field in
                        ('scope', 'citation_scope', 'numbering_scheme', 'numbering_scope'))
    # A surrounding chapter or another variant can carry a valid-looking
    # collection number. Neither is an occurrence reference for this quotation.
    return re.search(r'chapter|variant', metadata, re.I) is None


def source_references(record):
    references = record.get('references') or {}
    result = []
    if isinstance(references, dict):
        result.extend(parse_provider_references(references.get('bibliography_verbatim') or ''))
        for item in references.get('items') or []:
            if not narration_reference_scope(item):
                continue
            scope = item.get('scope')
            if scope and scope not in ('main_quote', 'source_citation'):
                continue
            wrapped = item.get('field') == 'citations_as_printed'
            terminal = str(item.get('citation_scope') or '').startswith(
                'Exact terminal citation for this source narration')
            if not wrapped and scope not in ('main_quote', 'source_citation') and not terminal:
                continue
            allowed = reference_pairs(item)
            candidates = item.get('value') if wrapped else [item]
            if not isinstance(candidates, list):
                continue
            for reference in candidates:
                if not narration_reference_scope(reference):
                    continue
                child_scope = reference.get('scope')
                if child_scope and child_scope not in ('main_quote', 'source_citation'):
                    continue
                number = reference.get('number')
                scalar = isinstance(number, str) and bool(number) or type(number) in (int, float)
                numbers = ([number] if scalar else reference.get('numbers')
                           if isinstance(reference.get('numbers'), list) else
                           [reference.get('number_as_printed')] if wrapped else [])
                for number in numbers:
                    pair = reference_pair({**reference, 'number': number})
                    if pair is None or pair not in allowed:
                        continue
                    key = ALIASES.get(pair[0], pair[0]), pair[1]
                    english, arabic = BOOK_NAMES.get(key[0], (reference.get('collection') or key[0], None))
                    new_shape = wrapped or not scalar or terminal
                    result.append({'book_key': key[0], 'collection': english, 'collection_ar': arabic,
                                   'number': number if new_shape else key[1],
                                   'numbering_scheme': reference.get('numbering_scheme'),
                                   'scope': 'source_quotation',
                                   'source_citation': reference.get('source_citation') or reference.get('citation_raw'),
                                   **({'source_reference': copy.deepcopy(reference),
                                       'source_reference_field': 'citations_as_printed' if wrapped else 'items'}
                                      if new_shape else {})})
    # Printed sequence/source-entry labels deliberately do not become canonical numbers.
    seen, unique = set(), []
    for item in result:
        key = reference_key(item)
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def citation(references, language):
    result = []
    for item in references:
        name = item.get('collection_ar') if language == 'arabic' else item.get('collection')
        name = name or item.get('collection') or item.get('book_key')
        if name and item.get('number') is not None:
            result.append(str(name) + ('، رقم ' if language == 'arabic' else ' no. ') + str(item['number']))
    return '[' + '; '.join(result) + ']' if result else None


class CounterpartResolver:
    def __init__(self, root, records=None):
        # Import lazily: provenance helpers also support the reader builder.
        # Each linked translation has its own source policy, never its parent's.
        from current_provenance import counterpart_decision_for, load_policy

        self.root = Path(root).resolve()
        self.provenance_policy = load_policy(self.root)
        self.quality_policy = load_quality_policy(self.root)
        self._counterpart_decision_for = counterpart_decision_for
        self.reviewed = ReviewedCounterpartResolver(self.root)
        self.provider_enabled = (self.root / MANIFEST).is_file()
        self.enabled = self.provider_enabled or self.reviewed.enabled
        self.entries, self.assets, self.translations = {}, dict(self.reviewed.assets), defaultdict(list)
        self.source_manifests = ([MANIFEST] if self.provider_enabled else []) + (
            [REVIEWED_MANIFEST] if self.reviewed.enabled else [])
        if self.quality_policy is not None:
            self.assets[self.quality_policy['policy_path']] = self.quality_policy['policy_sha256']
            self.source_manifests.append(self.quality_policy['policy_path'])
        self.normalized_translations = defaultdict(list)
        self.normalized_arabic = {}
        self.ref_ids, self.exact_arabic = defaultdict(set), defaultdict(set)
        self.source_versions = {}
        self.manifest = None
        if not self.provider_enabled:
            return
        self.manifest = json.loads(local(self.root, MANIFEST).read_text(encoding='utf-8'))
        if self.manifest.get('schema') != 'hadith-bank-hadeethenc-counterpart-sources-v1':
            raise ValueError('Unrecognized counterpart source manifest')
        for info in [self.manifest['english_database'], self.manifest['arabic_database'],
                     *self.manifest.get('auxiliary_translation_databases', []),
                     *self.manifest.get('raw_exports', []), self.manifest.get('version_evidence')]:
            if not info:
                continue
            path = local(self.root, info['path'])
            if (not path.is_file() or digest(path) != info['sha256'] or
                    ('bytes' in info and path.stat().st_size != info['bytes'])):
                raise ValueError('Counterpart source checksum mismatch: ' + info['path'])
            self.assets[info['path']] = info['sha256']
        self.assets[MANIFEST] = digest(local(self.root, MANIFEST))
        english = self._rows(self.manifest['english_database']['path'])
        arabic = defaultdict(list)
        for row in self._rows(self.manifest['arabic_database']['path']):
            arabic[str(row['id'])].append(row)
        for row in english:
            identifier = str(row['id'])
            if identifier in self.entries:
                raise ValueError('Duplicate English provider ID: ' + identifier)
            if not isinstance(row.get('hadeeth'), str) or not isinstance(row.get('hadeeth_ar'), str):
                raise ValueError('Counterpart lacks a source quotation: ' + identifier)
            aligned = [r for r in arabic[identifier] if r['version'] == row['ar_version']
                       and r['hadeeth'] == row['hadeeth_ar']]
            refs = parse_provider_references(aligned[0].get('reference') or '') if aligned else []
            self.entries[identifier] = {'id': identifier, 'english': row['hadeeth'],
                                        'arabic': row['hadeeth_ar'], 'ar_version': row['ar_version'],
                                        'references': refs, 'arabic_bibliography_aligned': bool(aligned)}
            self.normalized_arabic[identifier] = normalize_arabic_quote(row['hadeeth_ar'])
            self.exact_arabic[normalize_arabic_quote(row['hadeeth_ar'])].add(identifier)
            for ref in refs:
                if reference_key(ref):
                    self.ref_ids[reference_key(ref)].add(identifier)
        if records is None:
            records = self._registered_provider_records()
        self.add_source_translations(records)
        for database in self.manifest.get('auxiliary_translation_databases', []):
            self.add_source_translations([
                {'book_key': 'hadeethenc', 'provider_entry_id': str(row['id']),
                 'language': database['language'], 'text_translation': row['hadeeth'],
                 'text_arabic': row['hadeeth_ar'], '_source_ar_version': row['ar_version']}
                for row in self._rows(database['path'])])

    def _rows(self, relative):
        path = local(self.root, relative)
        connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
        connection.row_factory = sqlite3.Row
        try:
            return [dict(row) for row in connection.execute('SELECT rowid AS source_rowid,* FROM hadeeths')]
        finally:
            connection.close()

    def _registered_provider_records(self):
        catalog_path = self.root / 'datasets/hadeethenc/collections.json'
        if not catalog_path.is_file():
            return []
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
        result = []
        for item in catalog.get('collections', []):
            path = local(self.root, item['records_path'])
            expected = item.get('records_sha256')
            if expected and digest(path) != expected:
                raise ValueError('Provider record source checksum mismatch')
            with path.open(encoding='utf-8') as stream:
                for line in stream:
                    row = json.loads(line)
                    result.append({'book_key': 'hadeethenc', 'provider_entry_id': row['source_entry_id'],
                                   'language': row['language'], 'text_arabic': row['texts']['arabic_verbatim'],
                                   'text_translation': row['texts']['translation_verbatim'],
                                   '_source_ar_version': row['publication']['source_arabic_version']})
        return result

    def add_source_translations(self, records):
        for record in records:
            if record.get('book_key') != 'hadeethenc':
                continue
            identity = provider_identity(record)
            if identity['status'] != 'linked':
                continue
            text = record.get('text_translation')
            if isinstance(text, str) and text:
                pair = (identity['id'], record.get('language'))
                if not any(item['translation'] == text for item in self.translations[pair]):
                    version = record.get('_source_ar_version')
                    if version is None:
                        version = self._source_version(record)
                    self.translations[pair].append({'translation': text,
                        'arabic': record.get('text_arabic'), 'ar_version': version})
                    self.normalized_translations[record.get('language')].append(
                        (identity['id'], normalize_quote(text)))

    def _source_version(self, record):
        source = record.get('source') or {}
        relative, expected = source.get('original_file'), source.get('sha256')
        if not isinstance(relative, str) or not relative.endswith('.sqlite'):
            return None
        if relative not in self.source_versions:
            path = local(self.root, relative)
            if digest(path) != expected:
                raise ValueError('Original provider SQLite checksum mismatch')
            self.source_versions[relative] = {
                row['source_rowid']: (str(row['id']), row.get('ar_version'), row.get('hadeeth_ar'))
                for row in self._rows(relative)}
        data = self.source_versions[relative].get((record.get('page') or {}).get('row'))
        return data[1] if data and data[0] == str(record.get('provider_entry_id')) and data[2] == record.get('text_arabic') else None

    def _quotation_evidence(self, record, identifier):
        entry = self.entries[identifier]
        refs = {reference_key(ref) for ref in source_references(record)} - {None}
        target = {reference_key(ref) for ref in entry['references']} - {None}
        shared = refs.intersection(target)
        suffix_pairs = suffix_compatible_references(refs, target) if not shared else []
        if refs and target and not shared and not suffix_pairs:
            return None
        relation = arabic_quote_relation(record.get('text_arabic'), entry['arabic'],
                                        allow_target_excerpt=bool(shared))
        if relation:
            return {'field': 'text_arabic', 'relation': relation,
                    'source_record_id': record.get('id'),
                    'source_text_sha256': hashlib.sha256(record['text_arabic'].encode('utf-8')).hexdigest(),
                    'target_text_sha256': hashlib.sha256(entry['arabic'].encode('utf-8')).hexdigest(),
                    'source_file_sha256': (record.get('source') or {}).get('sha256'),
                    'normalization': 'NFKC, punctuation/diacritics/spacing/tatweel/format controls removed; Persian kaf and yeh compared as Arabic kaf and yeh; source bytes unchanged',
                    'shared_explicit_references': [list(value) for value in sorted(shared)],
                    **({'suffix_compatible_references': suffix_pairs,
                        'reference_qualification': 'Source and publisher retain their own numbers. A bare number and one suffixed form corroborate the Arabic quotation only; no numbered route equivalence is asserted.'}
                       if suffix_pairs else {})}
        # A translated phrase alone does not establish that a numbered suffix
        # denotes this Arabic route. Keep it for explicit content review.
        if suffix_pairs:
            return None
        for item in self.translations.get((identifier, record.get('language')), []):
            relation = quote_relation(record.get('text_translation'), item['translation'])
            if relation:
                return {'field': 'text_translation', 'relation': relation,
                        'source_provider_arabic_sha256': hashlib.sha256((item['arabic'] or '').encode('utf-8')).hexdigest(),
                        'source_provider_arabic_version': item['ar_version'],
                        'english_arabic_revision_equal': item['arabic'] == entry['arabic']
                            and (item['ar_version'] is None or item['ar_version'] == entry['ar_version'])}
        return None

    def _select(self, record):
        identity = provider_identity(record)
        if identity['status'] == 'conflict':
            return None, 'conflicting_provider_ids', identity, None
        if identity['status'] == 'linked':
            identifier = identity['id']
            if identifier not in self.entries:
                return None, 'provider_entry_not_downloaded', identity, None
            if record.get('book_key') == 'hadeethenc':
                return identifier, 'primary_provider_id', identity, None
            proof = self._quotation_evidence(record, identifier)
            if proof:
                return identifier, 'provider_id_and_source_quotation', identity, proof
            # A parent lesson URL cannot assign all quotations in its notes.
            return None, 'parent_source_link_without_quotation_alignment', identity, None
        refs = {reference_key(ref) for ref in source_references(record)} - {None}
        candidate_ids = set().union(*(self.ref_ids.get(ref, set()) for ref in refs)) if refs else set()
        normalized = normalize_arabic_quote(record.get('text_arabic'))
        if normalized:
            candidate_ids.update(self.exact_arabic.get(normalized, set()))
        # Match cached normalized strings before expensive field/provenance work.
        # A literal substring must retain at least 32 letters (16 for CJK).
        if len(normalized) >= 32:
            candidate_ids.update(identifier for identifier, text in self.normalized_arabic.items()
                                 if normalized in text)
        translated = normalize_quote(record.get('text_translation'))
        minimum = 16 if re.search(r'[\u3040-\u30ff\u3400-\u9fff]', record.get('text_translation') or '') else 32
        if len(translated) >= minimum:
            candidate_ids.update(identifier for identifier, text in
                                 self.normalized_translations.get(record.get('language'), [])
                                 if translated in text)
        matches = []
        for identifier in sorted(candidate_ids, key=int):
            proof = self._quotation_evidence(record, identifier)
            if proof:
                matches.append((identifier, proof))
                if len(matches) > 1:
                    return None, 'ambiguous_source_quotation', identity, None
        if len(matches) == 1:
            identifier, proof = matches[0]
            return identifier, 'unique_source_quotation_and_citation' if refs else 'unique_source_quotation', identity, proof
        return None, 'no_verified_source_counterpart', identity, None

    def _text(self, text, language, refs, source_name, source_url, snapshot, status, scope,
              origin='human', **extra):
        return {'text': text, 'citation': citation(refs, language), 'references': refs,
                'source_name': source_name, 'source_url': source_url,
                'source_snapshot': snapshot, 'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                'match_status': status, 'scope': scope, 'translation_origin': origin, **extra}

    def _apply_translation_policy(self, result):
        """Add current English-source display policy; retain all source evidence."""
        english = result.get('english')
        if isinstance(english, dict):
            decision = self._counterpart_decision_for(english, self.provenance_policy)
            if decision is not None:
                english['current_translation_policy'] = decision
        # Arabic originals are not translations and receive no origin overlay.
        return result

    def for_record(self, record):
        if not self.enabled:
            return None
        policy = record.get('counterpart_policy') or {}
        if policy.get('mode') == 'disabled':
            # The material's explicit decision wins over both reviewed links and
            # automatic matching. Keep original source text and review intact.
            return self._finalize_result({
                'schema': SCHEMA, 'status': 'unresolved',
                'match_method': 'material_counterparts_disabled',
                'match_note': policy['reason'], 'provider_identity': None,
                'quotation_evidence': None, 'arabic': None, 'english': None,
            })
        reviewed = self.reviewed.for_record(record)
        if reviewed is not None:
            # A stale or ambiguous reviewed assignment must not silently fall
            # through to another provider. The original source stays intact.
            return self._finalize_result(reviewed)
        identifier, method, identity, proof = (self._select(record) if self.provider_enabled else
            (None, 'no_verified_source_counterpart', None, None))
        original_refs = source_references(record)
        result = {'schema': SCHEMA, 'status': 'unresolved', 'match_method': method,
                  'match_note': None, 'provider_identity': identity, 'quotation_evidence': proof,
                  'arabic': None, 'english': None}
        source = record.get('source') or {}
        if record.get('text_arabic'):
            result['arabic'] = self._text(record['text_arabic'], 'arabic', original_refs,
                source.get('name') or record.get('source_id'), source.get('record_url') or source.get('url'),
                record.get('edition'), 'source_supplied', 'source_excerpt' if
                (record.get('extraction') or {}).get('is_excerpt') else 'same_provider_entry',
                origin='unknown', source_record_id=record['id'])
        if identifier is None:
            return self._finalize_result(result)
        entry = self.entries[identifier]
        exact = record.get('text_arabic') == entry['arabic']
        source_version = self._source_version(record) if record.get('book_key') == 'hadeethenc' else None
        related = record.get('book_key') == 'hadeethenc' and (
            not exact or source_version is not None and source_version != entry['ar_version'])
        if proof and proof.get('english_arabic_revision_equal') is False:
            related = True
        original_arabic = normalize_arabic_quote(record.get('text_arabic'))
        linked_arabic = normalize_arabic_quote(entry['arabic'])
        if original_arabic and original_arabic != linked_arabic and original_arabic not in linked_arabic:
            related = True
        status = 'related_version' if related else 'exact'
        refs = entry['references']
        # A bibliography from a different Arabic revision must not be silently
        # applied to this English-linked quotation (notably provider 65065).
        if not refs and not related and (exact or proof and (
                proof.get('field') == 'text_arabic' or proof.get('english_arabic_revision_equal') is True)):
            refs = original_refs
        snapshot = 'HadeethEnc English ' + str(self.manifest.get('english_version') or 'version not supplied')
        snapshot += '; Arabic revision ' + str(entry['ar_version'])
        snapshot += '; SQLite ' + self.manifest['english_database']['sha256'][:16]
        target_excerpt = proof is not None and proof.get('relation') == 'target_excerpt'
        common = {'source_name': 'HadeethEnc.com', 'snapshot': snapshot,
                  'status': status, 'scope': 'source_excerpt' if target_excerpt else 'full_narration',
                  'source_record_id': identifier, 'source_arabic_version': entry['ar_version'],
                  'original_arabic_version': source_version,
                  'database_path': self.manifest['english_database']['path'],
                  'database_sha256': self.manifest['english_database']['sha256'],
                  'bibliography_arabic_version_aligned': entry['arabic_bibliography_aligned']}
        result['arabic'] = self._text(entry['arabic'], 'arabic', refs,
            source_url='https://hadeethenc.com/ar/browse/hadith/' + identifier, **common)
        result['english'] = self._text(entry['english'], 'english', refs,
            source_url='https://hadeethenc.com/en/browse/hadith/' + identifier, **common)
        result['status'] = status
        if target_excerpt:
            result['match_note'] = 'The linked Arabic and English cover a literal excerpt of the selected source entry, supported by a shared explicit collection reference. Other source wording remains unchanged and is not covered by this counterpart.'
        elif related:
            result['match_note'] = 'Same publisher entry; the English-linked Arabic revision differs from the stored source. Original text remains unchanged.'
        return self._finalize_result(result)

    def _finalize_result(self, result):
        return apply_quality_policy(self._apply_translation_policy(result), self.quality_policy)


def enrich_records(root, records):
    resolver = CounterpartResolver(root, records)
    if not resolver.enabled:
        return None
    summary = Counter(total=0, arabic_available=0, english_available=0,
                      arabic_external_links=0, english_external_links=0,
                      exact_links=0, related_version_links=0, reviewed_parallel_links=0, unresolved=0,
                      with_numbered_references=0)
    languages, reasons, unresolved = defaultdict(Counter), Counter(), []
    for record in records:
        value = resolver.for_record(record)
        record['counterparts'] = value
        summary['total'] += 1
        language = languages[record['language']]
        language['total'] += 1
        for key, field in [('arabic_available', 'arabic'), ('english_available', 'english')]:
            if value[field] and value[field].get('text'):
                summary[key] += 1
                language[key] += 1
            elif value[field] and value[field].get('source_url'):
                external_key = field + '_external_links'
                summary[external_key] += 1
                language[external_key] += 1
        if value['status'] == 'reviewed_parallel':
            summary['reviewed_parallel_links'] += 1
            language['reviewed_parallel_links'] += 1
            if any(value[field] and value[field].get('references') for field in ('arabic', 'english')):
                summary['with_numbered_references'] += 1
        elif value['english'] and value['english'].get('text'):
            summary['related_version_links' if value['status'] == 'related_version' else 'exact_links'] += 1
            if value['english'].get('references'):
                summary['with_numbered_references'] += 1
        else:
            summary['unresolved'] += 1
            language['unresolved'] += 1
            reasons[value['match_method']] += 1
            unresolved.append({'record_id': record['id'], 'reason': value['match_method']})
    report = {'schema': 'hadith-bank-counterpart-coverage-v1', 'status': 'passed',
              **dict(summary), 'by_language': {k: dict(v) for k, v in sorted(languages.items())},
              'unresolved_reasons': dict(reasons), 'unresolved_records': unresolved,
              'provider_entries_available': len(resolver.entries),
              'reviewed_entries_available': sum(len(value['entries']) for value in resolver.reviewed.bundles.values()),
              'source_manifest': resolver.source_manifests[0], 'source_manifests': resolver.source_manifests,
              'source_assets': resolver.assets, 'original_record_count_unchanged': True,
              'source_text_unchanged': True, 'new_translations_created': False,
              'matching_policy': 'Publisher version identity, unique literal source-quotation alignment, or explicit reviewed narration evidence bound to source and target hashes; never collection number alone.'}
    from counterpart_coverage import write_reports
    availability = write_reports(root, records)
    report['availability'] = {
        'totals': availability['totals'], 'by_language': availability['by_language'],
        'report': 'reports/counterpart-availability.json',
        'book_report': 'reports/counterpart-availability.md',
    }
    output = Path(root) / 'reports/counterpart-coverage.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {**dict(summary), 'by_language': report['by_language'], 'availability': report['availability'],
            'report': 'reports/counterpart-coverage.json', 'source_manifest': resolver.source_manifests[0],
            'source_manifests': resolver.source_manifests}

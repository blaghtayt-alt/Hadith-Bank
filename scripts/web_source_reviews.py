"""Apply explicit website review decisions to derivatives of immutable sources.

Every admitted field is independently hash-bound. Missing field decisions retain
the complete field as source context, never as a quotation. This module validates
evidence binding and preservation; it does not perform a semantic review or an
authenticity assessment.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import json
from pathlib import Path
import web_commentary_quotes


SCHEMA = 'hadith-bank-web-source-review-v1'
FOLDERS = {
    'islom': 'imports/web-uzbek-20261112/islom',
    'hadisuz': 'imports/web-hadisuz-20261112',
    'deenhindi': 'imports/web-deenhindi-20261112',
}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical_hash(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':')).encode('utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError('Website source review: ' + message)


def alias(value, *names, default=None):
    found = [value[name] for name in names if name in value]
    require(not found or all(item == found[0] for item in found),
            'conflicting aliases: ' + ', '.join(names))
    return found[0] if found else default


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key ' + key)
        result[key] = value
    return result


class SourceReviews:
    def __init__(self, root, site):
        require(site in FOLDERS, 'unsupported site')
        self.root, self.site = Path(root).resolve(), site
        self.engine_sha256 = sha(Path(__file__).read_bytes() + Path(web_commentary_quotes.__file__).read_bytes())
        self.folder = self.root / FOLDERS[site] / 'reviews'
        self.decisions, self.seen, self.files = {}, set(), []
        self.commentary = web_commentary_quotes.CommentaryQuotes(self.root, site)
        baseline_files = {}
        paths = [*self.folder.glob('source-review*.json'), *self.folder.glob('source-review*.json.gz')]
        for path in sorted(paths):
            stored = path.read_bytes()
            data = gzip.decompress(stored) if path.suffix == '.gz' else stored
            document = json.loads(data, object_pairs_hook=unique_pairs)
            require(document.get('schema') == SCHEMA, 'unsupported review schema')
            require(alias(document, 'site', 'source') == site, 'review site mismatch')
            require(document.get('independent_pro_qc', 'not_performed') == 'not_performed',
                    'this workflow cannot claim independent Pro certification')
            if 'source_ledger_path' in document or 'source_ledger_sha256' in document:
                relative = document.get('source_ledger_path')
                require(isinstance(relative, str) and relative and '\\' not in relative,
                        'safe baseline ledger path required')
                pure = Path(relative)
                require(not pure.is_absolute() and '..' not in pure.parts and ':' not in pure.parts[0],
                        'baseline ledger path must stay inside the repository')
                ledger = self.root / pure
                require(ledger.is_file() and not any(part.is_symlink() for part in
                        [ledger, *ledger.parents] if part.is_relative_to(self.root))
                        and ledger.resolve().is_relative_to(self.root), 'baseline ledger is missing or unsafe')
                ledger_bytes = ledger.read_bytes()
                require(sha(ledger_bytes) == document.get('source_ledger_sha256'), 'baseline ledger checksum mismatch')
                baseline_files[relative] = {'path': relative, 'sha256': sha(ledger_bytes),
                    'size_bytes': len(ledger_bytes), 'role': 'immutable_source_review_baseline'}
            rows = alias(document, 'records', 'decisions')
            require(isinstance(rows, list) and rows, 'nonempty decision list required')
            relative = path.relative_to(self.root).as_posix()
            for decision in rows:
                require(isinstance(decision, dict), 'decision must be an object')
                identity = alias(decision, 'occurrence_id', 'id')
                require(isinstance(identity, str) and identity, 'missing occurrence ID')
                require(identity not in self.decisions, 'duplicate decision for ' + identity)
                action = alias(decision, 'decision', 'overalldecision')
                require(action in ('register', 'hold', 'exclude'), 'explicit record decision required for ' + identity)
                self.decisions[identity] = (decision, {'path': relative, 'sha256': sha(stored),
                    **({'compression': 'gzip', 'uncompressed_sha256': sha(data)} if path.suffix == '.gz' else {})}, action)
        require(not (set(self.decisions) & set(self.commentary.specs)), 'commentary child collides with primary source identity')
        # Companion ledgers are evidence dependencies as well as the decisions.
        for path in sorted(self.folder.rglob('*')) if self.folder.exists() else []:
            if path.is_file():
                require(not path.is_symlink(), 'symlink review evidence is not allowed')
                data = path.read_bytes()
                self.files.append({'path': path.relative_to(self.root).as_posix(),
                    'sha256': sha(data), 'size_bytes': len(data),
                    'role': 'source_bound_review_and_coverage_evidence'})
        present = {item['path'] for item in self.files}
        self.files.extend(value for key, value in sorted(baseline_files.items()) if key not in present)

    def supporting_files(self):
        return copy.deepcopy(self.files)

    def finish(self):
        require(self.seen == set(self.decisions), 'review IDs absent from source: ' +
                ', '.join(sorted(set(self.decisions) - self.seen)[:10]))
        self.commentary.finish()

    def commentary_children(self, row, baseline=None):
        return self.commentary.children(row, baseline)

    def additional_context_comments(self, decision, baseline, receipt):
        """Recover reviewed Hadis.uz list context from its exact saved HTML.

        These blocks were outside the original paragraph-only extraction. They
        remain comments, never primary report text or new source occurrences.
        """
        blocks = decision.get('additional_source_blocks', [])
        require(isinstance(blocks, list), 'additional source blocks must be an array')
        if not blocks:
            return {}
        versions = baseline.get('language_versions', [])
        require(self.site == 'hadisuz' and len(versions) == 1
                and versions[0].get('language') == 'uz-Cyrl',
                'additional block needs the explicit single Hadis.uz source language')
        version = versions[0]
        snapshot = decision.get('source_snapshot') or {}
        relative = snapshot.get('path')
        require(isinstance(relative, str) and relative and '\\' not in relative,
                'safe additional block snapshot path required')
        pure = Path(relative)
        require(not pure.is_absolute() and '..' not in pure.parts and ':' not in pure.parts[0],
                'additional block snapshot must stay inside the repository')
        path = self.root / pure
        require(path.is_file() and path.suffix == '.gz'
                and not any(part.is_symlink() for part in [path, *path.parents]
                            if part.is_relative_to(self.root))
                and path.resolve().is_relative_to(self.root),
                'additional block snapshot is missing or unsafe')
        stored = path.read_bytes()
        require(sha(stored) == snapshot.get('stored_sha256'),
                'additional block stored snapshot checksum mismatch')
        raw = gzip.decompress(stored)
        require(sha(raw) == snapshot.get('sha256'),
                'additional block original snapshot checksum mismatch')
        # Reuse the source parser's exact text and child-index conventions.
        # This local parse performs no source requests.
        from import_uzbek_web import Node, Tree, plain
        column = Tree(raw.decode('utf-8')).root.first(lambda node: node.has('col-md-9'))
        require(column is not None, 'additional block source column missing')
        comments, seen = [], set()
        for block in blocks:
            require(isinstance(block, dict), 'additional source block must be an object')
            text = block.get('text')
            require(isinstance(text, str) and text.strip(), 'additional block text required')
            require(block.get('decision') == 'source_context'
                    and not alias(block, 'selected_spans', 'spans', default=[]),
                    'additional block recovery cannot register an embedded report')
            require(block.get('sha256') == sha(text.encode('utf-8')),
                    'additional block text checksum mismatch')
            require(block.get('chars_reviewed') == len(text)
                    and block.get('bytes_reviewed') == len(text.encode('utf-8')),
                    'additional block complete review coverage required')
            index = block.get('child_index')
            require(block.get('source_selector') == '.col-md-9' and block.get('tag') == 'ol'
                    and type(index) is int and 0 <= index < len(column.children)
                    and index not in seen, 'additional block locator invalid or duplicated')
            child = column.children[index]
            require(isinstance(child, Node) and child.tag == 'ol' and plain(child, True) == text,
                    'additional block text differs from the exact saved HTML locator')
            seen.add(index)
            reason = block.get('reason')
            require(isinstance(reason, str) and reason.strip(), 'additional block reason required')
            comments.append({'text': text, 'language': version['language'],
                'scope': 'source_context_not_narration', 'kind': 'reviewed_additional_source_block',
                'source_url': (baseline.get('source') or {}).get('record_url')
                              or (baseline.get('source_locator') or {}).get('record_url'),
                'source_text_sha256': block['sha256'],
                'source_snapshot_path': relative, 'source_snapshot_sha256': snapshot['sha256'],
                'source_block_locator': {'selector': '.col-md-9', 'tag': 'ol', 'child_index': index,
                    'child_index_unit': 'zero-based parser child index including text nodes'},
                'retention_reason': reason,
                'source_bound_review': {**receipt, 'decision': 'source_context',
                    'chars_reviewed': block['chars_reviewed'], 'bytes_reviewed': block['bytes_reviewed'],
                    'embedded_report_registration': False, 'independent_pro_qc': 'not_performed'}})
        return {version['id']: comments}

    def apply(self, row, saved=None, baseline=None):
        if row['id'] not in self.decisions:
            return row, None
        decision, receipt, action = self.decisions[row['id']]
        baseline = row if baseline is None else baseline
        require(row['id'] == baseline['id'], 'baseline occurrence identity mismatch')
        if decision.get('baseline_record_sha256'):
            require(canonical_hash(baseline) == decision['baseline_record_sha256'],
                    'baseline record changed: ' + row['id'])
        else:
            require(self.site == 'deenhindi' and isinstance(saved, dict),
                    'baseline record hash required: ' + row['id'])
            encoded = (json.dumps(saved['source_record'], ensure_ascii=False,
                       sort_keys=True, indent=2) + '\n').encode('utf-8')
            require(sha(encoded) == decision.get('source_record_sha256'),
                    'original source object changed: ' + row['id'])
        snapshot = decision.get('source_snapshot') or {}
        locator = baseline.get('source_locator') or {}
        expected_hash = snapshot.get('sha256', decision.get('source_snapshot_sha256'))
        require(expected_hash and expected_hash == locator.get('sha256'),
                'source snapshot binding mismatch: ' + row['id'])
        if snapshot.get('path'):
            require(snapshot['path'] == locator.get('path'), 'source snapshot path mismatch')
        additional_comments = self.additional_context_comments(decision, baseline, receipt)
        versions = row.get('language_versions')
        require(isinstance(versions, list), 'source language versions required')
        baseline_versions = {v['id']: v for v in baseline.get('language_versions', [])}
        fields = alias(decision, 'fields', 'field_reviews')
        require(isinstance(fields, list), 'field decision list required')
        by_id, comment_fields = {}, {}
        for field in fields:
            identity = alias(field, 'version_id', 'language_version_id')
            path = field.get('field_path', [])
            if len(path) == 5 and path[0] == 'language_versions' and path[2] == 'comments' and path[4] == 'text':
                require(type(path[1]) is int and 0 <= path[1] < len(baseline['language_versions']),
                        'comment version index mismatch')
                parent = baseline['language_versions'][path[1]]
                require(parent['id'] == identity and parent['language'] == field.get('language'),
                        'comment language/version mismatch')
                comments = parent.get('comments', [])
                require(type(path[3]) is int and 0 <= path[3] < len(comments)
                        and isinstance(comments[path[3]], dict), 'comment path mismatch')
                comment = comments[path[3]]['text']
                require(isinstance(comment, str) and field.get('text_sha256') == sha(comment.encode('utf-8')),
                        'comment field hash mismatch')
                require(field.get('chars_reviewed') == len(comment)
                        and field.get('bytes_reviewed') == len(comment.encode('utf-8')),
                        'comment review coverage mismatch')
                require(alias(field, 'decision', 'action') in ('source_context', 'source_context_only')
                        and not alias(field, 'selected_spans', 'spans', default=[]),
                        'comment review cannot silently register embedded narrations')
                index = (identity, path[3])
                require(index not in comment_fields, 'duplicate comment review')
                comment_fields[index] = field
                continue
            require(identity in baseline_versions and identity not in by_id,
                    'unknown or duplicate language field ' + str(identity))
            by_id[identity] = field
        out = copy.deepcopy(row)
        out['language_versions'] = []
        selected_count = 0
        report_types = set()
        for original in versions:
            version = copy.deepcopy(original)
            for (identity, index), reviewed_comment in comment_fields.items():
                if identity == original['id']:
                    require(version['comments'][index]['text'] == baseline_versions[identity]['comments'][index]['text'],
                            'comment changed before review')
                    version['comments'][index]['source_bound_review'] = {
                        **receipt, 'decision': 'source_context', 'chars_reviewed': reviewed_comment['chars_reviewed'],
                        'reason': reviewed_comment.get('reason'), 'embedded_report_registration': False}
            text = original['text']
            require(isinstance(text, str), 'review input must be a complete source field')
            require(baseline_versions.get(original['id'], {}).get('text') == text,
                    'derived field changed before review')
            field = by_id.get(original['id'])
            if field is None:
                selection, spans = 'unreviewed', []
                reason = 'This language field has not yet received its own attribution and boundary review.'
            else:
                require(field.get('language') == original['language'], 'field language mismatch')
                require(field.get('text_sha256') == sha(text.encode('utf-8')), 'language field hash mismatch')
                require(field.get('text_chars', len(text)) == len(text), 'language field length mismatch')
                if field.get('field_path'):
                    path = field['field_path']
                    require(isinstance(path, list) and len(path) == 3 and path[0] == 'language_versions'
                            and type(path[1]) is int and path[2] == 'text'
                            and 0 <= path[1] < len(baseline['language_versions'])
                            and baseline['language_versions'][path[1]]['id'] == original['id'],
                            'field path does not identify its own language version')
                if saved is not None and field.get('source_field'):
                    require(saved['source_record'].get(field['source_field']) == text,
                            'saved provider field mismatch')
                selection = alias(field, 'decision', 'action')
                require(selection in ('whole', 'excerpt', 'excerpts', 'source_context',
                                      'source_context_only', 'uncertain', 'unreviewed', 'hold', 'exclude'),
                        'unsupported field decision ' + str(selection))
                reason = field.get('reason') or decision.get('reason')
                require(isinstance(reason, str) and reason.strip(), 'field reason required')
                spans = alias(field, 'selected_spans', 'spans', default=[])
                require(isinstance(spans, list), 'selected spans must be an array')
                reviewed = field.get('reviewed', field.get('chars_reviewed') == len(text))
                if selection in ('whole', 'excerpt', 'excerpts'):
                    require(reviewed is True, 'unread field cannot be admitted')
                    require(spans, 'admitted field needs exact spans')
                    if 'chars_reviewed' in field:
                        require(field['chars_reviewed'] == len(text), 'whole field must be read before selecting passages')
                    if 'bytes_reviewed' in field:
                        require(field['bytes_reviewed'] == len(text.encode('utf-8')), 'review byte coverage mismatch')
                else:
                    require(not spans, 'context-only field cannot select quotation spans')
            cursor = 0
            for span in spans:
                require(isinstance(span, dict), 'selected span must be an object')
                start, end = span.get('start'), span.get('end')
                require(type(start) is int and type(end) is int and 0 <= cursor <= start < end <= len(text),
                        'invalid, unordered or overlapping source span')
                require(text[start:end].strip(), 'empty quotation span')
                require(span.get('sha256') == sha(text[start:end].encode('utf-8')), 'selected span hash mismatch')
                cursor = end
            if selection == 'whole':
                require(len(spans) == 1 and spans[0]['start'] == 0 and spans[0]['end'] == len(text),
                        'whole-field approval must cover the complete field')
            version['source']['source_text_sha256'] = sha(text.encode('utf-8'))
            script_note = None
            if field and 'observed_script' in field:
                require(field.get('reviewed', field.get('chars_reviewed') == len(text)) is True,
                        'script correction requires an individually reviewed field')
                require(field['observed_script'] in ('Arab', 'Cyrl', 'Deva', 'Latn'),
                        'unsupported reviewed source script')
                script_note = field.get('source_script_note')
                require(isinstance(script_note, str) and script_note.strip(), 'visible source script note required')
                version['source']['importer_script_before_review'] = version.get('script')
                version['source']['source_script_note'] = script_note
                version['script'] = field['observed_script']
            version['source']['manual_review'] = {**receipt, 'decision': selection,
                'field_reviewed': bool(field and field.get('reviewed', field.get('chars_reviewed') == len(text))),
                'reason': reason, 'independent_pro_qc': 'not_performed'}
            if field and field.get('review_method'):
                version['source']['manual_review'].update(
                    method=field['review_method'], review_scope=field.get('review_scope'),
                    prior_review_evidence=copy.deepcopy(field.get('prior_review_evidence', [])))
            if not spans:
                version.update(text=None, scope='external_source', quotation_status='attribution_pending')
                version['source']['quotation_boundary_status'] = 'pending'
                version['source']['quotation_boundary_reason'] = reason
                version['source']['report_classification_note'] = reason
                version.setdefault('comments', []).append({'text': text,
                    'scope': 'source_context_not_narration', 'language': version['language'],
                    'source_url': version['source'].get('record_url') or version['source'].get('url'),
                    'source_span': [0, len(text)], 'source_text_sha256': sha(text.encode('utf-8')),
                    'retention_reason': reason})
            else:
                selected_count += 1
                pairs = [[span['start'], span['end']] for span in spans]
                notes, cursor = [], 0
                for start, end in pairs:
                    if cursor < start:
                        notes.append([cursor, start])
                    cursor = end
                if cursor < len(text):
                    notes.append([cursor, len(text)])
                version['text'] = ''.join(text[start:end] for start, end in pairs)
                version['scope'] = 'source_entry' if not notes else 'source_excerpt'
                version['quotation_status'] = 'bounded' if len(pairs) == 1 else 'disjoint_source_spans'
                version['source']['text_spans'] = {'quotation_spans': pairs, 'notes': notes,
                    'span_unit': 'unicode_codepoints', 'method': 'source_hash_bound_website_review_v1'}
                version['source']['quotation_boundary_status'] = 'bounded'
                for start, end in notes:
                    version.setdefault('comments', []).append({'text': text[start:end],
                        'scope': 'source_context_not_narration', 'language': version['language'],
                        'source_url': version['source'].get('record_url') or version['source'].get('url'),
                        'source_span': [start, end], 'source_text_sha256': sha(text[start:end].encode('utf-8')),
                        'retention_reason': 'Source text outside the explicitly reviewed narration spans.'})
                components, groups, classifications = [], [], []
                for index, span in enumerate(spans):
                    report_type = span.get('report_type', field.get('report_type', decision.get('report_type')))
                    speaker = span.get('speaker', field.get('speaker', decision.get('speaker')))
                    require(isinstance(report_type, str) and report_type.strip(), 'actual report type required')
                    require(isinstance(speaker, str) and speaker.strip(), 'explicit source attribution description required')
                    report_types.add(report_type)
                    component = span.get('component_id', 'passage-' + str(index + 1))
                    if component in components:
                        require(component == components[-1], 'one component cannot cross another component')
                        require(classifications[-1]['report_type'] == report_type
                                and classifications[-1]['speaker_description'] == speaker,
                                'one report component has inconsistent attribution')
                        groups[-1].append(pairs[index])
                    else:
                        components.append(component)
                        groups.append([pairs[index]])
                        classifications.append({'component_id': component, 'report_type': report_type,
                            'speaker_description': speaker,
                            'reason': span.get('reason', reason), 'spans': groups[-1],
                            **({key: copy.deepcopy(span[key]) for key in
                               ('source_report_family_id', 'language', 'ultimate_speaker') if key in span})})
                # Existing reader projection renders exact groups and passages
                # separately; the concatenated search payload adds no words.
                if len(pairs) > 1:
                    version['source'].update(source_report_groups=groups, source_report_count=len(groups))
                    version['quotation_status'] = 'multiple_source_reports' if len(groups) > 1 else 'disjoint_source_spans'
                families = [item.get('source_report_family_id') for item in classifications]
                if families and all(families) and len(set(families)) < len(families):
                    # Bilingual readings of the same report may recur later in
                    # one mixed source field. Preserve page order as separate
                    # excerpts without counting each reading as a new report.
                    version['source'].pop('source_report_groups', None)
                    version['source']['source_report_count'] = len(set(families))
                    version['source']['source_report_family_count'] = len(set(families))
                    version['quotation_status'] = 'disjoint_source_spans'
                    version['source']['source_report_alignment_note'] = (
                        str(len(classifications)) + ' ordered source reading components represent ' +
                        str(len(set(families))) + ' report families in this one provider entry. '
                        'Their original language order is preserved in separate excerpt blocks.')
                version['source']['report_component_classifications'] = classifications
                version['source']['report_type'] = classifications[0]['report_type'] if len(classifications) == 1 else 'mixed_attributed_reports'
                version['source']['report_classification_note'] = ' '.join(dict.fromkeys(
                    'Report type: ' + item['report_type'].replace('_', ' ') + '. Attribution: ' +
                    item['speaker_description'] + '. ' + item['reason'] for item in classifications))
                version['source']['reviewed_span_evidence'] = copy.deepcopy(spans)
                for name in ('nested_quotations', 'nested_quotation_annotations', 'quran_quote_spans',
                             'source_supplied_transliteration', 'transliteration_spans',
                             'source_text_annotations', 'text_role', 'source_content_mismatch'):
                    if name in field:
                        version['source'][name] = copy.deepcopy(field[name])
                if (field.get('source_content_mismatch') or {}).get('confirmed') is True:
                    version['match_status'] = 'same_provider_id_different_source_content'
                    version['source']['source_report_alignment_note'] = (
                        'The reviewed language fields differ in content. Each wording is preserved independently; '
                        'the shared provider ID does not establish translation equivalence. ' + reason)
            if script_note:
                version['source']['report_classification_note'] += ' ' + script_note
            version.setdefault('comments', []).extend(copy.deepcopy(additional_comments.get(original['id'], [])))
            external = decision.get('external_evidence', [])
            if external:
                version['source']['external_corroboration'] = copy.deepcopy(external)
                version['comments'].extend(web_commentary_quotes.external_evidence_comments(
                    self.root, external, version['language']))
            out['language_versions'].append(version)
        require(action != 'register' or selected_count > 0, 'registration requires an approved field')
        require(action == 'register' or selected_count == 0, 'held/excluded occurrence cannot admit quotation fields')
        out['review']['source_bound_review'] = {**receipt, 'decision': action,
            'independent_pro_qc': 'not_performed', 'approved_language_fields': selected_count}
        out['review']['status'] = 'source_bound_classification_reviewed' if action == 'register' else 'source_bound_' + action
        out['review']['independent_pro_qc'] = 'not_performed'
        out['review']['certified_release_eligible'] = False
        out['report_types'] = sorted(report_types)
        if action == 'register':
            out['content_kind'] = 'source_numbered_attributed_report'
            selected = [v for v in out['language_versions'] if v.get('text')]
            arabic = next((v['text'] for v in selected if v['language'] == 'ar'), None)
            translation = next((v['text'] for v in selected if v['language'] == row.get('source_language_code', row['language'])), None)
            # A registered Arabic/English reading never fills a missing or
            # unreviewed primary translation field.
            out['text'] = {'arabic': arabic, 'translation': translation}
            out['extraction']['is_excerpt'] = any(v.get('scope') == 'source_excerpt' for v in selected)
            out['extraction']['source_bound_review_applied'] = True
        self.seen.add(row['id'])
        return out, action

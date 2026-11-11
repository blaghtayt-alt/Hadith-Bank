"""Apply explicit owner source classifications without rewriting source history."""
import copy
import datetime
from pathlib import Path
from urllib.parse import urlsplit

from build_reader import local, parse_json


POLICY_PATH = 'catalog/provenance-policy.json'
CLASSIFICATIONS = ('human', 'ai', 'unknown')
MATCH_FIELDS = {'source_name', 'book_key', 'package_root', 'source_id', 'source_ids', 'kind'}
NEW_MATERIAL_SCOPE = 'registered_nonlegacy_materials_and_counterparts'
UNSUPPORTED_EVIDENCE_BASES = {
    'Original source attribution metadata; no additional evidence inferred',
    'No source-specific translation provenance supplied',
    'source_specific_translation_role_not_established',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_policy(root):
    path = local(Path(root).resolve(), POLICY_PATH)
    if not path.exists():
        return None
    policy = parse_json(path.read_text(encoding='utf-8'))
    require(isinstance(policy, dict) and policy.get('schema') == 'hadith-bank-provenance-policy-v1',
            'Invalid current provenance policy')
    date = policy.get('decision_date_japan')
    require(isinstance(date, str), 'Current provenance policy needs its decision date')
    datetime.date.fromisoformat(date)
    rules = policy.get('source_rules')
    require(isinstance(rules, list), 'Current provenance policy needs source_rules')
    for rule in rules + ([policy['legacy_rule']] if 'legacy_rule' in policy else []):
        require(isinstance(rule, dict) and rule.get('classification') in CLASSIFICATIONS,
                'Invalid current translation classification')
        match = rule.get('match')
        require(isinstance(match, dict) and bool(match) and not set(match) - MATCH_FIELDS,
                'Provenance rules need an explicit supported source match')
        for key, value in match.items():
            if key == 'source_ids':
                require(isinstance(value, list) and bool(value) and all(isinstance(x, str) and x for x in value),
                        'Provenance source_ids must be a nonempty string array')
            else:
                require(isinstance(value, str) and bool(value), 'Invalid provenance match value')
        require(isinstance(rule.get('basis'), str) and bool(rule['basis']), 'Provenance rule needs its evidence basis')
    default = policy.get('new_material_rule')
    if default is not None:
        require(isinstance(default, dict) and default.get('scope') == NEW_MATERIAL_SCOPE and
                default.get('classification') == 'human', 'Invalid new-material provenance default')
        require(isinstance(default.get('basis'), str) and bool(default['basis'].strip()),
                'New-material provenance default needs its evidence basis')
        require(default.get('source_declarations_take_precedence') is True,
                'New-material default must preserve explicit source declarations')
    return policy


def matches(record, match):
    source = record.get('source') or {}
    values = {'source_name': source.get('name', record.get('source_name')),
              'book_key': record.get('book_key'), 'source_id': record.get('source_id', record.get('dataset_id')),
              'kind': record.get('kind')}
    for key, expected in match.items():
        if key == 'package_root':
            path = source.get('original_file', record.get('source_file', ''))
            if not isinstance(path, str) or not path.startswith(expected.rstrip('/') + '/'):
                return False
        elif key == 'source_ids':
            if values['source_id'] not in expected:
                return False
        elif values.get(key) != expected:
            return False
    return True


def _metadata_chain(value, original_key):
    """Follow only the object's explicit original-metadata chain."""
    seen = set()
    while isinstance(value, dict) and id(value) not in seen:
        seen.add(id(value))
        yield value
        value = value.get(original_key)


def legacy_source(record):
    """Recognize retained old-bank identities and lineage, not processing tools."""
    if record.get('kind') == 'legacy_source_document':
        return True
    provenance = record.get('translation_provenance') or {}
    if (any(item.get('origin') == 'legacy_source_history'
            for item in _metadata_chain(provenance, 'original_provenance')) or
            record.get('origin') == 'legacy_source_history' or
            record.get('translation_origin') == 'legacy_source_history'):
        return True
    identity = record.get('source_id', record.get('dataset_id'))
    if isinstance(identity, str) and identity.startswith(('legacy-', 'quran-excerpts-')):
        return True
    source = record.get('source') or record.get('source_descriptor') or {}
    for original in _metadata_chain(source, 'original_metadata'):
        lineage = original.get('legacy_document') or {}
        if (isinstance(lineage, dict) and lineage.get('repository') == 'blaghtayt-alt/iman-companion' or
                original.get('repository') == 'blaghtayt-alt/iman-companion' and
                bool(original.get('commit') or original.get('revision'))):
            return True
    return False


def source_translation_declaration(record):
    """Read explicit translation authorship evidence, never OCR/reviewer flags.

    A declaration uses ``classification`` and a nonempty ``evidence`` statement
    or source locator. Historical ai_translation flags remain separately stored.
    """
    provenance = record.get('translation_provenance') or {}
    provenances = list(_metadata_chain(provenance, 'original_provenance'))
    source = record.get('source') or record.get('source_descriptor') or {}
    candidates = [item.get('source_declaration') for item in provenances]
    candidates.append(record.get('source_declaration'))
    for original in _metadata_chain(source, 'original_metadata'):
        candidates.extend([original.get('translation_declaration'), original.get('source_declaration')])
    found = []
    for declaration in candidates:
        if declaration is None:
            continue
        require(isinstance(declaration, dict) and declaration.get('classification') in CLASSIFICATIONS,
                'Invalid source translation declaration')
        evidence = declaration.get('evidence')
        require(isinstance(evidence, str) and bool(evidence.strip()),
                'Source translation declaration needs explicit source evidence')
        found.append({'classification': declaration['classification'], 'evidence': evidence})
    # Existing source records need no schema retrofit. The combination of an
    # explicit translation-AI origin, its true translation flag, and supplied
    # attribution evidence is already a source declaration. Processing/review
    # fields and generated fallback explanations are not attribution evidence.
    for attribution in provenances:
        if (attribution.get('origin') != 'ai_translation' or
                attribution.get('ai_translation', record.get('ai_translation')) is not True):
            continue
        basis = attribution.get('basis')
        evidence_ids = attribution.get('evidence_ids')
        evidence = []
        if isinstance(basis, str) and basis.strip() and basis not in UNSUPPORTED_EVIDENCE_BASES:
            evidence.append(basis)
        if isinstance(evidence_ids, list):
            evidence.extend(item for item in evidence_ids if isinstance(item, str) and item.strip())
        if evidence:
            found.append({'classification': 'ai', 'evidence': '; '.join(evidence)})
    require(len({item['classification'] for item in found}) <= 1,
            'Conflicting source translation declarations')
    return found[0] if found else None


def _decision(rule, policy, declaration=None):
    result = {'classification': rule['classification'], 'basis': rule['basis'],
              'decision_date_japan': policy['decision_date_japan'], 'policy_path': POLICY_PATH}
    if declaration:
        result['source_declaration_evidence'] = declaration['evidence']
    return result


def _registered_material(record):
    publication = record.get('publication') or {}
    path = publication.get('manifest_path')
    return (publication.get('authorized') is True and isinstance(path, str) and
            path.startswith('materials/') and path.endswith('/manifest.json') and
            all(part not in ('', '.', '..') for part in path.split('/')))


def decision_for(record, policy, registered_material=False):
    if not policy:
        return None
    if legacy_source(record):
        rule = policy.get('legacy_rule')
        if rule:
            return _decision(rule, policy)
        # A default for new books must never silently cover copied old sources.
        return None
    rules = policy['source_rules']
    found = [rule for rule in rules if matches(record, rule['match'])]
    require(len(found) <= 1, 'Overlapping current provenance rules for one source')
    default = policy.get('new_material_rule')
    registered = registered_material or _registered_material(record)
    if default and (registered or found):
        declaration = source_translation_declaration(record)
        if declaration:
            return _decision({'classification': declaration['classification'],
                              'basis': 'explicit_source_translation_declaration'}, policy, declaration)
    if found:
        return _decision(found[0], policy)
    return _decision(default, policy) if default and registered else None


def counterpart_decision_for(data, policy):
    """Classify a linked English source independently from its parent record."""
    if not policy or not policy.get('new_material_rule') or not isinstance(data, dict):
        return None
    text = data.get('text')
    linked = isinstance(text, str) and bool(text.strip())
    url = data.get('source_url')
    if not linked and data.get('scope') == 'external_source' and isinstance(url, str):
        try:
            parsed = urlsplit(url)
            linked = (parsed.scheme in ('http', 'https') and bool(parsed.netloc) and
                      not parsed.username and not parsed.password)
        except ValueError:
            linked = False
    if not linked:
        return None
    if legacy_source(data):
        rule = policy.get('legacy_rule')
        return _decision(rule, policy) if rule else None
    declaration = source_translation_declaration(data)
    if declaration:
        return _decision({'classification': declaration['classification'],
                          'basis': 'explicit_source_translation_declaration'}, policy, declaration)
    if data.get('translation_origin') == 'ai':
        return _decision({'classification': 'ai', 'basis': 'explicit_counterpart_translation_origin'}, policy)
    return _decision(policy['new_material_rule'], policy)


def apply_policy(record, policy, registered_material=False):
    decision = decision_for(record, policy, registered_material)
    if decision is not None:
        if record.get('kind') == 'legacy_source_document':
            record['current_policy'] = decision
        else:
            record['translation_provenance']['current_policy'] = decision
    return record


def apply_material_policy(record, material):
    overrides = material.get('current_translation_policy_overrides') or {}
    decision = overrides.get(record.get('id'), material.get('current_translation_policy'))
    if decision is not None:
        record['translation_provenance']['current_policy'] = copy.deepcopy(decision)
    return record


def classification(record):
    provenance = record.get('translation_provenance') or {}
    current = provenance.get('current_policy', record.get('current_policy', {}))
    if current.get('classification') in CLASSIFICATIONS:
        return current['classification']
    if record.get('kind') == 'legacy_source_document':
        return 'unknown'
    if provenance.get('ai_translation', record.get('ai_translation')) is True:
        return 'ai'
    if provenance.get('ai_translation', record.get('ai_translation')) is False:
        return 'human'
    if provenance.get('origin') in ('publisher_human_workflow', 'human_translator_credited'):
        return 'human'
    return 'unknown'

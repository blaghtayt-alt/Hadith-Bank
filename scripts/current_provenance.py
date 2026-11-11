"""Apply explicit owner source classifications without rewriting source history."""
import copy
import datetime
from pathlib import Path

from build_reader import local, parse_json


POLICY_PATH = 'catalog/provenance-policy.json'
CLASSIFICATIONS = ('human', 'ai', 'unknown')
MATCH_FIELDS = {'source_name', 'book_key', 'package_root', 'source_id', 'source_ids', 'kind'}


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


def decision_for(record, policy):
    if not policy:
        return None
    rules = policy['source_rules']
    if record.get('kind') == 'legacy_source_document':
        rules = [policy['legacy_rule']] if policy.get('legacy_rule') else []
    found = [rule for rule in rules if matches(record, rule['match'])]
    require(len(found) <= 1, 'Overlapping current provenance rules for one source')
    if not found:
        return None
    rule = found[0]
    return {'classification': rule['classification'], 'basis': rule['basis'],
            'decision_date_japan': policy['decision_date_japan'], 'policy_path': POLICY_PATH}


def apply_policy(record, policy):
    decision = decision_for(record, policy)
    if decision is not None:
        if record.get('kind') == 'legacy_source_document':
            record['current_policy'] = decision
        else:
            record['translation_provenance']['current_policy'] = decision
    return record


def apply_material_policy(record, material):
    if material.get('current_translation_policy') is not None:
        record['translation_provenance']['current_policy'] = copy.deepcopy(material['current_translation_policy'])
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

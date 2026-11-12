"""Apply exact-source quality decisions only to derived counterpart views.

Original exports, occurrence text, Arabic and translation-origin classifications
are not edited. A corrected translation hash does not inherit an older decision.
"""
import copy
import hashlib
import json
from pathlib import Path
import re

from counterpart_identity import provider_identity
from counterpart_review import local

POLICY_PATH = 'catalog/counterpart-quality-policy.json'
SCHEMA = 'hadith-bank-counterpart-quality-policy-v1'
ACTION = 'withhold_derived_counterpart_text'
PARTIAL_ACTION = 'qualify_partial_counterpart_text'


def load_quality_policy(root):
    root = Path(root).resolve()
    path = local(root, POLICY_PATH)
    if not path.is_file():
        return None
    raw = path.read_bytes()
    policy = json.loads(raw)
    if policy.get('schema') != SCHEMA or not isinstance(policy.get('decisions'), list):
        raise ValueError('Unrecognized counterpart quality policy')
    identities = set()
    for decision in policy['decisions']:
        if not isinstance(decision, dict):
            raise ValueError('Counterpart quality decision must be an object')
        for key in ('id', 'source_record_id', 'message', 'reason_code', 'reviewed_date'):
            if not isinstance(decision.get(key), str) or not decision[key].strip():
                raise ValueError('Counterpart quality decision requires ' + key)
        if decision['id'] in identities:
            raise ValueError('Duplicate counterpart quality decision')
        identities.add(decision['id'])
        if (decision.get('provider') != 'hadeethenc' or decision.get('language') != 'english' or
                decision.get('action') not in (ACTION, PARTIAL_ACTION) or
                not re.fullmatch(r'[1-9][0-9]*', decision['source_record_id']) or
                not isinstance(decision.get('text_sha256'), str) or
                not re.fullmatch(r'[0-9a-f]{64}', decision['text_sha256'])):
            raise ValueError('Quality decision needs an exact supported provider, language, ID and text hash')
        if not isinstance(decision.get('evidence'), dict) or not decision['evidence']:
            raise ValueError('Counterpart quality decision requires preserved source evidence')
        if decision['action'] == PARTIAL_ACTION and (
                not isinstance(decision.get('citation_note'), str) or not decision['citation_note'].strip()):
            raise ValueError('Partial counterpart qualification requires a specific citation note')
    return {**policy, 'policy_path': POLICY_PATH, 'policy_sha256': hashlib.sha256(raw).hexdigest()}


def _own_provider_identity(item):
    # Do not inherit the parent occurrence's provider or the reviewed bundle's
    # generic adapter name. The linked language has its own source identity.
    for key in ('provider', 'source_provider'):
        value = item.get(key)
        if value is not None and (not isinstance(value, str) or value.strip().casefold() != 'hadeethenc'):
            return None
    identity = provider_identity({'source': {'record_url': item.get('source_url')}})
    if identity['status'] != 'linked' or identity['id'] != item.get('source_record_id'):
        return None
    return identity['provider'], identity['id']


def apply_quality_policy(result, policy):
    """Return a narrowed view without making a withheld source an external link."""
    if not isinstance(result, dict) or not policy:
        return result
    english = result.get('english')
    if not isinstance(english, dict) or not isinstance(english.get('text'), str):
        return result
    identity = _own_provider_identity(english)
    if identity is None:
        return result
    actual_hash = hashlib.sha256(english['text'].encode('utf-8')).hexdigest()
    matching = [decision for decision in policy['decisions'] if
                (decision['provider'], decision['source_record_id']) == identity and
                decision['language'] == 'english' and decision['text_sha256'] == actual_hash]
    if not matching:
        return result
    value = copy.deepcopy(result)
    holds = [decision for decision in matching if decision['action'] == ACTION]
    if not holds:
        item = value['english']
        item.setdefault('source_scope', item.get('scope'))
        item.update(scope='source_excerpt', coverage='partial')
        notes = [item.get('citation_note') or '']
        for decision in matching:
            note = decision['citation_note'].strip()
            if not any(note in previous for previous in notes):
                notes.append(note)
        item['citation_note'] = ' '.join(note for note in notes if note)
        item['quality_qualification_ids'] = sorted(set(item.get('quality_qualification_ids') or []) |
                                                   {decision['id'] for decision in matching})
        item['quality_policy_path'] = policy['policy_path']
        item['quality_policy_sha256'] = policy['policy_sha256']
        return value
    matching = holds
    history = copy.deepcopy(english)
    history.pop('text', None)
    history.update(status='withheld', actual_text_sha256=actual_hash,
                   decision_id=matching[0]['id'],
                   quality_decision_ids=[decision['id'] for decision in matching],
                   quality_policy_path=policy['policy_path'], quality_policy_sha256=policy['policy_sha256'])
    value.setdefault('withheld_languages', {})['english'] = history
    value['english'] = None
    advisories = value.setdefault('quality_advisories', [])
    for decision in matching:
        advisories.append({'decision_id': decision['id'], 'language': 'english',
            'provider': decision['provider'], 'source_record_id': decision['source_record_id'],
            'text_sha256': actual_hash, 'reason_code': decision['reason_code'],
            'message': decision['message'], 'policy_path': policy['policy_path'],
            'policy_sha256': policy['policy_sha256']})
    # Keep the original matching status/evidence; quality is a separate decision.
    return value

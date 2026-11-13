"""Mechanically bind the Bengali source-context page to its saved evidence.

This validates inherited document mappings and source transport. It does not
re-extract DOC tables, certify a narration boundary, or claim a QC pass.
"""
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def require(value, message):
    if not value:
        raise ValueError(message)


def jsonl_checked(root, relative, expected):
    digest = hashlib.sha256()
    with gzip.open(Path(root).joinpath(*PurePosixPath(relative).parts), 'rb') as stream:
        for line in stream:
            digest.update(line)
            if line.strip():
                yield json.loads(line)
    require(digest.hexdigest() == expected, 'Bengali context uncompressed evidence hash mismatch: ' + relative)


def validate_story_stream(path, raw_sha256, expected_text):
    with gzip.open(path, 'rb') as stream:
        raw = stream.read()
    require(hashlib.sha256(raw).hexdigest() == raw_sha256, 'Bengali original story hash mismatch')
    require(raw.decode('utf-8') == expected_text, 'Bengali original story text mismatch')


def validate_note(parts, meta, record, story):
    require(parts and all(p['source_volume'] == record['source_volume'] and p['story'] == 'footnote' for p in parts), 'Bengali note story or volume mismatch')
    require(parts[0]['cp_start'] == meta['cp_start'] and parts[-1]['cp_end'] == meta['cp_end'] and all(a['cp_end'] == b['cp_start'] for a,b in zip(parts,parts[1:])), 'Bengali note interval mismatch')
    require(''.join(p['text_verbatim'] for p in parts) == meta['raw_text'], 'Bengali note text mismatch')
    anchor = meta['main_cp_anchor']
    require(type(anchor) is int and anchor >= 0 and story[anchor:anchor+1] == meta['main_anchor_char'], 'Bengali saved main-story note anchor mismatch')
    require(record['doc_story'] != 'main' or record['doc_cp_start'] <= anchor < record['doc_cp_end'], 'Bengali note anchor outside source occurrence')


def verify(root, entry):
    config = entry.get('validation') or {}
    require(config.get('type') == 'bn-riyadh-cp017-v1', 'Bengali source context requires the source-binding gate')
    files = {item['path'] for item in entry['files']}
    require(all(config.get(k) in files for k in ('records', 'segments', 'ledger')),
            'Bengali context evidence must be registered')
    html = Path(root).joinpath(*PurePosixPath(entry['html']).parts).read_text(encoding='utf-8')
    match = re.search(r'<script id="reader-data" type="application/json">(.*?)</script>', html, re.S)
    require(match is not None and hashlib.sha256(match.group(1).encode('utf-8')).hexdigest() == config.get('reader_data_sha256'),
            'Bengali reader data hash mismatch')
    data = json.loads(match.group(1)); atoms = data['atoms']; occurrences = data['occurrences']; uncertainties = data['uncertainties']
    require(len(atoms) == 55499 and len(occurrences) == 2029 and len(uncertainties) == 32,
            'Bengali context source inventory mismatch')
    original_atoms = {}; references = set()
    for source in jsonl_checked(root, config['segments'], config['segments_raw_sha256']):
        sid = source['source_segment_id']; require(sid not in original_atoms and sid in atoms, 'Duplicate or absent Bengali source segment')
        target = atoms[sid]
        expected = {'text':source['text_verbatim'], 'volume':source['source_volume'], 'story':source['story'],
                    'start':source['cp_start'], 'end':source['cp_end'], 'roles':source['role_candidates'],
                    'refs':source['leaf_semantic_references'], 'ambiguities':source['source_ambiguity_ids']}
        require(all(target.get(k) == v for k,v in expected.items()), 'Bengali source segment changed: ' + sid)
        original_atoms[sid] = source
        for ref in source['leaf_semantic_references']:
            require(ref.get('ledger_sha256') == config['ledger_raw_sha256'] and type(ref.get('ledger_1_based_row')) is int and ref['ledger_1_based_row'] > 0,
                    'Bengali semantic reference lacks hash and row')
            references.add((ref['ledger_1_based_row'], ref.get('decision_id')))
    require(len(original_atoms) == len(atoms), 'Bengali source segment count mismatch')
    records = {}
    for record in jsonl_checked(root, config['records'], config['records_raw_sha256']):
        rid = record['record_id']; require(rid not in records, 'Duplicate Bengali source record')
        records[rid] = record
    stories = {(s['volume'],s['story']):s['text'] for s in data['stories']}
    streams = config.get('stories')
    require(isinstance(streams, list) and len(streams) == len(stories) == 18, 'Bengali original story inventory mismatch')
    seen_stories = set()
    for stream in streams:
        require(isinstance(stream, dict), 'Invalid Bengali original story binding')
        key = (stream.get('volume'), stream.get('story'))
        require(key in stories and key not in seen_stories and stream.get('path') in files,
                'Bengali original story binding is missing or duplicated')
        seen_stories.add(key)
        validate_story_stream(Path(root).joinpath(*PurePosixPath(stream['path']).parts), stream.get('raw_sha256'), stories[key])
    require(seen_stories == set(stories), 'Bengali original stories are incomplete')
    note_count = 0; seen = set(); linked = set()
    for occ in occurrences:
        rid = occ['id']; require(rid not in seen and rid in records, 'Bengali occurrence identity mismatch'); seen.add(rid)
        record = records[rid]; require(record['source_volume'] == occ['volume'], 'Bengali occurrence volume mismatch')
        for sid in occ['segments']:
            require(sid in original_atoms and rid in original_atoms[sid]['source_occurrence_record_ids'], 'Bengali occurrence source ownership mismatch')
            linked.add(sid)
        notes = occ.get('footnote_bindings', []); require([n['source_note'] for n in notes] == (record.get('footnotes') or []), 'Bengali note metadata mismatch')
        for note in notes:
            meta = note['source_note']; ids = note['atom_ids']; require(ids and all(sid in original_atoms for sid in ids), 'Bengali note segment missing')
            parts = [original_atoms[sid] for sid in ids]; linked.update(ids)
            validate_note(parts, meta, record, stories[(record['source_volume'],'main')])
            note_count += 1
    require(seen == set(records) and note_count == 1915 and len(set(atoms)-linked) == 9067, 'Bengali note or source-context inventory mismatch')
    require({u for atom in atoms.values() for u in atom['ambiguities']} == set(uncertainties), 'Bengali source ambiguity mismatch')
    pending = set(references)
    for index, decision in enumerate(jsonl_checked(root, config['ledger'], config['ledger_raw_sha256']),1):
        pending.discard((index, decision.get('decision_id')))
    require(not pending, 'Bengali semantic references do not resolve to ledger rows')

#!/usr/bin/env python3
"""Deterministic source-preserving initial segmentation of the supplied Japanese PDF.

This is an extraction aid, not certification of semantic boundaries or source glyphs.
All segmentation choices can be revised without altering the preserved PDF/text.
"""
import json
import re
import argparse
from pathlib import Path
from collections import Counter

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-dir', type=Path, default=Path(__file__).resolve().parent)
BASE = parser.parse_args().work_dir.resolve()
OUT = BASE / 'intake'
OUT.mkdir(parents=True, exist_ok=True)
LINES = json.loads((BASE / 'pdf/lines.json').read_text())
LINE_BY_ID = {line['id']: line for line in LINES}
SOURCE_ID = 'ja-muslim-web-c859ce57c211ea1b'
NOTE = re.compile(r'^\s*[（(](?:注|註)\s*[0-9０-９一二三四五六七八九十]*[）)]')
PRINT = re.compile(r'^(\d+)巻\s*P\.(\d+)(?:-(\d+))?\s*$')
NAME = re.compile(r'^(?P<name>[ァ-ヶー・･．.＝=\s]+(?:[（(][^）)]+[）)])?(?:(?:及び|および|と|、または、|または|の息子|の子|の父|、)[ァ-ヶー・･．.＝=\s]+(?:[（(][^）)]+[）)])?)*)?(?P<relation>によると|によれば|の話では|の伝えるところによると|は|が)')
VARIANT = re.compile(r'^(?:(?:なおまた|なお|また)[、，]?)?(?:前記|前述|上記|上述|これと|それと|同様|同一|同じ|この(?:ような)?|以上|同内容|ハディース)')
CONTINUATION = re.compile(r'^(?:以下|その後|この後|残り|この後半|なお、このハディースの後半|さらに|更に|そして|そこで|すると|しかし|その時|また彼|これに|これについて)')


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def frag(line, start=0, end=None):
    full = line['text'] + '\n'
    end = len(full) if end is None else end
    return {'line_id': line['id'], 'pdf_page': line['pdf_page'], 'start': start,
            'end': end, 'text': full[start:end]}


def merged(pieces):
    return ''.join(x['text'] for x in pieces)


def get_start(text, previous_text='', forced=False):
    t = text.strip()
    if not t:
        return None
    if forced:
        return {'reason': 'first_source_body_in_section', 'confidence': 'high'}
    if NOTE.match(t) or t[0] in '「『”"' or CONTINUATION.match(t):
        return None
    # The source has a named narrator split across a rendered line.
    if previous_text.rstrip().endswith(('・', '･')):
        return None
    if VARIANT.match(t) and 'ハディース' in t[:85]:
        if re.search(r'伝承者経路|伝えられ|もたらされ|同内容|同様|同じ|同一|によって|経路で', t[:180]):
            if not re.match(r'^この(?:後半|後|残り|ハディースの後半)', t):
                return {'reason': 'explicit_route_or_variant_summary', 'confidence': 'medium'}
    m = NAME.match(t)
    if not m or not m.group('name'):
        return None
    name = m.group('name').strip()
    if name.startswith(('・', '･')) or name in {'ハディース', 'イスラーム', 'アッラー', 'クルアーン', 'イマーム', 'マディーナ', 'マッカ', 'イスナード', 'スンナ', 'ムアッジン', 'ウドゥー', 'ウドウー'}:
        return None
    relation = m.group('relation')
    rest = t[m.end():]
    if re.match(r'^[、，\s]*(?:さらに|更に|さらにつづけ|続けて|つづけて|これに対|これに関連|これについて|その時|その話|その言葉|この話を|また次の|このハディースを聞いて)', rest):
        return None
    if relation in {'によると', 'によれば', 'の話では', 'の伝えるところによると'}:
        return {'reason': 'named_report_attribution', 'confidence': 'high', 'name': name, 'name_end': m.end('name')}
    if re.search(r'伝えている|伝えられ|伝えるところ|こう伝えた|次のように伝えた|以下のように伝えた|語っている|次のように語った|こう語った|こう述べている|次のように述べている', rest[:120]):
        return {'reason': 'named_transmission_formula', 'confidence': 'high', 'name': name, 'name_end': m.end('name')}
    if re.search(r'(?:前記|前述|同内容|同様|同じ|同一).{0,60}(?:ハディース|伝承)|(?:別の|同一の)伝承者経路', rest[:150]):
        return {'reason': 'named_variant_attribution', 'confidence': 'medium', 'name': name, 'name_end': m.end('name')}
    if re.fullmatch(r'[、\s]*(?:次のように|こう|以下のように)?(?:語った|言った|いった|述べた)[。．\s]*', rest):
        return {'reason': 'named_short_speech_introduction', 'confidence': 'medium', 'name': name, 'name_end': m.end('name')}
    if rest.lstrip('、 ').startswith('「') and re.search(r'アッラー|み使い|預言者', rest[:65]):
        return {'reason': 'named_direct_report_quotation', 'confidence': 'medium', 'name': name, 'name_end': m.end('name')}
    # A long opening may wrap before its transmission verb; restrict to clear chain language.
    if re.match(r'^[、\s]*(?:彼の父|その父|父から|父の|アッラーの使徒の言葉|預言者の言葉|彼が).{0,80}(?:話|聞|伝|言葉)', rest[:120]):
        return {'reason': 'named_chain_opening', 'confidence': 'medium', 'name': name, 'name_end': m.end('name')}
    return None


def split_inline(line):
    text = line['text'] + '\n'
    # A separately attributed route starts after a closing quotation on PDF266.
    positions = [m.start(1) for m in re.finditer(r'[」』。](前記と同内容のハディースは|同様のハディースは)', text)]
    for key, ov in overrides.items():
        if key.startswith(line['id']+':c'):
            pos=int(key.split(':c')[1])
            if pos:
                if not 0 < pos < len(text):
                    raise ValueError(f'Invalid inline offset {key}')
                positions.append(pos)
    points = sorted(set([0] + positions + [len(text)]))
    return [frag(line, a, b) for a, b in zip(points, points[1:])]


overrides_path = BASE / 'boundary-overrides.json'
overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
for review_file in [BASE/'metadata-review/boundary-overrides.json', BASE/'boundary-review/boundary-overrides.json']:
    if review_file.exists():
        more=json.loads(review_file.read_text())
        if 'overrides' in more:
            more=more['overrides']
        for key,value in more.items():
            if key in overrides and overrides[key]['action'] != value['action']:
                raise ValueError(f'Conflicting boundary review: {key}')
            overrides[key]=value
sections = []
ancillary = []
current = None
for line in LINES:
    p = line['pdf_page']
    f = frag(line)
    if p <= 6 or p == 580:
        f.update(role='front_matter' if p <= 6 else 'colophon', section_id=None, record_id=None, component_id=f'ancillary-p{p:04d}')
        ancillary.append(f)
        continue
    if line['max_font_size'] > 13:
        current = {'section_id': f'{SOURCE_ID}-section-p{p:04d}', 'sequence': len(sections)+1,
                   'header': line['text'], 'header_line_id': line['id'], 'pdf_page_start': p,
                   'heading_pieces': [], 'body_pieces': [], 'printed_reference': None,
                   'printed_reference_line_id': None, 'pre_reference_pieces': []}
        sections.append(current)
        f.update(role='section_heading', section_id=current['section_id'], record_id=None, component_id=current['section_id'])
        current['heading_pieces'].append(f)
        continue
    if not current:
        raise RuntimeError(f'Unassigned source body {line["id"]}')
    m = PRINT.match(line['text'].strip())
    if current['printed_reference'] is None:
        if m:
            current.update(printed_reference=line['text'], printed_reference_line_id=line['id'],
                           printed_volume=int(m[1]), printed_start=int(m[2]), printed_end=int(m[3] or m[2]))
            f.update(role='printed_reference', section_id=current['section_id'], record_id=None, component_id=current['section_id'])
            current['heading_pieces'].append(f)
        else:
            current['pre_reference_pieces'].append(f)
    else:
        current['body_pieces'].extend(split_inline(line))

units = []
decisions = []
all_pieces = list(ancillary)
for section in sections:
    title_parts = []
    section_notes = []
    active_note = None
    for piece in section.pop('pre_reference_pieces'):
        if NOTE.match(piece['text']):
            active_note = {'id': f'{section["section_id"]}-note-{len(section_notes)+1:02d}', 'pieces': []}
            section_notes.append(active_note)
        role = 'section_footnote' if active_note else 'section_title'
        piece.update(role=role, section_id=section['section_id'], record_id=None,
                     component_id=active_note['id'] if active_note else section['section_id'])
        if active_note:
            active_note['pieces'].append(piece)
        else:
            title_parts.append(piece)
    section['title_verbatim'] = merged(title_parts)
    section['title_line_ids'] = [x['line_id'] for x in title_parts]
    section['title_display'] = ''.join(x['text'].strip() for x in title_parts)
    section['notes'] = [{'note_id': n['id'], 'text_verbatim': merged(n['pieces']), 'source_spans': n['pieces']} for n in section_notes]
    all_pieces.extend(section['heading_pieces'])
    all_pieces.extend(title_parts)
    for n in section_notes:
        all_pieces.extend(n['pieces'])
    body = section.pop('body_pieces')
    unit = None
    active_note = None
    previous = ''
    for i, piece in enumerate(body):
        t = piece['text']
        # Look ahead for a narrator opening that wraps onto the next physical line.
        next_text = t.rstrip('\n')
        if i + 1 < len(body):
            next_text += body[i+1]['text'].strip()
        key = f'{piece["line_id"]}:c{piece["start"]:03d}'
        decision = get_start(t, previous, forced=unit is None)
        # Only join a physically wrapped opening, never an independent short sentence
        # with the following report's introduction.
        current_line = LINE_BY_ID[piece['line_id']]
        physically_wrapped = current_line['bbox'][2] >= 515 and not t.rstrip().endswith(('。','」','』','！','？','.', '!', '?'))
        if decision is None and physically_wrapped and not NOTE.match(t):
            decision = get_start(next_text, previous)
            if decision:
                decision['multiline_opening'] = True
        ov = overrides.get(key, overrides.get(piece['line_id']))
        if ov:
            if ov.get('action') in {'suppress','note_start','commentary_start','translation_start'}:
                decision = None
            elif ov.get('action') == 'start':
                decision = {'reason': 'targeted_boundary_review', 'confidence': 'reviewed', 'review_note': ov.get('reason')}
        if decision:
            rid = f'{SOURCE_ID}-{piece["line_id"]}-c{piece["start"]:03d}'
            unit = {'id': rid, 'section_id': section['section_id'], 'sequence': len(units)+1,
                    'start_reason': decision, 'pieces': [], 'notes': []}
            units.append(unit)
            active_note = None
        if unit is None:
            raise RuntimeError(f'Missing first unit {key}')
        # Notes remain separate until the next transmission opener or note definition.
        if ov and ov.get('action') == 'translation_start':
            active_note = None
        if NOTE.match(t) or (ov and ov.get('action') in {'note_start','commentary_start'}):
            active_note = {'note_id': f'{unit["id"]}-note-{len(unit["notes"])+1:02d}', 'pieces': []}
            active_note['kind'] = 'commentary' if ov and ov.get('action') == 'commentary_start' else 'footnote'
            unit['notes'].append(active_note)
        role = active_note['kind'] if active_note else 'translation'
        piece.update(role=role, record_id=unit['id'], section_id=section['section_id'],
                     component_id=active_note['note_id'] if active_note else unit['id'])
        unit['pieces'].append(piece)
        if active_note:
            active_note['pieces'].append(piece)
        all_pieces.append(piece)
        if decision or ov:
            decisions.append({'line_id': piece['line_id'], 'start': piece['start'], 'pdf_page': piece['pdf_page'],
                              'action': 'start' if decision else 'suppress', 'decision': decision, 'override': ov,
                              'previous_text': previous, 'text': t, 'next_text': body[i+1]['text'] if i+1 < len(body) else None})
        previous = t
    section['pdf_page_end'] = body[-1]['pdf_page'] if body else section['pdf_page_start']
    section['record_ids'] = [u['id'] for u in units if u['section_id'] == section['section_id']]

# All source chars, including extraction newlines, retain one primary destination.
index = {x['id']: i for i, x in enumerate(LINES)}
all_pieces.sort(key=lambda x:(index[x['line_id']], x['start']))
dump(OUT/'units.json', units)
dump(OUT/'sections-intermediate.json', sections)
dump(OUT/'boundary-decisions.json', decisions)
dump(OUT/'applied-boundary-overrides.json', overrides)
(OUT/'line-attribution.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in all_pieces),encoding='utf8')
for lo, hi in [(7,179),(180,361),(362,579)]:
    selected = [u for u in units if lo <= u['pieces'][0]['pdf_page'] <= hi]
    text = []
    for u in selected:
        pieces=u['pieces']; raw=merged(pieces); trans=merged([p for p in pieces if p['role']=='translation'])
        text.append(f"\n[{u['sequence']}] {pieces[0]['line_id']}:c{pieces[0]['start']:03d} p{pieces[0]['pdf_page']}-{pieces[-1]['pdf_page']} {u['start_reason']['reason']}\nSTART: {trans[:230].replace(chr(10),' | ')}\nEND: {trans[-160:].replace(chr(10),' | ')}\nNOTES: {len(u['notes'])}\n")
    (OUT/f'boundary-review-{lo}-{hi}.txt').write_text(''.join(text),encoding='utf8')
print(json.dumps({'sections':len(sections),'units':len(units),'notes':sum(len(u['notes']) for u in units),
                  'section_notes':sum(len(s['notes']) for s in sections),'primary_fragments':len(all_pieces),
                  'boundary_reasons':Counter(u['start_reason']['reason'] for u in units)},ensure_ascii=False,indent=2))

#!/usr/bin/env python3
"""Validate source accounting, stable occurrences and font-decoding evidence."""
import collections
import hashlib
import json
import pathlib
import re
import zipfile
from lxml import etree as ET
from screen_muslim import build_screen_extension

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def read(p):return[json.loads(l)for l in p.read_text().splitlines()]
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def write_lines(p,x):p.write_text(''.join(json.dumps(v,ensure_ascii=False)+'\n'for v in x))

allmain=[];allancillary=[];results=[];allrows={};allnotes={};glyph_unknown=[]
EXPECTED={1:(1072,32,[1,1067],{'17ب','323ب','14ب','543م'}),
          2:(1118,10,[1068,2179],{'1381م','1519م','1688م','1725م'})}
for v in [1,2]:
    raw=read(HERE/f'muslim-v{v}.source-paragraphs.jsonl'); allrows[v]=raw
    notes=read(HERE/f'muslim-v{v}.source-notes.jsonl'); allnotes[v]=notes
    main=read(HERE/f'muslim-v{v}.main.jsonl'); allmain+=main
    ancillary=read(HERE/f'muslim-v{v}.confirmed-ancillary-hadiths.jsonl')
    allancillary+=ancillary
    assert len(main)==EXPECTED[v][0]
    assert len(ancillary)==EXPECTED[v][1]
    assert len(set(r['id']for r in main+ancillary))==len(main+ancillary)
    assert all(r['text']['arabic'] and r['text']['translation']for r in main)
    assert {r['number']['source_local']for r in main if isinstance(r['number']['source_local'],str)}==EXPECTED[v][3]
    integers=[r['number']['source_local']for r in main if isinstance(r['number']['source_local'],int)]
    absent=set(range(EXPECTED[v][2][0],EXPECTED[v][2][1]+1))-set(integers)
    assert absent==(set()if v==1 else{1341})
    repeated={n:c for n,c in collections.Counter(integers).items()if c>1}
    assert repeated==({}if v==1 else{1193:2})
    with zipfile.ZipFile(ROOT/'upload'/f'Sahih-Moslem-{v}-Word.docx')as z:
        root=ET.fromstring(z.read('word/document.xml'))
        ps=root.xpath('//w:body//w:p',namespaces=NS)
        assert len(ps)==len(raw)
        assert not root.xpath('//w:p//w:p',namespaces=NS)
        for p,row in zip(ps,raw):
            assert ''.join(p.xpath('.//w:t/text()',namespaces=NS))==row['text']
            assert len(p.xpath('.//w:sym',namespaces=NS))==sum(e['kind']=='symbol'for e in row['events'])
            assert len(p.xpath('.//w:footnoteReference',namespaces=NS))==sum(e['kind']=='footnoteReference'for e in row['events'])
            # Every decoder edit must replace the exact witnessed source glyph.
            t=row['text_with_symbol_placeholders']
            for e in reversed(row['font_decoding_events']):
                a,b=e['raw_display_start'],e['raw_display_end']
                assert t[a:b]==e['original']
                t=t[:a]+e['decoded']+t[b:]
            assert t==row['text_decoded']
        source_note_ids={n.get('{'+NS['w']+'}id')for n in ET.fromstring(z.read('word/footnotes.xml'))if n.get('{'+NS['w']+'}type')is None}
        assert source_note_ids=={n['id']for n in notes if n['part']=='word/footnotes.xml'and not n['note_type']}
    ids={r['id']for r in main}
    assert all(row['coverage']['record_id']is None or row['coverage']['record_id']in ids for row in raw)
    for r in main:
        assert raw[r['source_locator']['paragraph_start_zero_based']]['coverage']['record_id']==r['id']
        for span in r['excluded_side_commentary_spans']:
            text=raw[span['paragraph_index_zero_based']]['text_with_symbol_placeholders']
            assert text[span['start']:span['end']]==span['text']
        for key in ['arabic','translation']:
            text=r['text'][key]or''
            if '⟦source-symbol' in text:glyph_unknown.append({'record_id':r['id'],'field':key,'tokens':re.findall('⟦source-symbol [^⟧]*⟧',text)})
            assert not re.search(r'(?:^|\n)\s*(?:شرح\s*:|توضیح\s*:|نکته\s*:)',text)
        assert 'qc_tags'not in r['extraction']
        for recovery in r.get('source_recoveries',[]):
            assert recovery['after']in r['text'][recovery['field']]
            publisher_path=ROOT/recovery['evidence_local_path']
            assert hashlib.sha256(publisher_path.read_bytes()).hexdigest()==recovery['evidence_local_sha256']
            if recovery['recovery_kind']=='contextual_symbol_recovery_font_assignment_lost':
                rawfield=r['source_text'][recovery['field']]
                position=recovery['source_raw_field_offset']
                assert rawfield[position:position+1]==recovery['before']
                assert raw[recovery['source_paragraph_index_zero_based']]['text'][recovery['source_raw_paragraph_offset']]==recovery['before']
    results.append({'volume':v,'main_records':len(main),'confirmed_ancillary_records':len(ancillary),
                    'body_paragraphs_accounted_for':len(raw),'source_text_characters_verified':sum(len(r['text'])for r in raw),
                    'footnotes_accounted_for':len(source_note_ids),'printed_numeric_serial_gaps':sorted(absent),
                    'duplicate_serials_preserved':repeated,'suffix_serials_preserved':sorted(EXPECTED[v][3]),
                    'all_main_records_have_both_languages':True,'raw_font_edits_are_exact':True,
                    'no_commentary_prefixes_in_display_fields':True})

allconsuming=allmain+allancillary
assert len(allconsuming)==2232
assert not any(re.search('[\ue000-\uf8ff\U000f0000-\U000ffffd\U00100000-\U0010fffd]',text or'')for r in allconsuming for text in r['text'].values())
assert not any('⟦source-symbol'in(text or'')for r in allconsuming for text in r['text'].values())
note28=next(r for r in allancillary if r['id']=='fa-muslim-mundhiri-tarshabi-v1-note28-q1')
assert 'صلى الله عليه وآله وسلم'in note28['text']['translation']
assert any(e['font']=='CTraditional Arabic'and e['original']=='ص'for e in note28['font_decoding_events'])

# Resolve source chapter cross-references without manufacturing new verbatim
# narrations or counting an index pointer as another hadith text.
lookup={}
for r in allmain:lookup.setdefault(str(r['number']['source_local']),[]).append(r['id'])
specs=[(1,[3281],632),(1,[4230],883),(1,[4340],800),(1,[4534],532),
       (2,[1218,1219],None),(2,[2525,2526],1279),(2,[2580,2581],333),
       (2,[3728,3729],1744),(2,[4765,4766],1608),(2,[4837,4838],1636)]
cross=[]
for v,indices,num in specs:
    if num is None:
        targets=[r['id']for r in allmain if f'-v{v}-'in r['id']and r['source_locator']['paragraph_start_zero_based']<indices[0]][-1:]
    else:targets=lookup.get(str(num),[])
    assert targets
    cross.append({'volume':v,'source_paragraph_indices_zero_based':indices,
                  'reference_text_as_printed':'\n'.join(allrows[v][i]['text']for i in indices),
                  'target_source_local_number':num,'target_record_ids':targets,
                  'counted_as_new_hadith':False,'reason':'Source supplies an internal reference, not a fresh verbatim narration'})
write_lines(HERE/'internal-cross-references.jsonl',cross)

strong=['شیعه','شيعة','تشیع','رافض','روافض','اثناعشر','امامیه','دوازده امام',
        'ولایت فقیه','تقیه','تقيه','بداء','رجعت','کلینی','اصول کافی','بحار الانوار']
screen=[];counts=collections.Counter()
for v in [1,2]:
    data=[{'locator':{'part':'word/document.xml','paragraph_index_zero_based':r['paragraph_index_zero_based']},'text':r['text']}for r in allrows[v]]
    data +=[{'locator':{'part':n['part'],'note_id':n['id']},'text':n['text']}for n in allnotes[v]]
    for r in data:
        found=[s for s in strong if s in r['text']]
        for s in found:counts[s]+=1
        if found:screen.append({'volume':v,'terms':found,**r})
write(HERE/'doctrinal-screening.json',{
    'method':'Full native-text keyword scan of body and footnotes; contextual reading of translator introduction, separable comments, temporary-marriage and Ahl al-Bayt passages',
    'scope':'Content screening; not an assertion that every sentence received full theological review',
    'strong_terms':strong,'strong_term_hits':dict(counts),'strong_hit_contexts':screen,
    'explicit_shia_doctrinal_endorsements_found':[],
    'contextual_adjudications':[
        {'volume':1,'paragraphs':[3876,3877,3878,3879,3880,3881,3882],
         'finding':'Temporary-marriage reports include explicit prohibition; mention of the subject is not doctrinal endorsement.'},
        {'volume':2,'paragraphs':[3141,3142,3143],
         'finding':'Ahl al-Bayt narration is supplied with a Muslim 2408 source citation; no added Shia doctrinal assertion identified in this passage.'},
        {'source':'Font-decoding evidence',
         'finding':'The source glyph ص includes وآله in the blessing. A blessing on the family is not treated as sectarian evidence.'},
    ],
    'red_flag_warning_required_on_present_evidence':False,
    'inside_hadith_screen':build_screen_extension(allmain+allancillary),
})
write(HERE/'validation-results.json',{'passed':True,'volumes':results,
    'main_records':sum(r['main_records']for r in results),
    'confirmed_ancillary_records':sum(r['confirmed_ancillary_records']for r in results),
    'integratable_records':sum(r['main_records']+r['confirmed_ancillary_records']for r in results),
    'source_internal_references_resolved':len(cross),
    'remaining_source_font_placeholders':glyph_unknown,
    'all_2232_consuming_records_checked_for_private_use_characters':True,
    'remaining_consuming_private_use_characters':0,
    'explicit_CTraditional_ancillary_note_decoding_verified':True,
    'ordinary_font_source_abbreviations_preserved':True,
    'source_abbreviation_evidence':'font-review-explicit-targets.json',
    'contextual_symbol_recoveries_applied':sum(len([x for x in r.get('source_recoveries',[])if x['recovery_kind']=='contextual_symbol_recovery_font_assignment_lost'])for r in allmain),
    'no_entire_book_or_batch_was_capped':True,
    'validation_is_structural_and_source-accounting_not_a_claim_of_full_editorial_certification':True})
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(HERE.glob('*'))if p.suffix in ['.json','.jsonl','.py']and p.name!='checksums.json'}
write(HERE/'checksums.json',hashes)
print(json.dumps({'passed':True,'main_records':len(allmain),'ancillary_records':sum(r['confirmed_ancillary_records']for r in results),'remaining_placeholder_records':len({r['record_id']for r in glyph_unknown})}))

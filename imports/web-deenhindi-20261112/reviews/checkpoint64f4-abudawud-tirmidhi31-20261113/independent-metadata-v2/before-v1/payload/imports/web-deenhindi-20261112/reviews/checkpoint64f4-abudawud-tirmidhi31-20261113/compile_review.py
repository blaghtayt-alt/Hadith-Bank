#!/usr/bin/env python3
"""Serialize only explicit reviewed fields; validate exact saved sources and native preservation."""
import collections,copy,gzip,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MONITOR=ROOT.parent/'phase22-successor-acquisition-monitor'
ENGINE=ROOT.parent/'hindi-resolve/work/scripts'
sys.path.insert(0,str(ENGINE))
import import_deenhindi as importer
import web_source_reviews as review_module
import web_commentary_quotes as commentary_module
from manual_boundaries import records as instructions
from source_first_notes import NOTES
HEAD='64f4ed50ed6026855237a5d547a86dd03e73f804'
COHORT='checkpoint64f4-abudawud-tirmidhi31-20261113'
PREFIX='imports/web-deenhindi-20261112/reviews/'+COHORT
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-'+COHORT+'.json.gz'
OUT=ROOT/'publish-v1'
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
read=lambda p:json.loads(p.read_bytes())
def put(path,data):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 return {'path':path,'bytes':len(data),'sha256':sha(data),'git_blob_sha1':blob(data)}

def compile_field(key, language, instruction, text, field_name):
    assert isinstance(text, str) and text.strip()
    result = {'language_version_id': 'deenhindi-' + key + ':' + language,
        'language': language, 'source_field': field_name, 'action': instruction['action'],
        'reviewed': True, 'chars_reviewed': len(text), 'bytes_reviewed': len(text.encode()),
        'text_sha256': sha(text.encode()), 'reason': instruction['reason'],
        'review_method': 'manual_full_field_reading_of_saved_source',
        'review_scope': 'The complete own-language field was read for attribution and exact boundaries; this is not independent Pro certification.'}
    for name in ('report_type', 'speaker', 'observed_script', 'source_script_note'):
        if name in instruction:
            result[name] = instruction[name]
    if instruction['action'] == 'whole':
        assert not instruction.get('omit_source_context')
        result['spans'] = [{'start': 0, 'end': len(text), 'sha256': sha(text.encode())}]
        return result
    if instruction['action'] in ('source_context', 'source_context_only'):
        result['spans'] = []
        return result
    assert instruction['action'] in ('excerpt', 'excerpts')
    base_spans = []
    for index, selection in enumerate(instruction['spans']):
        for marker in (selection['from'], selection['to']):
            assert marker is None or text.count(marker) == 1, ('ambiguous boundary', key, language, marker)
        start = 0 if selection['from'] is None else text.index(selection['from'])
        end = len(text) if selection['to'] is None else text.index(selection['to'], start)
        assert 0 <= start < end <= len(text)
        base_spans.append({'start': start, 'end': end,
            'component_id': selection.get('component_id', 'passage-' + str(index + 1)),
            'report_type': selection['report_type'], 'speaker': selection['speaker'],
            **({'source_report_family_id': selection['source_report_family_id']}
               if 'source_report_family_id' in selection else {})})
    omissions = []
    for omission in instruction.get('omit_source_context', []):
        marker = omission['text']
        assert marker and text.count(marker) == omission['expected_count']
        offset = 0
        for _ in range(omission['expected_count']):
            start = text.index(marker, offset)
            end = start + len(marker)
            assert sum(s['start'] <= start < end <= s['end'] for s in base_spans) == 1
            omissions.append((start, end))
            offset = end
    omissions.sort()
    assert all(left[1] <= right[0] for left, right in zip(omissions, omissions[1:]))
    spans = []
    for base in base_spans:
        cuts = [pair for pair in omissions if base['start'] <= pair[0] < pair[1] <= base['end']]
        cursor = base['start']
        for start, end in cuts + [(base['end'], base['end'])]:
            if cursor < start and text[cursor:start].strip():
                spans.append({**base, 'start': cursor, 'end': start,
                              'sha256': sha(text[cursor:start].encode())})
            cursor = end
    assert spans and all(a['end'] <= b['start'] for a, b in zip(spans, spans[1:]))
    result['spans'] = spans
    return result


def main():
    assert not (ROOT/'delivery-manifest-v1.json').exists(), 'Refusing to alter a frozen primary candidate'
    first=read(ROOT/'complete-source-first-readings.json')
    assert sha((ROOT/'complete-source-first-readings.json').read_bytes())=='b043183c9fa4a3a46bc66053d878f978ab9d2b8c5afc9916485c5862dc9b486e'
    assert first['candidate_exists_at_freeze'] is False and first['full_fields_read']==65
    assert first['own_notes_sha256']==sha((ROOT/'source_first_notes.py').read_bytes())
    data=(ROOT/'input/cohort.jsonl').read_bytes();assert sha(data)=='0a13beaaab0870f9e9ca031bac2d29be050e456cae18fbe139d5db02f027cd7d'
    sources={r['collection']+':'+r['number']:r for r in map(json.loads,data.splitlines())}
    assert len(sources)==31 and set(sources)=={r['key'] for r in instructions}
    fieldsread={(r['occurrence_id'].removeprefix('deenhindi-'),r['language']):r for r in first['records']}
    assert fieldsread.keys()=={(r['key'],lang) for r in instructions for lang in r['fields']}
    artifact=read(MONITOR/'complete-held-evidence/evidence-manifest.json');checkpoint=read(MONITOR/'complete-held-evidence/checkpoint.json')
    state=read(MONITOR/'complete-held-evidence/held-state-entries.json')
    assert artifact['saved_head']==checkpoint['saved_head']==HEAD
    assert sha((MONITOR/'complete-held-evidence/evidence-manifest.json').read_bytes())=='c2abcc3fb29dbada01127031b902026f785be51b225d590407d8917465a80a0c'
    assert checkpoint['selected_held_entries']==checkpoint['held_entries_total']==273 and checkpoint['remaining_held_queue_count']==0
    assert checkpoint['original_bounded_selected_held_entries']==250 and checkpoint['original_bounded_remaining_held_queue_count']==23 and checkpoint['maximum_records']==250 and checkpoint['diagnostic_export_limits_unchanged'] is True
    assert checkpoint['input_receipts']['scripts/import_deenhindi.py']['sha256']==sha(Path(importer.__file__).read_bytes())
    assert sha(Path(review_module.__file__).read_bytes()+Path(commentary_module.__file__).read_bytes())=='cc253d0d89d839f79a99e5209824b953fa6ac21be80fdb898a130025cbc7114b'
    baseline_raw=b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() for r in sources.values())
    baseline=put(PREFIX+'/source-baseline.jsonl.gz',gzip.compress(baseline_raw,mtime=0))
    manual=put(PREFIX+'/manual-boundary-instructions.json',enc({'schema':'hadith-bank-explicit-own-field-boundaries-v1','source_checkpoint':HEAD,'records':instructions}))
    decisions=[];rawchecks=[];cuts=[]
    for instruction in instructions:
        k=instruction['key'];saved=sources[k];entry=state[k];sourcehash=sha(importer.json_bytes(saved['source_record']))
        assert entry['collection']==saved['collection'] and entry['number']==saved['number'] and entry['parsed']['path']==saved['parsed_path']
        assert sourcehash==artifact['source_record_sha256'][k]
        parsed_expected={n:saved[n] for n in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')};parsed_expected['classification']=saved['intake_classification']
        files=[]
        for kind,desc in [('raw',saved['snapshot']),('parsed',entry['parsed'])]:
            p=MONITOR/'complete-held-evidence/sources'/desc['path'];assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to((MONITOR/'complete-held-evidence/sources').resolve())
            stored=p.read_bytes();plain=gzip.decompress(stored);f=artifact['files'][desc['path']]
            assert len(stored)==f['bytes']==f['stored_bytes'] and sha(stored)==f['sha256']==f['stored_sha256']==desc['stored_sha256'] and blob(stored)==f['git_blob_sha1']
            assert sha(plain)==desc['sha256']
            if kind=='raw':
                assert len(plain)==desc['bytes'] and len(stored)==desc['stored_bytes']
                obj,ref=importer.parse_record(plain,saved['collection'],saved['number']);assert obj==saved['source_record'] and ref==saved['source_reference_verbatim']
            else:assert plain==importer.json_bytes(parsed_expected)
            files.append({'kind':kind,'path':desc['path'],'stored_bytes':len(stored),'stored_sha256':sha(stored),'git_blob_sha1':blob(stored),'bytes':len(plain),'sha256':sha(plain)})
        fs=[]
        for lang,rule in instruction['fields'].items():
            fieldname=importer.LANGUAGE_FIELDS[lang];text=saved['source_record'][fieldname]
            own=fieldsread[(k,lang)];assert own['complete_own_field_read'] is True and own['text_sha256']==sha(text.encode()) and own['characters']==len(text) and own['utf8_bytes']==len(text.encode())
            fs.append(compile_field(k,lang,rule,text,fieldname))
            for omission in rule.get('omit_source_context',[]):
                literal=omission['text'];start=0
                for _ in range(omission['expected_count']):
                    start=text.index(literal,start);end=start+len(literal)
                    cuts.append({'id':'deenhindi-'+k,'language':lang,'source_text_sha256':sha(text.encode()),'start':start,'end':end,'text':literal,'sha256':sha(literal.encode()),'reason':omission['reason']});start=end
        if instruction['decision']=='exclude':
            assert not any(f['spans'] for f in fs) and set(instruction['fields'])=={lang for lang,name in importer.LANGUAGE_FIELDS.items() if saved['source_record'].get(name)}
        else:assert any(f['spans'] for f in fs)
        decisions.append({'id':'deenhindi-'+k,'decision':instruction['decision'],'reason':instruction['reason'],'source_record_sha256':sourcehash,'source_snapshot_sha256':saved['snapshot']['sha256'],'source_record_url':saved['snapshot']['url'],'source_parsed_path':saved['parsed_path'],'source_parsed_sha256':entry['parsed']['sha256'],'source_reference_verbatim':saved['source_reference_verbatim'],'field_reviews':fs})
        rawchecks.append({'id':'deenhindi-'+k,'source_record_sha256':sourcehash,'exact_current_parser_object_and_reference':True,'files':files})
    document={'schema':'hadith-bank-web-source-review-v1','site':'deenhindi','source_checkpoint':HEAD,'source_ledger_path':baseline['path'],'source_ledger_sha256':baseline['sha256'],'source_ledger_uncompressed_sha256':sha(baseline_raw),'manual_decision_files':[manual],'review_scope':'Exactly65 complete own-field readings for31 saved64f4 occurrences: all31 Hindi and31 Urdu fields, plus the Arabic, English and Roman Urdu originals of AbuDawud2720. That parent is source-only after all five actual fields were read; the other30 parents retain actual supplied bodies in both priority languages. Finite transmitted variants, reception dialogues, material qualifiers and source-specific attribution defects remain explicit. Compiler legal/lexical/route apparatus and omitted-body pointers remain context. No canonical identity, absent wording or missing speaker is filled. The exact source packet is a documented local union of the bounded250 artifact and saved-GitHub23-row supplement, not an enlarged artifact or a change to source controls.','independent_pro_qc':'not_performed','independent_pro_qc_performed':False,'new_translation_created':False,'records':decisions}
    active=put(ACTIVE,gzip.compress(importer.json_bytes(document),mtime=0))
    native=review_module.SourceReviews(OUT,'deenhindi');assert set(native.decisions)=={'deenhindi-'+k for k in sources}
    totals=collections.Counter();books=collections.defaultdict(collections.Counter);languages=collections.defaultdict(collections.Counter);partitions=[];readings=[];families=[]
    for decision in decisions:
        k=decision['id'].removeprefix('deenhindi-');saved=sources[k];old=importer.canonical_record(saved);oldcopy=copy.deepcopy(old);savedcopy=copy.deepcopy(saved)
        new,action=native.apply(old,saved=saved);assert old==oldcopy and saved==savedcopy and action==decision['decision']
        for name in set(old)-{'language_versions','text','content_kind','review','report_types','extraction'}:
            assert new[name]==old[name],(k,name);totals['metadata_value_equalities']+=1
        for name in old['extraction']:
            if name!='is_excerpt':assert old['extraction'][name]==new['extraction'][name];totals['metadata_value_equalities']+=1
        assert new['number']['canonical'] is None and new['review']['independent_pro_qc']=='not_performed' and new['review']['certified_release_eligible'] is False
        fmap={f['language']:f for f in decision['field_reviews']};selected={}
        for oldv,newv in zip(old['language_versions'],new['language_versions'],strict=True):
            lang=oldv['language'];text=oldv['text'];f=fmap.get(lang);pieces=[]
            for name in set(oldv)-{'text','scope','quotation_status','source','comments','script'}:
                assert oldv[name]==newv[name];totals['metadata_value_equalities']+=1
            assert oldv['script']==newv['script']
            for name in oldv['source']:
                assert oldv['source'][name]==newv['source'][name];totals['metadata_value_equalities']+=1
            if f:
                assert f['chars_reviewed']==len(text) and f['bytes_reviewed']==len(text.encode()) and f['text_sha256']==sha(text.encode())
                for c in (totals,books[saved['collection']],languages[lang]):c.update(complete_fields_read=1,characters_read=len(text),utf8_bytes_read=len(text.encode()))
                if f['spans']:
                    positions=[[s['start'],s['end']] for s in f['spans']]
                    assert newv['source']['text_spans']['quotation_spans']==positions and newv['text']==''.join(text[a:b] for a,b in positions)
                    selected[lang]=newv['text']
                    for s in f['spans']:
                        a,b=s['start'],s['end'];assert text[a:b].strip() and s['sha256']==sha(text[a:b].encode());pieces.append((a,b,'quotation'))
                    for c in (totals,books[saved['collection']],languages[lang]):c.update(admitted_language_fields=1,quotation_spans=len(positions),selected_characters=sum(b-a for a,b in positions))
                    comp={s['component_id'] for s in f['spans']};family={s['source_report_family_id'] for s in f['spans']}
                    assert len(newv['source']['report_component_classifications'])==len(comp) and newv['source'].get('source_report_count',1)==len(family)
                    families.append({'id':oldv['id'],'components':sorted(comp),'source_report_families':sorted(family),'native_family_count':newv['source'].get('source_report_count',1)})
                else:
                    assert newv['text'] is None and newv['source']['manual_review']['field_reviewed'] is True
                    for c in (totals,books[saved['collection']],languages[lang]):c['read_context_fields']+=1
            else:
                assert newv['text'] is None and newv['source']['manual_review']['field_reviewed'] is False
                for c in (totals,books[saved['collection']],languages[lang]):c['unread_context_fields']+=1
            for comment in newv['comments']:
                a,b=comment['source_span'];assert comment['scope']=='source_context_not_narration' and comment['text']==text[a:b] and comment['source_text_sha256']==sha(text[a:b].encode()),(k,lang,'source context fragment binding');pieces.append((a,b,'context'))
            pieces.sort();cursor=0
            for a,b,role in pieces:assert a==cursor and b>a;cursor=b
            assert cursor==len(text) and ''.join(text[a:b] for a,b,_ in pieces)==text
            partition={'id':oldv['id'],'source_field':oldv['source']['source_field'],'source_text_sha256':sha(text.encode()),'source_chars':len(text),'read':f is not None,'parts':[{'start':a,'end':b,'role':role,'sha256':sha(text[a:b].encode())} for a,b,role in pieces]};partitions.append(partition)
            if f:readings.append({**fieldsread[(k,lang)],'text':text,'actual_field_review':f,'selected_spans':[{**s,'text':text[s['start']:s['end']]} for s in f['spans']],'retained_context':[{**s,'text':text[s['start']:s['end']]} for s in partition['parts'] if s['role']=='context']})
            for c in (totals,books[saved['collection']],languages[lang]):c.update(exact_complete_field_partitions=1,source_language_slots=1)
        for lang,fieldname in importer.LANGUAGE_FIELDS.items():
            value=saved['source_record'].get(fieldname)
            if value is None or value=='':
                assert not any(v['language']==lang for v in old['language_versions'])
                partitions.append({'id':old['id']+':'+lang,'source_field':fieldname,'source_original_state':value,'source_chars':0,'read':False,'parts':[]})
                for c in (totals,books[saved['collection']],languages[lang]):c.update(empty_source_fields_preserved=1,source_language_slots=1)
        if action=='register':assert set(selected)=={f['language'] for f in decision['field_reviews'] if f['spans']} and new['text']=={'arabic':selected.get('ar'),'translation':selected['hi']}
        else:assert not selected and new['text']==old['text']
        assert new['review']['source_bound_review']['approved_language_fields']==len(selected)
        for c in (totals,books[saved['collection']]):c.update(source_occurrences=1);c[action]+=1
    native.finish()
    assert totals['source_occurrences']==31 and totals['register']==30 and totals['exclude']==1
    assert totals['complete_fields_read']==65 and totals['characters_read']==28670 and totals['utf8_bytes_read']==61240
    assert totals['admitted_language_fields']==60 and totals['read_context_fields']==5 and totals['unread_context_fields']==90
    assert totals['exact_complete_field_partitions']==155 and totals['empty_source_fields_preserved']==0 and totals['source_language_slots']==155
    validation={'schema':'hadith-bank-source-bound-review-native-validation-v1','result':'PASS','source_checkpoint':HEAD,'active_ledger':active,'source_baseline':baseline,'totals':dict(totals),'by_book':{k:dict(v) for k,v in books.items()},'by_language':{k:dict(v) for k,v in languages.items()},'raw_and_parsed_files_reopened':62,'raw_html_reparses':31,'source_only_occurrences':1,'source_only_all_nonempty_fields_read_when_applicable':True,'source_and_canonical_inputs_unchanged':True,'all_original_metadata_preserved':True,'script_metadata_changes':0,'canonical_identity_fills':0,'new_translation_created':False,'source_http_requests':0,'github_writes':0,'engine_hashes':{Path(m.__file__).name:sha(Path(m.__file__).read_bytes()) for m in (importer,review_module,commentary_module)},'independent_pro_qc':'not_performed','limitations':'Primary exact-source review and native local validation only; independent second reading, full-repository export and actual reader/deployment remain separate gates.'}
    put(PREFIX+'/validation.json',enc(validation))
    put(PREFIX+'/source-evidence.json',enc({'source_checkpoint':HEAD,'source_worker_run_id':43480836830,'artifact_id':14067478999,'artifact_manifest_sha256':sha((MONITOR/'complete-held-evidence/evidence-manifest.json').read_bytes()),'source_rows_sha256':sha(data),'source_files_reopened':62,'raw_reparses':31,'records':rawchecks}))
    put(PREFIX+'/field-partitions.json.gz',gzip.compress(enc(partitions),mtime=0))
    put(PREFIX+'/complete-field-readings-and-boundaries.json.gz',gzip.compress(enc({'source_checkpoint':HEAD,'active_ledger_sha256':active['sha256'],'fields':readings}),mtime=0))
    put(PREFIX+'/explicit-source-apparatus-context.json',enc({'literal_omissions':len(cuts),'items':cuts,'scope':'Only the individually authored literal cuts inside admitted components. Complete external tails and source-only fields remain losslessly represented in the complete field partitions.'}))
    put(PREFIX+'/report-families.json',enc(families))
    put(PREFIX+'/complete-source-first-readings.json.gz',gzip.compress((ROOT/'complete-source-first-readings.json').read_bytes(),mtime=0))
    put(PREFIX+'/selected-state-entries.json',enc({k:state[k] for k in sources}))
    put(PREFIX+'/source-artifact-manifest.json.gz',gzip.compress((MONITOR/'complete-held-evidence/evidence-manifest.json').read_bytes(),mtime=0))
    put(PREFIX+'/saved-checkpoint-receipt.json',(MONITOR/'complete-held-evidence/checkpoint.json').read_bytes())
    put(PREFIX+'/original-partition-receipt.json',(ROOT/'input/partition-receipt.json').read_bytes())
    for n in ('source_first_notes.py','manual_boundaries.py','compile_review.py'):put(PREFIX+'/'+n,(ROOT/n).read_bytes())
    print(json.dumps({'status':'PASS','active_ledger':active,'source_baseline':baseline,'totals':dict(totals),'by_book':validation['by_book'],'literal_context_cuts':len(cuts)},indent=2))


if __name__=='__main__':main()


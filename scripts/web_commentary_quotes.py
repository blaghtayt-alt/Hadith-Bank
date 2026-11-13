"""Explicit source-commentary children, never inferred from main-field decisions.

Input parent rows are immutable source objects. Children use exact reviewed
comment spans and fresh metadata; primary-parent numbers, narrators, grades,
Arabic and canonical references are not inherited.
"""
from __future__ import annotations
import copy
import gzip
import hashlib
import json
from pathlib import Path

SCHEMA = 'hadith-bank-website-commentary-quotation-specs-v1'
FOLDER = 'imports/web-uzbek-20261112/islom/reviews'

def sha(value):
    return hashlib.sha256(value).hexdigest()

def canonical_hash(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8'))

def require(test, message):
    if not test:
        raise ValueError('Website commentary quotation: ' + message)

def pairs_unique(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, 'duplicate JSON key ' + key)
        out[key] = value
    return out

def local_bytes(root, relative, expected):
    require(isinstance(relative, str) and relative and '\\' not in relative,
            'local evidence path required')
    part = Path(relative)
    require(not part.is_absolute() and '..' not in part.parts and ':' not in part.parts[0],
            'unsafe local evidence path')
    path = root / part
    require(path.is_file() and path.resolve().is_relative_to(root)
            and not any(p.is_symlink() for p in [path, *path.parents] if p.is_relative_to(root)),
            'evidence file absent or unsafe: ' + relative)
    data = path.read_bytes()
    require(isinstance(expected, str) and sha(data) == expected, 'evidence checksum mismatch: ' + relative)
    return data

def external_evidence_comments(root, evidence, language):
    """Preserve verification scope visibly without changing source references."""
    require(isinstance(evidence, list), 'external evidence must be a list')
    result=[]
    for item in evidence:
        require(isinstance(item, dict), 'external evidence must be an object')
        local_bytes(root, item.get('path'), item.get('sha256'))
        require(isinstance(item.get('url'), str) and item['url'].startswith('https://'),
                'external public source URL required')
        require(all(isinstance(item.get(k), str) and item[k].strip() for k in ('work','relationship')),
                'scoped external reference description required')
        text='External corroboration; not a source-printed canonical identity: ' + item['work'] + '. ' + item['relationship']
        if item.get('grading_scope'):
            text += ' ' + item['grading_scope']
        text += ' ' + item['url']
        result.append({'text':text, 'scope':'external_corroboration_not_source_text',
            'language':language,'source_url':item['url'],'evidence_path':item['path'],
            'evidence_sha256':item['sha256'],
            'retention_reason':'External evidence is separate from publisher wording, numbers, chains, grades and attribution.'})
    return result

class CommentaryQuotes:
    def __init__(self, root, site):
        self.root=Path(root).resolve()
        self.specs, self.seen, self.parents = {}, set(), set()
        if site != 'islom':
            return
        folder=self.root/FOLDER
        for path in sorted([*folder.glob('commentary-quotations*.json'), *folder.glob('commentary-quotations*.json.gz')]):
            stored=path.read_bytes()
            raw=gzip.decompress(stored) if path.suffix=='.gz' else stored
            doc=json.loads(raw,object_pairs_hook=pairs_unique)
            require(doc.get('schema')==SCHEMA and doc.get('site')==site,
                    'unsupported commentary specification')
            require(doc.get('enabled') is True, 'commentary registration requires an explicit enabled document')
            require(doc.get('independent_pro_qc','not_performed')=='not_performed', 'independent QC claim forbidden')
            rows=doc.get('records')
            require(isinstance(rows,list) and rows, 'nonempty child list required')
            receipt={'path':path.relative_to(self.root).as_posix(),'sha256':sha(stored),
                     'uncompressed_sha256':sha(raw),'method':'source_hash_bound_commentary_child_v1'}
            if path.suffix=='.gz': receipt['compression']='gzip'
            for spec in rows:
                child=spec.get('proposed_occurrence_id');parent=spec.get('parent_occurrence_id')
                require(isinstance(parent,str) and parent.startswith('islom:'), 'explicit Islom parent required')
                require(isinstance(child,str) and child.startswith(parent+':commentary-')
                        and child==spec.get('supplement_id'), 'stable separate child identity required')
                require(child not in self.specs, 'duplicate commentary child identity')
                require(spec.get('decision')=='register', 'explicit child registration decision required')
                require(spec.get('registered_source_occurrences')==1, 'one source occurrence per child required')
                require(spec.get('independent_pro_qc')=='not_performed'
                        and spec.get('certified_release_eligible') is False, 'child certification must remain false')
                self.specs[child]=(copy.deepcopy(spec),receipt)
                self.parents.add(parent)

    def finish(self):
        require(self.seen==set(self.specs), 'commentary parents absent from source or not processed: ' +
                ', '.join(sorted(set(self.specs)-self.seen)[:10]))

    def children(self, row, baseline=None):
        baseline=row if baseline is None else baseline
        require(row['id']==baseline['id'],'parent identity mismatch')
        result=[]
        for child_id,(spec,receipt) in self.specs.items():
            if spec['parent_occurrence_id']!=row['id']:
                continue
            require(child_id not in self.seen, 'commentary child generated twice')
            require(canonical_hash(baseline)==spec.get('parent_baseline_record_sha256'),
                    'parent baseline changed: '+row['id'])
            locator=baseline.get('source_locator') or {}
            snapshot=spec.get('source_snapshot') or {}
            require(snapshot.get('path')==locator.get('path') and snapshot.get('sha256')==locator.get('sha256'),
                    'snapshot parent binding mismatch')
            stored=local_bytes(self.root,snapshot.get('path'),snapshot.get('stored_sha256'))
            require(sha(gzip.decompress(stored))==snapshot.get('sha256'), 'uncompressed snapshot checksum mismatch')
            path=spec.get('source_field_path') or []
            require(len(path)==5 and path[0]=='language_versions' and path[2]=='comments' and path[4]=='text'
                    and type(path[1]) is int and type(path[3]) is int, 'explicit comment field path required')
            versions=baseline.get('language_versions',[])
            require(0<=path[1]<len(versions), 'comment version index out of range')
            original=versions[path[1]]
            require(original.get('id')==spec.get('source_version_id') and original.get('language')==spec.get('language'),
                    'comment version identity mismatch')
            comments=original.get('comments',[])
            require(0<=path[3]<len(comments) and isinstance(comments[path[3]],dict), 'comment index out of range')
            text=comments[path[3]].get('text')
            require(isinstance(text,str) and sha(text.encode())==spec.get('source_field_sha256'), 'comment field checksum mismatch')
            require(spec.get('full_field_chars_reviewed')==len(text)
                    and spec.get('full_field_bytes_reviewed')==len(text.encode()), 'complete comment review required')
            spans=spec.get('selected_spans')
            require(isinstance(spans,list) and spans, 'exact child spans required')
            positions=[];cursor=0
            for span in spans:
                a,b=span.get('start'),span.get('end')
                require(type(a) is int and type(b) is int and 0<=cursor<=a<b<=len(text), 'invalid or overlapping child spans')
                require(sha(text[a:b].encode())==span.get('sha256') and text[a:b]==span.get('text'),
                        'child span checksum/text mismatch')
                require(all(isinstance(span.get(k),str) and span[k].strip() for k in ('component_id','report_type','speaker')),
                        'explicit child report attribution required')
                require(span.get('source_report_family_id')==child_id, 'child report family mismatch')
                positions.append([a,b]);cursor=b
            require(spec.get('quoted_passages')==len(spans) and spec.get('source_report_families')==1,
                    'child passage/family count mismatch')
            require(len({(s['component_id'],s['report_type'],s['speaker']) for s in spans})==1,
                    'one child must represent one explicitly coherent report')
            note_spans=[];cursor=0
            for a,b in positions:
                if cursor<a:note_spans.append([cursor,a])
                cursor=b
            if cursor<len(text):note_spans.append([cursor,len(text)])
            language=spec['language'];selected=''.join(text[a:b] for a,b in positions)
            description=spec.get('description')
            require(isinstance(description,str) and description.strip(), 'child scope description required')
            external=spec.get('external_corroboration',[])
            extra_comments=external_evidence_comments(self.root,external,language)
            source_url=baseline.get('source',{}).get('record_url') or locator.get('record_url')
            require(source_url==spec.get('source_record_url'), 'comment source URL mismatch')
            quoted=spans[0]
            note='Report type: '+quoted['report_type'].replace('_',' ')+'. Attribution: '+quoted['speaker']+'. '+description
            version_source={'name':baseline.get('source',{}).get('publisher','Hadis.islom.uz'),
                'url':source_url,'record_url':source_url,'snapshot_path':snapshot['path'],
                'snapshot_sha256':snapshot['sha256'],'source_text_sha256':sha(text.encode()),
                'parent_occurrence_id':row['id'],'source_field_path':path,
                'text_spans':{'quotation_spans':positions,'notes':note_spans,'span_unit':'unicode_codepoints',
                              'method':'source_hash_bound_commentary_child_v1'},
                'quotation_boundary_status':'bounded','report_type':quoted['report_type'],
                'report_classification_note':note,'source_report_count':1,
                'report_component_classifications':[{'component_id':quoted['component_id'],
                    'report_type':quoted['report_type'],'speaker_description':quoted['speaker'],
                    'spans':positions,'reason':description,'source_report_family_id':child_id}],
                'reviewed_span_evidence':copy.deepcopy(spans),'external_corroboration':copy.deepcopy(external),
                'manual_review':{**receipt,'field_reviewed':True,'decision':'separate_commentary_child',
                                 'independent_pro_qc':'not_performed'}}
            if len(positions)>1:version_source['source_report_groups']=[positions]
            # Only explicitly printed references from the commentary may enter
            # the child source-reference list. External parallels stay comments.
            references=copy.deepcopy(spec.get('source_printed_collection_references',[]))
            require(isinstance(references,list), 'commentary source references must be a list')
            for ref in references:
                require(ref.get('scope')=='source_commentary_collection_citation'
                        and ref.get('canonical_mapping_status')=='unverified' and ref.get('number') is None
                        and isinstance(ref.get('source_citation'),str) and ref['source_citation'] in text,
                        'unbound or inherited source reference')
            version={'id':child_id+':'+language,'language':language,'script':original.get('script'),
                'text':selected,'source':version_source,'references':references,
                'translation_provenance':copy.deepcopy(original.get('translation_provenance')),
                'scope':'source_excerpt','match_status':'independent_source_commentary_quotation',
                'quotation_status':'bounded' if len(positions)==1 else 'disjoint_source_spans',
                'comments':[{'text':text[a:b],'scope':'source_context_not_narration','language':language,
                    'source_url':source_url,'source_span':[a,b],'source_text_sha256':sha(text[a:b].encode()),
                    'retention_reason':'Complete original commentary outside the child quotation spans.'}
                    for a,b in note_spans]+extra_comments}
            child={'id':child_id,'language':baseline.get('language'),'source_language_code':language,
                'book_key':baseline['book_key'],'edition':baseline['edition'],
                'title':'Quoted report in source commentary', 'record_type':'source_narration_occurrence',
                'content_kind':'source_commentary_quotation',
                'classification':{'value':'source_commentary_quotation','basis':description},
                'text':{'arabic':selected if language=='ar' else None,
                        'translation':selected if language!='ar' else None},
                'language_versions':[version],
                'source':{'title':baseline.get('source',{}).get('title'),
                    'url':baseline.get('source',{}).get('url'),'record_url':source_url,
                    'publisher':baseline.get('source',{}).get('publisher'),
                    'metadata_scope':'separate_bounded_source_commentary_quotation',
                    'parent_occurrence_id':row['id'],'original_metadata':{'source_field_path':path,
                        'source_field_sha256':sha(text.encode()),'parent_occurrence_is_not_child_canonical_reference':True}},
                'number':{'source_entry_id':None,'in_book':None,'canonical':None,
                    'scope':'unnumbered_commentary_quotation','numbering_system':'No separate source number is printed for this commentary quotation'},
                'narrator':{'name':None,'basis':'No individual transmitter is printed for this commentary quotation; parent and external narrators are not inherited'},
                'translator':{'name':None,'evidence':None},
                'translation_provenance':copy.deepcopy(baseline.get('translation_provenance')),
                'ai_translation':baseline.get('ai_translation','unknown'),
                'references':{'items':references,'canonical_mapping_status':'unverified'},
                'commentary':{'arabic':None,'translation':None},'footnotes':[],
                'grading':{'grade':None,'grader':None,'basis':'No grade printed for this commentary quotation; no parent or external grade inherited'},
                'source_headings':[],'topic_tags':[],'related_versions':[],
                'related_source_occurrences':[{'id':row['id'],'relationship':'contains_source_commentary'}],
                'review':{'status':'source_bound_classification_reviewed','issues':[],
                    'source_bound_review':{**receipt,'decision':'register_commentary_child','approved_language_fields':1},
                    'independent_pro_qc':'not_performed','release_status':'source_import',
                    'release_eligible':False,'certified_release_eligible':False},
                'rights':copy.deepcopy(baseline.get('rights',{})),
                'extraction':{'method':'source_hash_bound_commentary_child_v1','ocr_used':False,'is_excerpt':True,
                    'original_html_sha256':snapshot['sha256'],'source_snapshot':snapshot['path'],
                    'parent_occurrence_id':row['id'],'source_field_path':path},
                'source_locator':{'path':snapshot['path'],'sha256':snapshot['sha256'],
                    'format':'gzip_compressed_original_http_html','record_url':source_url,
                    'source_field_path':path,'source_field_sha256':sha(text.encode()),
                    'source_spans':positions,'text_hashes':{language:sha(selected.encode())}},
                'page':{'pdf':[],'printed':[],'sheet':None,'row':None},
                'report_types':[quoted['report_type']]}
            result.append(child);self.seen.add(child_id)
        return result

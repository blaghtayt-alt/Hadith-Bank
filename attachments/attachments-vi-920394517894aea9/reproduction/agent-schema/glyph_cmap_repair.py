"""Version 2: resource-specific repair of damaged PDF ToUnicode ASCII digits.

Usage: decoder=GlyphMapDecoder(doc); page_dict,log=decoder.repair_page(page).
Returned dict has normal blocks/lines/spans with text, raw_text, repair_count;
rawdict chars are preserved unchanged. Arabic and Latin letters never change.

Exact /Tf resource identity is recovered by aligning parsed BT/ET text objects
with MuPDF text paint events. Only embedded Type0 fonts are decoded. Ambiguous
pages fail closed with no repairs. Family names are NEVER used to select fonts.
"""
from __future__ import annotations
import collections
import io
import re
from fontTools.ttLib import TTFont
from pypdf import PdfReader
from pypdf.generic import ContentStream

ASCII_DIGITS = frozenset('0123456789')
REPAIR_VERSION = '2.0.0-exact-resource-ascii-digits'

def _font_key(name):
    return re.sub(r'[^a-z0-9]', '', re.sub(r'^[A-Z]{6}\+', '', name.lstrip('/')).casefold())

def _origin_key(font, origin):
    return (_font_key(font), round(float(origin[0]), 3), round(float(origin[1]), 3))

class GlyphMapDecoder:
    def __init__(self, doc):
        self.doc = doc
        self.reader = PdfReader(doc.name) if doc.name else PdfReader(io.BytesIO(doc.tobytes()))
        self._xref_maps = {}
        self.font_diagnostics = []
        self.page_diagnostics = []

    def _font_map(self, xref):
        if xref in self._xref_maps:
            return self._xref_maps[xref]
        mapping = collections.defaultdict(set)
        try:
            name, ext, typ, raw = self.doc.extract_font(xref)
            if raw:
                font = TTFont(io.BytesIO(raw), lazy=False)
                cmap = font.getBestCmap() or {}
                for cp, glyph_name in cmap.items():
                    mapping[font.getGlyphID(glyph_name)].add(chr(cp))
                font.close()
                self.font_diagnostics.append({'font_xref':xref,'font_name':name,
                    'font_format':ext,'embedded_bytes':len(raw),'cmap_entries':len(cmap)})
            else:
                self.font_diagnostics.append({'font_xref':xref,'status':'unembedded_font_not_decoded'})
        except Exception as e:
            self.font_diagnostics.append({'font_xref':xref,'status':'font_not_decoded','error':str(e)})
        result = dict(mapping)
        self._xref_maps[xref] = result
        return result

    def _resource_events(self, page):
        """Return seqno -> exact font resource; empty on ambiguity."""
        pypage = self.reader.pages[page.number]
        cs = ContentStream(pypage.get_contents(), self.reader)
        resources = pypage['/Resources'].get('/Font',{})
        current_font = None
        current_mode = 0
        stack = []
        active = None
        expected = []
        for operands, operator in cs.operations:
            if operator == b'q':
                stack.append((current_font,current_mode))
            elif operator == b'Q':
                if stack: current_font,current_mode = stack.pop()
            elif operator == b'Tf':
                current_font = str(operands[0])
            elif operator == b'Tr':
                current_mode = int(operands[0])
            elif operator == b'BT':
                if active is not None:
                    return {}, {'status':'ambiguous_nested_BT_no_repairs'}
                active = {'fonts':set(),'modes':set(),'has_show':False}
            elif operator in (b'Tj',b'TJ',b"'",b'"') and active is not None:
                active['has_show'] = True
                active['fonts'].add(current_font)
                active['modes'].add(current_mode)
            elif operator == b'ET':
                if active is not None and active['has_show']:
                    if len(active['modes'])!=1:
                        return {}, {'status':'mixed_text_rendering_modes_no_repairs'}
                    mode = next(iter(active['modes']))
                    types = {0:['fill-text'],1:['stroke-text'],2:['fill-text','stroke-text'],
                             3:['ignore-text'],4:['fill-text'],5:['stroke-text'],
                             6:['fill-text','stroke-text']}.get(mode)
                    if types is None:
                        return {}, {'status':'unsupported_text_rendering_mode_no_repairs','mode':mode}
                    for typ in types: expected.append((typ,active['fonts'].copy()))
                active = None
        observed = [(seqno,t) for seqno,(t,*_) in enumerate(page.get_bboxlog())
                    if t in ('fill-text','stroke-text','ignore-text')]
        if len(expected)!=len(observed):
            return {}, {'status':'text_event_count_mismatch_no_repairs',
                        'expected':len(expected),'observed':len(observed)}
        if any(e[0]!=o[1] for e,o in zip(expected,observed)):
            return {}, {'status':'text_event_type_mismatch_no_repairs'}
        result = {}
        skipped = collections.Counter()
        for (typ,font_names),(seqno,_) in zip(expected,observed):
            if len(font_names)!=1:
                skipped['mixed_font_text_object']+=1;continue
            font_name = next(iter(font_names))
            if font_name not in resources:
                skipped['unresolved_font_resource']+=1;continue
            indirect = resources[font_name]
            font_obj = indirect.get_object()
            ref = getattr(indirect,'indirect_reference',None) or indirect
            xref = getattr(ref,'idnum',None)
            if font_obj.get('/Subtype')!='/Type0' or xref is None:
                skipped['not_embedded_type0_resource']+=1;continue
            cmap = self._font_map(xref)
            if not cmap:
                skipped['embedded_cmap_unavailable']+=1;continue
            result[seqno] = {'resource':font_name,'xref':xref,'cmap':cmap,
                             'base_font':str(font_obj.get('/BaseFont',''))}
        return result, {'status':'exact_content_stream_resource_alignment',
                        'text_paint_events':len(observed),'decodable_events':len(result),
                        'skipped_events':dict(skipped)}

    def repair_page(self, page):
        try:
            event_resources,diagnostic = self._resource_events(page)
        except Exception as e:
            event_resources = {}
            diagnostic = {'status':'resource_alignment_exception_no_repairs','error':str(e)}
        diagnostic.update({'pdf_page':page.number+1,'repair_version':REPAIR_VERSION})
        self.page_diagnostics.append(diagnostic)
        traces = collections.defaultdict(list)
        if event_resources:
            for span in page.get_texttrace():
                resource = event_resources.get(span['seqno'])
                if resource is None:continue
                # Cross-check family; resource identity is already exact.
                if _font_key(span['font']) != _font_key(resource['base_font']):continue
                for cp,gid,origin,bbox in span['chars']:
                    traces[_origin_key(span['font'],origin)].append({
                        'raw':chr(cp),'gid':gid,'bbox':list(bbox),'font':span['font'],
                        'xref':resource['xref'],'resource':resource['resource'],
                        'alternatives':resource['cmap'].get(gid,set()),'seqno':span['seqno']})
        data = page.get_text('rawdict')
        data['glyph_repair_diagnostics'] = diagnostic
        changes = []
        for bi,block in enumerate(data['blocks']):
            for li,line in enumerate(block.get('lines',[])):
                for si,span in enumerate(line['spans']):
                    chars = span.get('chars',[])
                    raw_text = ''.join(c['c'] for c in chars)
                    corrected = []
                    count = 0
                    for ci,char in enumerate(chars):
                        old=char['c'];new=old
                        if old in ASCII_DIGITS:
                            candidates=[t for t in traces.get(_origin_key(span['font'],char['origin']),[]) if t['raw']==old]
                            evidence={(t['xref'],t['gid']) for t in candidates}
                            if len(evidence)==1:
                                alternatives=set().union(*(t['alternatives'] for t in candidates))
                                if len(alternatives)==1:
                                    desired=next(iter(alternatives))
                                    if desired in ASCII_DIGITS and desired!=old:
                                        new=desired;count+=1;t=candidates[0]
                                        changes.append({'pdf_page':page.number+1,
                                            'block_index':bi,'line_index':li,'span_index':si,'char_index':ci,
                                            'old':old,'new':new,'font':span['font'],'glyph_id':t['gid'],
                                            'font_xref':t['xref'],'font_resource':t['resource'],'text_paint_seqno':t['seqno'],
                                            'origin':list(char['origin']),'bbox':list(char['bbox']),
                                            'method':'exact_pdf_font_resource_cmap_ascii_digit_repair',
                                            'repair_version':REPAIR_VERSION,'raw_span_text':raw_text})
                        corrected.append(new)
                    span['raw_text']=raw_text
                    span['text']=''.join(corrected)
                    span['repair_count']=count
        return data,changes

_CACHE={}

def repair_page(page):
    """Return (page_dict_with_raw_text, exact_resource_character_repair_log)."""
    doc=page.parent;key=id(doc)
    if key not in _CACHE or _CACHE[key].doc is not doc:_CACHE[key]=GlyphMapDecoder(doc)
    return _CACHE[key].repair_page(page)

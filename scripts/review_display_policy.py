"""Current reader policy: show QC tags for evidenced OCR extraction only.

This module reads structured extraction metadata. It never changes source
review fields, determines translation origin, or certifies source accuracy.
"""
import re


DEFAULT_DISPLAY_POLICY = {
    'scope': 'ocr_only',
    'historical_review_metadata_preserved': True,
    'independent_qc_performed': False,
    'note': 'QC labels apply to OCR extraction. Original review history remains in record details.',
}

_OCR_METHOD = re.compile(r'(^|[\s_-])ocr($|[\s_-])|tesseract|paddleocr|easyocr|ocrmypdf|abbyy', re.I)
_NO_OCR_METHOD = re.compile(r'(?:no|non|not|without)[\s_-]+ocr', re.I)
_DIGITAL_METHOD = re.compile(
    r'(?:native|embedded)[\s_-]+(?:pdf[\s_-]+)?text|'
    r'digital[\s_-]+(?:source|text|quote)|official[\s_-]+digital|'
    r'structured[\s_-]+(?:text|json)|json[\s_-]+(?:quote|span)', re.I)


def extraction_metadata(record):
    """Return a small, evidence-backed projection without mutating the source.

An absent OCR flag is unknown, not false. A PDF extension, human translator,
or a review warning containing the word OCR is not extraction evidence.
Conflicting explicit flags remain marked; positive OCR evidence keeps QC visible.
"""
    if not isinstance(record, dict):
        raise ValueError('Extraction metadata requires a record object')
    containers = [('', record)]
    for key in ('extraction', 'provenance'):
        value = record.get(key)
        if isinstance(value, dict):
            containers.append((key + '.', value))
    source = record.get('source')
    if isinstance(source, dict):
        for prefix, value in (('source.', source), ('source.original_metadata.', source.get('original_metadata'))):
            if isinstance(value, dict):
                containers.append((prefix, value))
                for key in ('extraction', 'provenance'):
                    child = value.get(key)
                    if isinstance(child, dict):
                        containers.append((prefix + key + '.', child))
    positive, negative, methods, evidence = [], [], [], []
    for prefix, value in containers:
        for key in ('ocr_used', 'used_ocr', 'ocr_applied'):
            flag = value.get(key)
            if type(flag) is bool:
                (positive if flag else negative).append(prefix + key)
                evidence.append(prefix + key)
        for key in ('extraction_method', 'acquisition_method', 'method'):
            # A general source/review method is not a text-extraction method.
            if key == 'method' and not prefix.endswith('extraction.'):
                continue
            method = value.get(key)
            if isinstance(method, str) and method.strip():
                methods.append(method)
                field = prefix + key
                if _NO_OCR_METHOD.search(method):
                    negative.append(field)
                    evidence.append(field)
                elif _OCR_METHOD.search(method):
                    positive.append(field)
                    evidence.append(field)
                elif _DIGITAL_METHOD.search(method):
                    negative.append(field)
                    evidence.append(field)
    used = True if positive else False if negative else None
    return {
        'ocr_used': used,
        'method': methods[0] if methods else None,
        'classification': 'ocr' if used is True else 'digital_text' if used is False else 'not_recorded',
        'evidence_fields': list(dict.fromkeys(evidence)),
        'conflicting_evidence': bool(positive and negative),
    }


def is_ocr(record):
    return extraction_metadata(record)['ocr_used'] is True


def needs_ocr_review(record):
    if not is_ocr(record):
        return False
    review = record.get('review') or {}
    state = review.get('ocr_qc') or review.get('independent_pro_qc') or review.get('status')
    return not (isinstance(state, str) and state.strip().lower() in ('passed', 'complete', 'completed', 'verified'))


def review_badges(record):
    if not is_ocr(record):
        return []
    review = record.get('review') or {}
    state = review.get('ocr_qc') or review.get('independent_pro_qc') or review.get('status')
    label = str(state) if isinstance(state, (str, int, float)) and str(state) else 'not recorded'
    return [{'label': 'OCR review: ' + label, 'pending': needs_ocr_review(record)}]


def text_direction(language, arabic=False):
    primary = str(language or '').lower().replace('_', '-').split('-')[0]
    return 'rtl' if arabic or primary in ('ar', 'fa', 'ur') else 'auto'

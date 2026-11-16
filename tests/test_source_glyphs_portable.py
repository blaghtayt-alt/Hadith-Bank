"""Portable exact French glyph authorization regression against real registry.

No fixed workspace paths, network, original PDF bytes, or publication. All
source clip, PNG, raw text and literal review hashes remain authoritative.
"""
import base64
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import pytest

REPO = Path(__file__).resolve().parents[1]
PRIVATE = REPO/'tests/fixtures/software_rebase/french/materials/fr-maach-nawawi-2021'
REL = 'materials/fr-maach-nawawi-2021'
assert REPO.is_dir() and (REPO/'scripts/material_registry.py').is_file()
sys.path.insert(0, str(REPO/'scripts'))
from material_registry import normalized_projection
from bank_discovery import expected_discovery_row
from source_glyphs import escaped_source_glyph_prose, _FRENCH_H2_LITERAL_AUTHORITY

ID='maach-2021-french-nawawi2:fr:p0007-0009:entry0002'
CLAIM='independent_literal_words_and_letters_passed_unvowelled_only;_production_accessibility_pending'
PENDING='proposed_pending_independent_qc'
PASSED='independent_literal_word_sequence_passed'
PDF='3d36eb9be1657c0d8fc683d34ddc73db450800ae91b9eefb2746d0ff12c0e90d'
TEXT='295cc8a6f976a05309f428368da76730f0838910cee77ce8b9fc846a32b59386'
PNG1='cfd1cf9621c0f14103115ae4494f2fb49fd4de525533ba5b98fe93a93f5ad230'
PNG2='87ef734b566b609ec0891f6a495d27c5a1bf78238f9e48c9481410993d0d5ae5'
REPORT='115fe308cd48b0f7254311cb563087d2842a764bdf8b4059173949b0b1f4c607'

def sha(x): return hashlib.sha256(x).hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

@pytest.fixture
def fixture(tmp_path):
    dest=tmp_path/REL;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(PRIVATE,dest)
    row=read(dest/'records.json')[0]
    original=copy.deepcopy(row)
    supporting=[]
    for filename in ('assets/F074.png','assets/F072.png','evidence/glyph-review/context-F074.png',
                     'evidence/glyph-review/context-F072.png','evidence/literal-qc/QC-RESULT.json',
                     'evidence/source-preservation/records-before-literal-qc-promotion.json'):
        p=dest/filename
        supporting.append({'path':REL+'/'+filename,'sha256':sha(p.read_bytes()),'size_bytes':p.stat().st_size})
    material={
        'canonical_records_path':REL+'/records.json', 'source_sha256':PDF,
        'source_descriptor':{'name':'Les 40 hadiths de l’imam An-Nawawi', 'format':'pdf'},
        'source_file':REL+'/source.pdf', 'dataset_id':'maach-2021-french-nawawi2',
        'language':'fr','book_key':'nawawi','edition':'maach-first-2021',
        'publication':{'visibility':'public','status':'published_pending_review',
           'authorized':True,'decision':'owner_requested_public_pending_review',
           'decision_date_japan':'2026-11-16','manifest_path':REL+'/manifest.json',
           'independent_qc_asserted':False,'rights_clearance_asserted':False},
        'supporting_files':supporting,
    }
    assert row['id']==ID and row['review']['glyph_accessibility_status']==CLAIM
    assert row['text']['arabic'] is None and sha(row['text']['translation'].encode())==TEXT
    # Deliberately no PDF bytes in portable QA fixture; source is a pinned
    # SHA reference only and no PDF download/source-recheck is asserted.
    assert row['source']['sha256']==PDF and material['source_sha256']==PDF
    assert not (dest/'source.pdf').exists()
    assert [sha((dest/f'assets/F0{x}.png').read_bytes()) for x in (74,72)]==[PNG1,PNG2]
    assert sha((dest/'evidence/literal-qc/QC-RESULT.json').read_bytes())==REPORT
    return row, material, tmp_path, dest, original

def project(fixture):
    row,material,root,*_=fixture
    before=copy.deepcopy(row)
    projected=normalized_projection(row,material,0,root)
    assert row==before,'projector edited the canonical raw row'
    assert projected['text_translation']==row['text']['translation']
    assert projected['text_arabic'] is None
    assert projected['id']==row['id']
    assert projected['review']['certified_release_eligible'] is False
    assert projected['review']['release_eligible'] is False
    return projected

def assert_pending(fixture):
    row,*_=fixture
    p=project(fixture)
    assert p['review']['glyph_accessibility_status']==PENDING
    assert p['review']['glyph_accessibility_status_as_source_claim']==row['review']['glyph_accessibility_status']
    assert p['review']['glyph_accessibility_result_sha256']==row['review']['glyph_accessibility_result_sha256']
    for g in p.get('source_glyphs') or []:
        assert g['accessibility_status']==PENDING
        assert 'independent_literal_review' not in g
        assert sha(base64.b64decode(g['data_uri'].split(',')[1],validate=True))==g['sha256']
    preview=expected_discovery_row(p,0)['readings'][0]
    assert preview['text']==row['text']['translation'][:len(preview['text'])]
    assert [g['accessibility_status'] for g in preview.get('source_glyphs',[])]==[PENDING]*len(preview.get('source_glyphs',[]))
    visible=escaped_source_glyph_prose(p['text_translation'],p.get('source_glyphs'))
    assert '<script' not in visible
    assert 'data-accessibility-status="independent_literal_word_sequence_passed"' not in visible
    return p

def test_exact_two_images_still_narrow_pass(fixture):
    p=project(fixture)
    assert p['review']['glyph_accessibility_status']==CLAIM
    assert 'glyph_accessibility_status_as_source_claim' not in p['review']
    assert [g['accessibility_status'] for g in p['source_glyphs']]==[PASSED,PASSED]
    assert [g['start'] for g in p['source_glyphs']]==[7,110]
    assert [g['alt_ar'] for g in p['source_glyphs']]==['رضي الله عنه','صلى الله عليه وسلم']
    assert [g['independent_literal_review']['result_sha256'] for g in p['source_glyphs']]==[REPORT,REPORT]
    assert _FRENCH_H2_LITERAL_AUTHORITY['result_sha256']==REPORT
    view=escaped_source_glyph_prose(p['text_translation'],p['source_glyphs'])
    assert view.count('data-accessibility-status="'+PASSED+'"')==2
    assert '\uf074' not in view and '\uf072' not in view

@pytest.mark.parametrize('change',[lambda r:r.pop('source_glyphs'),lambda r:r.__setitem__('source_glyphs',None)],ids=['removed','null'])
def test_missing_mapping_record_claim_is_downgraded(fixture,change):
    change(fixture[0]);p=assert_pending(fixture)
    assert p.get('source_glyphs') is None
    assert 'source_glyphs' not in p or p['source_glyphs'] is None
    assert '\uf074' in escaped_source_glyph_prose(p['text_translation'],p.get('source_glyphs'))
    assert '\uf072' in escaped_source_glyph_prose(p['text_translation'],p.get('source_glyphs'))

@pytest.mark.parametrize('variant',['first_only','second_only'])
def test_incomplete_valid_pair_cannot_claim_record_approval(fixture,variant):
    row=fixture[0]
    row['source_glyphs']=[row['source_glyphs'][0 if variant=='first_only' else 1]]
    p=assert_pending(fixture)
    assert len(p['source_glyphs'])==1
    assert p['source_glyphs'][0]['accessibility_status']==PENDING

@pytest.mark.parametrize('variant',['empty','empty_object','string','numeric','fake_null_string'])
def test_unsupported_mapping_is_rejected_not_approved(fixture,variant):
    values={'empty':[],'empty_object':{},'string':'[]','numeric':5,'fake_null_string':'null'}
    fixture[0]['source_glyphs']=values[variant]
    with pytest.raises((ValueError,TypeError)):
        project(fixture)

@pytest.mark.parametrize('variant',['bad_png_hash','external_url','traversal','html_literal','misaligned_offset','missing_asset','tampered_png'])
def test_invalid_mapping_or_asset_hard_fails(fixture,variant):
    row,mat,root,d,*_=fixture
    g=row['source_glyphs'][0]
    if variant=='bad_png_hash':g['sha256']='0'*64
    elif variant=='external_url':g['file']='https://attacker.invalid/X.png'
    elif variant=='traversal':g['file']='../../X.png'
    elif variant=='html_literal':g['accessibility']['arabic_literal']='<svg onload=alert(1)>'
    elif variant=='misaligned_offset':g['start']=8
    elif variant=='missing_asset':(d/'assets/F074.png').unlink()
    elif variant=='tampered_png':(d/'assets/F074.png').write_bytes(b'bad')
    with pytest.raises((ValueError,FileNotFoundError,TypeError)):
        project(fixture)

@pytest.mark.parametrize('variant',['review_missing','review_changed','coherent_rehash','record_ref_mismatch','glyph_ref_mismatch','predecessor_ref_mismatch'])
def test_incomplete_or_wrong_review_authority_returns_pending(fixture,variant):
    row,mat,root,d,*_=fixture
    q=d/'evidence/literal-qc/QC-RESULT.json'
    if variant=='review_missing':q.unlink()
    elif variant in ('review_changed','coherent_rehash'):
        report=read(q);report['verdicts'][0]['source_visual_basis']='TAMPERED NON-AUTHORIZED REPORT'
        write(q,report)
        if variant=='coherent_rehash':
            digest=sha(q.read_bytes())
            row['review']['glyph_accessibility_result_sha256']=digest
            for g in row['source_glyphs']:
                g['accessibility']['independent_review']['result_sha256']=digest
            for f in mat['supporting_files']:
                if f['path'].endswith('QC-RESULT.json'):f['sha256']=digest
    elif variant=='record_ref_mismatch':row['review']['glyph_accessibility_result_sha256']='0'*64
    elif variant=='glyph_ref_mismatch':row['source_glyphs'][0]['accessibility']['independent_review']['result_id']='SPOOF'
    elif variant=='predecessor_ref_mismatch':row['source_glyphs'][0]['accessibility']['independent_review']['reviewed_candidate_sha256']='0'*64
    p=assert_pending(fixture)
    assert len(p['source_glyphs'])==2

@pytest.mark.parametrize('variant',['original_unmapped_pending','other_record_unmapped','another_material_unmapped'])
def test_unrelated_legacy_remains_unchanged(fixture,variant):
    row,mat,root,d,*_=fixture
    row.pop('source_glyphs')
    if variant=='original_unmapped_pending':row['review']['glyph_accessibility_status']=PENDING
    elif variant=='other_record_unmapped':row['id']='unrelated-french-occurrence';row['review']['glyph_accessibility_status']='historical-other-source-review'
    elif variant=='another_material_unmapped':mat['canonical_records_path']='materials/other-source/records.json'
    p=project(fixture)
    assert p['review']['glyph_accessibility_status']==row['review']['glyph_accessibility_status']
    assert 'glyph_accessibility_status_as_source_claim' not in p['review']
    assert 'source_glyphs' not in p

def test_malicious_html_without_mapping_is_plain_text(fixture):
    row=fixture[0]
    row.pop('source_glyphs')
    value='<script>alert(1)</script>'
    # Only test the isolated renderer's escaping; source record never edited.
    p=assert_pending(fixture)
    html=escaped_source_glyph_prose(value,p.get('source_glyphs'))
    assert '<script>' not in html and '&lt;script&gt;' in html

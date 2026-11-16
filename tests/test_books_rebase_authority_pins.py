"""Bounded source-authority and current-main preservation guards for the rebase.

Source content, manual decisions, and accepted glyph images are not reassessed.
These exact hashes are software-reconciliation checks, not release certificates.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'tests/fixtures/software_rebase'
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def test_exact_approved_source_authorities_and_current_discovery_engine():
    pinned={
        'scripts/source_glyphs.py':'384e5e70dadeaab91e73d1b4dcc62501b44b788dad6bef15c53f3b7d378570a6',
        'reader/source-uncertainty.js':'4d6c01d99528813344684600a11f45c23443b80f846ee3bd3c60425021498c39',
        'reader/discovery-engine.js':'511357f470fd83b908fb367559d42b057eab9c9a73e294ec0f62a5eea86c224e',
    }
    for name,digest in pinned.items():assert SHA(ROOT/name)==digest,name
    # Compute the closed Hindi authority digest from its pinned accepted bytes.
    assert SHA(ROOT/'scripts/source_uncertainty_authority.json') == (
        'a67c25a06be950798a45050a52a68c0dd77a6bc73389a184953eeee011a2c895')

def test_pinned_fixture_files_and_immutable_historical_holds():
    manifest=json.loads((FIX/'FIXTURE_HASHES.json').read_text())
    for name,info in manifest['files'].items():
        p=FIX/name
        assert p.stat().st_size==info['bytes'],name
        assert SHA(p)==info['sha256'],name
    rows=json.loads((FIX/'hindi-fourteen.json').read_text())
    assert len(rows)==14
    kind_counts={}
    for r in rows:
        for x in r['source_uncertainty_projection']['annotations']:
            kind_counts[x['kind']]=kind_counts.get(x['kind'],0)+1
    assert kind_counts=={'accepted_uncertain_reading':15,'unfilled_source_gap':1,'unreviewed_source_gap':2}

"""Portable actual Node/Python 14-record and actual 6pt/3de projector proof.

Uses the production projection script and lazy reader builder; never a private
work-tree, mock singleton, hosted route or material registration. See proof/.
"""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def test_real_node_python_exact_records_and_negative_controls(tmp_path):
    proc=subprocess.run([sys.executable,str(ROOT/'proof/replay_real_callers.py'),
                         '--out',str(tmp_path)],cwd=ROOT,capture_output=True,text=True,timeout=70)
    assert proc.returncode==0,(proc.stdout+'\n'+proc.stderr)[-4000:]
    proof=json.loads((tmp_path/'actual-real-callers-results.json').read_text())
    phases=proof['phases']
    assert proof['status']=='PASS_BOUNDED'
    assert phases['source_controls']['count']==14
    assert phases['source_controls']['annotations']=={
        'accepted_uncertain_reading':15,'unfilled_source_gap':1,'unreviewed_source_gap':2}
    assert phases['real_node_projection']['records']==14
    assert phases['real_python_lazy_builder']['record_count']==14
    assert phases['real_python_lazy_builder']['full_record_detail_bytes_exact']
    assert phases['real_python_lazy_builder']['module_shim_used'] is False
    assert phases['real_python_lazy_builder']['raw_audit_tokens_in_search'] is False
    assert len(phases['negative_controls']['rejections'])==7
    assert len(phases['negative_controls']['actual_python_builder_rejections'])==2
    assert phases['ordinary_actual_pt6_de3']['byte_identical_to_current_main']
    assert phases['ordinary_actual_pt6_de3']['records']==9
    assert (tmp_path/'actual-details-source-stream.jsonl').is_file()
    assert (tmp_path/'actual14-node-projection.jsonl').is_file()

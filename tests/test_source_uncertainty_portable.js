"use strict";
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const helper=fs.readFileSync(path.join(root,'reader/source-uncertainty.js'),'utf8');
const note=vm.runInNewContext(helper+'\nHadithSourceUncertainty;', {TextEncoder,TextDecoder,BigInt,DataView,Uint8Array,Uint32Array});
const records=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/software_rebase/hindi-fourteen.json'),'utf8'));
let checks=0;const test=(name,fn)=>{fn();checks++;process.stdout.write('PASS '+name+'\n');};
const valid=record=>note.validatedParts(record.text_translation,record.source_uncertainty_projection,record.id,record.source_uncertainty_projection.expected_body_sha256);
for(const [index,r] of records.entries())test('fixture exact bound reconstruction '+(index+1)+' '+r.id,()=>{
  const parts=valid(r);
  assert.equal(note.sourceReconstruction(parts),r.text_translation);
  if(note.hasGaps(parts))assert.throws(()=>note.exactQuotation(parts),/incomplete source quotation/);
  else assert.equal(note.exactQuotation(parts),r.text_translation);
  assert.equal(parts.filter(p=>p.kind==='note').length,r.source_uncertainty_projection.annotations.length);
  assert.equal(parts.filter(p=>p.kind==='note').map(p=>p.text).every(t=>t==='(OCR wasn’t clear)'),true);
  assert.equal(parts.filter(p=>p.kind==='quotation').some(p=>p.source_text.includes('⟦')),false);
});
test('18 notes / 2 held / 3 source gaps',()=>{
  const all=records.flatMap(valid);assert.equal(all.filter(p=>p.kind==='note').length,18);
  assert.equal(all.filter(p=>p.review_status==='unreviewed').length,2);
  assert.equal(all.filter(p=>p.kind==='gap').length,3);
});
for(const input of ['', 'abc', 'आ😀<script>', 'देवनागरी 🌐 शब्द', '🌎'.repeat(500), 'क'.repeat(50000)])
  test('SHA exact UTF8 '+input.length,()=>assert.equal(note.digest(input),crypto.createHash('sha256').update(input).digest('hex')));
function mustThrow(modifier){const copy=structuredClone(records[4]);modifier(copy);assert.throws(()=>valid(copy),/quotation withheld/);}
test('boolean start forbidden',()=>mustThrow(r=>{r.source_uncertainty_projection.annotations[0].start=true}));
test('boolean end forbidden',()=>mustThrow(r=>{r.source_uncertainty_projection.annotations[0].end=false}));
test('bound digest changed',()=>mustThrow(r=>{r.source_uncertainty_projection.expected_body_sha256='f'.repeat(64)}));
test('source mismatch',()=>mustThrow(r=>{r.text_translation+='x'}));
test('parent ID mismatch',()=>mustThrow(r=>{r.source_uncertainty_projection.record_id='other'}));
test('duplicate ID forbidden',()=>mustThrow(r=>{r.source_uncertainty_projection.annotations[1].issue_id=r.source_uncertainty_projection.annotations[0].issue_id}));
test('overlapping spans forbidden',()=>mustThrow(r=>{r.source_uncertainty_projection.annotations[1].start=r.source_uncertainty_projection.annotations[0].start}));
test('unannotated gap forbidden',()=>mustThrow(r=>{r.source_uncertainty_projection.annotations=r.source_uncertainty_projection.annotations.filter(x=>!x.kind.endsWith('source_gap'))}));
test('glyph combination fail closed',()=>assert.throws(()=>note.validatedParts(records[0].text_translation,records[0].source_uncertainty_projection,records[0].id,null,[{start:1}]),/quotation withheld/));
test('external expected binding fail closed',()=>assert.throws(()=>note.validatedParts(records[0].text_translation,records[0].source_uncertainty_projection,records[0].id,'0'.repeat(64)),/quotation withheld/));
test('unicode codepoints, UTF16 boundaries, malformed surrogate',()=>{
  const body='आ😀नमाज़';
  assert.equal(body.length,Array.from(body).length+1);
  assert.equal(note.cpLength(body),Array.from(body).length);
  assert.equal(note.utf16AtCodepoint(body,2),3);
  assert.equal(note.isScalarBoundary(body,2),false);
  assert.equal(note.isScalarBoundary(body,1),true);
  assert.equal(note.isScalarBoundary(body,3),true);
  assert.equal(note.cpSlice(body,1,2),'😀');
  assert.equal(note.isScalarBoundary(body,0),true);
  assert.equal(note.isScalarBoundary(body,body.length),true);
  const r=structuredClone(records[0]);r.text_translation+='\uD800';
  assert.throws(()=>valid(r),/quotation withheld/);
});
test('no untrusted synthetic text/record identity can opt in',()=>{
  const body='ab⟦GAP⟧cd',start=2,end=7;
  const projection={schema:'source_uncertainty_projection.v1',record_id:'synthetic',text_record_id:'synthetic-HI',field:'text.translation',expected_body_sha256:note.digest(body),annotations:[{issue_id:'gap',start,end,span_sha256:note.digest(body.slice(start,end)),kind:'unfilled_source_gap'}]};
  assert.throws(()=>note.validatedParts(body,projection,'synthetic'),/quotation withheld/);
});
console.log('RESULT '+checks+' JS pure tests PASS');

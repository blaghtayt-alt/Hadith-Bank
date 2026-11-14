"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),path=require("node:path"),{execFileSync}=require("node:child_process");
const engineAPI=require("../reader/discovery-engine.js");
const payload=JSON.parse(execFileSync("python",[path.join(__dirname,"test_bank_discovery.py"),"--fixture"],{encoding:"utf8",maxBuffer:8*1024*1024}));
const engine=engineAPI.create(payload);
const fs=require("node:fs"),os=require("node:os"),zlib=require("node:zlib"),crypto=require("node:crypto");

test("exact reference ranks and groups accepted translations without number collisions",()=>{
  const result=engine.search({query:"Bukhari 1",mode:"reference"});
  assert.equal(result.results.length,1);assert.deepEqual(result.results[0].members,[0,1]);
  assert.deepEqual(result.matchedOccurrences,[0,1]);assert.equal(result.results[0].matchKind,"exact-reference");
  assert.equal(engine.search({query:"١",mode:"reference"}).results.length,0);
  assert.equal(engine.search({query:"بُخَارِي ١",mode:"reference"}).results.length,1);
  assert.equal(engine.search({query:"Bukhari 1-2",mode:"reference"}).results.length,0);
});

test("quoted phrases require exact consecutive words and outrank scattered wording",()=>{
  const exact=engine.search({query:'"actions depend on intentions"',mode:"wording"});
  assert.deepEqual(exact.matchedOccurrences,[0]);assert.equal(exact.results[0].matchKind,"exact-phrase");
  const loose=engine.search({query:"actions depend on intentions",mode:"wording"});
  assert.equal(loose.results[0].ordinal,0);assert.ok(loose.matchedOccurrences.includes(2));
});

test("remembered wording gets explicit partial quotation matches only after exact words fail",()=>{
  const data=JSON.parse(execFileSync("python",[path.join(__dirname,"test_bank_discovery.py"),"--broader-fixture"],{encoding:"utf8"}));
  const e=engineAPI.create(data),result=e.search({query:"actions depend on intentions",mode:"wording"});
  assert.ok(result.broaderWording);assert.deepEqual(result.broaderWording.ignoredTerms,["on"]);
  assert.deepEqual([...result.matchedOccurrences].sort((a,b)=>a-b),[0,1,6]);
  for(const hit of result.results){assert.equal(hit.matchKind,"broader-wording");assert.deepEqual(hit.matchedTerms,["actions","intentions"]);assert.deepEqual(hit.missingTerms,["depend"]);assert.equal(hit.matchLocation.term,"actions");assert.equal(hit.matchLocation.field,"quotation");}
  for(const [query,mode] of [['"actions depend on intentions"',"wording"],["actions depend on intentions","reference"],["Bukhari 1 actions depend on intentions","wording"],["actions missingword","wording"]]){
    const strict=e.search({query,mode});assert.equal(strict.broaderWording,null);assert.equal(strict.results.length,0);
  }
  assert.equal(e.search({query:"actions intentions",mode:"wording"}).broaderWording,null);
  assert.equal(e.search({query:"TEST-broader-positive",mode:"wording"}).results[0].matchKind,"exact-occurrence");
});

test("broader wording retains English Arabic and cross-reading negation boundaries",()=>{
  const data=JSON.parse(execFileSync("python",[path.join(__dirname,"test_bank_discovery.py"),"--broader-fixture"],{encoding:"utf8"}));
  const e=engineAPI.create(data),negative=e.search({query:"not actions depend on intentions",mode:"wording"});
  assert.deepEqual(negative.matchedOccurrences,[1]);assert.deepEqual(negative.broaderWording.requiredTerms,["not"]);
  assert.equal(e.search({query:"never actions depend on intentions",mode:"wording"}).results.length,0);
  const arabic=e.search({query:"لا تجريب لفظ عمل",mode:"wording"});
  assert.deepEqual(arabic.matchedOccurrences,[5]);assert.deepEqual(arabic.broaderWording.requiredTerms,["لا"]);
  assert.equal(e.search({query:"without actions depend on intentions",mode:"wording"}).results.length,0);
  assert.equal(e.search({query:"don't actions depend on intentions",mode:"wording"}).results.length,0);
});

test("full quotation indexing finds late words outside every short preview",()=>{
  const result=engine.search({query:"needleword",mode:"wording"});
  assert.deepEqual(result.matchedOccurrences,[6]);assert.equal(result.results[0].excerptKind,"source-preview");
  assert.equal(result.results[0].matchLocation.language,"en");assert.ok(result.results[0].matchLocation.tokenPosition>100);
  assert.ok(!result.results[0].excerpt.includes("needleword"));
});

test("Arabic diacritics, alif forms, digits and transliteration are disposable query aids",()=>{
  assert.deepEqual(engine.search({query:"اعمال",mode:"wording"}).matchedOccurrences,[5]);
  assert.equal(engineAPI.normalize("صَلَاة ١۲"),engineAPI.normalize("صلاة 12"));
  const result=engine.search({query:"salah",mode:"topic"});
  assert.ok(result.matchedOccurrences.includes(5));assert.ok(result.editorialExpansion.label.includes("Editorial"));
  assert.ok(result.editorialExpansion.terms.includes("الصلاة"));
});

test("Japanese Chinese and Indic words remain searchable without destroying vowel marks",()=>{
  assert.deepEqual(engine.search({query:"行為",mode:"wording"}).matchedOccurrences,[1]);
  assert.deepEqual(engine.search({query:"父母",mode:"wording"}).matchedOccurrences,[7]);
  assert.deepEqual(engine.search({query:"की",mode:"wording"}).matchedOccurrences,[8]);
  assert.deepEqual(engine.search({query:"क",mode:"wording"}).matchedOccurrences,[]);
  assert.deepEqual(engineAPI.tokenize("ガ"),["ガ"]);
});

test("preferred language selects supplied text inside accepted group without translation",()=>{
  const result=engine.search({query:"Bukhari 1",mode:"reference",preferredLanguage:"ja"});
  assert.equal(result.results[0].ordinal,1);assert.equal(result.results[0].language,"ja");
  assert.equal(result.results[0].excerpt,payload.rows[1].readings.find(item=>item.language==="ja").text);
  assert.equal(result.results[0].row.readings.find(item=>item.language==="ar").translationOrigin,null);
});

test("preferred family translation preserves the actual matched occurrence and locator",()=>{
  const result=engine.search({query:'"actions depend on intentions"',mode:"wording",preferredLanguage:"ja"}).results[0];
  assert.equal(result.ordinal,1);assert.equal(result.language,"ja");assert.equal(result.excerptKind,"source-preview");
  assert.equal(result.matchedOrdinal,0);assert.deepEqual(result.matchedMembers,[0]);
  assert.equal(result.matchLocation.language,"en");assert.equal(result.matchLocation.readingId,"source-translation");
  assert.equal(result.matchLocation.term,"actions");assert.equal(result.matchLocation.editorialExpansion,false);
  const filtered=engine.search({query:"intentions",mode:"wording",preferredLanguage:"ja",filters:{language:"en"}}).results[0];
  assert.equal(filtered.ordinal,0);
  const topic=engine.search({query:"salah",mode:"topic"}).results.find(item=>item.matchedOrdinal===5);
  assert.equal(topic.matchLocation.language,"ar");assert.equal(topic.matchLocation.editorialExpansion,true);
  assert.ok(engineAPI.excerpt("والصلاة",topic.matchLocation.term).matched);
});

test("source facets keep narrator, report type, named grade and chapter together",()=>{
  const grade=payload.rows[3].grades[0].value;
  const result=engine.search({filters:{narrator:"TEST Named Narrator",chapter:"TEST Book / TEST Chapter",reportType:"companion_report",grade,topic:payload.rows[3].topics[0].value}});
  assert.deepEqual(result.matchedOccurrences,[3]);
  assert.equal(engine.search({filters:{grade:"TEST Uncredited"}}).results.length,0);
  assert.equal(engine.search({filters:{availability:"both-text"}}).matchedOccurrences.includes(0),true);
  assert.equal(engine.search({filters:{availability:"missing-english"}}).matchedOccurrences.includes(1),true);
});

test("topic expansion and spelling suggestions are visible and never silently applied",()=>{
  const exact=engine.search({query:"anger",mode:"wording"});assert.equal(exact.results.length,0);
  assert.ok(exact.suggestions.some(item=>item.kind==="editorial-topic"));
  const broad=engine.search({query:"anger",mode:"topic"});assert.deepEqual(broad.matchedOccurrences,[4]);
  const typo=engine.search({query:"intentionz",mode:"wording"});assert.equal(typo.results.length,0);
  assert.ok(typo.suggestions.some(item=>item.kind==="spelling"&&item.query==="intentions"));
});

test("source annotations and absent text never enter default quotation search",()=>{
  assert.equal(engine.search({query:"hiddenannotationword"}).results.length,0);
  assert.equal(engine.search({query:"definitelyunfindableword"}).complete,true);
});

test("source preview refinement uses exact original substring with Unicode-safe offsets",()=>{
  const text="😀 TEST prefix ".repeat(30)+"أَعْمَال نَصٌّ matchedword";
  const refined=engineAPI.excerpt(text,"اعمال",60);
  assert.equal(refined.matched,true);assert.equal(refined.text,text.slice(refined.start,refined.end));
  assert.ok(refined.text.includes("أَعْمَال"));assert.ok(refined.start>0);assert.ok(!/^[\uDC00-\uDFFF]/.test(refined.text));
});

test("exact occurrence deep links retain selection and expose raw-ID ambiguity",()=>{
  const result=engine.search({query:"TEST-provider-en",preferredLanguage:"ja"});assert.equal(result.results[0].ordinal,0);
  const ambiguous=JSON.parse(JSON.stringify(payload));ambiguous.rows[2].id=ambiguous.rows[4].id;ambiguous.rows[2].edition="TEST-second-edition";
  const alternate=engineAPI.create(ambiguous);assert.equal(alternate.getOrdinal(ambiguous.rows[2].id),undefined);
  assert.deepEqual(alternate.getOrdinals(ambiguous.rows[2].id),[2,4]);
  assert.equal(alternate.search({query:ambiguous.rows[2].id}).matchingOccurrenceCount,2);
});

test("corrupt postings and overlapping groups fail honestly",()=>{
  assert.throws(()=>engineAPI.decodePosting("gA==",10,1),/truncated/);
  const bad=JSON.parse(JSON.stringify(payload));bad.groups.push({...bad.groups[0],id:"TEST-overlap"});
  assert.throws(()=>engineAPI.create(bad),/ambiguous family/);
  const before=JSON.stringify(payload);engine.search({query:"TEST"});assert.equal(JSON.stringify(payload),before);
});

function hosted(t) {
  const folder=fs.mkdtempSync(path.join(os.tmpdir(),"hadith-discovery-test-"));t.after(()=>fs.rmSync(folder,{recursive:true,force:true}));
  const descriptor=JSON.parse(execFileSync("python",[path.join(__dirname,"test_bank_discovery.py"),"--sharded-fixture",folder],{encoding:"utf8"}));
  function read(part){const data=fs.readFileSync(path.join(folder,part.path));assert.equal(data.length,part.bytes);assert.equal(crypto.createHash("sha256").update(data).digest("hex"),part.sha256);const raw=zlib.gunzipSync(data);assert.equal(raw.length,part.uncompressed_bytes);assert.equal(crypto.createHash("sha256").update(raw).digest("hex"),part.uncompressed_sha256);return JSON.parse(raw);}
  const wire=read(descriptor),requests=[];
  const loadShard=async(part,{signal}={})=>{if(signal?.aborted)throw new DOMException("cancelled","AbortError");requests.push(part);return read(part);};
  return {wire,requests,engine:engineAPI.create(wire,{loadShard}),loadShard,descriptor};
}

test("hosted reference search needs no postings and only visible source previews",async t=>{
  const fixture=hosted(t),e=fixture.engine;
  assert.ok(e.rows.every(row=>!row.readings.length));
  await e.prepare({query:"Bukhari 1",mode:"reference"});
  const result=e.search({query:"Bukhari 1",mode:"reference",preferredLanguage:"ja"});
  assert.equal(fixture.requests.length,0);assert.equal(result.results.length,1);
  await e.prepareResults(result.results);
  assert.equal(fixture.requests.length,1);assert.ok(fixture.requests[0].schema.endsWith("-previews"));
  assert.equal(result.results[0].language,"ja");assert.ok(result.results[0].excerpt.includes("行為"));
});

test("hosted wording loads relevant term shards and reuses warm cache",async t=>{
  const fixture=hosted(t),e=fixture.engine;
  const query={query:'"actions depend on intentions"',mode:"wording"};
  assert.throws(()=>e.search(query),/not prepared/);
  await e.prepare(query);const cold=fixture.requests.length;
  assert.ok(cold>0);assert.ok(cold<fixture.wire.postings_shards.length);
  const result=e.search(query);assert.deepEqual(result.matchedOccurrences,[0]);
  await e.prepareResults(result.results.slice(0,1));assert.ok(result.results[0].excerpt.includes("intentions"));
  const warm=fixture.requests.length;await e.prepare(query);await e.prepareResults(result.results);
  assert.equal(fixture.requests.length,warm);
});

test("shard failure and cancellation cannot masquerade as complete zero results",async t=>{
  const fixture=hosted(t);
  const bad=engineAPI.create(fixture.wire,{loadShard:async()=>{throw new Error("TEST network unavailable");}});
  await assert.rejects(bad.prepare({query:"intentions",mode:"wording"}),/network unavailable/);
  assert.throws(()=>bad.search({query:"intentions",mode:"wording"}),/not prepared/);
  const controller=new AbortController();controller.abort();
  await assert.rejects(fixture.engine.prepare({query:"intentions"},{signal:controller.signal}),{name:"AbortError"});
  assert.equal(fixture.requests.length,0);
});

test("wrong source binding in a fetched posting part is rejected",async t=>{
  const fixture=hosted(t),e=engineAPI.create(fixture.wire,{loadShard:async(part,options)=>({...await fixture.loadShard(part,options),records_sha256:"wrong"})});
  await assert.rejects(e.prepare({query:"intentions"}),/source binding mismatch/);
});

test("decoded posting eviction cannot lose another term in the prepared phrase",async t=>{
  const fixture=hosted(t),e=engineAPI.create(fixture.wire,{loadShard:fixture.loadShard,maxPostingCacheUnits:5});
  for(const query of ["intentions",'"actions depend on intentions"',"actions depend on intentions"]){
    await e.prepare({query,mode:"wording"});const result=e.search({query,mode:"wording"});
    assert.ok(result.matchedOccurrences.includes(0));assert.ok(e.metrics().cachedPostingUnits<=5);
  }
});

test("missing preview ranges fail before a false empty source preview",t=>{
  const fixture=hosted(t),bad=JSON.parse(JSON.stringify(fixture.wire));bad.preview_shards.shift();
  assert.throws(()=>engineAPI.create(bad,{loadShard:fixture.loadShard}),/descriptor coverage/);
});

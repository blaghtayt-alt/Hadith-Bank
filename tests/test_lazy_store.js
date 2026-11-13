"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {createHash, webcrypto} = require("node:crypto");
const {gzipSync, gunzipSync} = require("node:zlib");
const Lazy = require("../reader/lazy-store.js");
const BASE = "https://example.test/bank/reader.html";
const digest = bytes => createHash("sha256").update(bytes).digest("hex");
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const jsonl = rows => Buffer.from(rows.map(row => JSON.stringify(row) + "\n").join(""));

function fixture({count=6, detailBytes=91, rowsPerPart=2, padding=0}={}) {
  const records=Array.from({length:count},(_,i)=>({
    id:"id-"+i, language:"en", book_key:"muslim", edition:"test-edition", source_id:"source-test",
    text_translation:["alpha العربية 東京","gamma فارسی ۱۲۳","alpha beta","delta ٤٥","epsilon","alpha beta"][i%6]+" "+"x".repeat(padding),
    notes:[{exact:"Original context "+i,uncertain:null}], unknown:null, false_value:false,
  }));
  const primary=records.map((record,i)=>["alpha العربية 東京","gamma فارسی 123","alpha beta","delta 45","epsilon","alpha beta"][i%6]);
  const annotation=records.map((record,i)=>["beta commentary","alpha notes","","independent context","delta","endnote"][i%6]);
  let offset=0;
  const directory=records.map(record=>{
    const length=Buffer.byteLength(JSON.stringify(record)+"\n");
    const row={id:record.id,language:record.language,book_key:record.book_key,edition:record.edition,source_id:record.source_id,_reader:{languages:["en","ar"],origin:"human",availability:{arabic:"text",english:"text"},ocr_pending:false,citation_pairs:["muslim:1"],detail:[offset,length]}};
    offset+=length;return row;
  });
  const assets=new Map(), manifest={schema:"hadith-bank-reader-lazy-v2",encoding:"gzip-jsonl-lazy-v2",record_count:count,jsonl_sha256:digest(jsonl(records)),max_shard_bytes:65536};
  function part(name,index,plain,first,last) {
    const compressed=gzipSync(plain),path="reader-data/"+name+"/part-"+index+".jsonl.gz";
    assets.set(new URL(path,BASE).href,compressed);
    const item={path,sha256:digest(compressed),bytes:compressed.length,uncompressed_bytes:plain.length,count:plain.filter(byte=>byte===10).length};
    if(first!==undefined)Object.assign(item,{first_ordinal:first,last_ordinal:last});
    return item;
  }
  for(const [name,rows] of [["directory",directory],["search",primary.map((key,i)=>[i,key])],["annotations",annotation.map((key,i)=>[i,key])]]){
    const plain=jsonl(rows),spec={encoding:"gzip-jsonl-shards",record_count:count,jsonl_sha256:digest(plain),max_shard_bytes:65536,shards:[]};
    for(let i=0;i<rows.length;i+=rowsPerPart)spec.shards.push(part(name,spec.shards.length,jsonl(rows.slice(i,i+rowsPerPart)),i,Math.min(i+rowsPerPart,rows.length)-1));
    manifest[name]=spec;
  }
  const plain=jsonl(records),details={schema:"hadith-bank-reader-shards-v1",encoding:"gzip-jsonl-shards",record_count:count,jsonl_sha256:digest(plain),max_shard_bytes:65536,plain_part_bytes:detailBytes,shards:[]};
  for(let i=0;i<plain.length;i+=detailBytes)details.shards.push(part("details",details.shards.length,plain.subarray(i,i+detailBytes)));
  manifest.details=details;
  return {manifest,assets,records,primary,annotation,directory,part};
}
function transport(f,options={}) {
  const stats={calls:[],active:0,peak:0,aborts:0,options:[]};
  const fetch=async(url,init)=>{
    stats.calls.push(url);stats.options.push(init);stats.active++;stats.peak=Math.max(stats.peak,stats.active);
    try {
      const duration=typeof options.delay==="function"?options.delay(url):options.delay||0;
      if(duration)await new Promise((resolve,reject)=>{
        const finish=()=>{clearTimeout(timer);init.signal.removeEventListener("abort",abort);};
        const abort=()=>{finish();stats.aborts++;reject(Object.assign(new Error("aborted"),{name:"AbortError"}));};
        const timer=setTimeout(()=>{finish();resolve();},duration);
        if(init.signal.aborted)abort();else init.signal.addEventListener("abort",abort,{once:true});
      });
      if(options.fail && options.fail(url))throw new Error("network fixture failure");
      let bytes=f.assets.get(url);assert.ok(bytes,"unexpected request "+url);
      if(options.changeBytes)bytes=options.changeBytes(url,bytes);
      const response=new Response(bytes,{status:200,headers:{"content-length":String(bytes.length)}});
      if(options.response)options.response(url,response);
      return response;
    } finally{stats.active--;}
  };
  return {fetch,stats};
}
function create(f,networkOptions={},storeOptions={},events=[]) {
  const network=transport(f,networkOptions);
  const store=Lazy.create(f.manifest,BASE,event=>events.push(event),{fetch:network.fetch,crypto:webcrypto,...storeOptions});
  return {store,...network,events};
}
function mutatePart(f,name,index,change) {
  const part=f.manifest[name].shards[index],url=new URL(part.path,BASE).href;
  let plain=gunzipSync(f.assets.get(url));plain=Buffer.from(change(plain));
  const compressed=gzipSync(plain);f.assets.set(url,compressed);
  Object.assign(part,{bytes:compressed.length,sha256:digest(compressed),uncompressed_bytes:plain.length});
  const all=Buffer.concat(f.manifest[name].shards.map(item=>gunzipSync(f.assets.get(new URL(item.path,BASE).href))));
  f.manifest[name].jsonl_sha256=digest(all);
  if(name==="details")f.manifest.jsonl_sha256=digest(all);
}
function mutateDirectory(f,change) {
  const rows=f.directory.map(row=>structuredClone(row));change(rows);
  const amount=f.manifest.directory.shards[0]?.count||1;
  for(let i=0;i<f.manifest.directory.shards.length;i++)mutatePart(f,"directory",i,()=>jsonl(rows.slice(i*amount,(i+1)*amount)));
}
const paths = stats => stats.calls.map(url=>new URL(url).pathname);

test("directory startup verifies only directory parts and freezes all locator metadata",async()=>{
  const f=fixture(),{store,stats,events}=create(f);
  const rows=await store.loadDirectory();assert.deepEqual(rows,f.directory);
  assert.ok(paths(stats).every(path=>path.includes("/directory/")));
  assert.equal(stats.calls.length,f.manifest.directory.shards.length);
  assert.equal(store.cacheStats().bytes,0);
  assert.ok(Object.isFrozen(rows)&&Object.isFrozen(rows[0])&&Object.isFrozen(rows[0]._reader.detail)&&Object.isFrozen(rows[0]._reader.availability));
  assert.throws(()=>{rows[0]._reader.detail[0]=9;},TypeError);
  assert.strictEqual(await store.loadDirectory(),rows);
  assert.equal(events.at(-1).complete,true);
  const cancelled=new AbortController();cancelled.abort();await assert.rejects(store.loadDirectory({signal:cancelled.signal}),{name:"AbortError"});
});

test("empty directory validates its exact SHA-256 and makes no requests",async()=>{
  const f=fixture({count:0}),{store,stats}=create(f);
  assert.deepEqual(await store.loadDirectory(),[]);assert.equal(stats.calls.length,0);
  assert.deepEqual(await store.getRecords([]),[]);
});

test("full record reconstructs cross-part UTF-8 exactly and fetches only intersecting chunks",async()=>{
  const f=fixture({detailBytes:3}),{store,stats}=create(f,{}, {cacheBytes:0});
  await store.loadDirectory();stats.calls.length=0;
  const index=0,[start,length]=f.directory[index]._reader.detail;
  const expected=f.manifest.details.shards.slice(Math.floor(start/3),Math.floor((start+length-1)/3)+1).map(part=>new URL(part.path,BASE).href);
  assert.deepEqual(await store.getRecord(index),f.records[index]);
  assert.deepEqual(stats.calls,expected);
  assert.ok(expected.some(url=>{try{new TextDecoder("utf-8",{fatal:true}).decode(gunzipSync(f.assets.get(url)));return false;}catch{return true;}}));
});

test("concurrent callers share a shard; cancelling one subscription preserves the other",async()=>{
  const f=fixture({detailBytes:1000}),{store,stats}=create(f,{delay:12});
  await store.loadDirectory();stats.calls.length=0;
  const cancelled=new AbortController();
  const one=store.getRecord(0,{signal:cancelled.signal});const rejected=assert.rejects(one,{name:"AbortError"});
  const two=store.getRecord(0);setTimeout(()=>cancelled.abort(),1);
  assert.deepEqual(await two,f.records[0]);await rejected;
  assert.equal(stats.calls.length,1);assert.equal(stats.aborts,0);
  assert.ok(stats.options.every(option=>option.credentials==="same-origin"&&option.redirect==="error"));
});

test("cancelling every subscription aborts transport and a later caller can retry",async()=>{
  const f=fixture({detailBytes:1000}),{store,stats}=create(f,{delay:25});
  await store.loadDirectory();const controller=new AbortController();
  const request=store.getRecord(0,{signal:controller.signal});const rejection=assert.rejects(request,{name:"AbortError"});
  await delay(2);controller.abort();await rejection;await delay(1);
  assert.equal(stats.aborts,1);assert.deepEqual(await store.getRecord(0),f.records[0]);
  assert.equal(store.cacheStats().activeRequests,0);
});

test("decoded LRU never exceeds its cap; record objects are not retained",async()=>{
  const f=fixture({detailBytes:100}),{store,stats}=create(f,{}, {cacheBytes:200});
  const first=await store.getRecord(0);
  for(let i=1;i<f.records.length;i++){assert.deepEqual(await store.getRecord(i),f.records[i]);assert.ok(store.cacheStats().bytes<=200);}
  const before=stats.calls.length;first.notes[0].exact="caller changed its object";
  assert.deepEqual(await store.getRecord(0),f.records[0]);assert.ok(stats.calls.length>before);
  assert.ok(store.cacheStats().entries<=2);
});

test("record larger than cache remains complete without entering an oversized cache",async()=>{
  const f=fixture({padding:3000,detailBytes:800}),{store}=create(f,{}, {cacheBytes:600});
  assert.deepEqual(await store.getRecord(0),f.records[0]);assert.equal(store.cacheStats().bytes,0);
});

test("search skips irrelevant ordinal ranges and keeps deduplicated candidate order",async()=>{
  const f=fixture(),{store,stats}=create(f);
  assert.deepEqual(await store.search([5,0,5],["alpha"],false),[5,0]);
  assert.deepEqual(paths(stats),["/bank/reader-data/search/part-0.jsonl.gz","/bank/reader-data/search/part-2.jsonl.gz"]);
  assert.ok(stats.calls.every(url=>!url.includes("annotations")&&!url.includes("details")&&!url.includes("directory")));
});

test("terms may match separate primary and annotation fields only with commentary enabled",async()=>{
  const f=fixture(),{store,stats}=create(f);
  assert.deepEqual(await store.search([0,2],["alpha","beta"],false),[2]);
  assert.ok(!stats.calls.some(url=>url.includes("annotations")));
  assert.deepEqual(await store.search([0,2],["alpha","beta"],true),[0,2]);
  assert.deepEqual(paths(stats).filter(path=>path.includes("annotations")),["/bank/reader-data/annotations/part-0.jsonl.gz"]);
});

test("bitsets retain every term across more than one 32-bit word",async()=>{
  const f=fixture({count:2});const terms=Array.from({length:70},(_,i)=>"token-"+i+";");
  mutatePart(f,"search",0,()=>jsonl([[0,terms.slice(0,35).join("")],[1,terms.join("")]]));
  mutatePart(f,"annotations",0,()=>jsonl([[0,terms.slice(35).join("")],[1,""]]));
  const {store}=create(f);
  assert.deepEqual(await store.search([0,1],terms,false),[1]);
  assert.deepEqual(await store.search([0,1],terms,true),[0,1]);
});

test("empty search or candidate sets require no text request",async()=>{
  const {store,stats}=create(fixture());
  assert.deepEqual(await store.search([5,0,5],[],true),[5,0]);
  assert.deepEqual(await store.search([], ["alpha"],false),[]);assert.equal(stats.calls.length,0);
});

test("manifest rejects unsafe URLs, ambiguous ranges, limits and unsupported protocols",()=>{
  for(const path of ["../private.jsonl.gz","/absolute.jsonl.gz","https://other.test/x","data//part","data/./part","data/%2e%2e/part","data\\part","data/part?query","data/part#hash"]){const f=fixture();f.manifest.directory.shards[0].path=path;assert.throws(()=>create(f),/unsafe|URL/);}
  for(const base of ["file:///tmp/reader.html","https://user:pass@example.test/bank/"]){assert.throws(()=>Lazy.create(fixture().manifest,base),/HTTP/);}
  const cases=[m=>m.directory.shards[1].first_ordinal++,m=>m.details.shards[0].uncompressed_bytes--,m=>m.search.record_count++,m=>m.details.jsonl_sha256="0".repeat(64),m=>m.directory.shards[0].bytes=m.max_shard_bytes+1,m=>m.annotations.shards[0].path=m.search.shards[0].path];
  for(const change of cases){const f=fixture();change(f.manifest);assert.throws(()=>create(f));}
  assert.throws(()=>create(fixture(),{}, {maxRequests:5}),/bound/);
  assert.throws(()=>create(fixture(),{}, {cacheBytes:8*1024*1024+1}),/bound/);
});

test("directory rejects bad hashes, lengths, UTF-8, metadata and incomplete coverage without partial success",async t=>{
  const cases={
    "compressed digest":f=>{f.manifest.directory.shards[0].sha256="0".repeat(64);},
    "compressed length":f=>{f.manifest.directory.shards[0].bytes++;},
    "decoded length":f=>{f.manifest.directory.shards[0].uncompressed_bytes--;},
    "directory digest":f=>{f.manifest.directory.jsonl_sha256="0".repeat(64);},
    "invalid UTF-8":f=>mutatePart(f,"directory",0,bytes=>{const changed=Buffer.from(bytes);changed[20]=255;return changed;}),
    "missing newline":f=>mutatePart(f,"directory",0,bytes=>bytes.subarray(0,-1)),
    "null identifier":f=>mutateDirectory(f,rows=>{rows[0].source_id=null;}),
    "duplicate ID":f=>mutateDirectory(f,rows=>{rows[1].id=rows[0].id;}),
    "unknown origin":f=>mutateDirectory(f,rows=>{rows[0]._reader.origin="original";}),
    "language metadata":f=>mutateDirectory(f,rows=>{rows[0]._reader.languages=[false];}),
    "availability metadata":f=>mutateDirectory(f,rows=>{rows[0]._reader.availability.arabic="available";}),
    "OCR metadata":f=>mutateDirectory(f,rows=>{rows[0]._reader.ocr_pending="false";}),
    "citation metadata":f=>mutateDirectory(f,rows=>{rows[0]._reader.citation_pairs=[{}];}),
    "span gap":f=>mutateDirectory(f,rows=>{rows[1]._reader.detail[0]++;}),
    "span overlap":f=>mutateDirectory(f,rows=>{rows[1]._reader.detail[0]--;}),
    "final span short":f=>mutateDirectory(f,rows=>{rows.at(-1)._reader.detail[1]--;})
  };
  for(const [name,change] of Object.entries(cases))await t.test(name,async()=>{const f=fixture();change(f);const {store,events}=create(f);await assert.rejects(store.loadDirectory());assert.ok(events.every(event=>!event.complete));});
});

test("streamed compressed excess is rejected even without Content-Length",async()=>{
  const f=fixture();const {store}=create(f,{changeBytes:(url,bytes)=>Buffer.concat([bytes,Buffer.alloc(100)]),response:(url,response)=>response.headers.delete("content-length")});
  await assert.rejects(store.loadDirectory(),/exceeds declared bound/);
});

test("detail identity mismatches reject the complete record",async()=>{
  const f=fixture({detailBytes:10000});
  mutatePart(f,"details",0,bytes=>Buffer.from(bytes.toString().replace('"id":"id-0"','"id":"id-x"')));
  const {store}=create(f);await assert.rejects(store.getRecord(0),/identity mismatch/);
});

test("corrupt required search rows never return a complete zero-match result",async t=>{
  for(const [name,change] of [["ordinal",rows=>rows[0][0]=1],["key",rows=>rows[0][1]=null]])await t.test(name,async()=>{
    const f=fixture();mutatePart(f,"search",0,bytes=>{const rows=bytes.toString().trimEnd().split("\n").map(JSON.parse);change(rows);return jsonl(rows);});
    const {store,events}=create(f);await assert.rejects(store.search([0],["alpha"],true),/search row/);assert.ok(events.every(event=>!event.complete));
  });
  const f=fixture();f.manifest.search.shards[1].sha256="0".repeat(64);const {store}=create(f);
  assert.deepEqual(await store.search([0],["alpha"],false),[0]);
  await assert.rejects(store.search([2],["alpha"],false),/SHA-256/);
});

test("newer search cancels old results and remains usable",async()=>{
  const f=fixture(),{store,stats}=create(f,{delay:20});
  const old=store.search([0,2,5],["alpha"],true),rejected=assert.rejects(old,{name:"AbortError"});
  await delay(2);assert.deepEqual(await store.search([1],["gamma"],false),[1]);await rejected;
  assert.ok(stats.aborts>=1);assert.equal(store.cacheStats().activeRequests,0);
});

test("an empty newer query still cancels an ongoing text scan",async()=>{
  const {store}=create(fixture(),{delay:20});
  const old=store.search([0],["alpha"],false),rejected=assert.rejects(old,{name:"AbortError"});
  await delay(2);assert.deepEqual(await store.search([5,0],[],false),[5,0]);await rejected;
});

test("global request concurrency includes parallel pages and search",async()=>{
  const f=fixture({detailBytes:250}),{store,stats}=create(f,{delay:2});await store.loadDirectory();
  const [page,matches]=await Promise.all([store.getRecords([5,0,3,1,2,4],{concurrency:20}),store.search([0,1,2,3,4,5],["alpha"],true)]);
  assert.deepEqual(page,[5,0,3,1,2,4].map(i=>f.records[i]));assert.deepEqual(matches,[0,1,2,5]);
  assert.ok(stats.peak<=4);assert.ok(store.cacheStats().maxActiveRequests<=4);assert.equal(store.cacheStats().activeRequests,0);
});

test("a failed page request cancels the operation's other outstanding subscriptions",async()=>{
  const f=fixture({detailBytes:250});let enabled=false;
  const failurePath=f.manifest.details.shards[0].path;
  const {store,stats}=create(f,{delay:url=>url.endsWith(failurePath)?1:20,fail:url=>enabled&&url.endsWith(failurePath)});
  await store.loadDirectory();enabled=true;
  await assert.rejects(store.getRecords([0,3,5],{concurrency:3}),/network fixture/);await delay(1);
  assert.ok(stats.aborts>=1);assert.equal(store.cacheStats().activeRequests,0);
});

test("timeout is explicit, bounded, and does not leave a stale pending request",async()=>{
  const f=fixture();const {store,stats,events}=create(f,{delay:100},{timeoutMs:8});
  await assert.rejects(store.loadDirectory(),{name:"TimeoutError"});await delay(1);
  assert.ok(stats.aborts>=1);assert.equal(store.cacheStats().activeRequests,0);assert.ok(events.every(event=>!event.complete));
});

test("HTTP redirect and alternate response URLs fail closed",async()=>{
  for(const prop of [{redirected:true},{url:"https://other.test/reader-data/part"}]){
    const {store}=create(fixture(),{response:(url,response)=>{for(const [key,value] of Object.entries(prop))Object.defineProperty(response,key,{value});}});
    await assert.rejects(store.loadDirectory(),/failed|URL/);
  }
});

test("selected JSON retains exact original objects after paging, filtering and eviction",async()=>{
  const f=fixture(),{store}=create(f,{}, {cacheBytes:100});
  await store.getRecords([0,1,2]);const selected=[0,3,5];
  await store.search([5,2],["alpha"],true);await store.getRecords([4,2]);
  const pieces=["["];
  for(let i=0;i<selected.length;i++)pieces.push((i?",":"")+JSON.stringify(await store.getRecord(selected[i])));
  pieces.push("]");assert.deepEqual(JSON.parse(pieces.join("")),selected.map(i=>f.records[i]));
});


test("browser base URLs must retain the containing page origin",()=>{
  const old=globalThis.location;
  try {
    globalThis.location={href:"https://different.test/reader.html"};
    assert.throws(()=>create(fixture()),/same-origin/);
    globalThis.location={href:"file:///tmp/reader.html"};
    assert.throws(()=>create(fixture()),/same-origin/);
  } finally {if(old===undefined)delete globalThis.location;else globalThis.location=old;}
});

test("failing response validation aborts its underlying request signal",async()=>{
  const f=fixture();let signal;
  const store=Lazy.create(f.manifest,BASE,()=>{}, {crypto:webcrypto,fetch:async(url,options)=>{
    signal=options.signal;return new Response(f.assets.get(url),{headers:{"content-length":"1"}});
  }});
  await assert.rejects(store.loadDirectory(),/content length/);assert.equal(signal.aborted,true);
});

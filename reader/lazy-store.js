/* Bounded, source-preserving reader transport. No full-record cache is kept. */
(function (root, factory) {
  "use strict";
  const api = factory(root);
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HadithLazyStore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  "use strict";
  const DEFAULT_CACHE_BYTES = 8 * 1024 * 1024;
  const DEFAULT_TIMEOUT_MS = 30000;
  const IDENTITIES = ["id", "language", "book_key", "edition", "source_id"];
  const HEX = /^[0-9a-f]{64}$/;
  const hash = value => typeof value === "string" && HEX.test(value);
  const languageCode = /^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$/;
  const error = message => new Error("Reader data: " + message);
  const abortError = () => Object.assign(new Error("Reader operation was cancelled"), {name: "AbortError"});
  const abortReason = signal => signal && signal.reason && signal.reason.name === "TimeoutError" ? signal.reason : abortError();
  const checkAbort = signal => { if (signal && signal.aborted) throw abortReason(signal); };
  const integer = (n, min = 0) => Number.isSafeInteger(n) && n >= min;
  const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
  const identifier = value => typeof value === "string" && value.trim().length > 0 && !/[\u0000-\u001f\u007f]/.test(value);
  function freeze(value) {
    if (value && typeof value === "object" && !Object.isFrozen(value)) {
      for (const child of Object.values(value)) freeze(child);
      Object.freeze(value);
    }
    return value;
  }
  function waitFor(promise, signal) {
    if (!signal) return Promise.resolve(promise);
    if (signal.aborted) return Promise.reject(abortReason(signal));
    return new Promise((resolve, reject) => {
      const onAbort = () => finish(reject, abortReason(signal));
      const finish = (callback, value) => { signal.removeEventListener("abort", onAbort); callback(value); };
      signal.addEventListener("abort", onAbort, {once: true});
      Promise.resolve(promise).then(value => finish(resolve, value), reason => finish(reject, reason));
    });
  }
  function operation(signal) {
    const controller = new AbortController();
    const onAbort = () => controller.abort(abortError());
    if (signal) {
      if (signal.aborted) onAbort();
      else signal.addEventListener("abort", onAbort, {once: true});
    }
    return {controller, signal: controller.signal, dispose() { if (signal) signal.removeEventListener("abort", onAbort); }};
  }

  // Streaming SHA-256 keeps directory verification independent of its total byte
  // size. Per-part hashes use WebCrypto; the directory never retains its raw stream.
  const SHA_K = new Uint32Array([
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
  ]);
  const rotate = (n, k) => n >>> k | n << (32 - k);
  class Sha256 {
    constructor() {
      this.state = new Uint32Array([0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]);
      this.block = new Uint8Array(64); this.words = new Uint32Array(64); this.used = 0; this.size = 0;
    }
    compress() {
      const w = this.words, b = this.block;
      for (let i=0;i<16;i++) w[i] = (b[i*4]<<24 | b[i*4+1]<<16 | b[i*4+2]<<8 | b[i*4+3]) >>> 0;
      for (let i=16;i<64;i++) {
        const x=w[i-15], y=w[i-2];
        w[i] = (w[i-16] + (rotate(x,7)^rotate(x,18)^x>>>3) + w[i-7] + (rotate(y,17)^rotate(y,19)^y>>>10)) >>> 0;
      }
      let [a,c,d,e,f,g,h,j] = this.state;
      for (let i=0;i<64;i++) {
        const t1=(j+(rotate(f,6)^rotate(f,11)^rotate(f,25))+((f&g)^(~f&h))+SHA_K[i]+w[i])>>>0;
        const t2=((rotate(a,2)^rotate(a,13)^rotate(a,22))+((a&c)^(a&d)^(c&d)))>>>0;
        j=h; h=g; g=f; f=(e+t1)>>>0; e=d; d=c; c=a; a=(t1+t2)>>>0;
      }
      const next=[a,c,d,e,f,g,h,j];
      for(let i=0;i<8;i++) this.state[i]=(this.state[i]+next[i])>>>0;
    }
    update(bytes) {
      this.size += bytes.length;
      let cursor=0;
      while(cursor<bytes.length) {
        const take=Math.min(64-this.used,bytes.length-cursor);
        this.block.set(bytes.subarray(cursor,cursor+take),this.used); this.used+=take; cursor+=take;
        if(this.used===64) { this.compress(); this.used=0; }
      }
    }
    hex() {
      const original=this.size, tail=new Uint8Array(this.used<56?64-this.used:128-this.used);
      tail[0]=0x80;
      const view=new DataView(tail.buffer);
      view.setUint32(tail.length-8,Math.floor(original/0x20000000));
      view.setUint32(tail.length-4,(original*8)>>>0);
      this.update(tail);
      return Array.from(this.state,word=>word.toString(16).padStart(8,"0")).join("");
    }
  }

  function validateManifest(input, baseURL) {
    if (!object(input)) throw error("manifest must be an object");
    let manifest;
    try { manifest = JSON.parse(JSON.stringify(input)); } catch (_) { throw error("manifest must be JSON data"); }
    if (manifest.schema !== "hadith-bank-reader-lazy-v2" || manifest.encoding !== "gzip-jsonl-lazy-v2") throw error("unsupported manifest schema");
    if (!integer(manifest.record_count) || !integer(manifest.max_shard_bytes,1) || !hash(manifest.jsonl_sha256)) throw error("invalid manifest limits or digest");
    let base;
    try { base = new URL(baseURL); } catch (_) { throw error("an absolute HTTP(S) base URL is required"); }
    if (!["http:","https:"].includes(base.protocol) || base.username || base.password) throw error("HTTP(S) is required; file-protocol loading is unsupported");
    if (root.location && typeof root.location.href === "string") {
      const page = new URL(root.location.href);
      if (!["http:","https:"].includes(page.protocol) || page.origin !== base.origin) throw error("reader base URL must remain same-origin with the page");
    }
    const paths = new Set(), urls = new Map(), prefix = new URL(".",base).pathname;
    let detailBytes = 0;
    for (const name of ["directory","search","annotations","details"]) {
      const spec=manifest[name], whole=name!=="details";
      if (!object(spec) || spec.encoding!=="gzip-jsonl-shards" || spec.record_count!==manifest.record_count || !hash(spec.jsonl_sha256) || !integer(spec.max_shard_bytes,1) || spec.max_shard_bytes>manifest.max_shard_bytes || !Array.isArray(spec.shards)) throw error("invalid " + name + " store");
      if (!whole && (spec.schema!=="hadith-bank-reader-shards-v1" || spec.jsonl_sha256!==manifest.jsonl_sha256 || !integer(spec.plain_part_bytes,1) || spec.plain_part_bytes>spec.max_shard_bytes)) throw error("invalid detail stream metadata");
      let count=0, total=0;
      for (let index=0;index<spec.shards.length;index++) {
        const part=spec.shards[index];
        if (!object(part) || typeof part.path!=="string" || !/^[A-Za-z0-9_./-]+$/.test(part.path) || part.path.startsWith("/") || part.path.split("/").some(segment=>!segment || segment==="." || segment==="..") || paths.has(part.path)) throw error("unsafe or duplicate shard path");
        const url=new URL(part.path,base);
        if (url.origin!==base.origin || !url.pathname.startsWith(prefix)) throw error("shard URL must remain in the reader directory");
        paths.add(part.path); urls.set(part.path,url.href);
        if (!hash(part.sha256) || !integer(part.bytes,1) || part.bytes>spec.max_shard_bytes || !integer(part.uncompressed_bytes,1) || part.uncompressed_bytes>spec.max_shard_bytes || !integer(part.count)) throw error("invalid shard bounds in " + name);
        if (whole && (!integer(part.first_ordinal) || !integer(part.last_ordinal) || part.first_ordinal!==count || part.count<1 || part.last_ordinal-part.first_ordinal+1!==part.count)) throw error("noncontiguous ordinals in " + name);
        if (!whole && (part.uncompressed_bytes>spec.plain_part_bytes || index<spec.shards.length-1 && part.uncompressed_bytes!==spec.plain_part_bytes)) throw error("noncontiguous detail byte chunks");
        count+=part.count; total+=part.uncompressed_bytes;
        if (!integer(count) || !integer(total)) throw error("store size exceeds safe integer range");
      }
      if (count!==manifest.record_count || (manifest.record_count===0)!==(spec.shards.length===0)) throw error("store count mismatch in " + name);
      if (!whole) detailBytes=total;
    }
    return {manifest:freeze(manifest),urls,detailBytes};
  }

  function create(input, baseURL, onProgress = () => {}, options = {}) {
    const {manifest,urls,detailBytes} = validateManifest(input,baseURL);
    if (typeof onProgress!=="function" || !object(options)) throw error("invalid options or progress callback");
    const cacheLimit=options.cacheBytes===undefined?DEFAULT_CACHE_BYTES:options.cacheBytes;
    const timeoutMs=options.timeoutMs===undefined?DEFAULT_TIMEOUT_MS:options.timeoutMs;
    const requestLimit=options.maxRequests===undefined?4:options.maxRequests;
    if (!integer(cacheLimit) || cacheLimit>DEFAULT_CACHE_BYTES || !integer(timeoutMs,1) || timeoutMs>DEFAULT_TIMEOUT_MS || !integer(requestLimit,1) || requestLimit>4) throw error("invalid cache, timeout or request bound");
    const fetcher=options.fetch || (typeof root.fetch==="function" && root.fetch.bind(root));
    const cryptoAPI=options.crypto || root.crypto;
    if (typeof fetcher!=="function" || !cryptoAPI || !cryptoAPI.subtle || typeof root.DecompressionStream!=="function") throw error("fetch, WebCrypto and gzip decompression are required");
    const cache=new Map(), inFlight=new Map(), queue=[];
    let cacheBytes=0, active=0, peak=0, requests=0, directory=null, directoryFlight=null, currentSearch=null;
    const progress=(event,callback=onProgress)=>{ if (callback) callback(event); };
    function acquire(signal) {
      checkAbort(signal);
      return new Promise((resolve,reject)=>{
        const item={signal,resolve,reject,onAbort:null};
        item.onAbort=()=>{const index=queue.indexOf(item);if(index!==-1)queue.splice(index,1);reject(abortReason(signal));};
        signal.addEventListener("abort",item.onAbort,{once:true});
        queue.push(item); drain();
      });
    }
    function drain() {
      while(active<requestLimit && queue.length) {
        const item=queue.shift(); item.signal.removeEventListener("abort",item.onAbort);
        if(item.signal.aborted) {item.reject(abortReason(item.signal));continue;}
        active++; peak=Math.max(peak,active); let released=false;
        item.resolve(()=>{if(!released){released=true;active--;drain();}});
      }
    }
    function remember(path,bytes) {
      if(bytes.length>cacheLimit || cacheLimit===0)return;
      if(cache.has(path)){cacheBytes-=cache.get(path).length;cache.delete(path);}
      while(cacheBytes+bytes.length>cacheLimit && cache.size) {const key=cache.keys().next().value;cacheBytes-=cache.get(key).length;cache.delete(key);}
      cache.set(path,bytes);cacheBytes+=bytes.length;
    }
    async function readBounded(stream,length,signal,label) {
      if(!stream || typeof stream.getReader!=="function")throw error(label+" response has no readable body");
      const reader=stream.getReader(), bytes=new Uint8Array(length);let offset=0;
      const onAbort=()=>{Promise.resolve(reader.cancel(abortReason(signal))).catch(()=>{});};
      signal.addEventListener("abort",onAbort,{once:true});
      try {
        while(true) {
          checkAbort(signal);
          const {done,value}=await waitFor(reader.read(),signal);
          if(done)break;
          if(!(value instanceof Uint8Array) || offset+value.length>length)throw error(label+" length exceeds declared bound");
          bytes.set(value,offset);offset+=value.length;
        }
        checkAbort(signal);
        if(offset!==length)throw error(label+" length does not match manifest");
        return bytes;
      } catch(reason) {
        Promise.resolve(reader.cancel(reason)).catch(()=>{});throw reason;
      } finally {
        signal.removeEventListener("abort",onAbort);
        try {reader.releaseLock();} catch (_) { /* Pending cancelled reads settle separately. */ }
      }
    }
    async function fetchPart(part,controller) {
      const signal=controller.signal,release=await acquire(signal);
      try {
        checkAbort(signal);requests++;
        const url=urls.get(part.path);
        const response=await waitFor(fetcher(url,{credentials:"same-origin",redirect:"error",signal}),signal);
        if(!response || !response.ok || response.redirected)throw error("shard request failed" + (response?" (HTTP "+response.status+")":""));
        if(response.url && response.url!==url)throw error("unexpected shard response URL");
        const declared=response.headers && response.headers.get("content-length");
        if(declared!==null && declared!==undefined && (!/^\d+$/.test(declared) || Number(declared)!==part.bytes))throw error("compressed content length does not match manifest");
        const compressed=await readBounded(response.body,part.bytes,signal,"compressed shard");
        const digest=await waitFor(cryptoAPI.subtle.digest("SHA-256",compressed),signal);
        const hex=Array.from(new Uint8Array(digest),value=>value.toString(16).padStart(2,"0")).join("");
        if(hex!==part.sha256)throw error("compressed shard SHA-256 mismatch");
        checkAbort(signal);
        const stream=new Blob([compressed]).stream().pipeThrough(new root.DecompressionStream("gzip"));
        const decoded=await readBounded(stream,part.uncompressed_bytes,signal,"decoded shard");
        let lines=0;for(const byte of decoded)if(byte===10)lines++;
        if(lines!==part.count)throw error("shard newline count mismatch");
        return decoded;
      } catch(reason) {
        // Stop an unconsumed response body on header, URL or digest failure.
        if(!signal.aborted)controller.abort(abortError());
        throw reason;
      } finally { release(); }
    }
    function subscribe(entry,signal) {
      checkAbort(signal);
      return new Promise((resolve,reject)=>{
        const sub={resolve,reject,signal,onAbort:null};
        sub.onAbort=()=>{
          if(!entry.users.delete(sub))return;
          if(signal)signal.removeEventListener("abort",sub.onAbort);
          reject(abortReason(signal));
          if(entry.users.size===0 && !entry.done){entry.controller.abort(abortError());entry.onEmpty();}
        };
        entry.users.add(sub);
        if(signal)signal.addEventListener("abort",sub.onAbort,{once:true});
      });
    }
    function shared(task,onEmpty,onSuccess) {
      const entry={controller:new AbortController(),users:new Set(),done:false,onEmpty};
      Promise.resolve().then(()=>task(entry.controller.signal)).then(value=>{
        checkAbort(entry.controller.signal);
        if(onSuccess)onSuccess(value);
        finish(null,value);
      },reason=>finish(reason)).catch(reason=>finish(reason));
      function finish(reason,value) {
        if(entry.done)return;entry.done=true;
        if(reason && !entry.controller.signal.aborted)entry.controller.abort(abortError());
        for(const sub of entry.users){if(sub.signal)sub.signal.removeEventListener("abort",sub.onAbort);reason?sub.reject(reason):sub.resolve(value);}
        entry.users.clear();onEmpty();
      }
      return entry;
    }
    function requestPart(part,kind,signal) {
      checkAbort(signal);
      if(cache.has(part.path)) {const bytes=cache.get(part.path);cache.delete(part.path);cache.set(part.path,bytes);return Promise.resolve(bytes);}
      let entry=inFlight.get(part.path);
      if(!entry) {
        let created;
        created=shared(async()=>{
          const timeout=new Error("Reader shard request timed out after "+timeoutMs+" ms");timeout.name="TimeoutError";
          const timer=setTimeout(()=>created.controller.abort(timeout),timeoutMs);
          try{return await fetchPart(part,created.controller);}finally{clearTimeout(timer);}
        },()=>{if(inFlight.get(part.path)===created)inFlight.delete(part.path);},bytes=>{if(kind!=="directory")remember(part.path,bytes);});
        entry=created;inFlight.set(part.path,entry);
      }
      return subscribe(entry,signal);
    }
    function parseRows(bytes,part,callback) {
      const text=new TextDecoder("utf-8",{fatal:true,ignoreBOM:true}).decode(bytes);
      if(!text.endsWith("\n"))throw error("JSONL shard must end with a newline");
      let start=0, count=0;
      while(start<text.length) {
        const end=text.indexOf("\n",start);
        if(end<0 || end===start)throw error("empty or incomplete JSONL row");
        let row;
        try {row=JSON.parse(text.slice(start,end));} catch (_) {throw error("invalid JSONL row");}
        callback(row,count++);start=end+1;
      }
      if(count!==part.count)throw error("JSONL row count mismatch");
    }
    function validateDirectoryRow(row,offset,ids) {
      if(!object(row) || IDENTITIES.some(key=>!identifier(row[key])) || !languageCode.test(row.language))throw error("invalid directory identity");
      if(ids.has(row.id))throw error("duplicate directory occurrence ID");ids.add(row.id);
      const data=row._reader;
      if(!object(data) || !Array.isArray(data.languages) || !data.languages.length || data.languages.some(code=>typeof code!=="string" || !languageCode.test(code)) || new Set(data.languages).size!==data.languages.length || !["human","ai","unknown"].includes(data.origin))throw error("invalid directory language or origin metadata");
      if(!object(data.availability) || ["arabic","english"].some(key=>!["text","external_link","missing"].includes(data.availability[key])) || typeof data.ocr_pending!=="boolean" || !Array.isArray(data.citation_pairs) || data.citation_pairs.some(pair=>!identifier(pair)) || new Set(data.citation_pairs).size!==data.citation_pairs.length)throw error("invalid directory filtering metadata");
      if(!Array.isArray(data.detail) || data.detail.length!==2 || data.detail[0]!==offset || !integer(data.detail[1],2) || !integer(offset+data.detail[1]) || offset+data.detail[1]>detailBytes)throw error("noncontiguous or invalid detail span");
      return freeze(row);
    }
    async function loadDirectory({signal}={}) {
      checkAbort(signal);if(directory)return directory;
      if(!directoryFlight) {
        let created;
        created=shared(async taskSignal=>{
          const rows=[],ids=new Set(),sha=new Sha256();let offset=0;
          const parts=manifest.directory.shards;
          progress({phase:"directory",loaded:0,total:manifest.record_count,part:0,parts:parts.length,complete:false});
          for(let index=0;index<parts.length;index++) {
            const part=parts[index],bytes=await requestPart(part,"directory",taskSignal);checkAbort(taskSignal);sha.update(bytes);
            parseRows(bytes,part,(row,local)=>{
              if(rows.length!==part.first_ordinal+local)throw error("directory row ordinal mismatch");
              rows.push(validateDirectoryRow(row,offset,ids));offset+=row._reader.detail[1];
            });
            progress({phase:"directory",loaded:rows.length,total:manifest.record_count,part:index+1,parts:parts.length,complete:false});
          }
          checkAbort(taskSignal);
          if(rows.length!==manifest.record_count || offset!==detailBytes || sha.hex()!==manifest.directory.jsonl_sha256)throw error("complete directory digest, count or detail coverage mismatch");
          return Object.freeze(rows);
        },()=>{if(directoryFlight===created)directoryFlight=null;},rows=>{
          directory=rows;progress({phase:"directory",loaded:rows.length,total:rows.length,part:manifest.directory.shards.length,parts:manifest.directory.shards.length,complete:true});
        });
        directoryFlight=created;
      }
      return subscribe(directoryFlight,signal);
    }
    const validateOrdinal=ordinal=>{if(!integer(ordinal) || ordinal>=manifest.record_count)throw error("invalid occurrence ordinal");return ordinal;};
    async function getRecord(ordinal,{signal}={}) {
      validateOrdinal(ordinal);checkAbort(signal);
      const rows=await loadDirectory({signal});checkAbort(signal);
      const row=rows[ordinal],[offset,length]=row._reader.detail, size=manifest.details.plain_part_bytes;
      const bytes=new Uint8Array(length), last=Math.floor((offset+length-1)/size);let written=0;
      for(let index=Math.floor(offset/size);index<=last;index++) {
        const part=manifest.details.shards[index],decoded=await requestPart(part,"details",signal);checkAbort(signal);
        const start=Math.max(offset-index*size,0),end=Math.min(offset+length-index*size,decoded.length);
        bytes.set(decoded.subarray(start,end),written);written+=end-start;
      }
      if(written!==length || bytes[length-1]!==10)throw error("incomplete detail record span");
      let lines=0;for(const byte of bytes)if(byte===10)lines++;
      if(lines!==1)throw error("detail span must contain exactly one JSONL record");
      const text=new TextDecoder("utf-8",{fatal:true,ignoreBOM:true}).decode(bytes);
      let record;try {record=JSON.parse(text.slice(0,-1));} catch (_) {throw error("invalid detail JSON");}
      if(!object(record) || IDENTITIES.some(key=>record[key]!==row[key]))throw error("detail record identity mismatch");
      checkAbort(signal);return record;
    }
    async function getRecords(ordinals,{signal,concurrency=3}={}) {
      if(!Array.isArray(ordinals) || !integer(concurrency,1))throw error("invalid record request");
      ordinals=ordinals.map(validateOrdinal);const task=operation(signal),result=new Array(ordinals.length);let cursor=0;
      const workers=Array.from({length:Math.min(concurrency,requestLimit,ordinals.length)},async()=>{
        while(cursor<ordinals.length){checkAbort(task.signal);const position=cursor++;result[position]=await getRecord(ordinals[position],{signal:task.signal});}
      });
      try {checkAbort(task.signal);await Promise.all(workers);checkAbort(task.signal);return result;}
      catch(reason){task.controller.abort(abortError());await Promise.allSettled(workers);throw reason;}
      finally{task.dispose();}
    }
    async function search(candidateOrdinals,normalizedTerms,includeCommentary,{signal,onProgress:searchProgress}={}) {
      if(!Array.isArray(candidateOrdinals) || !Array.isArray(normalizedTerms) || normalizedTerms.some(term=>typeof term!=="string") || typeof includeCommentary!=="boolean" || searchProgress!==undefined && typeof searchProgress!=="function")throw error("invalid search request");
      const candidates=[...new Set(candidateOrdinals.map(validateOrdinal))], terms=[...new Set(normalizedTerms.filter(term=>term.length))];
      if(currentSearch)currentSearch.controller.abort(abortError());
      const task=operation(signal);currentSearch=task;
      const report=event=>progress(event,searchProgress||onProgress);
      try {
        checkAbort(task.signal);
        if(!terms.length || !candidates.length){report({phase:"search",loaded:0,total:0,part:0,parts:0,complete:true});return candidates;}
        const wordCount=Math.ceil(terms.length/32),slots=wordCount*candidates.length;
        if(!integer(slots) || slots>0x3fffffff)throw error("search term set exceeds supported memory bound");
        const bits=new Uint32Array(slots),remaining=new Uint32Array(candidates.length);remaining.fill(terms.length);
        const positions=new Map(candidates.map((ordinal,index)=>[ordinal,index]));
        const statuses=[];
        async function scan(name,needed) {
          const sorted=needed.slice().sort((a,b)=>a-b),parts=[];let at=0;
          for(const part of manifest[name].shards){while(at<sorted.length && sorted[at]<part.first_ordinal)at++;if(at<sorted.length && sorted[at]<=part.last_ordinal)parts.push(part);}
          const total=parts.reduce((sum,part)=>sum+part.count,0);let loaded=0;
          report({phase:name,loaded:0,total,part:0,parts:parts.length,complete:false});
          for(let index=0;index<parts.length;index++) {
            checkAbort(task.signal);const part=parts[index],bytes=await requestPart(part,name,task.signal);checkAbort(task.signal);
            parseRows(bytes,part,(row,local)=>{
              if(!Array.isArray(row) || row.length!==2 || row[0]!==part.first_ordinal+local || typeof row[1]!=="string")throw error("invalid search row ordinal or key");
              const position=positions.get(row[0]);if(position===undefined || remaining[position]===0)return;
              const start=position*wordCount;
              for(let term=0;term<terms.length;term++) {const slot=start+(term>>>5),mask=1<<(term&31);if(!(bits[slot]&mask) && row[1].includes(terms[term])){bits[slot]|=mask;remaining[position]--;}}
            });
            loaded+=part.count;report({phase:name,loaded,total,part:index+1,parts:parts.length,complete:false});
            // Let new input cancel a large scan between bounded pieces.
            await new Promise(resolve=>setTimeout(resolve,0));
          }
          statuses.push({phase:name,loaded,total,part:parts.length,parts:parts.length,complete:true});
        }
        await scan("search",candidates);
        if(includeCommentary)await scan("annotations",candidates.filter((_,index)=>remaining[index]>0));
        checkAbort(task.signal);
        const matches=candidates.filter((_,index)=>remaining[index]===0);
        for(const status of statuses){checkAbort(task.signal);report(status);}
        checkAbort(task.signal);return matches;
      } finally {if(currentSearch===task)currentSearch=null;task.dispose();}
    }
    return Object.freeze({loadDirectory,getRecord,getRecords,search,cacheStats:()=>({bytes:cacheBytes,entries:cache.size,limitBytes:cacheLimit,activeRequests:active,queuedRequests:queue.length,maxActiveRequests:peak,requestCount:requests,inFlight:inFlight.size})});
  }
  return Object.freeze({create});
});

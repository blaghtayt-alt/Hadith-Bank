/* Disposable navigation/search over immutable source-occurrence ordinals.
 * No source mutation, text translation, canonical matching or network access.
 */
(function (root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.HadithDiscovery = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const SCHEMA = "hadith-bank-discovery-v1";
  const ARABIC_MARKS = /[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u08d3-\u08ff]/g;
  const WORD = /[\p{L}\p{N}\p{M}]/u, LETTER = /\p{L}/u, MARK = /\p{M}/u;
  const MAP = {"أ":"ا","إ":"ا","آ":"ا","ٱ":"ا","ى":"ي","ی":"ي","ک":"ك"};
  const digit = ch => String((ch.codePointAt(0) - (ch >= "۰" ? 0x6f0 : 0x660)));
  const isCJK = ch => {const n=ch.codePointAt(0);return n>=0x3040&&n<=0x30ff||n>=0x3400&&n<=0x9fff||n>=0xf900&&n<=0xfaff||n>=0x20000&&n<=0x2fa1f;};
  const object = value => !!value && typeof value === "object" && !Array.isArray(value);
  const scalar = value => typeof value === "string" && value.length > 0;
  const fail = message => {throw new Error("Search index: " + message);};
  function normalize(value) {
    let text=String(value).normalize("NFKC").toLowerCase().replace(/[٠-٩۰-۹]/g,digit)
      .replace(/[أإآٱىیک]/g,ch=>MAP[ch]).replace(ARABIC_MARKS,"").replace(/ـ/g,"");
    let result="",latin=false;
    for(const ch of text.normalize("NFD")) {
      if(/\p{Cf}/u.test(ch))continue;
      if(MARK.test(ch)){if(!latin)result+=ch;continue;}
      latin=/\p{Script=Latin}/u.test(ch);result+=ch;
    }
    return result.normalize("NFC");
  }
  function tokenize(value) {
    const words=[];let current="";
    for(const ch of normalize(value)) {
      if(isCJK(ch)){if(current){words.push(current);current="";}words.push(ch);}
      else if(WORD.test(ch))current+=ch;
      else if(current){words.push(current);current="";}
    }
    if(current)words.push(current);return words;
  }
  function citationNormalize(value) {
    return String(value).normalize("NFKC").toLowerCase().replace(/[٠-٩۰-۹]/g,digit)
      .replace(/ي/g,"ی").replace(/ك/g,"ک").replace(/[\u200c\u200dـ]/g,"").replace(ARABIC_MARKS,"").trim();
  }
  function bytesFromBase64(value) {
    if(typeof value!=="string" || value.length%4 || !/^[A-Za-z0-9+/]*={0,2}$/.test(value))fail("invalid postings encoding");
    if(typeof Buffer!=="undefined")return new Uint8Array(Buffer.from(value,"base64"));
    const raw=atob(value),bytes=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);return bytes;
  }
  function decodePosting(encoded, recordCount, expectedCount) {
    const bytes=bytesFromBase64(encoded);let offset=0,ordinal=-1;
    function integer() {
      let value=0,multiplier=1,steps=0;
      while(offset<bytes.length && steps++<8){const byte=bytes[offset++];value+=(byte&127)*multiplier;
        if(!Number.isSafeInteger(value))fail("posting integer overflow");
        if(!(byte&128))return value;multiplier*=128;}
      fail("truncated posting integer");
    }
    const list=[];
    while(offset<bytes.length) {
      const delta=integer();if(delta<1)fail("unordered posting");ordinal+=delta;
      if(ordinal>=recordCount)fail("posting outside occurrence range");
      const mask=integer(),count=integer();if(mask<1||mask>127||count>bytes.length-offset)fail("invalid posting fields");
      const positions=[];let position=-1;
      for(let i=0;i<count;i++){const step=integer();if(step<1)fail("unordered phrase positions");position+=step;positions.push(position);}
      list.push({ordinal,mask,positions});
    }
    if(list.length!==expectedCount)fail("posting frequency mismatch");return list;
  }
  function lowerBound(array,value) {let a=0,b=array.length;while(a<b){const m=(a+b)>>>1;if(array[m]<value)a=m+1;else b=m;}return a;}
  function phraseAt(postings,tokens,ordinal) {
    if(tokens.length<2)return false;
    const first=postings.get(tokens[0])?.get(ordinal)?.positions;
    if(!first?.length)return false;
    for(const start of first) {
      let matches=true;
      for(let i=1;i<tokens.length;i++) {
        const positions=postings.get(tokens[i])?.get(ordinal)?.positions;
        if(!positions || positions[lowerBound(positions,start+i)]!==start+i){matches=false;break;}
      }
      if(matches)return true;
    }
    return false;
  }
  function sameLanguage(a,b) {return a===b || !!a&&!!b&&a.split("-")[0]===b.split("-")[0];}
  function tokensWithOffsets(text) {
    const mapped=[];let offset=0;
    const characters=Array.from(text);
    for(let i=0;i<characters.length;i++) {
      const start=offset;let cluster=characters[i];offset+=characters[i].length;
      while(i+1<characters.length&&MARK.test(characters[i+1])){cluster+=characters[++i];offset+=characters[i].length;}
      for(const ch of normalize(cluster))mapped.push({ch,start,end:offset});
    }
    const result=[];let current=null;
    for(const item of mapped) {
      if(isCJK(item.ch)){if(current){result.push(current);current=null;}result.push({token:item.ch,start:item.start,end:item.end});}
      else if(WORD.test(item.ch)){if(!current)current={token:"",start:item.start,end:item.end};current.token+=item.ch;current.end=item.end;}
      else if(current){result.push(current);current=null;}
    }
    if(current)result.push(current);return result;
  }
  function excerpt(text,query,limit=180) {
    text=typeof text==="string"?text:"";limit=Math.max(32,Math.min(1000,Number(limit)||180));
    const sought=tokenize(query),source=tokensWithOffsets(text);let hit=-1,phrase=false;
    if(sought.length){for(let i=0;i<source.length;i++)if(source[i].token===sought[0]&&sought.every((token,j)=>source[i+j]?.token===token)){hit=i;phrase=true;break;}
      if(hit<0)hit=source.findIndex(item=>sought.includes(item.token));}
    const boundaries=[0];let offset=0;for(const ch of text){offset+=ch.length;boundaries.push(offset);}
    const matchingOffset=hit<0?0:source[hit].start,matchingCharacter=Math.max(0,lowerBound(boundaries,matchingOffset));
    const startCharacter=hit<0?0:Math.max(0,matchingCharacter-Math.floor(limit/3)),endCharacter=Math.min(boundaries.length-1,startCharacter+limit);
    const start=boundaries[startCharacter],end=boundaries[endCharacter];
    return {text:text.slice(start,end),start,end,matched:hit>=0,phrase,truncated:start>0||end<text.length};
  }
  function editDistanceOne(a,b) {
    if(Math.abs(a.length-b.length)>1)return false;
    let i=0,j=0,errors=0;
    while(i<a.length&&j<b.length){if(a[i]===b[j]){i++;j++;continue;}if(++errors>1)return false;
      if(a.length>=b.length)i++;if(b.length>=a.length)j++;}
    return errors+(i<a.length||j<b.length?1:0)<=1;
  }
  function expandPayload(payload) {
    if(!object(payload)||!payload.row_columns)return payload;
    const columns=payload.row_columns,pools=payload.row_pools||{};
    if(!Array.isArray(columns)||new Set(columns).size!==columns.length)fail("invalid compact row columns");
    const expanded=payload.rows.map((values,ordinal)=>{
      if(!Array.isArray(values)||values.length!==columns.length)fail("invalid compact row");
      const row={ordinal};columns.forEach((key,i)=>{const value=values[i];if(Object.prototype.hasOwnProperty.call(pools,key)){
        if(!Number.isSafeInteger(value)||value<0||value>=pools[key].length)fail("invalid compact row value");row[key]=pools[key][value];
      }else row[key]=value;});row.readings=row.readings||[];return row;
    });
    return {...payload,rows:expanded};
  }
  function create(input,options={}) {
    const payload=expandPayload(input);
    if(!object(payload)||payload.schema!==SCHEMA||!Number.isSafeInteger(payload.record_count)||payload.record_count<0)fail("unsupported schema or count");
    if(!Array.isArray(payload.rows)||payload.rows.length!==payload.record_count||!Array.isArray(payload.terms)||!Array.isArray(payload.postings)||payload.terms.length!==payload.postings.length)fail("incomplete rows or term index");
    const rows=payload.rows,ids=new Map(),terms=new Map(),groups=new Map(),groupByOrdinal=new Map();
    const identities=new Set();
    rows.forEach((row,i)=>{if(!object(row))fail("invalid occurrence row");const identity=JSON.stringify([row.id,row.language,row.book_key,row.edition,row.source_id]);if(row.ordinal!==i||[row.id,row.language,row.book_key,row.edition,row.source_id].some(value=>!scalar(value))||identities.has(identity)||!Array.isArray(row.readings)||!Array.isArray(row.languages)||!Array.isArray(row.references))fail("invalid occurrence row");identities.add(identity);if(!ids.has(row.id))ids.set(row.id,[]);ids.get(row.id).push(i);});
    payload.terms.forEach((term,i)=>{if(!scalar(term)||terms.has(term)||!Array.isArray(payload.postings[i])||payload.postings[i].length!==2||!Number.isSafeInteger(payload.postings[i][0])||payload.postings[i][0]<1||payload.postings[i][0]>rows.length)fail("invalid term descriptor");terms.set(term,i);});
    for(const group of payload.groups||[]) {
      if(!object(group)||!scalar(group.id)||groups.has(group.id)||!Array.isArray(group.members)||group.members.length<2||!object(group.evidence))fail("invalid family group");
      for(const ordinal of group.members){if(!Number.isSafeInteger(ordinal)||ordinal<0||ordinal>=rows.length||groupByOrdinal.has(ordinal))fail("ambiguous family group");groupByOrdinal.set(ordinal,group.id);}
      groups.set(group.id,group);
    }
    const referenceIndex=object(payload.reference_index)?payload.reference_index:{};
    for(const [pair,list] of Object.entries(referenceIndex)) {
      if(!scalar(pair)||!Array.isArray(list)||list.some((ordinal,i)=>!Number.isSafeInteger(ordinal)||ordinal<0||ordinal>=rows.length||i>0&&ordinal<=list[i-1]||!rows[ordinal].references.includes(pair)))fail("invalid reference index");
    }
    for(const [kind,total,firstKey,countKey] of [["postings",payload.terms.length,"first_term","term_count"],["preview",rows.length,"first_ordinal","row_count"]]) {
      const descriptors=payload[kind==="preview"?"preview_shards":"postings_shards"];
      if(descriptors===undefined)continue;
      if(!Array.isArray(descriptors))fail("invalid "+kind+" descriptors");
      let covered=0;for(const part of descriptors){if(!object(part)||part[firstKey]!==covered||!Number.isSafeInteger(part[countKey])||part[countKey]<1||part.records_sha256!==payload.records_sha256||part.record_count!==rows.length)fail("incomplete "+kind+" descriptor coverage");covered+=part[countKey];}
      if(covered!==total)fail("incomplete "+kind+" descriptor coverage");
    }
    const rules=(payload.collection_aliases||[]).map(([key,pattern])=>({key,pattern:new RegExp("(?<![\\p{L}\\p{N}_])(?:"+pattern+")[\\s:：,،#№.()\\[\\]-]*(?:(?:no\\.?|number|hadith|hadīth|رقم|حدیث)\\s*[.:#№-]?\\s*)?([0-9]+[a-z]?)(?![0-9a-z]|\\s*[/\\\\:–—-]\\s*[0-9])","giu")}));
    const topicAids=(payload.editorial?.topics||[]).map(topic=>({...topic,normalizedTerms:[...new Set(topic.terms.flatMap(tokenize))]}));
    const topicById=new Map(topicAids.map(topic=>[topic.id,topic]));
    const postingParts=new Map(),previewParts=new Map(),resultContexts=new WeakMap();
    let postingPartBytes=0,previewPartBytes=0;
    const POSTING_PART_CACHE=64*1024*1024,PREVIEW_PART_CACHE=16*1024*1024;
    const checkAbort=signal=>{if(signal?.aborted)throw new DOMException("Search cancelled.","AbortError");};
    async function loadParts(indices,kind,signal) {
      const descriptors=kind==="postings"?payload.postings_shards:payload.preview_shards;
      const cache=kind==="postings"?postingParts:previewParts;
      const required=new Set(indices);let cursor=0;
      if(indices.length&&typeof options.loadShard!=="function")fail("this hosted index needs a verified shard loader");
      async function worker() {
        while(cursor<indices.length) {
          const index=indices[cursor++];checkAbort(signal);
          if(cache.has(index)){const data=cache.get(index);cache.delete(index);cache.set(index,data);continue;}
          const descriptor=descriptors?.[index];if(!object(descriptor))fail("missing "+kind+" part descriptor");
          const data=await options.loadShard(descriptor,{signal});checkAbort(signal);
          if(!object(data)||data.schema!==SCHEMA+"-"+kind||data.record_count!==rows.length||data.records_sha256!==payload.records_sha256)fail("source binding mismatch in "+kind+" part");
          if(kind==="postings") {
            if(data.first_term!==descriptor.first_term||!Array.isArray(data.postings)||data.postings.length!==descriptor.term_count||data.postings.some(value=>typeof value!=="string"))fail("invalid postings part");
            if(!cache.has(index))postingPartBytes+=descriptor.uncompressed_bytes||0;
          } else {
            if(data.first_ordinal!==descriptor.first_ordinal||!Array.isArray(data.previews)||data.previews.length!==descriptor.row_count||data.previews.some(value=>!Array.isArray(value)))fail("invalid previews part");
            if(!cache.has(index))previewPartBytes+=descriptor.uncompressed_bytes||0;
          }
          cache.set(index,data);
        }
      }
      await Promise.all(Array.from({length:Math.min(4,indices.length)},()=>worker()));checkAbort(signal);
      const budget=kind==="postings"?POSTING_PART_CACHE:PREVIEW_PART_CACHE;
      for(const [index] of cache) {
        if((kind==="postings"?postingPartBytes:previewPartBytes)<=budget)break;
        if(required.has(index))continue;
        cache.delete(index);const descriptor=descriptors[index],bytes=descriptor.uncompressed_bytes||0;
        if(kind==="postings")postingPartBytes-=bytes;
        else {previewPartBytes-=bytes;for(let ordinal=descriptor.first_ordinal;ordinal<descriptor.first_ordinal+descriptor.row_count;ordinal++)rows[ordinal].readings=[];}
      }
    }
    const cache=new Map();let cacheUnits=0,searchCalls=0;
    const CACHE_UNITS=Number.isSafeInteger(options.maxPostingCacheUnits)&&options.maxPostingCacheUnits>=0?Math.min(options.maxPostingCacheUnits,1_000_000):1_000_000;
    function posting(term) {
      const stored=cache.get(term);if(stored){cache.delete(term);cache.set(term,stored);return stored.map;}
      const index=terms.get(term);if(index===undefined)return new Map();
      const [count,wire]=payload.postings[index];let encoded=wire;
      if(Number.isSafeInteger(wire)) {
        const part=postingParts.get(wire);if(!part)fail("query postings are not prepared; call prepare before search");
        encoded=part.postings[index-part.first_term];
      }
      const list=decodePosting(encoded,rows.length,count),map=new Map(list.map(item=>[item.ordinal,item]));
      const units=list.reduce((n,item)=>n+4+item.positions.length,0);
      if(units<=CACHE_UNITS){while(cacheUnits+units>CACHE_UNITS&&cache.size){const [old,value]=cache.entries().next().value;cache.delete(old);cacheUnits-=value.units;}cache.set(term,{map,units});cacheUnits+=units;}
      return map;
    }
    function parseReference(query) {
      const value=citationNormalize(query),matches=[];
      for(const {key,pattern} of rules){pattern.lastIndex=0;for(const match of value.matchAll(pattern))matches.push({start:match.index,end:match.index+match[0].length,pair:key+":"+match[1].replace(/^0+(?=\d)/,"")});}
      matches.sort((a,b)=>a.start-b.start||(b.end-b.start)-(a.end-a.start));
      const accepted=[];for(const item of matches)if(!accepted.some(other=>item.start<other.end&&other.start<item.end))accepted.push(item);
      let end=0;const pieces=[];for(const item of accepted){pieces.push(value.slice(end,item.start));end=item.end;}pieces.push(value.slice(end));
      return {pairs:[...new Set(accepted.map(item=>item.pair))],text:accepted.length?pieces.join(" ").replace(/^[\s,;،()[\]{}]+|[\s,;،()[\]{}]+$/g,""):query};
    }
    function matchesAvailability(row,value) {
      const a=row.availability?.arabic||"missing",e=row.availability?.english||"missing";
      return !value||value==="both-text"&&a==="text"&&e==="text"||value==="both-available"&&a!=="missing"&&e!=="missing"||value==="arabic-text"&&a==="text"||value==="english-text"&&e==="text"||value==="english-link"&&e==="external_link"||value==="missing-arabic"&&a==="missing"||value==="missing-english"&&e==="missing"||value==="neither"&&a==="missing"&&e==="missing";
    }
    function filterRow(row,filters) {
      return (!filters.language||row.languages.some(code=>sameLanguage(code,filters.language)))&&
        (!filters.book||row.book_key===filters.book)&&(!filters.source||row.source_id===filters.source||row.editionGroup===filters.source)&&
        (!filters.origin||row.origin===filters.origin)&&matchesAvailability(row,filters.availability)&&
        (!filters.sourceBook||row.sourceBooks?.includes(filters.sourceBook))&&
        (!filters.narrator||row.narrators?.includes(filters.narrator))&&(!filters.chapter||row.chapters?.includes(filters.chapter))&&
        (!filters.reportType||row.reportType===filters.reportType||row.reportTypes?.includes(filters.reportType))&&
        (!filters.grade||row.grades?.some(item=>item.value===filters.grade))&&(!filters.topic||row.topics?.some(item=>item.value===filters.topic));
    }
    function suggestedQueries(query,mode="all") {
      const tokens=tokenize(query),result=[];
      for(const topic of topicAids) {
        if(tokens.some(token=>topic.normalizedTerms.includes(token)))result.push({query:topic.label,mode:"topic",kind:"editorial-topic",label:"Explore "+topic.label.toLowerCase(),explanation:"Broader editorial keyword suggestions, not a source classification."});
      }
      if(tokens.length===1&&tokens[0].length>=4&&!terms.has(tokens[0])) {
        const sought=tokens[0],candidates=[];
        for(let i=0;i<payload.terms.length;i++){const term=payload.terms[i];if(term[0]===sought[0]&&editDistanceOne(sought,term))candidates.push({term,count:payload.postings[i][0]});}
        candidates.sort((a,b)=>b.count-a.count||a.term.localeCompare(b.term));
        for(const candidate of candidates.slice(0,3))result.push({query:candidate.term,mode:mode==="reference"?"wording":mode,kind:"spelling",label:"Try “"+candidate.term+"”",explanation:"Possible spelling match; your original query has not been changed."});
      }
      return result.slice(0,5);
    }
    function preferredReading(row,preferred) {
      return row.readings.find(item=>item.language===preferred)||row.readings.find(item=>sameLanguage(item.language,preferred))||
        row.readings.find(item=>item.language===row.language)||row.readings.find(item=>item.language==="en")||row.readings[0]||null;
    }
    async function prepare(searchOptions={},prepareOptions={}) {
      const signal=prepareOptions.signal;checkAbort(signal);
      if(!payload.postings_shards)return;
      const query=String(searchOptions.query||"").trim(),mode=searchOptions.mode||"all";
      if(query.length>(payload.limits?.max_query_characters||512))throw new Error("Please shorten the search to 512 characters or fewer.");
      if(ids.has(query))return;
      const parsed=mode==="wording"||mode==="topic"?{pairs:[],text:query}:parseReference(query);
      if(mode==="reference"&&!parsed.pairs.length)return;
      const tokens=tokenize(parsed.text);
      if(tokens.length>(payload.limits?.max_query_tokens||128))throw new Error("Please use 128 search words or fewer.");
      const expanded=mode==="topic"?[...new Set([...tokens,...topicAids.filter(topic=>topic.id===normalize(query)||tokens.some(token=>topic.normalizedTerms.includes(token))).flatMap(topic=>topic.normalizedTerms)])]:tokens;
      // Pin every needed encoded part during preparation. A cached decoded
      // term can be evicted while another term is decoded in the same query.
      const parts=new Set();for(const term of expanded){const index=terms.get(term);if(index!==undefined&&Number.isSafeInteger(payload.postings[index][1]))parts.add(payload.postings[index][1]);}
      await loadParts([...parts].sort((a,b)=>a-b),"postings",signal);
    }
    function fillResultPreview(result,context) {
      const row=rows[result.ordinal],reading=preferredReading(row,context.preferred),preview=excerpt(reading?.text||"",context.query,payload.preview_characters||180);
      result.row=row;result.excerpt=preview.text;result.language=reading?.language||row.language;result.reference=row.reference;result.excerptTruncated=!!reading?.truncated||preview.truncated;
      result.excerptKind=preview.matched?"matched-excerpt":"source-preview";
    }
    async function prepareResults(results,prepareOptions={}) {
      const signal=prepareOptions.signal;checkAbort(signal);
      if(!payload.preview_shards)return results;
      const parts=new Set(),partForOrdinal=new Map();
      for(const result of results) {
        const index=payload.preview_shards.findIndex(part=>result.ordinal>=part.first_ordinal&&result.ordinal<part.first_ordinal+part.row_count);
        if(index<0)fail("no source preview part for selected occurrence");parts.add(index);partForOrdinal.set(result.ordinal,index);
      }
      await loadParts([...parts].sort((a,b)=>a-b),"previews",signal);
      for(const result of results) {
        const part=previewParts.get(partForOrdinal.get(result.ordinal)),previews=part.previews[result.ordinal-part.first_ordinal];
        if(previews.some(item=>!object(item)||typeof item.text!=="string"||typeof item.language!=="string"||!rows[result.ordinal].languages.includes(item.language)))fail("invalid source preview language or text");
        rows[result.ordinal].readings=previews;
        fillResultPreview(result,resultContexts.get(result)||{preferred:"",query:""});
      }
      return results;
    }
    function search(options={}) {
      searchCalls++;
      const query=String(options.query||"").trim(),mode=["reference","wording","topic","all"].includes(options.mode)?options.mode:"all",filters=options.filters||{},preferred=options.preferredLanguage||"";
      if(query.length>(payload.limits?.max_query_characters||512))throw new Error("Please shorten the search to 512 characters or fewer.");
      const exact=ids.get(query),parsed=mode==="wording"||mode==="topic"?{pairs:[],text:query}:parseReference(query);
      const quoted=[...parsed.text.matchAll(/[“\"]([^”\"]+)[”\"]/g)].map(match=>tokenize(match[1]));
      const queryTokens=tokenize(parsed.text),unique=[...new Set(queryTokens)];
      if(queryTokens.length>(payload.limits?.max_query_tokens||128))throw new Error("Please use 128 search words or fewer.");
      const relevantTopics=mode==="topic"?topicAids.filter(topic=>topic.id===normalize(query)||queryTokens.some(token=>topic.normalizedTerms.includes(token))):[];
      const expanded=mode==="topic"?[...new Set([...unique,...relevantTopics.flatMap(topic=>topic.normalizedTerms)])]:unique;
      const mapTerms=exact!==undefined||mode==="reference"&&!parsed.pairs.length?[]:expanded;
      const maps=new Map(mapTerms.map(term=>[term,posting(term)]));
      let candidates;
      if(exact!==undefined)candidates=[...exact];
      else if(mode==="reference"&&!parsed.pairs.length)candidates=[];
      else if(parsed.pairs.length){candidates=[...(referenceIndex[parsed.pairs[0]]||[])];for(const pair of parsed.pairs.slice(1)){const set=new Set(referenceIndex[pair]||[]);candidates=candidates.filter(value=>set.has(value));}}
      else if(expanded.length&&mode==="topic")candidates=[...new Set([...maps.values()].flatMap(map=>[...map.keys()]))];
      else if(unique.length){const smallest=[...unique].sort((a,b)=>maps.get(a).size-maps.get(b).size)[0];candidates=[...maps.get(smallest).keys()];}
      else candidates=rows.map(row=>row.ordinal);
      const ranked=[];
      for(const ordinal of candidates) {
        const row=rows[ordinal];if(!filterRow(row,filters))continue;
        if(exact===undefined&&mode!=="topic"&&unique.some(term=>!maps.get(term)?.has(ordinal)))continue;
        if(exact===undefined&&mode==="wording"&&unique.some(term=>!(maps.get(term)?.get(ordinal)?.mask&1)))continue;
        if(exact===undefined&&quoted.some(tokens=>tokens.length>1&&!phraseAt(maps,tokens,ordinal)))continue;
        let score=exact?.includes(ordinal)?100000:parsed.pairs.length?50000:0;
        let wordingMatches=0,metadataMatches=0;
        for(const term of expanded) {
          const item=maps.get(term)?.get(ordinal);if(!item)continue;
          const df=payload.postings[terms.get(term)][0],idf=Math.log(1+(rows.length+1)/(df+1));
          const direct=unique.includes(term),factor=direct?1:0.42;
          let weight=0;if(item.mask&1){weight+=9+Math.min(3,Math.log2(1+item.positions.length));wordingMatches++;}
          if(item.mask&2)weight+=5;if(item.mask&4)weight+=6;if(item.mask&8)weight+=5;if(item.mask&16)weight+=3;if(item.mask&32)weight+=1.2;if(item.mask&64)weight+=0.4;
          if(!(item.mask&1))metadataMatches++;
          score+=weight*idf*factor;
        }
        const phrase=queryTokens.length>1&&phraseAt(maps,queryTokens,ordinal);
        if(phrase)score+=10000;
        if(preferred&&row.languages.some(code=>sameLanguage(code,preferred)))score+=0.25;
        ranked.push({ordinal,score,matchKind:exact?.includes(ordinal)?"exact-occurrence":parsed.pairs.length?"exact-reference":phrase?"exact-phrase":mode==="topic"?"editorial-topic":wordingMatches?"wording":metadataMatches?"source-metadata":"browse"});
      }
      ranked.sort((a,b)=>b.score-a.score||a.ordinal-b.ordinal);
      const matchedOccurrences=ranked.map(item=>item.ordinal),matchesByGroup=new Map(),results=[];
      for(const hit of ranked) {
        const groupId=options.group===false?null:groupByOrdinal.get(hit.ordinal),key=groupId||"occurrence:"+hit.ordinal;
        const existing=matchesByGroup.get(key);if(existing){existing.matchedMembers.push(hit.ordinal);continue;}
        const family=groupId?groups.get(groupId):null;
        const result={...hit,members:family?[...family.members]:[hit.ordinal],matchedMembers:[hit.ordinal],groupEvidence:family?.evidence||null};
        matchesByGroup.set(key,result);results.push(result);
      }
      for(const result of results) {
        result.matchedOrdinal=result.ordinal;
        result.matchReference=rows[result.matchedOrdinal].reference;
        if(exact===undefined&&preferred){const selected=result.members.find(ordinal=>filterRow(rows[ordinal],filters)&&rows[ordinal].languages.some(code=>sameLanguage(code,preferred)));if(selected!==undefined)result.ordinal=selected;}
        const row=rows[result.ordinal],context={preferred,query:parsed.text};resultContexts.set(result,context);fillResultPreview(result,context);
        let location=null;const matchedRow=rows[result.matchedOrdinal];
        for(const token of expanded){const position=maps.get(token)?.get(result.matchedOrdinal)?.positions[0];if(position===undefined)continue;
          const segment=matchedRow.searchSegments?.find(item=>position>=item.start&&position<item.start+item.length);
          if(segment){location={field:"quotation",language:segment.language,readingId:segment.readingId,term:token,editorialExpansion:!unique.includes(token),tokenPosition:position-segment.start,globalTokenPosition:position};break;}}
        result.matchLocation=location||{field:result.matchKind==="exact-reference"?"reference":result.matchKind==="exact-occurrence"?"occurrence-id":"metadata",language:null};
      }
      return {results,matchedOccurrences,matchingOccurrenceCount:matchedOccurrences.length,facets:payload.facets||{},
              suggestions:suggestedQueries(query,mode),query,mode,
              editorialExpansion:mode==="topic"?{label:payload.editorial?.label||"Editorial keyword search",terms:expanded,topics:relevantTopics.map(topic=>topic.label)}:null,
              complete:true,sourceRecordCount:rows.length};
    }
    return {rows,facets:payload.facets||{},groups:payload.groups||[],editorial:payload.editorial||{},search,prepare,prepareResults,
            getRow:ordinal=>rows[ordinal]||null,getOrdinal:id=>ids.get(id)?.length===1?ids.get(id)[0]:undefined,getOrdinals:id=>[...(ids.get(id)||[])],suggestions:suggestedQueries,
            parseReference,preferredReading,excerpt,
            metrics:()=>({recordCount:rows.length,termCount:terms.size,cachedPostingUnits:cacheUnits,cachedTerms:cache.size,postingPartBytes,previewPartBytes,searchCalls}),
            clearCache:()=>{cache.clear();cacheUnits=0;postingParts.clear();previewParts.clear();postingPartBytes=previewPartBytes=0;if(payload.preview_shards)rows.forEach(row=>{row.readings=[];});}};
  }
  return {SCHEMA,normalize,tokenize,create,decodePosting,excerpt,expandPayload};
});

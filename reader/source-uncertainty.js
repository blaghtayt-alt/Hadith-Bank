// Source uncertainty presentation v1. Pure and self-contained for offline reader.
// These notes carry no publication, authenticity or release certification.
const HadithSourceUncertainty = (() => {
  "use strict";
  const WARNING = "(OCR wasn’t clear)", SCHEMA = "source_uncertainty_projection.v1";
  // Closed Hindi owner-application authority, mechanically compiled from the
  // independently pinned scripts/source_uncertainty_authority.json. Not data
  // supplied by the selected record. Code/bundle integrity is the trust edge.
  const APPROVED_BINDINGS = {"HI-MSB-V1-P0219-N0227":{"annotations":[{"end":2396,"issue_id":"QC11-SOURCE-0050","kind":"accepted_uncertain_reading","span_sha256":"c6ed93a8af0d4583c58f7dd452652179b30594fb98d09052985abb0e0ec1cc9b","start":2390}],"body_sha256":"2adedc1c17f998d40b4a5d627b846821457b51ec133d423617024e032ca2a37a","text_record_id":"HI-MSB-V1-P0219-N0227-HI"},"HI-MSB-V1-P0244-N0250":{"annotations":[{"end":560,"issue_id":"QC11-SOURCE-0055","kind":"accepted_uncertain_reading","span_sha256":"e4c96825d3adb080217d8b69cc78db96bf4234a0aaf239b98677aa7a2538c0d9","start":557}],"body_sha256":"fc6f6663a20fe081d1b9b1c84266508fa316f4f3a68423e2512998d43015f68a","text_record_id":"HI-MSB-V1-P0244-N0250-HI"},"HI-MSB-V1-P0317-N0352":{"annotations":[{"end":133,"issue_id":"QC11-SOURCE-0058","kind":"accepted_uncertain_reading","span_sha256":"8eb922dce463def14af793dc336b4be2533c0fae6d3cc12134f33ac0d82350fb","start":125}],"body_sha256":"3a0197b20244e1e51a2ed9039405b33b9c5299f0110c43b26be26615b0acf486","text_record_id":"HI-MSB-V1-P0317-N0352-HI"},"HI-MSB-V1-P0344-N0393":{"annotations":[{"end":260,"issue_id":"QC11-SOURCE-0060","kind":"accepted_uncertain_reading","span_sha256":"b7723e088ba7bff018c0c7fbdd7769f062c4f52357c603fadde564e7fb0a5a6d","start":256}],"body_sha256":"0f5583d1187dca473c97024266733e927fc2c6fd4b24764453754ec8ed4e8a0e","text_record_id":"HI-MSB-V1-P0344-N0393-HI"},"HI-MSB-V1-P0374-N0434":{"annotations":[{"end":517,"issue_id":"UNREVIEWED:⟦HI-MSB-B06-HI-U014⟧","kind":"unreviewed_source_gap","span_sha256":"b68c514085fce458ecb702394af33194ab81df6c86e648410986bcb5623031e8","start":497},{"end":1322,"issue_id":"QC11-SOURCE-0062","kind":"accepted_uncertain_reading","span_sha256":"b58e94d564e543ee704b07feb3578ec090c5f661f817962ae052974be765828b","start":1317},{"end":1468,"issue_id":"QC11-SOURCE-0063","kind":"accepted_uncertain_reading","span_sha256":"e1475426c5a49ac0de1e96ade9662cf625cf9c3047713f1df30ba29c21580cc8","start":1464},{"end":1521,"issue_id":"QC11-SOURCE-0064","kind":"accepted_uncertain_reading","span_sha256":"78b718d68390d73bdbab144db425d318519addca4983a793fcdb6ba19c912921","start":1517}],"body_sha256":"6acf4cfb189f90fafae2016f22357a0a96e8d4a7d6408753d56e16d27d9ae05b","text_record_id":"HI-MSB-V1-P0374-N0434-HI"},"HI-MSB-V2-P0090-N0839":{"annotations":[{"end":324,"issue_id":"UNREVIEWED:⟦HI-MSB-B07-V2-HI-U007⟧","kind":"unreviewed_source_gap","span_sha256":"995104896241fac5c8f4cf81e3587960ab53515d5f8bf34548a703e4c2392f13","start":301},{"end":687,"issue_id":"QC11-SOURCE-0106","kind":"accepted_uncertain_reading","span_sha256":"837e969f4cac920d188f08cfe0e2ae705a4fae3015c7109cd00a19e573c5f731","start":682}],"body_sha256":"0f02991b0c0213bca57a5ffc59d3e1b959d9fecb9f59c2dd0cfbc9ae55bb4283","text_record_id":"HI-MSB-V2-P0090-N0839-HI"},"HI-MSB-V3-P0188-N1675":{"annotations":[{"end":202,"issue_id":"QC11-SOURCE-0149","kind":"unfilled_source_gap","span_sha256":"5d456efb92f7fe3dbad6a4ea82fe84523a544c7ab9eb6318d75d642b1369ebf7","start":172}],"body_sha256":"ff968f464d1ca66c5672ceae416251d2524e6e831ea5316b20b5ca1bb35e8a14","text_record_id":"HI-MSB-V3-P0188-N1675-HI"},"HI-MSB-V3-P0193-N1680":{"annotations":[{"end":146,"issue_id":"QC11-SOURCE-0150","kind":"accepted_uncertain_reading","span_sha256":"1b4a9ddcff28a673db75cf295069e88da15bbb1689bcf10542e44bbcb0d8f2bd","start":136}],"body_sha256":"606b28a016ae364bdc20d8a61af8b3b85c43f4139414967519d51103a613c736","text_record_id":"HI-MSB-V3-P0193-N1680-HI"},"HI-MSB-V3-P0214-N1699":{"annotations":[{"end":14798,"issue_id":"QC11-SOURCE-0156","kind":"accepted_uncertain_reading","span_sha256":"6ac11f8dd53f9db8fa88d1f96beaa29742a64a55e9453201da864bd76c51ff3e","start":14790}],"body_sha256":"28de828e924042dd19b15d8d103eda90f3377da64406b74f53a20c3626033308","text_record_id":"HI-MSB-V3-P0214-N1699-HI"},"HI-MSB-V3-P0316-N1791":{"annotations":[{"end":12,"issue_id":"QC11-SOURCE-0167","kind":"accepted_uncertain_reading","span_sha256":"f66211b23f1c7c9efd30fbbc1f8f0a9f3f9427b1f1a71b42762c7d8d33c5fd54","start":8}],"body_sha256":"9c912b2b29d13c5fd9748421856e76d2e3b9a6876a53284666e8b8efc3c9ce5c","text_record_id":"HI-MSB-V3-P0316-N1791-HI"},"HI-MSB-V3-P0317-N1793":{"annotations":[{"end":138,"issue_id":"QC11-SOURCE-0168","kind":"accepted_uncertain_reading","span_sha256":"350026e686d9a0fe8f893ef79c52ed14811ba57e7f0fed4c6ece10f51e16575b","start":134}],"body_sha256":"e7618caba9e1171b191e4382a63e41f0dcec4bdce46eedba92e7b7291522ad03","text_record_id":"HI-MSB-V3-P0317-N1793-HI"},"HI-MSB-V3-P0321-N1799":{"annotations":[{"end":12,"issue_id":"QC11-SOURCE-0170","kind":"accepted_uncertain_reading","span_sha256":"fa5b9e0f7c8d3d033b59baca6354bd0e90d52fc184301c4bc1aa3d4fde1db796","start":10}],"body_sha256":"fb9c18d86bd0ccf5575a494fd48bc67462b908af075d24f04b0c5aeb9779bc7a","text_record_id":"HI-MSB-V3-P0321-N1799-HI"},"HI-MSB-V3-P0418-N1922":{"annotations":[{"end":45,"issue_id":"QC11-SOURCE-0188","kind":"accepted_uncertain_reading","span_sha256":"f7a3ce36bc21257f7bbd6d7c743f0d9eac91c220cb84e8cde752cace29049e1b","start":41}],"body_sha256":"88df14a1021174efd8e6d48a29270eea380085787ff49bf468c019bfec5e6c97","text_record_id":"HI-MSB-V3-P0418-N1922-HI"},"HI-MSB-V3-P0436-N1952":{"annotations":[{"end":22,"issue_id":"QC11-SOURCE-0196","kind":"accepted_uncertain_reading","span_sha256":"08cd469ac353716b075b090a499d9fc5db22dbf5c4c5730b2594d8894c82ab6c","start":20}],"body_sha256":"22c4d82c6523454ed2d5318c94ecc70de5067a12df1903213ee53168564df9a1","text_record_id":"HI-MSB-V3-P0436-N1952-HI"}};

  const K = [
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
  ];
  const rotate = (v,n) => (v>>>n) | (v<<(32-n));
  // SHA-256 of UTF-8, synchronous to validate before any quotation DOM exists.
  // No normalization: Devanagari combinations/non-BMP keep their exact bytes.
  function digest(text) {
    const bytes = new TextEncoder().encode(text), size = Math.ceil((bytes.length+9)/64)*64;
    const data = new Uint8Array(size);data.set(bytes);data[bytes.length]=128;
    const view = new DataView(data.buffer), bits = BigInt(bytes.length)*8n;
    view.setUint32(size-8,Number((bits>>32n)&0xffffffffn));view.setUint32(size-4,Number(bits&0xffffffffn));
    const h=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    const w = new Uint32Array(64);
    for(let base=0;base<size;base+=64){
      for(let i=0;i<16;i++)w[i]=view.getUint32(base+i*4);
      for(let i=16;i<64;i++){
        const a=w[i-15],b=w[i-2];
        w[i]=(w[i-16]+(rotate(a,7)^rotate(a,18)^(a>>>3))+w[i-7]+(rotate(b,17)^rotate(b,19)^(b>>>10)))>>>0;
      }
      let [a,b,c,d,e,f,g,q]=h;
      for(let i=0;i<64;i++){
        const t1=(q+(rotate(e,6)^rotate(e,11)^rotate(e,25))+((e&f)^(~e&g))+K[i]+w[i])>>>0;
        const t2=((rotate(a,2)^rotate(a,13)^rotate(a,22))+((a&b)^(a&c)^(b&c)))>>>0;
        q=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;
      }
      for(const [i,v] of [a,b,c,d,e,f,g,q].entries())h[i]=(h[i]+v)>>>0;
    }
    return h.map(v=>v.toString(16).padStart(8,"0")).join("");
  }
  const fail = () => {throw new Error("Invalid source-bound uncertainty projection; quotation withheld");};
  const equalFields = (item,names) => item&&typeof item==="object"&&!Array.isArray(item) &&
    Object.keys(item).length===names.length && names.every(name=>Object.prototype.hasOwnProperty.call(item,name));
  const cpLength = text => Array.from(text).length;
  const cpSlice = (text,start,end) => Array.from(text).slice(start,end).join("");
  const wellFormed = text => typeof text==="string" && !Array.from(text).some(c=>
    c.length===1 && c.charCodeAt(0)>=0xd800 && c.charCodeAt(0)<=0xdfff);
  const isScalarBoundary = (text,offset) => Number.isSafeInteger(offset)&&offset>=0&&offset<=text.length&&
    !(offset>0&&offset<text.length&&text.charCodeAt(offset-1)>=0xd800&&
      text.charCodeAt(offset-1)<=0xdbff&&text.charCodeAt(offset)>=0xdc00&&text.charCodeAt(offset)<=0xdfff);
  function utf16AtCodepoint(text,offset){
    if(!Number.isSafeInteger(offset)||offset<0||offset>cpLength(text))fail();
    return Array.from(text).slice(0,offset).join("").length;
  }
  function validatedParts(text,p,recordId,externalExpectedHash=null,glyphs=null) {
    const fields=["schema","record_id","text_record_id","field","expected_body_sha256","annotations"];
    if(!wellFormed(text)||!wellFormed(recordId)||!recordId||!equalFields(p,fields)||
       p.schema!==SCHEMA||p.record_id!==recordId||!wellFormed(p.text_record_id)||
       !/^[A-Za-z0-9][A-Za-z0-9:._-]{0,159}$/.test(p.text_record_id)||p.field!=="text.translation"||
       !/^[0-9a-f]{64}$/.test(p.expected_body_sha256)||digest(text)!==p.expected_body_sha256||
       (externalExpectedHash!==null&&externalExpectedHash!==p.expected_body_sha256)||
       !Array.isArray(p.annotations)||!p.annotations.length||(glyphs&&(!Array.isArray(glyphs)||glyphs.length)))fail();
    const chars=Array.from(text),ids=new Set(),notes=[];
    for(const note of p.annotations){
      if(!equalFields(note,["issue_id","start","end","span_sha256","kind"])||
         !Number.isSafeInteger(note.start)||!Number.isSafeInteger(note.end)||note.start<0||
         note.start>=note.end||note.end>chars.length||!wellFormed(note.issue_id)||
         !note.issue_id||cpLength(note.issue_id)>160||ids.has(note.issue_id)||
         !["accepted_uncertain_reading","unfilled_source_gap","unreviewed_source_gap"].includes(note.kind)||
         !/^[a-f0-9]{64}$/.test(note.span_sha256))fail();
      const word=chars.slice(note.start,note.end).join("");
      if(digest(word)!==note.span_sha256||
         (note.kind.endsWith("source_gap")?!/^⟦[^⟦⟧\r\n]{1,160}⟧$/u.test(word):/⟦[^⟧]*⟧/u.test(word)))fail();
      ids.add(note.issue_id);notes.push({start:note.start,end:note.end,issue_id:note.issue_id,kind:note.kind});
    }
    notes.sort((a,b)=>a.start-b.start||a.end-b.end);
    for(let i=1;i<notes.length;i++)if(notes[i-1].end>notes[i].start)fail();
    // A complete frozen annotation tuple list is independent of the mutable
    // body's internally self-attested digest. Never promote U014 or U007.
    const trusted=APPROVED_BINDINGS[recordId];
    if(!Object.prototype.hasOwnProperty.call(APPROVED_BINDINGS,recordId)||
       !trusted||p.text_record_id!==trusted.text_record_id||
       p.expected_body_sha256!==trusted.body_sha256||digest(text)!==trusted.body_sha256||
       JSON.stringify(notes.map(n=>[n.issue_id,n.start,n.end,n.kind,digest(cpSlice(text,n.start,n.end))]))!==
       JSON.stringify(trusted.annotations.map(n=>[n.issue_id,n.start,n.end,n.kind,n.span_sha256])))fail();
    for(const match of text.matchAll(/⟦[^⟧]*⟧|⟦|⟧/gu)){
      const start=cpLength(text.slice(0,match.index)),end=start+cpLength(match[0]);
      if(!notes.some(n=>n.start===start&&n.end===end&&n.kind.endsWith("source_gap")))fail();
    }
    const parts=[];let position=0;
    for(const n of notes){
      if(n.start>position)parts.push({kind:"quotation",start:position,end:n.start,source_text:chars.slice(position,n.start).join("")});
      parts.push({...n,kind:n.kind.endsWith("source_gap")?"gap":"quotation",source_text:chars.slice(n.start,n.end).join("")});
      parts.push({kind:"note",start:n.start,end:n.end,issue_id:n.issue_id,text:WARNING,
                  review_status:n.kind==="unreviewed_source_gap"?"unreviewed":"owner_decision_applied"});
      position=n.end;
    }
    if(position<chars.length)parts.push({kind:"quotation",start:position,end:chars.length,source_text:chars.slice(position).join("")});
    if(parts.filter(p=>p.kind!=="note").map(p=>p.source_text).join("")!==text)fail();
    return parts;
  }
  function exactQuotation(parts){
    if(parts.some(p=>p.kind==="gap"))throw new Error("Cannot copy an incomplete source quotation with unresolved gaps");
    return parts.filter(p=>p.kind==="quotation").map(p=>p.source_text).join("");
  }
  function validatedRecordParts(record){
    if(!record||typeof record!=="object"||Array.isArray(record))fail();
    const p=record.source_uncertainty_projection;
    const source=record.source||{},number=record.number||{};
    if(!p||typeof source!=="object"||Array.isArray(source)||
       typeof number!=="object"||Array.isArray(number))fail();
    const original=source.original_metadata;
    if(original!==undefined&&(original===null||typeof original!=="object"||Array.isArray(original)))fail();
    const declared=[number.source_entry_id,source.source_text_record_id,original?.source_text_record_id];
    if(declared.some(id=>id!==undefined&&id!==null&&id!==p.text_record_id))fail();
    return validatedParts(record.text_translation,p,record.id,null,record.source_glyphs);
  }
  const hasGaps = parts => parts.some(p=>p.kind==="gap");
  function quotationFragments(parts){
    const chunks=[{text:"",start:0,end:0}];
    for(const part of parts){
      if(part.kind==="quotation"){const last=chunks[chunks.length-1];
        if(!last.text)last.start=part.start;last.text+=part.source_text;last.end=part.end;
      }else if(part.kind==="gap")chunks.push({text:"",start:part.end,end:part.end});
      else if(part.kind!=="note")fail();
    }
    return chunks.filter(p=>p.text);
  }
  const sourceReconstruction = parts => parts.filter(p=>p.kind!=="note").map(p=>p.source_text).join("");
  // Show a bound excerpt, potentially clipped mid-annotation. A clipped gap is
  // always replaced by a source-gap notice (never an internal marker string).
  function appendParts(container,parts,language,start=0,end=null){
    if(!Array.isArray(parts)||!parts.length)fail();
    const max=parts.reduce((m,p)=>Math.max(m,p.end),0);if(end===null)end=max;
    if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start<0||end<start||end>max)fail();
    for(const part of parts){
      if(part.end<=start||part.start>=end)continue;
      let node;
      if(part.kind==="quotation"){
        node=document.createElement("span");node.className="quotation source-quote";node.lang=language;
        node.textContent=cpSlice(part.source_text,Math.max(0,start-part.start),Math.min(part.end,end)-part.start);
      }else if(part.kind==="gap"){
        node=document.createElement("span");node.className="source-gap";node.setAttribute("role","note");
        node.textContent="[Source gap: exact reading unavailable]";
      }else if(part.kind==="note"){
        node=document.createElement("span");node.className="source-uncertainty";node.setAttribute("role","note");
        node.dataset.issueHash=digest(part.issue_id);node.textContent=WARNING;
      }else fail();
      node.dataset.sourceStart=part.start;node.dataset.sourceEnd=part.end;container.append(node);
      if(part.kind==="note"&&part.review_status==="unreviewed"){
        const hold=document.createElement("span");hold.className="source-unreviewed";
        hold.setAttribute("role","note");hold.textContent="Separate unresolved hold";container.append(hold);
      }
    }
  }
  // Preview callers must consult this code-pinned 14-parent identity, never
  // the compact index's own (removable) uncertainty flags or preview fields.
  // These lookups expose identity only, not source wording or editable anchors.
  const isBoundParent = id => typeof id==="string" &&
    Object.prototype.hasOwnProperty.call(APPROVED_BINDINGS,id);
  const isBoundTextRecord = id => typeof id==="string" &&
    Object.values(APPROVED_BINDINGS).some(binding=>binding.text_record_id===id);
  return {digest,cpLength,cpSlice,utf16AtCodepoint,isScalarBoundary,validatedParts,validatedRecordParts,exactQuotation,hasGaps,quotationFragments,sourceReconstruction,appendParts,isBoundParent,isBoundTextRecord};
})();

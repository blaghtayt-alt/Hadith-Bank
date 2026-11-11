#!/usr/bin/env python3
"""Offline search and source resolution for the independent Hadith Bank."""
import argparse,hashlib,json,pathlib,re,sys,unicodedata
from search_hadeethenc import local
ROOT=pathlib.Path(__file__).resolve().parents[1]
def source_materials(root):
 """Read accepted source locations, including material folders outside languages/."""
 root=pathlib.Path(root).resolve()
 if (root/'catalog/materials.json').is_file():
  catalog=json.loads(local(root,'catalog/materials.json').read_text(encoding='utf-8'))
  if catalog.get('schema')!='hadith-bank-materials-v1':raise ValueError('Unrecognized material catalog')
  return [{'language':row['language'],'path':row['canonical_records_path'],'sha256':row['canonical_records_sha256']} for row in catalog['materials']]
 if (root/'datasets/hadeethenc/collections.json').is_file():
  catalog=json.loads(local(root,'datasets/hadeethenc/collections.json').read_text(encoding='utf-8'))
  return [{'language':row['language'],'path':row['records_path'],'sha256':row['records_sha256']} for row in catalog['collections']]
 return []
def available_languages(root,materials=None):
 root=pathlib.Path(root).resolve();materials=source_materials(root) if materials is None else materials
 languages={row['language'] for row in materials}
 if (root/'organized/INDEX.json').is_file():
  languages.update(json.loads(local(root,'organized/INDEX.json').read_text(encoding='utf-8'))['languages'])
 if any(not isinstance(lang,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*',lang) for lang in languages):raise ValueError('Unsafe source language')
 return sorted(languages)
def fulltext_paths(root,language=None):
 """Keep legacy source formats and include each registered canonical file once."""
 materials=source_materials(root);languages=available_languages(root,materials);paths=[];seen=set()
 if language is not None and language not in languages:raise ValueError('Unknown source language: '+str(language))
 for lang in ([language] if language else languages):
  for path in sorted((root/'languages'/lang/'books').rglob('*')):
   if not path.is_file() or path.suffix not in ('.txt','.md','.json','.jsonl'):continue
   path=local(root,path.relative_to(root).as_posix())
   if path not in seen:paths.append(path);seen.add(path)
 for row in materials:
  if language and row['language']!=language:continue
  path=local(root,row['path']);expected=row['sha256']
  if not isinstance(expected,str) or not re.fullmatch(r'[0-9a-fA-F]{64}',expected):raise ValueError('Missing/invalid source SHA-256: '+row['path'])
  if hashlib.sha256(path.read_bytes()).hexdigest()!=expected.lower():raise ValueError('Source SHA-256 mismatch: '+row['path'])
  if path not in seen:paths.append(path);seen.add(path)
 return paths
def norm(s):return "".join(c for c in unicodedata.normalize("NFKD",str(s)).casefold() if not unicodedata.combining(c))
def matching_excerpt(text, query, width=350):
 """Show the actual matched characters, even far into a long JSONL record."""
 needle=norm(query);offset=norm(text).find(needle)
 if offset<0:return text[:width]
 # Normalization can change character counts (diacritics, ligatures, casefold).
 # Map the folded match back to source offsets instead of slicing at that index.
 folded_length=0;start=None;end=0
 for i,char in enumerate(text):
  next_length=folded_length+len(norm(char))
  if start is None and next_length>offset:start=i
  if next_length>=offset+len(needle):end=i+1;break
  folded_length=next_length
 if start is None:start=0
 if not needle:start=0;end=0
 left=max(0,start-80);right=min(len(text),max(left+width,end+80))
 if right==len(text):left=max(0,min(left,right-width))
 return ('…' if left else '')+text[left:right]+('…' if right<len(text) else '')
def fulltext_search(root,query,language=None,limit=20):
 """Search local source lines; JSONL remains one narration per source line."""
 root=pathlib.Path(root).resolve();matches=[];files=0;matched=0;needle=norm(query)
 for path in fulltext_paths(root,language):
  files+=1
  with path.open(encoding="utf-8",errors="replace") as stream:
   for i,line in enumerate(stream,1):
    line=line.rstrip("\r\n")
    if needle not in norm(line):continue
    matched+=1
    if len(matches)>=max(0,limit):continue
    hit={"path":path.relative_to(root).as_posix(),"line":i,"excerpt":matching_excerpt(line,query)}
    if path.suffix==".jsonl":
     try:
      record=json.loads(line)
      if isinstance(record,dict) and record.get("record_id"):hit["record_id"]=record["record_id"]
     except json.JSONDecodeError:pass
    matches.append(hit)
 return {"searched_files":files,"matched":matched,"shown":len(matches),"match_unit":"source_line","results":matches}
def emit(obj):print(json.dumps(obj,ensure_ascii=False,indent=2))
def verified(loc):
 p=(ROOT/loc["path"]).resolve()
 if not p.is_relative_to(ROOT.resolve()) or not p.is_file():raise ValueError("Missing/unsafe local file "+str(p))
 data=p.read_bytes()
 if loc.get("bytes") is not None and len(data)!=loc["bytes"]:raise ValueError("Size mismatch "+loc["path"])
 if loc.get("sha256") and hashlib.sha256(data).hexdigest()!=loc["sha256"]:raise ValueError("SHA mismatch "+loc["path"])
 return data
def at_pointer(obj,path):
 if not path:return obj
 if not path.startswith("/"):raise ValueError("Invalid JSON Pointer")
 for k in path.split("/")[1:]:
  key=k.replace("~1","/").replace("~0","~")
  obj=obj[int(key)] if isinstance(obj,list) else obj[key]
 return obj
def main():
 if len(sys.argv)>1 and sys.argv[1]=='hadith':
  from search_hadeethenc import main as hadeethenc_main
  return hadeethenc_main(sys.argv[2:])
 p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest="action",required=True)
 q=sp.add_parser("search");q.add_argument("query",nargs="?",default="")
 q.add_argument("--kind",choices=["package","reading","source","lesson","chapter"])
 languages=available_languages(ROOT)
 q.add_argument("--language",choices=languages);q.add_argument("--limit",type=int,default=15)
 r=sp.add_parser("resolve");r.add_argument("id");r.add_argument("--pointer");r.add_argument("--reading",action="store_true")
 f=sp.add_parser("fulltext");f.add_argument("query");f.add_argument("--language",choices=languages);f.add_argument("--limit",type=int,default=20)
 a=p.parse_args()
 if a.action=="fulltext":
  emit(fulltext_search(ROOT,a.query,a.language,a.limit));return
 idx=json.loads((ROOT/"organized/INDEX.json").read_text(encoding="utf-8"))
 groups={"package":"packages","reading":"readingsOnly","source":"sourceRecords","lesson":"lessons","chapter":"chapters"}
 if a.action=="search":
  matches=[]
  for kind,key in groups.items():
   if a.kind and kind!=a.kind:continue
   for item in idx[key]:
    if a.language and kind not in ("lesson","chapter") and item.get("language")!=a.language:continue
    if all(norm(w) in norm(json.dumps(item,ensure_ascii=False)) for w in a.query.split()):
     matches.append({"kind":kind,"record":item})
  emit({"count":len(matches),"results":matches[:max(0,a.limit)]});return
 item=None;kind=None
 for k,key in groups.items():
  if k in ("lesson","chapter"):continue
  for x in idx[key]:
   if x.get("id")==a.id:kind,item=k,x;break
  if item:break
 if not item:raise ValueError("Unknown ID")
 if kind=="package":
  loc=item["locators"]["reading"] if a.reading else item["locators"].get("sourceEnvelope")
  if not loc:raise ValueError("No source envelope: consult individual source files in language catalog")
  member=None;ptr=a.pointer or ""
 elif kind=="reading":loc=item["reading"];member=None;ptr=a.pointer or ""
 else:
  source=item["locator"];loc=source.get("envelope",source.get("file"))
  member=source.get("member")
  ptr=a.pointer if a.pointer is not None else source.get("memberJsonPointer",source.get("jsonPointer",""))
 obj=json.loads(verified(loc))
 if member:
  x=[x for x in obj["files"] if x["name"]==member]
  if len(x)!=1:raise ValueError("Missing/ambiguous member")
  txt=x[0]["text"]
  if hashlib.sha256(txt.encode()).hexdigest()!=item["locator"]["memberSha256"]:raise ValueError("Member hash mismatch")
  obj=json.loads(txt)
 emit({"id":a.id,"source_path":loc["path"],"member":member,"pointer":ptr,"value":at_pointer(obj,ptr)})
if __name__=="__main__":
 try:main()
 except (OSError,ValueError,KeyError,IndexError) as e:sys.exit("Error: "+str(e))

#!/usr/bin/env python3
"""Offline search and source resolution for the independent Hadith Bank."""
import argparse,hashlib,json,pathlib,sys,unicodedata
ROOT=pathlib.Path(__file__).resolve().parents[1]
def norm(s):return "".join(c for c in unicodedata.normalize("NFKD",str(s)).casefold() if not unicodedata.combining(c))
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
 q.add_argument("--language",choices=["ja","fil","vi","zh-CN","uz","hi"]);q.add_argument("--limit",type=int,default=15)
 r=sp.add_parser("resolve");r.add_argument("id");r.add_argument("--pointer");r.add_argument("--reading",action="store_true")
 f=sp.add_parser("fulltext");f.add_argument("query");f.add_argument("--language",choices=["ja","fil","vi","zh-CN","uz","hi"]);f.add_argument("--limit",type=int,default=20)
 a=p.parse_args()
 if a.action=="fulltext":
  matches=[];files=0
  for lang in ([a.language] if a.language else ["ja","fil","vi","zh-CN","uz","hi"]):
   for path in (ROOT/"languages"/lang/"books").rglob("*"):
    if not path.is_file() or path.suffix not in (".txt",".md",".json"):continue
    files+=1
    for i,line in enumerate(path.read_text(encoding="utf-8",errors="replace").splitlines(),1):
     if norm(a.query) in norm(line) and len(matches)<max(0,a.limit):
      matches.append({"path":path.relative_to(ROOT).as_posix(),"line":i,"excerpt":line[:350]})
  emit({"searched_files":files,"results":matches});return
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

#!/usr/bin/env python3
"""Validate all local source locators, known hashes, envelope members and six-language scope."""
import hashlib,json,pathlib,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
LANGS=["ja","fil","vi","zh-CN","uz","hi"]
errors=[];checked=set();members=0;pointers=0
def check(loc):
 path=loc.get("path")
 if not isinstance(path,str):errors.append("Missing path locator "+str(loc)[:150]);return None
 real=(ROOT/path).resolve()
 if not real.is_relative_to(ROOT.resolve()) or not real.is_file():
  errors.append("Missing/unsafe "+path);return None
 data=real.read_bytes()
 if loc.get("bytes") is not None and loc["bytes"]!=len(data):errors.append("Byte count "+path)
 if loc.get("sha256") and hashlib.sha256(data).hexdigest()!=loc["sha256"]:errors.append("Hash "+path)
 checked.add(path);return data
def ptr(obj,p):
 if not p:return obj
 if not p.startswith("/"):raise ValueError("Pointer without /")
 for part in p.split("/")[1:]:
  key=part.replace("~1","/").replace("~0","~")
  obj=obj[int(key)] if isinstance(obj,list) else obj[key]
 return obj
idx=json.loads((ROOT/"organized/INDEX.json").read_text(encoding="utf-8"))
if idx["languages"]!=LANGS:errors.append("Unexpected language list")
for lang in LANGS:
 cat_path=ROOT/"languages"/lang/"catalog.json"
 cat=json.loads(cat_path.read_text(encoding="utf-8"))
 if cat["language"]!=lang:errors.append("Language mismatch "+lang)
 for r in cat.get("records",[])+cat.get("notIndexed",[]):
  for k in ("reading","sourceEnvelope"):
   if r.get(k):check(r[k])
  for v in r.get("sourceFiles",[]):check(v)
for pkg in idx["packages"]:
 for k in ("reading","sourceEnvelope"):
  if pkg["locators"].get(k):check(pkg["locators"][k])
 for v in pkg["locators"].get("sourceFiles",[]):check(v)
for r in idx["readingsOnly"]:check(r["reading"])
for r in idx["sourceRecords"]:
 loc=r["locator"];ref=loc.get("envelope",loc.get("file"))
 if ref is None:errors.append("Missing source locator "+r["id"]);continue
 data=check(ref)
 if data is None:continue
 try:
  ob=json.loads(data)
  if loc.get("member"):
   entries=[x for x in ob["files"] if x["name"]==loc["member"]]
   if len(entries)!=1:raise ValueError("Member missing/multiple")
   raw=entries[0]["text"].encode("utf-8")
   if hashlib.sha256(raw).hexdigest()!=loc["memberSha256"]:raise ValueError("Bad member hash")
   members+=1;ob=json.loads(raw)
  p=loc.get("memberJsonPointer",loc.get("jsonPointer",""))
  ptr(ob,p);pointers+=1
 except (ValueError,TypeError,KeyError,IndexError) as e:errors.append(r["id"]+": "+str(e))
audit=json.loads((ROOT/"reports/IMPORT-STATUS.json").read_text(encoding="utf-8"))
for x in audit["files"]:
 data=check(x)
 if data and len(data)!=x["bytes"]:errors.append("Manifest length "+x["path"])
for path in [ROOT/"organized/INDEX.json"]+[ROOT/"languages"/l/"catalog.json" for l in LANGS]:
 text=path.read_text(encoding="utf-8")
 if "iman-companion" in text.lower() or "raw.githubusercontent.com/blaghtayt-alt" in text:
  errors.append("Runtime pointer to former repository "+str(path))
for child in (ROOT/"languages").iterdir():
 if child.is_dir() and child.name not in LANGS:errors.append("Unrequested language "+child.name)
if audit["missing"] or audit["mismatches"]:errors.append("Source import audit contains unresolved problems")
summary={"success":not errors,"selected_languages":LANGS,"copied_source_files":len(audit["files"]),
"checked_local_files":len(checked),"source_metadata_records":len(idx["sourceRecords"]),
"source_members_checked":members,"source_pointers_resolved":pointers,
"cataloged_packages":len(idx["packages"]),"reading_only":len(idx["readingsOnly"]),
"errors":errors[:60],"total_errors":len(errors)}
print(json.dumps(summary,ensure_ascii=False,indent=2))
sys.exit(0 if not errors else 1)

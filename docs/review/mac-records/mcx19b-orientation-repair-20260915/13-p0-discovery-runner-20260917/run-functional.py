import importlib.util,json,os,sys
from pathlib import Path
from datetime import datetime,timezone
os.umask(0o077)
sys.dont_write_bytecode=True
root=Path("LOCAL_HOME/Developer/sqe-platform-release-layout")
evidence=Path(__file__).parent
if datetime.now(timezone.utc)>=datetime.fromisoformat("2026-09-16T21:35:00+00:00"):
    raise SystemExit("Native start withheld: insufficient reserved time before block deadline.")
spec=importlib.util.spec_from_file_location("ace",root/"tools/ace_ios_local.py")
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
expected=json.loads((evidence/"clean-candidate.json").read_text())
assert m.candidate()==expected,"Candidate changed before functional verification"
previous=Path("LOCAL_HOME/ace-private/mcx19b-implementation-20260914/pilot-preparation-20260915/settings-navigation-fix/functional-runs/20260915T025431Z-selected-2c2c3ea9ae6c/manifest.json")
selectors=json.loads(previous.read_text())["selectors"]
assert len(selectors)==len(set(selectors))==68
assert sum("/AcceptanceEvidenceContractTests/" in s for s in selectors)==43
(evidence/"functional-selector-record.json").write_text(json.dumps({"selectorSource":str(previous),"selectorSourceSha256":m.sha256(previous),"totalTests":68,"contractSubset":43,"candidate":expected,"selectors":selectors},indent=2)+"\n")
args=["--evidence-root",str(evidence/"functional-runs"),"selected"]
for selector in selectors:args += ["--test",selector]
sys.exit(m.main(args))

from pathlib import Path
import importlib.util,sys,json,os
os.umask(0o077)
root=Path("LOCAL_HOME/Developer/sqe-platform-release-layout")
stage=Path("LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915")
spec=importlib.util.spec_from_file_location("ace",root/"tools/ace_ios_local.py")
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
old=Path("LOCAL_HOME/ace-private/mcx19b-implementation-20260914/pilot-preparation-20260915/settings-navigation-fix/functional-runs/20260915T025431Z-selected-2c2c3ea9ae6c/manifest.json")
selectors=json.loads(old.read_text())["selectors"]
assert len(selectors)==68 and len(set(selectors))==68
assert m.candidate()==json.loads((stage/"clean-candidate.json").read_text())
args=["--evidence-root",str(stage/"functional-runs"),"selected"]
for selector in selectors: args += ["--test",selector]
sys.exit(m.main(args))

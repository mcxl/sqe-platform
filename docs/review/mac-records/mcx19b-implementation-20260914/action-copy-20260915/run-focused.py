from pathlib import Path
import json,subprocess,sys
p=Path(__file__).parent
args=[sys.executable,str(p/"run-selected.py"),"unit-focused-record-correction"]
for t in json.loads((p/"focused-selectors.json").read_text()): args += ["--test",t]
sys.exit(subprocess.run(args).returncode)

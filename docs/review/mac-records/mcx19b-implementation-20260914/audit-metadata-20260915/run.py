import subprocess,sys
from pathlib import Path
cmd=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3', 'LOCAL_HOME/Developer/sqe-platform-audit-metadata/tools/ace_ios_local.py', '--evidence-root', 'LOCAL_HOME/ace-private/mcx19b-implementation-20260914/audit-metadata-20260915/runs', 'selected', '--diagnostic-dirty', '--device', 'iPhone 17 Pro Max', '--test', 'ACEClientAppUITests/ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls', '--test-env-json', 'LOCAL_HOME/ace-private/mcx19b-implementation-20260914/audit-metadata-20260915/light.json']
sys.exit(subprocess.run(cmd,cwd='LOCAL_HOME/Developer/sqe-platform-audit-metadata').returncode)

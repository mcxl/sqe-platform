from pathlib import Path
import subprocess,sys,json,datetime
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/native-list-comparison-20260915')
variant,label=sys.argv[1:3]
assert variant in ['control','trial']
assert label.replace('-','').replace('_','').isalnum()
repo=Path('LOCAL_HOME/Developer/sqe-platform-native-list-'+variant)
cmd=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3',str(repo/'tools/ace_ios_local.py'),'--evidence-root',str(base/(variant+'-runs')),'selected','--diagnostic-dirty','--device','iPhone 17 Pro Max']+sys.argv[3:]
record={'variant':variant,'label':label,'command':cmd,'startUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(base/(variant+'-'+label+'-command.json')).write_text(json.dumps(record,indent=2)+'\n')
p=subprocess.run(cmd,cwd=repo)
record.update(endUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit=p.returncode)
(base/(variant+'-'+label+'-command.json')).write_text(json.dumps(record,indent=2)+'\n')
sys.exit(p.returncode)

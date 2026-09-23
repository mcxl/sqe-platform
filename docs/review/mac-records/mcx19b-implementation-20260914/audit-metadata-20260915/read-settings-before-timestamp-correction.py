from pathlib import Path
import importlib.util,sys,json,datetime
repo=Path('LOCAL_HOME/Developer/sqe-platform-audit-metadata')
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/audit-metadata-20260915')
spec=importlib.util.spec_from_file_location('ace_metadata_runner',repo/'tools/ace_ios_local.py')
runner=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=runner
spec.loader.exec_module(runner)
manifest=json.loads((base/'runs/20260914T220936Z-selected-5d3c95e880df/manifest.json').read_text())
candidate=runner.candidate(allow_dirty=True)
assert candidate==manifest['candidate'], 'Candidate changed'
environment=runner.preflight()
assert runner.environment_identity(environment)==runner.environment_identity(manifest['environment']), 'Environment changed'
build=runner.reuse_build(candidate,manifest)
record={'candidate':candidate,'environment':environment,'buildIdentity':build['identity'],'request':{'mode':'read'},'startUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
 record['observed']=runner.native_flags('D1BAA05C-52DD-4E57-832F-C0A75718E085',Path(build['template']),base,'metadata-read',{'mode':'read'})
 assert runner.candidate(allow_dirty=True)==candidate, 'Candidate changed during read'
 record['status']='passed'
except Exception as error:
 record['status']='failed'
 record['error']=str(error)
 raise
finally:
 record['endUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (base/'settings-read-result.json').write_text(json.dumps(record,indent=2)+chr(10))
print(json.dumps({'status':record['status'],'observed':record.get('observed')}))

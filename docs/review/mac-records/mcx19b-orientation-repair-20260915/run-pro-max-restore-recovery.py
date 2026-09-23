from pathlib import Path
import importlib.util,sys,json,subprocess,datetime,os
os.umask(0o077)
s=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
r=s/'pilot-runs/20260915T064440Z-pilot-478288537d90'
repo=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
sp=importlib.util.spec_from_file_location('ace_restore',repo/'tools/ace_ios_local.py');m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)
out=s/'04-pro-max-restore-recovery';out.mkdir(mode=0o700,exist_ok=False)
c=m.candidate();assert c['commit']=='a84f67010362c9e87e49576af8cf40b2c23a807b' and c['status']=='clean'
assert not subprocess.run(['pgrep','-x','xcodebuild'],capture_output=True,text=True).stdout.strip()
record={'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':c,'status':'running','question':'Can original Pro Max settings be restored and observed after normal restart, with iPhone17 now shut down?','pilotCasesCredited':0}
identifier='D1BAA05C-52DD-4E57-832F-C0A75718E085'
try:
 assert m.simulator_state('2EB0863C-470E-467D-A0C6-CD216DA70C67')=='Shutdown'
 expected=m.marker_records(r/'native-settings/iPhone 17 Pro Max-read/native.log','ACE_SETTINGS_RESULT')[0]['observed'];record['expectedNativeFlags']=expected
 template=next((r/'build/Build/Products').glob('*.xctestrun'))
 m.boot_required_simulator(identifier,m.simulator_state(identifier))
 record['observedNativeFlags']=m.native_flags(identifier,template,out,'restore',{'mode':'set',**expected})
 assert record['observedNativeFlags']==expected
 record['observedSimctlSettings']=m.current_simctl_settings(identifier)
 prior=json.loads((r/'restoration/iPhone 17 Pro Max-simctl-readback.json').read_text())['expected']
 assert record['observedSimctlSettings']==prior
 record['status']='passed'
except Exception as e:record['status']='failed';record['error']=str(e)
finally:
 record['finalBootStates']={d:m.simulator_state(i) for d,i in [('iPhone 17','2EB0863C-470E-467D-A0C6-CD216DA70C67'),('iPhone 17 Pro Max',identifier),('unrelated iPhone 16 Pro Max','3BF9AAA5-33AA-4EF3-BFEC-65C83DF5D79F')]}
 record['candidateUnchanged']=m.candidate()==c;record['finishedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ['status','finalBootStates','candidateUnchanged']},indent=2),flush=True)
sys.exit(0 if record['status']=='passed' and record['candidateUnchanged'] else 2)

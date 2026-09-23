from pathlib import Path
import subprocess,json,time
p=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/native-copy-paste-probe-2')
record={'question':'Does the unchanged app copy expire from the simulator clipboard after the retained Copy action?','copyConfirmationCaptureTime':1789386045.34,'baseline':json.loads((p/'clipboard-post-probe-observation.json').read_text()),'reads':[],'acceptance':'Focused simulator observation only. The capture time is an upper bound on write time; physical and exact-boundary checks remain pending.'}
stop=time.monotonic()+150
while time.monotonic()<stop:
 r=subprocess.run(['xcrun','simctl','pbpaste','D1BAA05C-52DD-4E57-832F-C0A75718E085'],capture_output=True,timeout=15)
 row={'time':time.time(),'exit':r.returncode,'matchesExpectedFictionalValue':r.stdout.decode(errors='replace').rstrip('\n')=='Fictional Engagement','empty':len(r.stdout)==0}
 record['reads'].append(row);(p/'clipboard-expiry-observation.json').write_text(json.dumps(record,indent=2))
 if row['exit']!=0 or not(row['matchesExpectedFictionalValue'] or row['empty']):record['error']='Unexpected clipboard state';break
 if row['empty']:record['transitionObserved']=True;break
 time.sleep(5)
record['finished']=time.time();(p/'clipboard-expiry-observation.json').write_text(json.dumps(record,indent=2))
print(json.dumps({'transitionObserved':record.get('transitionObserved',False),'error':record.get('error'),'reads':len(record['reads']),'record':str(p/'clipboard-expiry-observation.json')}))

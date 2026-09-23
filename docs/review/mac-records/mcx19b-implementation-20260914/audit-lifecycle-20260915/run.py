from pathlib import Path
import subprocess,sys,json,datetime
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/audit-lifecycle-20260915')
repo=Path('LOCAL_HOME/Developer/sqe-platform-audit-lifecycle')
record={'startUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
logcmd=['xcrun','simctl','spawn','D1BAA05C-52DD-4E57-832F-C0A75718E085','log','stream','--level','debug','--style','json','--predicate','subsystem == "com.auditco.ace.audit-diagnostic"']
cmd=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3',str(repo/'tools/ace_ios_local.py'),'--evidence-root',str(base/'runs'),'selected','--diagnostic-dirty','--device','iPhone 17 Pro Max','--test','ACEClientAppUITests/ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls','--test-env-json',str(base/'light.json')]
record.update({'logCommand':logcmd,'testCommand':cmd})
(base/'run-command.json').write_text(json.dumps(record,indent=2)+chr(10))
with (base/'lifecycle.jsonlog').open('w') as out, (base/'lifecycle-stderr.log').open('w') as err:
 logger=subprocess.Popen(logcmd,stdout=out,stderr=err,text=True)
 record['loggerPid']=logger.pid
 try:
  result=subprocess.run(cmd,cwd=repo)
  record['runnerExit']=result.returncode
  record['loggerAliveUntilTestEnd']=logger.poll() is None
 finally:
  if logger.poll() is None:
   logger.terminate()
   try: logger.wait(timeout=15)
   except subprocess.TimeoutExpired:
    logger.kill()
    logger.wait()
  record['loggerExitAfterRequestedStop']=logger.returncode
  record['endUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  (base/'run-command.json').write_text(json.dumps(record,indent=2)+chr(10))
sys.exit(record.get('runnerExit',2))

import subprocess,sys
command = ["/Library/Frameworks/Python.framework/Versions/3.14/bin/python3", "LOCAL_HOME/Developer/sqe-platform-release-layout/tools/ace_ios_local.py", "--evidence-root", "LOCAL_HOME/ace-private/mcx19b-implementation-20260914/ace-ios-local-runs", "selected", "--diagnostic-dirty", "--device", "iPhone 17 Pro Max", "--test", "ACEClientAppUITests/ACEClientAppUITests/testAllReleaseClipboardValuesPasteExactly", "--test-env-json", "LOCAL_HOME/ace-private/mcx19b-implementation-20260914/native-eleven-clipboard-input.json"]
sys.exit(subprocess.run(command).returncode)

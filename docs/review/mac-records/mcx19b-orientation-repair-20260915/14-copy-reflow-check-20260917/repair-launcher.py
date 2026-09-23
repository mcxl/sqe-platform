from pathlib import Path
import hashlib, json

p = Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/14-copy-reflow-check-20260917/d2_execution.py')
s = p.read_text()
assert hashlib.sha256(p.read_bytes()).hexdigest() == '72059cbd651246b1d99c78ef364726acb3792b24bc22401f304784525329bd37'
p.with_name('d2_execution.pre-review.py').write_text(s)
start = s.index('def check_build(')
end = s.index('\ndef run_command(', start)
s = s[:start] + '''def check_build(record_path: Path, runner: Any) -> dict[str, Any]:
    record = read_json(record_path)
    candidate = "52b212aca02190ee0e742debe383fa6016fe36b9"
    worktree = Path("LOCAL_HOME/Developer/sqe-platform-d2-reflow-20260917")
    assert record["exit"] == 0 and not record["timedOut"] and record["candidate"] == candidate
    assert record["appSourcesVerifiedAfterBuild"] is True
    template = Path(record["template"])
    assert sha256(template) == record["templateSha256"]
    source = record["source"]
    assert len(source["appSources"]) == 9
    for rel, digest in source["appSources"].items():
        assert sha256(worktree / rel) == digest, rel
    assert sha256(worktree / "ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift") == source["testSourceSha256"]
    assert sha256(ROOT / "D2-test.patch") == record["patchSha256"] == source["patchSha256"]
    assert subprocess.check_output(["git", "-C", str(worktree), "rev-parse", "HEAD"], text=True).strip() == candidate
    bundles = {}
    for key in ("appBundle", "testBundle"):
        item = record[key]
        directory = Path(item["path"])
        files = {f.relative_to(directory).as_posix(): sha256(f) for f in sorted(directory.rglob("*")) if f.is_file()}
        assert files == item["files"] and files, key
        digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert digest == item["sha256"], key
        bundles[key] = {"path": str(directory), "sha256": digest, "hashMethod": item["hashMethod"]}
    return {"recordPath": str(record_path), "recordSha256": sha256(record_path),
            "template": str(template), "templateSha256": sha256(template), **bundles,
            "source": source, "patchSha256": record["patchSha256"], "candidate": candidate,
            "runnerPath": str(Path(runner.__file__).resolve()), "runnerSha256": sha256(Path(runner.__file__))}

''' + s[end:]
# Only the native command uses this log argument. Stream it durably during execution.
needle = '    started = time.monotonic()\n    started_at = now()\n    try:\n'
replacement = '''    started = time.monotonic()
    started_at = now()
    if log is not None:
        with log.open("w", encoding="utf-8") as stream:
            process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            timed_out = False
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            stream.flush()
            os.fsync(stream.fileno())
        return {"command": command, "start": started_at, "end": now(), "exit": process.returncode,
                "timedOut": timed_out, "seconds": round(time.monotonic() - started, 3)}
    try:
'''
assert s.count(needle) == 1
s = s.replace(needle, replacement)
s = s.replace('    current: dict[str, Any] | None = None\n', '    current: dict[str, Any] | None = None\n')
s = s.replace('        for marker in MARKERS:\n', '''        if current is not None and "Accessibility audit failed for copyConfirmation initial:" in line:
            current["error"] = line
        for marker in MARKERS:
''')
s = s.replace('            except json.JSONDecodeError:\n                continue\n', '            except json.JSONDecodeError as error:\n                raise ValueError("Malformed diagnostic marker: " + line) from error\n')
s = s.replace('                calls.append(item)\n', '''                if current and current.get("error"):
                    item["error"] = current["error"]
                calls.append(item)
''')
s = s.replace('        if index >= 2 and prior == NAMES[index - 1] and gate_file(prior) is None:', '        if prior == NAMES[index - 1] and gate_file(prior) is None:')
s = s.replace('        if settings_exact and initial_states.get(identifier) == "Shutdown" and current == "Booted":', '        if initial_states.get(identifier) == "Shutdown" and current == "Booted":')
needle = '    require_ledger(args.execution)\n'
s = s.replace(needle, '''    expected_arm = "X" if args.execution == "03-arm-X" else "Y"
    if args.arm != expected_arm:
        die("Arm does not match the fixed execution order")
    if any((ROOT / name).exists() for name in NAMES[NAMES.index(args.execution):]):
        die("This or a later execution directory already exists")
    if dt.datetime.now(dt.timezone.utc) >= dt.datetime(2026, 9, 17, 4, 2, 2, tzinfo=dt.timezone.utc):
        die("Insufficient time before D2 hard deadline to start a new execution")
    require_ledger(args.execution)
''')
settings = '''        original_settings = {name: setting(TARGET, name) for name in ("appearance", "content_size", "increase_contrast")}
        record["originalSimctlSettings"] = original_settings
        write_json(target_dir / "execution.json", record)
'''
assert settings in s
s = s.replace(settings, '')
needle = '        runfile = target_dir / "ACEClientAppUITests.xctestrun"\n'
s = s.replace(needle, settings + '''        if "unknown" in original_settings.values():
            die("Booted simulator settings are unavailable")
''' + needle)
s = s.replace('        if any(actual_env.get(k) != v for k, v in env.items()):', '        if any(actual_env.get(k) != v for k, v in env.items()) or (not args.force_fail and "ACE_D2_FORCE_FAIL" in actual_env) or "ACE_UI_TEST_APPEARANCE" in actual_env:')
s = s.replace('        record["nativeOutcome"] = "PASS" if isinstance(summary, dict) and summary.get("result") == "Passed" else "FAIL"', '        record["nativeOutcome"] = {"Passed": "PASS", "Failed": "FAIL"}.get((summary or {}).get("result"), "UNKNOWN")')
start = s.index('        record["mechanicalGateSuccess"] = method_proof_ok')
end = s.index('        record["status"] = "completed"', start)
s = s[:start] + '''        stop_records = [json.loads(line.split("ACE_D2_STOP ", 1)[1]) for line in raw_markers if "ACE_D2_STOP " in line]
        record["stopRecords"] = stop_records
        numbers = [call.get("call") for call in calls]
        contiguous = bool(numbers) and numbers == list(range(len(calls)))
        full_count = numbers == list(range(args.max_calls + 1))
        copy_stop = bool(stop_records and calls and stop_records[-1].get("call") == calls[-1].get("call")
                         and stop_records[-1].get("reason") == "Copy contrast finding")
        no_errors = all(not call.get("error") for call in calls) and not native.get("timedOut")
        call0_ok = bool(calls and calls[0].get("helperReturned") is True)
        # A native genuine call0 issue may leave helperReturned true while recording failure; retained separately.
        record["settingsRecords"] = [json.loads(line.split("ACE_D2_SETTINGS ", 1)[1])
                                     for line in native_log.read_text().splitlines() if "ACE_D2_SETTINGS " in line]
        expected_settings = {"appearance":"light", "contentSize":"large", "orientation":"portrait",
                             "boldText":False, "reduceMotion":False, "increaseContrast":False}
        settings_ok = len(record["settingsRecords"]) == 1 and record["settingsRecords"][0].get("observed") == expected_settings
        attachment_files_ok = isinstance(manifest_entries, list) and len(manifest_entries) == 1
        attachment_inventory = []
        for entry in manifest_entries or []:
            for item in entry.get("attachments", []):
                file = attachments / item.get("exportedFileName", "")
                valid = file.is_file() and file.stat().st_size > 0
                if valid and file.suffix.lower() == ".png":
                    valid = file.read_bytes()[:8] == b"\\x89PNG\\r\\n\\x1a\\n"
                attachment_files_ok = attachment_files_ok and valid
                attachment_inventory.append({"file": str(file), "name": item.get("suggestedHumanReadableName"),
                                             "valid": valid, "sha256": sha256(file) if valid else None})
        record["attachments"]["inventory"] = attachment_inventory
        artifacts_ok = bool(record["methodProof"]["exactlyOne"] and result_bundle.is_dir()
                            and summary_cmd.get("exit") == 0 and tests_cmd.get("exit") == 0
                            and attach_cmd.get("exit") == 0 and record["attachments"]["manifestExactMethod"]
                            and attachment_files_ok and attachment_inventory and settings_ok)
        native_ok = native.get("exit") in (0, 65) and record["nativeOutcome"] in ("PASS", "FAIL")
        base_gate = artifacts_ok and native_ok and no_errors and call0_ok and contiguous
        if args.execution in NAMES[:2]:
            failures = _failure_texts(summary)
            clean_calls = all(not call.get("resolvedIssues") and not call.get("error") for call in calls)
            clean_calls = clean_calls and calls[0].get("nativeFailureCountDelta") == 0 if calls else False
            if args.execution == NAMES[0]:
                outcome_ok = native.get("exit") == 65 and record["nativeOutcome"] == "FAIL" and failures == ["D2 deliberate harness failure"]
            else:
                outcome_ok = native.get("exit") == 0 and record["nativeOutcome"] == "PASS" and not failures
            record["mechanicalGateSuccess"] = bool(base_gate and full_count and clean_calls and outcome_ok and not stop_records)
        else:
            count_ok = full_count or (copy_stop and 1 <= len(calls) - 1 <= args.max_calls)
            record["mechanicalGateSuccess"] = bool(base_gate and count_ok)
        record["gateChecks"] = {"artifacts": artifacts_ok, "native": native_ok, "noErrors": no_errors,
                                "call0Returned": call0_ok, "contiguous": contiguous, "fullCount": full_count,
                                "copyStop": copy_stop, "settings": settings_ok}
''' + s[end:]
s = s.replace('        if initial_states and original_settings:\n', '        if initial_states:\n')
s = s.replace('    if failed:\n        return 2\n    return 0\n', '    if failed or record.get("mechanicalGateSuccess") is not True:\n        return 2\n    return 0\n')
p.write_text(s)
compile(s, str(p), 'exec')
print(hashlib.sha256(p.read_bytes()).hexdigest())

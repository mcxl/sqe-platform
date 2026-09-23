import hashlib, pathlib, sys
actual = hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest()
expected = sys.argv[2]
print("expected=" + expected + " actual=" + actual)
raise SystemExit(0 if actual == expected else 1)

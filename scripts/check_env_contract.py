#!/usr/bin/env python3
# Validate that docs/env.contract.json keys are represented in the example env files
# without requiring real secrets.

import json, os, sys, glob

CONTRACT_PATH = os.path.join("docs", "env.contract.json")

def _load_contract():
    if not os.path.exists(CONTRACT_PATH):
        print(f"SKIP: {CONTRACT_PATH} not found; nothing to validate.")
        return None
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _collect_env_examples():
    candidates = [".env.example", ".env.example.phase1", ".env.sample"]
    found = []
    for c in candidates:
        if os.path.exists(c):
            found.append(c)
    found.extend(glob.glob("docs/*.env*example*"))
    return list(dict.fromkeys(found))

def _keys_in_file(fn):
    keys = set()
    try:
        with open(fn, "r", encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k = line.split("=", 1)[0].strip()
                    if k:
                        keys.add(k)
    except Exception as e:
        print(f"WARN: failed to read {fn}: {e}")
    return keys

def main():
    contract = _load_contract()
    if not contract:
        sys.exit(0)

    required = set(contract.get("required", []))
    if not required:
        print("SKIP: no 'required' keys specified in env.contract.json")
        sys.exit(0)

    examples = _collect_env_examples()
    if not examples:
        print("FAIL: no .env example file found. Provide .env.example with all required keys.")
        sys.exit(2)

    union = set()
    for e in examples:
        union |= _keys_in_file(e)

    missing = sorted(required - union)
    if missing:
        print("FAIL: the following required env keys are not present in any example env file:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(3)

    print("PASS: All required env keys are represented in example env files.")
    sys.exit(0)

if __name__ == "__main__":
    main()

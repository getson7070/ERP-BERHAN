import sys, subprocess, shlex, re
def sh(cmd):
    p = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()
def main():
    rc, out, err = sh('flask db heads -v')
    if rc != 0: print(err or out, file=sys.stderr); sys.exit(2)
    heads = re.findall(r'^\s*([0-9a-f]+)\s+\(head\)', out, flags=re.MULTILINE)
    if len(heads) <= 1: print('OK: single head'); return
    print('Multi-head detected:', heads)
    rc2, out2, err2 = sh('alembic merge -m "auto-merge branches" ' + ' '.join(heads))
    if rc2 != 0: print(err2 or out2, file=sys.stderr); sys.exit(3)
    rc3, out3, err3 = sh('flask db upgrade')
    if rc3 != 0: print(err3 or out3, file=sys.stderr); sys.exit(4)
    print('Merged and upgraded OK')
if __name__ == '__main__': main()
#!/usr/bin/env python3
"""
verify_xkb.py - prove that linux/aek leaves the base layout alone.

Compiles plain ara(basic) and AEK with xkbcomp and compares every key:
  * levels 1-2 (the Arabic 101 layer) must be identical, except Space level 2 (ZWNJ);
  * levels 3-4 may change only on the keys/levels that layout/aek.json declares;
  * any base symbol that AEK displaces is listed, so it is a conscious choice.
Needs xkbcomp and the xkb-data package. Exit code 1 on any unexpected change.

License: MIT (see LICENSE).
"""
import json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XKB = "/usr/share/X11/xkb"
KEYMAP = ('xkb_keymap { xkb_keycodes { include "evdev+aliases(qwerty)" };'
          ' xkb_types { include "complete" }; xkb_compat { include "complete" };'
          ' xkb_symbols { include "%s" }; };')


def compile_keymap(tmp, name, symbols):
    src, out = os.path.join(tmp, name + ".xkb"), os.path.join(tmp, name + ".out")
    open(src, "w").write(KEYMAP % symbols)
    subprocess.run(["xkbcomp", "-w", "0", "-I" + tmp, "-I" + XKB, "-xkb", src, out],
                   check=True, capture_output=True)
    return open(out, encoding="utf-8").read()


def levels(text):
    keys = {}
    for m in re.finditer(r"key <(\w+)>\s*\{(.*?)\};", text, re.S):
        body = m.group(2)
        lv = re.search(r"symbols\[Group1\]\s*=\s*\[([^\]]*)\]", body) or re.match(r"\s*\[([^\]]*)\]", body)
        if lv:
            s = [x.strip() for x in lv.group(1).split(",")]
            keys[m.group(1)] = (s + ["NoSymbol"] * 4)[:4]
    return keys


def main():
    spec = json.load(open(os.path.join(ROOT, "layout", "aek.json"), encoding="utf-8"))
    lvl = {n: v["xkb_level"] for n, v in spec["layers"].items()}
    allowed = {(e["xkb"], lvl[e["layer"]]) for e in spec["entries"] if len(e["codepoints"]) == 1}
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "symbols"))
        open(os.path.join(tmp, "symbols", "aek"), "w").write(open(os.path.join(ROOT, "linux", "aek")).read())
        base = levels(compile_keymap(tmp, "base", "pc+ara(basic)+level3(ralt_switch)+inet(evdev)"))
        aek = levels(compile_keymap(tmp, "aek", "pc+aek+inet(evdev)"))
    bad, displaced = [], []
    for k in sorted(base):
        for i in range(4):
            b, a = base[k][i], aek[k][i]
            if b == a:
                continue
            if (k, i + 1) not in allowed:
                bad.append((k, i + 1, b, a))
            elif b != "NoSymbol":
                displaced.append((k, i + 1, b, a))
    print("keys compared:", len(base))
    for k, l, b, a in displaced:
        print("  displaced base symbol: <%s> level %d: %s -> %s" % (k, l, b, a))
    for k, l, b, a in bad:
        print("  UNEXPECTED CHANGE: <%s> level %d: %s -> %s" % (k, l, b, a))
    print("FAIL" if bad else "OK: everything outside the declared AEK slots is identical to ara(basic)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

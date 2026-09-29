#!/usr/bin/env python3
"""
build_aek.py - generate AEK layout files from aek.json (the single source of truth).
License: MIT (see LICENSE).

  python3 build_aek.py xkb                 -> aek (XKB symbols file)
  python3 build_aek.py xcompose            -> aek.XCompose (multi-character keys)
  python3 build_aek.py klc --base A.klc    -> aek.klc (MSKLC / KbdEdit source)
  python3 build_aek.py all --base A.klc

The Windows step needs a base file: in MSKLC use File > Load Existing Keyboard >
Arabic (101), then File > Save Source File As... (gives A.klc). The script overlays
only the AEK entries on that file, so the Arabic 101 base layer stays exactly as
Microsoft ships it.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "aek.json"), encoding="utf-8"))
ENTRIES = DATA["entries"]
LAYERS = DATA["layers"]


def chars(entry):
    return "".join(chr(int(cp, 16)) for cp in entry["codepoints"])


# ---------------------------------------------------------------- XKB
def gen_xkb():
    """Single-code-point entries only; XKB cannot emit sequences (see XCompose)."""
    keys = {}
    for e in ENTRIES:
        if len(e["codepoints"]) != 1:
            continue
        lvl = LAYERS[e["layer"]]["xkb_level"]
        keys.setdefault(e["xkb"], {})[lvl] = "U" + e["codepoints"][0]
    out = [
        "// AEK v%s - Arabic-Extended Keyboard. GENERATED from aek.json; do not edit." % DATA["version"],
        "// SPDX-License-Identifier: MIT - Copyright (c) 2026 Diaa Hassouna",
        "// Install: copy to /usr/share/X11/xkb/symbols/aek (or ~/.config/xkb/symbols/aek)",
        "// Use:     setxkbmap -layout aek -option compose:rctrl",
        "default partial alphanumeric_keys",
        'xkb_symbols "basic" {',
        '    include "ara(basic)"',
        '    include "level3(ralt_switch)"',
        '    name[Group1] = "Arabic (Extended, AEK)";',
        "",
    ]
    for name, levels in sorted(keys.items()):
        n = max(levels)
        syms = [levels.get(i, "NoSymbol") for i in range(1, n + 1)]
        typ = "TWO_LEVEL" if n == 2 else "FOUR_LEVEL"
        out.append('    key <%s> { type[Group1] = "%s", [ %s ] };' % (name, typ, ", ".join(syms)))
    out.append("};")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- XCompose
KEYSYM = {"0627": "Arabic_alef", "064A": "Arabic_yeh", "0648": "Arabic_waw"}


def gen_xcompose():
    out = [
        "# AEK v%s - multi-character keys for Linux. GENERATED from aek.json." % DATA["version"],
        "# SPDX-License-Identifier: MIT - Copyright (c) 2026 Diaa Hassouna",
        "# Install as ~/.XCompose. Press Compose (Right Ctrl with compose:rctrl), then the letter twice.",
        'include "%L"',
        "",
    ]
    for e in ENTRIES:
        if len(e["codepoints"]) > 1:
            k = KEYSYM[e["codepoints"][0]]
            out.append('<Multi_key> <%s> <%s> : "%s"   # %s' % (k, k, chars(e), e["unicode_name"]))
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- MSKLC
SECTIONS = {"SHIFTSTATE", "LAYOUT", "DEADKEY", "LIGATURE", "KEYNAME", "KEYNAME_EXT",
            "KEYNAME_DEAD", "DESCRIPTIONS", "LANGUAGENAMES", "ATTRIBUTES", "ENDKBD"}


def read_klc(path):
    raw = open(path, "rb").read()
    enc = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    return raw.decode(enc).replace("\r\n", "\n").split("\n")


def write_klc(path, lines):
    with open(path, "w", encoding="utf-16", newline="") as f:  # BOM + UTF-16, as MSKLC expects
        f.write("\r\n".join(lines))


def first_token(line):
    s = line.split("//")[0].strip()
    return s.split()[0] if s else ""


def patch_klc(base, out_path):
    lines = read_klc(base)
    # split into (section, lines) blocks; header lines belong to section ""
    blocks, cur, cur_lines = [], "", []
    for ln in lines:
        tok = first_token(ln)
        if tok in SECTIONS and ln.strip().split()[0] == tok:
            blocks.append([cur, cur_lines])
            cur, cur_lines = tok, [ln]
        else:
            cur_lines.append(ln)
    blocks.append([cur, cur_lines])
    get = lambda name: next((b for b in blocks if b[0] == name), None)

    # header: KBD line
    hdr = get("")
    for i, ln in enumerate(hdr[1]):
        if ln.startswith("KBD"):
            hdr[1][i] = 'KBD\taek\t"Arabic Extended (AEK)"'
        elif ln.startswith("COPYRIGHT"):
            hdr[1][i] = 'COPYRIGHT\t"(c) 2026 Diaa Hassouna, MIT License"'

    # shift states
    ss = get("SHIFTSTATE")
    states = [int(first_token(l)) for l in ss[1][1:] if first_token(l).isdigit()]
    old_states = list(states)
    for need in (1, 6, 7):
        if need not in states:
            states.append(need)
    states.sort()
    ss[1] = ["SHIFTSTATE", ""] + ["%d\t//Column %d" % (s, i + 4) for i, s in enumerate(states)] + [""]

    # layout rows
    lay = get("LAYOUT")
    rows, order = {}, []
    for ln in lay[1][1:]:
        toks = ln.split("//")[0].split()
        if len(toks) >= 3 and re.fullmatch(r"[0-9A-Fa-f]{2}", toks[0]):
            vals = toks[3:]
            vals += ["-1"] * (len(old_states) - len(vals))
            cells = dict(zip(old_states, vals))
            rows[toks[0].upper()] = {"vk": toks[1], "cap": toks[2], "cells": cells}
            order.append(toks[0].upper())
    lig = []
    for e in ENTRIES:
        sc, st = e["sc"].upper(), LAYERS[e["layer"]]["klc_state"]
        if sc not in rows:
            sys.exit("base layout has no row for scancode %s (%s)" % (sc, e["id"]))
        r = rows[sc]
        if r["vk"] != e["vk"]:
            print("warning: scancode %s is VK_%s in the base, expected VK_%s" % (sc, r["vk"], e["vk"]))
        prev = r["cells"].get(st, "-1")
        if prev not in ("-1", "", "%%"):
            print("note: overwrote base cell %s (state %d) (was %s) with %s" % (e["vk"], st, prev, e["id"]))
        if len(e["codepoints"]) == 1:
            r["cells"][st] = e["codepoints"][0].lower()
        else:
            r["cells"][st] = "%%"
            lig.append((e["vk"], st, [c.lower() for c in e["codepoints"]]))
    body = ["LAYOUT", "", "//SC\tVK_\t\tCap\t" + "\t".join(str(s) for s in states), ""]
    for sc in order:
        r = rows[sc]
        cells = [r["cells"].get(s, "-1") for s in states]
        body.append("\t".join([sc, r["vk"], r["cap"]] + cells))
    body.append("")
    lay[1] = body

    # ligatures
    lg = get("LIGATURE")
    if lg is None:
        lg = ["LIGATURE", [""]]
        blocks.insert(blocks.index(lay) + 1, lg)
    lg[1] = ["LIGATURE", "", "//VK_\tMod#\tChar0\tChar1\tChar2\tChar3", "//----\t----\t-----\t-----\t-----\t-----"] + \
            ["\t".join([vk, str(st)] + cs) for vk, st, cs in lig] + [""]

    # description
    ds = get("DESCRIPTIONS")
    if ds:
        ds[1] = [ds[1][0]] + [l if not l.strip() else l.split("\t")[0] + "\tArabic Extended (AEK)" for l in ds[1][1:]]

    flat = [ln for _, ls in blocks for ln in ls]
    write_klc(out_path, flat)
    print("wrote", out_path)


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", choices=["xkb", "xcompose", "klc", "all"])
    ap.add_argument("--base", help="Arabic 101 .klc exported from MSKLC")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    if a.target in ("xkb", "all"):
        open(os.path.join(a.out, "aek"), "w", encoding="utf-8").write(gen_xkb()); print("wrote aek")
    if a.target in ("xcompose", "all"):
        open(os.path.join(a.out, "aek.XCompose"), "w", encoding="utf-8").write(gen_xcompose()); print("wrote aek.XCompose")
    if a.target in ("klc", "all"):
        if not a.base:
            sys.exit("--base is required for klc")
        patch_klc(a.base, os.path.join(a.out, "aek.klc"))


if __name__ == "__main__":
    main()

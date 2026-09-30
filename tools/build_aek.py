#!/usr/bin/env python3
"""
build_aek.py - generate the AEK layout files from layout/aek.json (the single source of truth).

Run it from anywhere:
  python tools/build_aek.py xkb                 -> linux/aek
  python tools/build_aek.py xcompose            -> linux/aek.XCompose
  python tools/build_aek.py klc --base A.klc    -> windows/AEK.klc
  python tools/build_aek.py all --base A.klc

Add --out DIR to write into one flat folder instead. For klc, --with-helpers also adds the
three long-vowel keys as ligatures (experimental, untested in MSKLC).

The Windows step needs a base file: in MSKLC use File > Load Existing Keyboard >
Arabic (101), then File > Save Source File As... (gives A.klc). The script overlays
only the AEK entries on that file, so the Arabic 101 base layer stays exactly as
Microsoft ships it. Then open windows/AEK.klc in MSKLC and build the package.

License: MIT (see LICENSE).
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = json.load(open(os.path.join(ROOT, "layout", "aek.json"), encoding="utf-8"))
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
        # No explicit type: an explicit type[Group1] makes xkbcomp discard the base key's
        # other levels (e.g. the RLM that ara(basic) keeps on Shift+AltGr+[). Only the
        # Space key needs one, because its base type is single-level.
        typ = 'type[Group1] = "TWO_LEVEL", ' if name == "SPCE" else ""
        out.append("    key <%s> { %s[ %s ] };" % (name, typ, ", ".join(syms)))
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


def patch_klc(base, out_path, helpers=False):
    """Overlay the AEK entries on an MSKLC source file. Everything not touched
    (comments, dead keys, existing ligatures such as lam-alef, key names) is kept."""
    lines = read_klc(base)
    blocks, cur, cur_lines = [], "", []
    for ln in lines:
        tok = first_token(ln)
        if tok in SECTIONS:
            blocks.append([cur, cur_lines])
            cur, cur_lines = tok, [ln]
        else:
            cur_lines.append(ln)
    blocks.append([cur, cur_lines])
    get = lambda name: next((b for b in blocks if b[0] == name), None)

    hdr = get("")
    for i, ln in enumerate(hdr[1]):
        if ln.startswith("KBD") and "AEK" not in ln.upper():
            hdr[1][i] = 'KBD\tAEK\t"Arabic (101) - Extended"'
        elif ln.startswith("COPYRIGHT") and "Hassouna" not in ln:
            hdr[1][i] = 'COPYRIGHT\t"(c) 2026 Diaa Hassouna, MIT License"'

    # --- shift states: keep the base's lines, add 1/6/7 if missing
    ss = get("SHIFTSTATE")
    state_line = {int(first_token(l)): l for l in ss[1][1:] if first_token(l).isdigit()}
    old_states = [int(first_token(l)) for l in ss[1][1:] if first_token(l).isdigit()]
    new_states = sorted(set(old_states) | {1, 6, 7})
    added = [s for s in new_states if s not in old_states]
    ss[1] = ["SHIFTSTATE", ""] + [state_line.get(s, "%d\t//Column %d" % (s, i + 4))
                                 for i, s in enumerate(new_states)] + [""]

    # --- layout: parse rows, keep every other line (comments, blanks) as it is
    lay = get("LAYOUT")
    items, rows = [], {}
    for ln in lay[1]:
        body, _, comment = ln.partition("//")
        toks = body.split()
        if len(toks) >= 3 and re.fullmatch(r"[0-9A-Fa-f]{2}", toks[0]):
            vals = (toks[3:] + ["-1"] * len(old_states))[:len(old_states)]
            rows[toks[0].upper()] = {"sc": toks[0], "vk": toks[1], "cap": toks[2], "comment": comment,
                                     "cells": dict(zip(old_states, vals))}
            items.append(toks[0].upper())
        else:
            items.append(ln)

    lig_new, skipped = [], 0
    for e in ENTRIES:
        sc, st = e["sc"].upper(), LAYERS[e["layer"]]["klc_state"]
        multi = len(e["codepoints"]) > 1
        if e.get("klc") is False:
            print("note: %s not added on Windows (%s)" % (e["id"], e.get("windows_note", "")))
            continue
        if multi and not helpers:
            skipped += 1
            continue
        if sc not in rows:
            sys.exit("base layout has no row for scancode %s (%s)" % (sc, e["id"]))
        r = rows[sc]
        if r["vk"] != e["vk"]:
            print("warning: scancode %s is VK_%s in the base, expected VK_%s" % (sc, r["vk"], e["vk"]))
        prev = r["cells"].get(st, "-1")
        if prev not in ("-1", "", "%%"):
            print("note: overwrote base cell %s (state %d) (was %s) with %s" % (e["vk"], st, prev, e["id"]))
        if prev == "%%":
            sys.exit("base cell %s (state %d) is already a ligature; refusing to overwrite it" % (e["vk"], st))
        if multi:
            r["cells"][st] = "%%"
            lig_new.append((e["vk"], st, [c.lower() for c in e["codepoints"]]))
        else:
            r["cells"][st] = e["codepoints"][0].lower()

    out_lay = []
    for it in items:
        if it in rows:
            r = rows[it]
            row = "\t".join([r["sc"], r["vk"], r["cap"]] + [r["cells"].get(s, "-1") for s in new_states])
            if r["comment"].strip():
                row += "\t//" + r["comment"].rstrip()
            out_lay.append(row)
        else:
            out_lay.append(it)
    lay[1] = out_lay

    # --- ligatures: keep the base's (Arabic 101 has lam-alef), append ours only if asked
    lg = get("LIGATURE")
    if lig_new:
        if lg is None:
            lg = ["LIGATURE", ["LIGATURE", "", "//VK_\tMod#\tChar0\tChar1\tChar2\tChar3", ""]]
            blocks.insert(blocks.index(lay) + 1, lg)
        have = {tuple(l.split("//")[0].split()[:2]) for l in lg[1] if first_token(l) and first_token(l) != "LIGATURE"}
        end = max(i for i, l in enumerate(lg[1]) if l.strip()) + 1
        add = ["\t".join([vk, str(st)] + cs) for vk, st, cs in lig_new if (vk, str(st)) not in have]
        lg[1][end:end] = add

    # --- sanity check: every ligature cell needs a ligature row for its key
    lig_vks = {first_token(l) for l in (lg[1] if lg else []) if first_token(l) not in ("", "LIGATURE")}
    need = {r["vk"] for r in rows.values() if "%%" in r["cells"].values()}
    if need - lig_vks:
        print("WARNING: ligature cells without ligature rows for:", ", ".join(sorted(need - lig_vks)))

    # --- description
    ds = get("DESCRIPTIONS")
    if ds:
        ds[1] = [re.sub(r"^(\S+)\s+.*$", r"\1\tArabic (101) - Extended", l)
                 if re.match(r"^[0-9A-Fa-f]{4}\s", l) and "Extended" not in l else l
                 for l in ds[1]]

    write_klc(out_path, [ln for _, ls in blocks for ln in ls])
    print("base: %d keys, shift states %s, ligature rows kept: %d" % (
        len(rows), old_states, sum(1 for l in (lg[1] if lg else []) if first_token(l) not in ("", "LIGATURE"))))
    if added:
        print("note: added shift state(s) %s; if MSKLC reports a problem, send me A.klc" % added)
    if skipped:
        print("note: %d long-vowel key(s) not added on Windows (experimental: use --with-helpers)" % skipped)
    print("wrote", out_path)


# ---------------------------------------------------------------- CLI
def dest(out, folder, name):
    d = out or os.path.join(ROOT, folder)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", choices=["xkb", "xcompose", "klc", "all"])
    ap.add_argument("--base", help="Arabic 101 .klc exported from MSKLC")
    ap.add_argument("--with-helpers", action="store_true",
                    help="klc: also add the three long-vowel keys as ligatures (experimental, untested in MSKLC)")
    ap.add_argument("--out", help="write all outputs into this one folder instead of linux/ and windows/")
    a = ap.parse_args()
    if a.target in ("xkb", "all"):
        p = dest(a.out, "linux", "aek")
        open(p, "w", encoding="utf-8").write(gen_xkb()); print("wrote", p)
    if a.target in ("xcompose", "all"):
        p = dest(a.out, "linux", "aek.XCompose")
        open(p, "w", encoding="utf-8").write(gen_xcompose()); print("wrote", p)
    if a.target in ("klc", "all"):
        if not a.base:
            sys.exit("--base is required for klc")
        patch_klc(a.base, dest(a.out, "windows", "AEK.klc"), a.with_helpers)


if __name__ == "__main__":
    main()

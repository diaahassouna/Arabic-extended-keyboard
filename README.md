# Arabic-Extended Keyboard (AEK) v0.2

A unified alternative Arabic keyboard layout. It keeps the standard Arabic 101 layout untouched and adds, on the AltGr layers, the letters and marks needed to write the spoken varieties of Arabic (Egyptian, Lebanese, Iraqi and others) faithfully, in print and on screen.

It was designed to serve the three Arabic-script representations of the Masri Writing System (*El Abgadeyya El Maṣreyya*, by Diaa Hassouna, CC BY 4.0), and to stay useful for other dialects and languages that share these letters.

Author: Diaa Hassouna. Version 0.2, 29 September 2026.

## Files

| File | What it is |
|---|---|
| `aek.json` | The single source of truth: every added key, its code points, layer, key position and role. |
| `build_aek.py` | Generates the platform files from `aek.json`. |
| `aek` | Linux XKB symbols file (generated). |
| `aek.XCompose` | Linux Compose sequences for the three long-vowel keys (generated). |
| `README.md`, `README.txt` | This document, in two formats. |
| `LICENSE` | MIT License. |

The Windows file (`aek.klc`) is produced on your machine, see "Windows" below.

## Design principles

1. The base layer is untouched. Arabic 101 stays as it is, so muscle memory and hardware labels keep working.
2. Each new letter sits on the same physical key as its parent letter, one layer up (AltGr).
3. Additions live only on AltGr and Shift+AltGr, plus Shift+Space for ZWNJ.
4. Desktop keys and mobile long-press popups match, so each teaches the other.
5. Letters are encoded as letters, not as sounds. Each orthography decides the sound value.

## Layout

| Output | Code point | Key (Arabic 101 position) | Layer | Mobile |
|---|---|---|---|---|
| پ | U+067E | F (ب) | AltGr | long-press ب |
| چ | U+0686 | `[` (ج) | AltGr | long-press ج |
| ڤ | U+06A4 | T (ف) | AltGr | long-press ف |
| گ | U+06AF | `;` (ك) | AltGr | long-press ك |
| ۆ | U+06C6 | `,` (و) | AltGr | long-press و |
| ێ | U+06CE | D (ي) | AltGr | long-press ي |
| ژ | U+0698 | `.` (ز) | AltGr | long-press ز |
| ◌ۜ small high seen | U+06DC | S (س) | AltGr | harakat popup |
| ◌ٔ hamza above | U+0654 | X (ء) | AltGr | harakat popup |
| ٴ high hamza | U+0674 | X (ء) | Shift+AltGr | harakat popup |
| ـّْا (alef + shadda + sukūn) | U+0627 U+0651 U+0652 | H (ا) | Shift+AltGr | vowels popup |
| ـّْي (yeh + shadda + sukūn) | U+064A U+0651 U+0652 | D (ي) | Shift+AltGr | vowels popup |
| ـّْو (waw + shadda + sukūn) | U+0648 U+0651 U+0652 | `,` (و) | Shift+AltGr | vowels popup |
| ZWNJ | U+200C | Space | Shift | long-press space |

The standard harakat stay where Arabic 101 already has them.

## Who uses what

**Arabic-V** (vocalized Masri): U+06DC separates a consonantal و/ي from its fatha (*wa*, *ya*) and marks Cairene ث → /s/ and ذ → /z/. U+0654 marks Cairene ق → /ʔ/. Long vowels are a carrier letter with shadda and sukūn, which the three helper keys type in one stroke. Arabic-V does not use ۆ or ێ.

**Arabic-S and Arabic-P** (no diacritics): ۆ and ێ are the dedicated vowel letters. In Arabic-S, ێ is é /ɛ/ and ۆ is ou /o/; doubling gives the long vowel (ێێ, ۆۆ).

**Other varieties and languages:**
- گ is the /g/ of Iraqi and Gulf speech.
- چ and ژ serve loanwords in many dialects.
- پ and ڤ are the /p/ and /v/ of loanwords.
- ۆ and ێ are also standard letters in Kurdish and other languages.

In Masri, چ is /ʒ/ and ج is Cairene hard /g/; other varieties assign their own values to the same letters.

## Install

### Linux

1. Copy `aek` to `~/.config/xkb/symbols/aek` (or to `/usr/share/X11/xkb/symbols/` for all users).
2. Activate it: `setxkbmap -layout aek -option compose:rctrl`
3. Copy `aek.XCompose` to `~/.XCompose`.
4. For a long vowel, press Compose (Right Ctrl), then the same letter twice: ا ا, ي ي or و و.

### Windows (MSKLC or KbdEdit)

Microsoft's Arabic 101 base layer is not reproduced here, so the Windows file is built from your own copy of it.

1. In Microsoft Keyboard Layout Creator: File, Load Existing Keyboard, Arabic (101); then File, Save Source File As, `A.klc`.
2. Run: `python3 build_aek.py klc --base A.klc`
3. Open the resulting `aek.klc` in MSKLC and build the installer, or import it into KbdEdit.

The script overlays only the AEK entries, adds the AltGr columns if the base lacks them, and reports any base cell it overwrites. The long-vowel keys use MSKLC ligatures.

### Not yet available

macOS (Ukelele), Android (long-press layout) and iOS. `aek.json` already carries the mobile long-press mappings needed to generate them.

## Regenerating

    python3 build_aek.py xkb
    python3 build_aek.py xcompose
    python3 build_aek.py klc --base A.klc
    python3 build_aek.py all --base A.klc

Edit `aek.json`, never the generated files.

## Notes and limitations

- **Tested:** the XKB file compiles with `xkbcomp` on top of `ara(basic)` and resolves to the intended keys. The Windows patcher was tested on a synthetic base file only, not inside MSKLC.
- **U+0674 is a letter**, not a combining mark. It does not stack over the previous letter and it interrupts joining, so it is a secondary key. Use ZWNJ around it and test with your target fonts (Amiri, Scheherazade New, Noto Naskh Arabic).
- **U+0654 and NFC:** after ا, و or ي it recombines into أ, ؤ or ئ under NFC normalization. Arabic-V puts it only on ق, so this does not arise there.
- **Mark order** for Arabic-V is haraka, then shadda, then sukūn, then U+06DC.
- **Shift+Space** may clash with a layout-switching hotkey on some systems.
- **Yeh policy:** the keyboard emits ي (U+064A), never ى (U+0649) or Persian ی (U+06CC), in line with Arabic-V.
- **Base layers** differ slightly between Linux `ara(basic)` and Windows Arabic 101; AEK adds only new keys, so its additions sit on the same physical keys on both.

## License

MIT License, Copyright (c) 2026 Diaa Hassouna. See `LICENSE`. This covers the AEK layout files and the generator script; the Masri Writing System documentation it refers to remains under its own license (CC BY 4.0).

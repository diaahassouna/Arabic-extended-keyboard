# Arabic-Extended Keyboard (AEK)

A unified alternative Arabic keyboard layout. It keeps the standard Arabic 101 layout untouched and adds, on the AltGr layers, the letters and marks needed to write the spoken varieties of Arabic (Egyptian, Lebanese, Iraqi and others) faithfully, in print and on screen.

It was designed to serve the three Arabic-script representations of the Masri Writing System (*El Abgadeyya El Maṣreyya*, by Diaa Hassouna, CC BY 4.0): Arabic-V, Arabic-S and Arabic-P. It stays useful for other dialects and languages that share these letters.

Version 0.2 · Author: Diaa Hassouna · [MIT License](LICENSE)

## Install

### Windows (ready-made installer)

1. Download the whole `windows/installer` folder. Keep its contents together: the `.msi` files need the `amd64`, `i386` and `wow64` folders next to them.
2. Run `setup.exe` and approve the administrator prompt. The installer is not code-signed, so Windows SmartScreen may show "unrecognized app"; choose *More info*, then *Run anyway*.
3. Open *Settings → Time & language → Language & region*, add **Arabic (Egypt)** if it is not there, then *⋯ → Language options → Add a keyboard → Arabic (101) - Extended*.
4. Switch layouts with Win+Space.

The keyboard is registered under Arabic (Egypt) but types any Arabic variety. To remove it, uninstall *Arabic (101) - Extended* from *Settings → Apps*.

### Linux

1. Copy `linux/aek` to `~/.config/xkb/symbols/aek` (or to `/usr/share/X11/xkb/symbols/` for all users).
2. Activate it: `setxkbmap -layout aek -option compose:rctrl`
3. Copy `linux/aek.XCompose` to `~/.XCompose`.
4. For a long vowel, press Compose (Right Ctrl), then the same letter twice: ا ا, ي ي or و و.

### Not yet available

macOS (Ukelele), Android (long-press layout) and iOS. `layout/aek.json` already carries the mobile long-press mappings needed to generate them.

## Layout

AltGr is Right Alt. All additions sit on the same physical key as their parent letter, one layer up. The base Arabic 101 layer is untouched.

| Output | Code point | Key (Arabic 101 position) | Layer | Windows | Linux |
|---|---|---|---|---|---|
| پ | U+067E | F (ب) | AltGr | ✓ | ✓ |
| چ | U+0686 | `[` (ج) | AltGr | ✓ | ✓ |
| ڤ | U+06A4 | T (ف) | AltGr | ✓ | ✓ |
| گ | U+06AF | `;` (ك) | AltGr | ✓ | ✓ |
| ۆ | U+06C6 | `,` (و) | AltGr | ✓ | ✓ |
| ێ | U+06CE | D (ي) | AltGr | ✓ | ✓ |
| ژ | U+0698 | `.` (ز) | AltGr | ✓ | ✓ |
| ◌ۜ small high seen | U+06DC | S (س) | AltGr | ✓ | ✓ |
| ◌ٔ hamza above | U+0654 | X (ء) | AltGr | ✓ | ✓ |
| ٴ high hamza | U+0674 | X (ء) | Shift+AltGr | ✓ | ✓ |
| ـّْا (alef + shadda + sukūn) | U+0627 U+0651 U+0652 | Compose, ا, ا | | | ✓ |
| ـّْي (yeh + shadda + sukūn) | U+064A U+0651 U+0652 | Compose, ي, ي | | | ✓ |
| ـّْو (waw + shadda + sukūn) | U+0648 U+0651 U+0652 | Compose, و, و | | | ✓ |
| ZWNJ | U+200C | Shift+Space | Shift | Ctrl+Shift+2 (built in) | ✓ |

The standard harakat stay where Arabic 101 already has them. On mobile, the letters are planned as long-press popups on their parent letter (پ on چ , ب on ڤ , ج on گ , ف on ۆ , ك on ێ , و on ژ , ي on ز).

## Who uses what

**Arabic-V** (vocalized Masri): U+06DC separates a consonantal و/ي from its fatha (*wa*, *ya*) and marks Cairene ث → /s/ and ذ → /z/. U+0654 marks Cairene ق → /ʔ/. Long vowels are a carrier letter with shadda and sukūn, which the Compose sequences type in one go. Arabic-V does not use ۆ or ێ.

**Arabic-S and Arabic-P** (no diacritics): ۆ and ێ are the dedicated vowel letters. In Arabic-S, ێ is é /ɛ/ and ۆ is ou /o/; doubling gives the long vowel (ێێ, ۆۆ).

**Other varieties and languages:**
- گ is the /g/ of Iraqi and Gulf speech.
- چ and ژ serve loanwords in many dialects.
- پ and ڤ are the /p/ and /v/ of loanwords.
- ۆ and ێ are also standard letters in Kurdish and other languages.

In Masri, چ is /ʒ/ and ج is Cairene hard /g/; other varieties assign their own values to the same letters.

## Repository structure

```
arabic-extended-keyboard/
├── LICENSE
├── README.md
├── layout/
│   └── aek.json             source of truth: every added key, code points, layer, role
├── linux/
│   ├── aek                  XKB symbols file (generated)
│   └── aek.XCompose        Compose sequences for the long-vowel keys (generated)
├── windows/
│   ├── AEK.klc              MSKLC source: Arabic 101 + AEK (generated)
│   └── installer/           ready-to-run package built from AEK.klc
│       ├── setup.exe
│       ├── AEK_amd64.msi
│       ├── AEK_i386.msi
│       ├── amd64/  i386/  wow64/    AEK.dll for each architecture
│       └── README.txt
└── tools/
    └── build_aek.py         generates linux/ and windows/AEK.klc from layout/aek.json
```

## Building from source

Edit `layout/aek.json`, never the generated files. From the repository root:

```
python tools/build_aek.py xkb
python tools/build_aek.py xcompose
python tools/build_aek.py klc --base A.klc
python tools/build_aek.py all --base A.klc
```

(On Windows the command is usually `python`, not `python3`.)

The Windows step needs `A.klc`, your own copy of the Arabic 101 source file: in Microsoft Keyboard Layout Creator choose *File → Load Existing Keyboard → Arabic (101)*, then *File → Save Source File As…*. The script overlays only the AEK entries on it and keeps everything else, including the base's ligatures such as lam-alef. It adds the AltGr columns if the base lacks them and reports any base cell it overwrites.

To rebuild the installer, open `windows/AEK.klc` in MSKLC and choose *Project → Build DLL and Setup Package*.

The three long-vowel keys are not added on Windows by default; `--with-helpers` adds them as MSKLC ligatures, but that option is experimental and untested.

## Notes and limitations

- **Tested:** the XKB file compiles with `xkbcomp` on top of `ara(basic)` and resolves to the intended keys. `windows/AEK.klc` was built into the installer with MSKLC, and the built DLLs contain all ten added characters.
- **ZWNJ on Windows:** MSKLC accepts only whitespace on the Space key, so the Windows layout has no Shift+Space ZWNJ. Use Ctrl+Shift+2, which Arabic 101 already provides. On Linux, Shift+Space may clash with a layout-switching hotkey on some systems.
- **MSKLC warnings:** the verifier warns that ۆ ێ پ ڤ ◌ۜ ◌ٔ ٴ are outside code page 1256. That only affects non-Unicode legacy applications and does not block the build.
- **U+0674 is a letter**, not a combining mark. It does not stack over the previous letter and it interrupts joining, so it is a secondary key. Use ZWNJ around it and test with your target fonts (Amiri, Scheherazade New, Noto Naskh Arabic).
- **U+0654 and NFC:** after ا, و or ي it recombines into أ, ؤ or ئ under NFC normalization. Arabic-V puts it only on ق, so this does not arise there.
- **Mark order** for Arabic-V: haraka, then shadda, then sukūn, then U+06DC.
- **Yeh policy:** the keyboard emits ي (U+064A), never ى (U+0649) or Persian ی (U+06CC), in line with Arabic-V.
- **Base layers** differ slightly between Linux `ara(basic)` and Windows Arabic 101; AEK adds only new keys, so its additions sit on the same physical keys on both.

## License

MIT License, Copyright (c) 2026 Diaa Hassouna. See [LICENSE](LICENSE). It covers the AEK additions, the generator script and the Linux files. The Windows package also contains the Arabic 101 base layout as shipped by Microsoft, which the MIT license does not relicense. The Masri Writing System documentation remains under its own license (CC BY 4.0).

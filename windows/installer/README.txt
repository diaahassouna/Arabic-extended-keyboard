ARABIC-EXTENDED KEYBOARD (AEK) - WINDOWS INSTALLER
==================================================

Keep this whole folder together. The .msi files need the amd64, i386 and
wow64 folders next to them.

INSTALL
  1. Run setup.exe and approve the administrator prompt.
     The installer is not code-signed, so Windows SmartScreen may show
     "unrecognized app": choose "More info", then "Run anyway".
  2. Open Settings > Time & language > Language & region.
  3. Add "Arabic (Egypt)" if it is not in the list, then:
     ... > Language options > Add a keyboard > Arabic (101) - Extended
  4. Switch layouts with Win+Space.

The keyboard is registered under Arabic (Egypt) but types any Arabic variety.

REMOVE
  Settings > Apps > uninstall "Arabic (101) - Extended".

KEYS (AltGr = Right Alt)
  AltGr+F  پ      AltGr+[  چ      AltGr+T  ڤ      AltGr+;  گ
  AltGr+,  ۆ      AltGr+D  ێ      AltGr+.  ژ
  AltGr+S  small high seen (U+06DC)
  AltGr+X  hamza above (U+0654)
  Shift+AltGr+X  high hamza (U+0674)
  ZWNJ: Ctrl+Shift+2 (already in Arabic 101)

Full documentation, Linux files and sources:
the README.md at the root of the repository.

License: MIT for the AEK additions. The package also contains the Arabic 101
base layout as shipped by Microsoft.

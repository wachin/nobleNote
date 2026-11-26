# Changelog

All notable changes to nobleNote. The history of the versions before this port
is still kept in [NEWS](NEWS).

## Unreleased — PyQt6 port

### Added

- Complete port from C++/Qt6 to Python/PyQt6: all 26 `.cpp` files have an
  equivalent module in `src/noblenote/`, and the 5 `.ui` forms are ported to
  `src/noblenote/ui/`.
- Custom frameless title bar with the note title, the formatting toolbar and
  the minimize, maximize and close buttons in a single row. The window can be
  moved and resized from its edges.
- Monochrome icons for dark color schemes in `src/noblenote/icons/dark/`; they
  are recolored when the system palette changes.
- Spell checking with Hunspell in the note editor: red wavy underline for
  misspelled words, suggestions and "Add to dictionary" in the context menu,
  and dictionary selection and toggle in the preferences. It is optional:
  without the Hunspell bindings or dictionaries the editor works as before.

### Changed

- The editor font family and size are chosen in Preferences; the formatting
  toolbar makes room for the note title and gets a button to open Preferences.
- Translations regenerated with `pylupdate6 --no-obsolete`. Form strings are
  now extracted from the Python UI code (`translate(...)` calls) instead of the
  original `.ui` files, so they no longer depend on them. The new strings are
  translated into Spanish and available for the other languages, which show
  the English text until they are translated.

### Removed

- The original C++ sources (`src/*.cpp`, `src/*.h`, `nobleNote.pro`,
  `nobleNote.qrc`, `icon.rc`) and the five `.ui` forms, now that the PyQt6 port
  no longer needs them. They remain available at the tag `v1.5.0-cpp`.

### Notes

- The C++ sources and the `.ui` forms were the reference for the port and are
  kept in the `v1.5.0-cpp` tag.

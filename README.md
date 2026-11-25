# nobleNote

nobleNote is a cross-platform note taking application.
Manage notes in a simple two-pane layout with notebooks and an integrated rich text editor.
Notes are stored in the html format for maximum compatibility with other applications.

It is compatible to the [nobleNoteAndroid](https://github.com/taiko000/nobleNoteAndroid) app for Android.

> **This fork**: nobleNote has been ported from C++/Qt to Python/PyQt6.
> The port lives in `src/noblenote/` and is what you should run; the original C++
> sources are still in `src/` for reference and can be dropped (see
> [PYQT6_PORT_STATUS.md](PYQT6_PORT_STATUS.md) for the state of the migration).

## Supported Platforms

Any platform supported by Qt: Windows, Linux, macOS

## Sync notes between desktop and mobile devices

1.) Install [nobleNote](https://github.com/hakaishi/nobleNote) on your Linux/Windows/macOS device and find the folder containing the nobleNote notebooks.

2.) In nobleNoteAndroid, select a folder on the external storage (sd-card) using the overflow menu on the main screen.

3.) Use a sync software of your choice (e.g. [Syncthing](https://syncthing.net), Dropbox) to sync the folder containining the notebooks with the same folder on your Linux/Windows/macOS device. nobleNote will detect when notes have been changed on the file system and reload them automatically.

## Screenshots

![Alt text](/screenshot/Screenshot0.png?raw=true "")

![Alt text](/screenshot/Screenshot1.png?raw=true "")

## Running the PyQt6 port

### Requirements

- Python 3.10 or newer
- PyQt6 6.5 or newer, including `PyQt6-QtSvg` (all of it is declared in `pyproject.toml`)

### Install

A dedicated virtualenv keeps the `noblenote` command in a predictable place:

```bash
python3 -m venv ~/.local/share/noblenote/venv
~/.local/share/noblenote/venv/bin/pip install --upgrade pip
~/.local/share/noblenote/venv/bin/pip install .
```

If you are working on the code, install the checkout in editable mode instead, so
every edit takes effect without reinstalling:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

Both forms install the icons, the translations and `version.txt` as package data,
so the application finds them wherever the package is installed.

### Without a virtualenv (Linux, system Python)

If your distribution already ships PyQt6 6.5 or newer, you can skip the virtualenv
entirely. On Debian/Ubuntu:

```bash
sudo apt install python3-pyqt6 python3-pyqt6.qtsvg
```

On other distributions install the equivalent PyQt6 packages for `python3` (for
instance `python-pyqt6`); what matters is PyQt6 6.5 or newer plus its `QtSvg` module.

Then either run it straight from the checkout, with nothing installed at all:

```bash
PYTHONPATH=src python3 -m noblenote
```

or install it for your user only, still without a venv:

```bash
python3 -m pip install --user .
~/.local/bin/noblenote
```

Debian 12, Ubuntu 23.04 and newer mark the system Python as "externally managed",
so `pip` rejects that command with `error: externally-managed-environment`, even with
`--user`. In that case either stay with `PYTHONPATH=src python3 -m noblenote`
(nothing is installed), or add `--break-system-packages`, which still writes only
under your home directory (`~/.local/lib/python3.X/site-packages` and
`~/.local/bin`):

```bash
python3 -m pip install --user --break-system-packages .
```

Do not use `sudo pip install`: it drops files where your distribution's package
manager does not expect them and can break system tools.

For the desktop entry, when nothing is installed, `Exec` can carry the path itself:

```ini
Exec=env PYTHONPATH=/home/<you>/Dev/noblenote/src /usr/bin/python3 -m noblenote
```

### Run

```bash
~/.local/share/noblenote/venv/bin/noblenote      # if installed as above
.venv/bin/noblenote                              # editable install
PYTHONPATH=src python3 -m noblenote              # straight from the checkout
```

The layout is `src/noblenote/`, so `python3 -m noblenote` from the repository root
only works with `PYTHONPATH=src` (or after installing the package).

On the first start nobleNote asks for the folder where the notes are stored; it can
be changed later in *Preferences*. The configuration file is `~/.config/nobleNote.conf`
(an `.ini` file, the same keys the C++ version used, so an existing setup is picked up).

### Desktop entry and icon

The repository ships the two files a launcher needs: `noblenote.desktop` and the SVG
icon at `src/noblenote/icons/noblenote.svg`.

Per user (no root needed):

```bash
install -Dm644 noblenote.desktop ~/.local/share/applications/noblenote.desktop
install -Dm644 src/noblenote/icons/noblenote.svg \
        ~/.local/share/icons/hicolor/scalable/apps/noblenote.svg
update-desktop-database ~/.local/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor 2>/dev/null || true
```

System-wide:

```bash
sudo install -Dm644 noblenote.desktop /usr/share/applications/noblenote.desktop
sudo install -Dm644 src/noblenote/icons/noblenote.svg \
     /usr/share/icons/hicolor/scalable/apps/noblenote.svg
sudo update-desktop-database /usr/share/applications
sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor
```

Two details decide whether the entry actually starts the program:

- **`Icon=noblenote`** is an icon *theme* name, not a path. It resolves because the
  SVG above is installed as `noblenote.svg` inside the hicolor theme. If you prefer
  not to touch the icon theme, put an absolute path in the entry instead:
  `Icon=/home/<you>/.local/share/noblenote/noblenote.svg`
- **`Exec=noblenote`** needs that command in the `PATH` of the desktop session. A
  virtualenv is *not* activated there, so with the installation above use the
  absolute path: `Exec=/home/<you>/.local/share/noblenote/venv/bin/noblenote`

After copying the files, log out and back in (or restart the shell) so the menu is
rebuilt.

### Translations

The port ships 11 translations (`src/noblenote/translations/*.qm`) for: Asturian,
Czech, German, Spanish, French, Galician, Malay, Polish, Russian and Ukrainian, plus
`de_DE`. They are loaded automatically for the system language; there is no setting
to change it.

To refresh them after changing strings in the code:

```bash
# extract the strings from the Python modules and the .ui forms
pylupdate6 --no-obsolete src/noblenote --ts src/noblenote/translations/noblenote_es.ts

# compile the .ts into the .qm that the application loads
lrelease src/noblenote/translations/noblenote_es.ts \
         -qm src/noblenote/translations/noblenote_es.qm
```

`pylupdate6` keeps the translations that already exist (it matches them by context
and source text), so it is safe to run it over an already translated file.

### State of the migration

Coverage, known gaps and what still needs a graphical session to be verified are
tracked in [PYQT6_PORT_STATUS.md](PYQT6_PORT_STATUS.md). The last commit that still
carries the C++ sources is tagged `v1.5.0-cpp`.

## Installation (C++ version, still in `src/`)

Windows: Binary releases can be found on the releases page of this github repository

Debian based Linux distributions (Ubuntu):

`sudo apt install noblenote`

Building from source requires at least Qt 6.0 or newer.

It can also be build using the QtCreator IDE.

## Building From CLI

Dependencies: build-essential, qt6-base-dev, qt6-tools-dev-tools

To compile from source, open a terminal and change into the nobleNote source folder.
To install type:

`qmake6`

`sudo make install distclean`

To uninstall type:

`qmake6`     (if the Makefile has been removed)

`sudo make deinstall`

(Note that ~/.config/nobleNote.conf and
 the notes at their location won't be removed.
Backups are in their default data location.)

## License

nobleNote is licensed under the MIT License

(C) 2022 The creators of nobleNote

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

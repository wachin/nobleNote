# nobleNote - port a PyQt6

Estado del port de C++/Qt6 a Python/PyQt6.

## Estado actual: COMPLETO (a nivel de codigo)

- **26/26** archivos `.cpp` tienen equivalente en `src/noblenote/` (34 modulos, todos importan).
- **164 metodos** del C++: 149 con el mismo nombre en snake_case, 15 renombrados o codigo muerto (ver abajo).
- **5/5** formularios `.ui` portados a `src/noblenote/ui/ui_*.py`.
- **Traducciones funcionando**: 11 idiomas, `.qm` versionados y traductor cargado al arrancar.
- **Iconos reales** (20 SVG + 11 variantes oscuras + `.ico`), **arrastrar y soltar** con `MoveAction`, **19 claves de `QSettings`** identicas al C++ (mas 3 nuevas de ortografia).
- **Barra de titulo propia** (sin marco nativo) con la barra de formato dentro, y **correccion ortografica opcional con Hunspell**.

Pendiente: validar en una sesion grafica real. El codigo C++ y los `.ui` originales ya
se borraron de `src/`; siguen disponibles en el tag **`v1.5.0-cpp`**.

## Como ejecutar

```bash
# Desde la raiz del repo, sin instalar nada
PYTHONPATH=src python3 -m noblenote

# Instalado en un entorno virtual (deja el comando `noblenote` en el PATH)
python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/noblenote

# Sin entorno grafico (pruebas)
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 -m noblenote
```

Layout `src`, asi que `PYTHONPATH=src` (o la instalacion) es obligatorio: el paquete **no** esta en la raiz.

## Estructura del port

```
src/noblenote/                 # 34 modulos
├── __init__.py                # marca de paquete
├── __main__.py                # python3 -m noblenote
├── main.py                    # QApplication, QSettings portables, traductores
├── mainwindow.py              # ventana principal
├── note.py                    # ventana de una nota
├── notedescriptor.py          # capa sobre el archivo de nota (guardado/carga)
├── textdocument.py            # QTextDocument con modificacion diferida
├── textbrowser.py             # QTextBrowser con señales propias
├── textformattingtoolbar.py   # barra de formato
├── textsearchtoolbar.py       # barra de busqueda
├── htmlnotereader.py          # lector de notas HTML
├── htmlnotewriter.py          # escritor de notas HTML (+ write_xml_2_html)
├── xmlnotereader.py           # lector de notas XML (tomboy/gnote)
├── xmlnotewriter.py           # escritor de notas XML
├── highlighter.py             # resaltado de la busqueda
├── filesystemmodel.py         # QFileSystemModel con flags() y drop corregidos
├── findfilemodel.py           # modelo de resultados de busqueda
├── findfilesystemmodel.py     # proxy unificado
├── fileiconprovider.py        # iconos de archivo (incluye estado "cortado")
├── lineedit.py                # QLineEdit con boton de limpiar
├── progressreceiver.py        # progreso desde hilos (via señales)
├── preferences.py             # dialogo de preferencias
├── welcome.py                 # dialogo de bienvenida
├── trash.py                   # papelera
├── backup.py                  # indexado de la papelera
├── noteimporter.py            # importador de notas tomboy/gnote
├── systemtraycreator.py       # menu "abrir notas desde la bandeja"
├── datetimeutil.py            # fechas y UUID
├── xorcipher.py               # cifrado XOR (sin uso, igual que en el C++)
├── abstractnotereader.py      # clase base
├── resources.py               # iconos SVG + alias del resource original
├── titlebar.py                # barra de titulo propia (modulo nuevo)
├── spellchecker.py            # correccion ortografica con Hunspell (nuevo)
├── version.py                 # version.txt
├── version.txt                # 1.5.0
├── requirements.txt           # dependencias (tambien en pyproject.toml)
├── icons/                     # 20 SVG + dark/ (11 SVG) + noblenote.ico
├── translations/              # 11 .ts + 11 .qm
└── ui/                        # ui_*.py
```

En la raiz: `pyproject.toml` (src-layout, `noblenote` como entry point), `noblenote.desktop`,
`README.md`, `CHANGELOG.md`, `NEWS`, `COPYING` y `screenshot/`. El C++ original y los `.ui`
ya no estan: viven en el tag `v1.5.0-cpp`.

## Metodos del C++ renombrados o sin equivalente

Ninguno es una funcionalidad perdida:

| C++ | Situacion en el port |
|-----|----------------------|
| `MainWindow::updateMyTrayIcon` | cuerpo = `trayMenu` dentro de un bloque `#ifdef` comentado; nadie lo llama |
| `TextFormattingToolbar::removeWhitespace` | comentado en el propio C++ |
| `ProgressReceiver::event` | sustituido por señales de PyQt (ya son thread-safe y encoladas) |
| `MainWindow::folderActivated` / `noteActivated` | `folder_activated_index`, `note_activated_index`, `*_selection` |
| `NoteDescriptor::loadHtml` | `on_html_load_finished` |
| `NoteDescriptor::findOrReCreate` | `find_or_recreate` |
| `HtmlNoteWriter::insertMetaElement` | `_insert_meta_element` |
| `HtmlNoteWriter::writeXml2Html` | `write_xml_2_html` (staticmethod) |
| `XmlNoteReader::parseUuid` / `parseXml` / `readContent` | `_parse_uuid` / `_parse_xml` / `_read_content` |
| `FindFileModel::findInFilesFinished` | `_find_in_files_finished` |
| `FindFileModel::restoreOverrideCursor` | `QApplication.restoreOverrideCursor()` en linea |
| `main.cpp: setStyle()` | `app.setStyle(QStyleFactory.create("Fusion"))` en `main.py` |

## Traducciones (i18n)

Los `.ts` se generan **solo desde el codigo Python** y los `.qm` se versionan
(por eso la excepcion `!src/noblenote/translations/*.qm` en `.gitignore`). Los `.ui`
originales ya no participan en la extraccion: se pueden borrar sin perder traducciones.

```bash
# extraer/actualizar (conserva las traducciones ya existentes por contexto + texto)
pylupdate6 --no-obsolete src/noblenote/*.py src/noblenote/ui/*.py \
  --ts src/noblenote/translations/noblenote_es.ts

# compilar
lrelease src/noblenote/translations/noblenote_es.ts -qm src/noblenote/translations/noblenote_es.qm
```

`main.py` carga `noblenote_<locale>.qm` despues del traductor de Qt.

| idioma | traducidas |
|--------|-----------|
| es | 148/148 |
| cs, de, de_DE, pl, ru | 137/148 |
| ms, uk | 136/148 |
| gl | 134/148 |
| fr | 133/148 |
| ast | 128/148 |

Los huecos restantes son textos que nunca estuvieron traducidos en el `.ts` original (no fallos
del cableado). Los formularios usan `translate = QCoreApplication.translate` y llamadas
`translate(...)` en `ui/ui_*.py`; `pylupdate6` resuelve ese alias, pero **no** un alias con otro
nombre (por ejemplo `_translate`), asi que las cadenas nuevas deben escribirse como
`translate(...)` o `self.tr(...)` para que se extraigan al regenerar los `.ts`.

## Verificado

- `python3 -m compileall src/noblenote` sin errores.
- Los 34 modulos importan; `MainWindow`, `Preferences`, `Trash` y `Welcome` se instancian
  sin el C++ ni los `.ui` en el arbol de trabajo.
- Smoke test de 7 pasos (abajo) completo.
- Escritura/lectura de nota HTML con UUID y `find_uuid`.
- Traduccion en ejecucion con `es` y `fr` (textos de menu, barras, Preferencias, Papelera y Bienvenida).
- Arranque real (`python3 -m noblenote`) hasta el dialogo de bienvenida, en offscreen.

## No verificado (requiere sesion grafica)

- Icono de bandeja del sistema y su menu contextual.
- Arrastrar y soltar notas/libretas con el raton.
- Sobrescritura de notas abiertas al cerrar la aplicacion.
- Importacion real de archivos `.note` de tomboy/gnote.

## Pendiente

- [ ] Validar lo anterior en una sesion grafica real.
- [x] Borrar el C++ (`src/*.cpp|h`, `nobleNote.pro`, `nobleNote.qrc`, `icon.rc`) y los 5 `.ui`
      de `src/noblenote/ui/`. Recuperable con `git checkout v1.5.0-cpp -- src/`.
- [ ] Valorar borrar `xorcipher.py` (sin uso, igual que en el C++).
- [ ] Ajustar `noblenote.desktop` (`Exec=noblenote`, `Icon=noblenote` -> instalar `noblenote.svg`
      en `/usr/share/pixmaps/` o en el tema hicolor).
- [ ] Rellenar los huecos de ast/gl/cs/de/ms/pl/ru/uk si se quieren completar.
- [ ] El texto de "Acerca de" es propio del port (menciona PyQt6), asi que es una cadena nueva.

## Smoke test

```bash
cd /home/wachin/Dev/noblenote
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 - <<'EOF'
import sys, os, tempfile
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)
from noblenote.xmlnotereader import XmlNoteReader
from noblenote.htmlnotereader import HtmlNoteReader
from noblenote.htmlnotewriter import HtmlNoteWriter
from noblenote.notedescriptor import NoteDescriptor
from noblenote.textdocument import TextDocument
from noblenote.textbrowser import TextBrowser
from noblenote.note import Note
from noblenote.mainwindow import MainWindow
from noblenote.datetimeutil import create_quid
from PyQt6.QtGui import QTextDocument as QTD, QTextCursor
from PyQt6.QtCore import QDateTime

tmp = tempfile.mkdtemp()
html_path = os.path.join(tmp, "note.html")
uuid = create_quid()

doc = QTD()
c = QTextCursor(doc)
c.insertText("Hello ")
f = c.charFormat()
f.setFontWeight(700)
c.insertText("bold", f)
c.insertText(" world")

w = HtmlNoteWriter(html_path)
w.set_document(doc); w.set_uuid(uuid); w.set_title("Test Note")
now = QDateTime.currentDateTime()
w.set_create_date(now); w.set_last_change(now)
w.write()
print("1. HTML escrito:", os.path.getsize(html_path), "bytes")

reader = HtmlNoteReader(html_path); reader.read()
print("2. HTML leido titulo:", reader.title(), "| uuid ok:", reader.uuid() == uuid)

tb = TextBrowser(); td = TextDocument()
tb.setDocument(td)
desc = NoteDescriptor(html_path, tb, td)
print("3. NoteDescriptor file_path ok:", desc.file_path() == html_path)

note = Note(html_path); note.show_after_loaded()
print("4. Note widget creado")

print("5. might_be_xml_note(html):", XmlNoteReader.might_be_xml_note(html_path))

mw = MainWindow()
print("6. MainWindow creada")

found = HtmlNoteReader.find_uuid(uuid, tmp)
print("7. find_uuid ok:", found == html_path)

print("\n=== SMOKE TEST OK ===")
EOF
```

Resultado esperado:

```
1. HTML escrito: 902 bytes
2. HTML leido titulo: Test Note | uuid ok: True
3. NoteDescriptor file_path ok: True
4. Note widget creado
5. might_be_xml_note(html): False
6. MainWindow creada
7. find_uuid ok: True

=== SMOKE TEST OK ===
```

En offscreen aparecen avisos inofensivos (`QFileSystemWatcher::addPaths: list is empty`,
`This plugin does not support propagateSizeHints()`, mensajes de `Qt6CTPlatformTheme`).

## Mapeo C++ -> Python

| C++ | Python |
|-----|--------|
| `src/mainwindow.{cpp,h}` | `src/noblenote/mainwindow.py` |
| `src/note.{cpp,h}` | `src/noblenote/note.py` |
| `src/notedescriptor.{cpp,h}` | `src/noblenote/notedescriptor.py` |
| `src/textdocument.{cpp,h}` | `src/noblenote/textdocument.py` |
| `src/textbrowser.{cpp,h}` | `src/noblenote/textbrowser.py` |
| `src/textformattingtoolbar.{cpp,h}` | `src/noblenote/textformattingtoolbar.py` |
| `src/textsearchtoolbar.{cpp,h}` | `src/noblenote/textsearchtoolbar.py` |
| `src/htmlnotereader.{cpp,h}` | `src/noblenote/htmlnotereader.py` |
| `src/htmlnotewriter.{cpp,h}` | `src/noblenote/htmlnotewriter.py` |
| `src/xmlnotereader.{cpp,h}` | `src/noblenote/xmlnotereader.py` |
| `src/xmlnotewriter.{cpp,h}` | `src/noblenote/xmlnotewriter.py` |
| `src/highlighter.{cpp,h}` | `src/noblenote/highlighter.py` |
| `src/filesystemmodel.{cpp,h}` | `src/noblenote/filesystemmodel.py` |
| `src/findfilemodel.{cpp,h}` | `src/noblenote/findfilemodel.py` |
| `src/findfilesystemmodel.{cpp,h}` | `src/noblenote/findfilesystemmodel.py` |
| `src/fileiconprovider.{cpp,h}` | `src/noblenote/fileiconprovider.py` |
| `src/lineedit.{cpp,h}` | `src/noblenote/lineedit.py` |
| `src/progressreceiver.{cpp,h}` | `src/noblenote/progressreceiver.py` |
| `src/preferences.{cpp,h}` | `src/noblenote/preferences.py` |
| `src/welcome.{cpp,h}` | `src/noblenote/welcome.py` |
| `src/trash.{cpp,h}` | `src/noblenote/trash.py` |
| `src/backup.{cpp,h}` | `src/noblenote/backup.py` |
| `src/noteimporter.{cpp,h}` | `src/noblenote/noteimporter.py` |
| `src/systemtraycreator.{cpp,h}` | `src/noblenote/systemtraycreator.py` |
| `src/datetime.{cpp,h}` | `src/noblenote/datetimeutil.py` |
| `src/xorcipher.{cpp,h}` | `src/noblenote/xorcipher.py` (sin uso) |
| `src/abstractnotereader.{cpp,h}` | `src/noblenote/abstractnotereader.py` |
| `src/ui/*.ui` | `src/noblenote/ui/ui_*.py` |
| `nobleNote.qrc` | `src/noblenote/resources.py` + `icons/` |
| `nobleNote.pro` (`TRANSLATIONS`) | `pylupdate6` + `lrelease` (ver arriba) |
| `version.txt` | `src/noblenote/version.txt` (leido por `version.py`) |

Las rutas de la columna C++ corresponden al tag `v1.5.0-cpp`.

Dos modulos no tienen equivalente en el C++: `titlebar.py` (barra de titulo propia, con la
barra de formato dentro y agarres para redimensionar) y `spellchecker.py` (correccion
ortografica opcional con Hunspell, con las palabras propias en `QSettings`).

## Diferencias de API Qt5 -> Qt6 aplicadas

| Problema | Solucion |
|----------|----------|
| `QAction(QPixmap, ...)` | `QAction(QIcon(QPixmap), ...)` |
| `setFilter([flag1, flag2])` | `setFilter(flag1 \| flag2)` |
| `entryList([filter])` | `entryList(filter)` |
| `QAbstractItemView.SelectionFlag` | `QItemSelectionModel.SelectionFlag` |
| `QFileIconProvider` en QtGui | movido a `QtWidgets` |
| `QFileSystemModel` en QtCore | movido a `QtGui` |
| `QTreeWidgetItemFromPtr` | no existe en PyQt6 (eliminado) |
| `isEmpty()` en indexes | reemplazado por `not indexes()` |

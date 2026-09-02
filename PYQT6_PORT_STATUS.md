# nobleNote - PyQt6 Port

Estado del puerto de C++/Qt5 a Python/PyQt6.

## Estado actual: COMPLETADO Y VERIFICADO

- **34/34 modulos** importan correctamente
- **Todos los archivos compilan** sin errores (`python3 -m compileall pyqt6`)
- **Smoke test funcional** pasa 7 pasos criticos (ver abajo)

## Ejecutar

```bash
# Entorno grafico normal
python3 -m pyqt6

# Headless (tests)
QT_QPA_PLATFORM=offscreen python3 -m pyqt6
```

## Estructura del puerto

```
pyqt6/
├── __init__.py              # Package marker
├── __main__.py              # Entry point (python3 -m pyqt6)
├── main.py                  # QApplication bootstrap
├── mainwindow.py            # Ventana principal
├── note.py                  # Widget de nota individual
├── notedescriptor.py        # Abstraccion de archivo de nota
├── textdocument.py          # QTextDocument con delayed modification
├── textbrowser.py           # QTextBrowser con senales custom
├── textformattingtoolbar.py # Toolbar de formato
├── textsearchtoolbar.py     # Toolbar de busqueda
├── htmlnotereader.py        # Lector de notas HTML
├── htmlnotewriter.py        # Escritor de notas HTML
├── xmlnotereader.py         # Lector de notas XML (tomboy/gnote)
├── xmlnotewriter.py         # Escritor de notas XML
├── highlighter.py           # Resaltado de sintaxis
├── filesystemmodel.py       # QFileSystemModel override
├── findfilemodel.py         # Modelo para busqueda en archivos
├── findfilesystemmodel.py   # Proxy model unificado
├── fileiconprovider.py      # Proveedor de iconos
├── lineedit.py              # QLineEdit con placeholder
├── progressreceiver.py      # Receiver de progreso
├── preferences.py           # Dialogo de preferencias
├── welcome.py               # Pantalla de bienvenida
├── trash.py                 # Papelera
├── backup.py                # Sistema de respaldo
├── noteimporter.py          # Importador de notas
├── systemtraycreator.py     # Icono en system tray
├── datetimeutil.py          # Utilidades de fecha/UUID
├── xorcipher.py             # Cifrado XOR
├── resources.py             # Manejo de recursos/iconos
├── version.py               # Version de la app
├── abstractnotereader.py    # Clase base abstracta
└── ui/                      # Widgets generados de .ui files
    ├── ui_mainwindow.py
    ├── ui_note.py
    ├── ui_welcome.py
    ├── ui_trash.py
    └── ui_preferences.py
```

## Smoke test

```bash
cd /home/wachin/Dev/nobleNote
QT_QPA_PLATFORM=offscreen python3 - <<'EOF'
import sys, os, tempfile
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)
from pyqt6.xmlnotereader import XmlNoteReader
from pyqt6.htmlnotereader import HtmlNoteReader
from pyqt6.htmlnotewriter import HtmlNoteWriter
from pyqt6.notedescriptor import NoteDescriptor
from pyqt6.textdocument import TextDocument
from pyqt6.textbrowser import TextBrowser
from pyqt6.note import Note
from pyqt6.mainwindow import MainWindow
from pyqt6.datetimeutil import create_quid
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

## Mapeo C++ -> Python

| C++ | Python |
|-----|--------|
| `src/mainwindow.{cpp,h}` | `pyqt6/mainwindow.py` |
| `src/note.{cpp,h}` | `pyqt6/note.py` |
| `src/notedescriptor.{cpp,h}` | `pyqt6/notedescriptor.py` |
| `src/textdocument.{cpp,h}` | `pyqt6/textdocument.py` |
| `src/textbrowser.{cpp,h}` | `pyqt6/textbrowser.py` |
| `src/textformattingtoolbar.{cpp,h}` | `pyqt6/textformattingtoolbar.py` |
| `src/textsearchtoolbar.{cpp,h}` | `pyqt6/textsearchtoolbar.py` |
| `src/htmlnotereader.{cpp,h}` | `pyqt6/htmlnotereader.py` |
| `src/htmlnotewriter.{cpp,h}` | `pyqt6/htmlnotewriter.py` |
| `src/xmlnotereader.{cpp,h}` | `pyqt6/xmlnotereader.py` |
| `src/xmlnotewriter.{cpp,h}` | `pyqt6/xmlnotewriter.py` |
| `src/highlighter.{cpp,h}` | `pyqt6/highlighter.py` |
| `src/filesystemmodel.{cpp,h}` | `pyqt6/filesystemmodel.py` |
| `src/findfilemodel.{cpp,h}` | `pyqt6/findfilemodel.py` |
| `src/findfilesystemmodel.{cpp,h}` | `pyqt6/findfilesystemmodel.py` |
| `src/fileiconprovider.{cpp,h}` | `pyqt6/fileiconprovider.py` |
| `src/lineedit.{cpp,h}` | `pyqt6/lineedit.py` |
| `src/progressreceiver.{cpp,h}` | `pyqt6/progressreceiver.py` |
| `src/preferences.{cpp,h}` | `pyqt6/preferences.py` |
| `src/welcome.{cpp,h}` | `pyqt6/welcome.py` |
| `src/trash.{cpp,h}` | `pyqt6/trash.py` |
| `src/backup.{cpp,h}` | `pyqt6/backup.py` |
| `src/noteimporter.{cpp,h}` | `pyqt6/noteimporter.py` |
| `src/systemtraycreator.{cpp,h}` | `pyqt6/systemtraycreator.py` |
| `src/datetime.{cpp,h}` | `pyqt6/datetimeutil.py` |
| `src/xorcipher.{cpp,h}` | `pyqt6/xorcipher.py` |
| `src/abstractnotereader.{cpp,h}` | `pyqt6/abstractnotereader.py` |
| `src/ui/*.ui` | `pyqt6/ui/ui_*.py` |

## Diferencias de API Qt5 -> Qt6 aplicadas

| Problema | Solucion |
|----------|----------|
| `QAction(QPixmap, ...)` | `QAction(QIcon(QPixmap), ...)` |
| `setFilter([flag1, flag2])` | `setFilter(flag1 | flag2)` |
| `entryList([filter])` | `entryList(filter)` |
| `QAbstractItemView.SelectionFlag` | `QItemSelectionModel.SelectionFlag` |
| `QFileIconProvider` en QtGui | Movido a `QtWidgets` |
| `QFileSystemModel` en QtCore | Movido a `QtGui` |
| `QTreeWidgetItemFromPtr` | No existe en PyQt6 (eliminado) |
| `isEmpty()` en model indexes | Reemplazado por `not indexes()` |

## Notas importantes

1. **XmlNoteWriter** no tiene consumidores directos en el codigo actual (solo se usa HtmlNoteWriter). Existe como utilidad y para `write_xml_2_html()`.

2. **NoteDescriptor** carga notas HTML de forma asincrona (thread). El uuid puede ser `None` inmediatamente despues de construir el objeto; se popula tras `loadFinished`.

3. **Los archivos `.ui`** originales estan en `src/ui/`. Los archivos `pyqt6/ui/ui_*.py` se generan con `pyuic6` si se regeneran desde los `.ui`.

4. **Recursos**: `resources.py` usa un enfoque simplificado. Los iconos originales estan en `nobleNote.qrc` (C++). El puerto usa `QIcon.fromTheme()` y placeholders.

5. **Portabilidad**: el codigo usa `QSettings` y `QStandardPaths` para rutas configurables, igual que el C++.

## Proximos pasos sugeridos

- [ ] Agregar tests unitarios (pytest) para cada modulo
- [ ] Integrar los recursos/iconos originales via `pyrcc6`
- [ ] Agregar type hints completos
- [ ] Documentar funciones publicas con docstrings
- [ ] Agregar logging en vez de prints
- [ ] Implementar `write_xml_2_html()` como CLI tool de migracion
- [ ] Agregar soporte para arrastrar/soltar (drag & drop) entre carpetas
- [ ] Tests de integracion con notas reales de tomboy/gnote

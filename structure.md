# Projektstruktur und Funktionsweise

Technische Übersicht über **Import-LIB-KiCad-Plugin** (`impartGUI`) – ein KiCad-Addon,
das heruntergeladene Bauteil-Bibliotheken von Octopart, Samacsys (Component Search
Engine), UltraLibrarian, SnapEDA und EasyEDA/LCSC in lokale KiCad-Bibliotheken
(Symbole, Footprints, 3D-Modelle) überführt.

---

## 1. Überblick

| Eigenschaft | Wert |
| --- | --- |
| Identifier | `com.github.Steffen-W.impartGUI` |
| Lizenz | GPL-3.0 (`LICENSE.txt`) |
| Sprache | Python 3.9+ (`ruff.toml` / `mypy.ini` zielen auf `py39`) |
| GUI-Toolkit | wxPython (in KiCad mitgeliefert) |
| Min. KiCad | 8.0.4 (`metadata.json`, `KiCadApp(min_version=...)`) |
| Verteilung | KiCad Plugin And Content Manager (PCM), ZIP-Paket |

Das Plugin läuft in **zwei Betriebsarten**, je nachdem wie KiCad es startet:

1. **IPC-API-Modus (empfohlen)** – KiCad startet `plugins/impart_action.py` als
   eigenständigen Python-Prozess in einer von KiCad verwalteten venv. Registriert
   über `plugins/plugin.json`. Verfügbar in *PCB Editor* **und** *Schematic Editor*.
2. **Fallback-Modus (SWIG/pcbnew)** – KiCad lädt `plugins/__init__.py` als klassisches
   `pcbnew.ActionPlugin` in den PCB-Editor-Prozess. Kein separater Prozess, keine
   automatische Dependency-Verwaltung.

Zusätzlich gibt es einen **CLI-Modus** ohne GUI (`python -m KiCadImport`).

---

## 2. Verzeichnisbaum

```
Import-LIB-KiCad-Plugin/
├── metadata.json                 # PCM-Manifest (Schema: go.kicad.org/pcm/schemas/v1)
├── generate_zip.sh               # Build-Skript → Import-LIB-KiCad-Plugin.zip
├── ruff.toml, mypy.ini, pyrightconfig.json
├── .github/workflows/nightly.yml # Nightly Pre-Release bei Push auf master
├── doc/                          # Screenshots, demo.gif/mp4 für README
├── resources/                    # icon.png / icon.svg für PCM
└── plugins/
    ├── plugin.json               # IPC-API-Manifest (go.kicad.org/api/schemas/v1)
    ├── __init__.py               # Fallback: pcbnew.ActionPlugin + sys.path-Setup
    ├── __main__.py               # Standalone-Start (python -m plugins)
    ├── impart_action.py          # Kern: Backend + Frontend + IPC-Entrypoint
    ├── impart_gui.py             # wxFormBuilder-generiertes Dialog-Layout
    ├── KiCad_Plugin_wxFormbuilder_dialog.fbp  # Quelle für impart_gui.py
    ├── component_search.py       # JLCPCB/EasyEDA-Suchdialog
    ├── impart_easyeda.py         # EasyEDA/LCSC-Import (Wrapper um easyeda2kicad)
    ├── single_instance_manager.py# TCP-basierte Single-Instance-Steuerung
    ├── config.ini                # Persistente Einstellungen (update-sicher)
    ├── icon.png
    ├── ConfigHandler/            # INI-Lesen/Schreiben
    ├── FileHandler/              # Ordner-Polling nach neuen ZIPs
    ├── KiCadImport/              # ZIP-Import-Pipeline (+ CLI __main__.py)
    │   ├── __init__.py           # LibImporter, REMOTE_TYPES, main()
    │   ├── __main__.py           # argparse-CLI
    │   └── footprint_model_parser.py  # Regex-Manipulation von .kicad_mod
    ├── KiCadSettingsPaths/       # KiCad-Erkennung: IPC / SWIG / Fallback
    ├── KiCad_Settings/           # sym-lib-table, fp-lib-table, kicad_common.json
    ├── kicad_cli/                # Wrapper um `kicad-cli` (sym/fp upgrade)
    ├── kiutils/        [submodule] S-Expression-Parser für KiCad-Dateien
    └── easyeda2kicad/  [submodule] EasyEDA-API + Konverter
```

### Git-Submodule

Beide Submodule sind Forks des Maintainers (`.gitmodules`):

| Pfad | Fork | Zweck |
| --- | --- | --- |
| `plugins/kiutils` | `Steffen-W/kiutils` | Lesen/Schreiben von `.kicad_sym`, `fp-lib-table`, `sym-lib-table` |
| `plugins/easyeda2kicad` | `Steffen-W/easyeda2kicad.py` | EasyEDA-API, Symbol-/Footprint-/3D-Export, SVG-Rendering |

Die Pfade werden zur Laufzeit per `sys.path.insert()` eingebunden – es gibt keine
`pip install`-Abhängigkeit. Einstiegspunkte des Path-Setups:
`plugins/__init__.py::setup_submodule_paths()`, sowie lokale Setups in
`KiCadImport/__init__.py`, `impart_easyeda.py` und `component_search.py`.

---

## 3. Start- und Kontrollfluss

### 3.1 IPC-API-Modus

```
KiCad (Schematic/PCB) → Tools → External Plugins → "impartGUI (IPC API)"
   └─ plugin.json  entrypoint: impart_action.py
        └─ impart_action.py (__main__)
             ├─ quick_instance_check()        # TCP-Probe → Logging-Modus wählen
             ├─ instance_manager.is_already_running()
             │     ├─ Port belegt  → Fokus-Kommando senden, sys.exit(0)
             │     └─ Port frei    → Socket gebunden, weiter
             ├─ wx.App() + ImpartFrontend(fallback_mode=False)
             ├─ instance_manager.start_server(frontend)
             └─ frontend.ShowModal()
```

### 3.2 Fallback-Modus (pcbnew)

```
KiCad PCB-Editor lädt plugins/__init__.py beim Start
   └─ ActionImpartPlugin().register()
        └─ Run()
             ├─ setup_logging()            → plugins/plugin_fallback.log
             ├─ setup_submodule_paths()    → kiutils, easyeda2kicad, plugins/
             └─ ImpartFrontend(fallback_mode=True).ShowModal()
```

Im Fallback-Modus wird der IPC-Server **nicht** gestartet; jeder Aufruf erzeugt eine
neue Instanz, weil der Prozess ohnehin an KiCad gebunden ist.

### 3.3 Single-Instance-Mechanismus (`single_instance_manager.py`)

- Der Port wird deterministisch aus dem Installationspfad abgeleitet:
  `49152 + md5(plugin_dir) % 16383` (IANA Dynamic Range). Zwei parallel installierte
  Kopien kollidieren dadurch nicht.
- Der **gebundene TCP-Port ist die einzige Wahrheitsquelle** – kein Lockfile.
- `SO_REUSEADDR` ist gesetzt, `SO_REUSEPORT` bewusst **nicht** (unter Linux würde der
  Kernel sonst mehrere Listener zulassen und Verbindungen verteilen).
- Ein zweiter Start sendet ein Fokus-Kommando; der Server-Thread ruft
  `_bring_to_foreground()` auf dem bestehenden Frontend auf.
- `atexit.register(instance_manager.stop_server)` sichert die Freigabe ab.

---

## 4. Kernmodule im Detail

### 4.1 `impart_action.py` – Backend und Frontend

Die zentrale Datei (~950 Zeilen) enthält drei Ebenen:

**`ImpartBackend`** – zustandsbehaftete Import-Logik ohne GUI-Bezug:

- Aggregiert `KiCadApp`, `ConfigHandler`, `KiCad_Settings`, `FileHandler`, `LibImporter`.
- `print_buffer: str` – alle Ausgaben sammeln sich in einem String; `LibImporter.print`
  wird auf `print_to_buffer` umgebogen.
- `find_and_import_new_files()` – pollt das Quellverzeichnis und ruft pro neuem ZIP
  `_import_single_file()` auf. Läuft entweder einmalig oder als Dauerschleife
  (`run_thread`, 1 s Intervall) in einem separaten Thread.
- Flags: `auto_import`, `overwrite_import`, `compress_models`, `local_lib`, `auto_lib`.
- `SUPPORTED_LIBRARIES = ["Octopart", "Samacsys", "UltraLibrarian", "Snapeda", "EasyEDA"]`

**`PluginThread`** – Daemon-Thread, der alle 0,5 s die Länge des `print_buffer` prüft
und bei Änderung ein `ResultEvent` per `wx.PostEvent` an den GUI-Thread schickt
(`EVT_UPDATE` → `update_display`). So bleibt die GUI thread-sicher.

**`ImpartFrontend(impartGUI)`** – Event-Handler des Dialogs:

| Handler | Auslöser | Wirkung |
| --- | --- | --- |
| `BottonClick` | Start/Stop-Button | Einmal-Import; bei `auto_import` zusätzlich Dauerthread |
| `ButtomManualImport` | EasyEDA-Import-Button | `_perform_easyeda_import()` mit LCSC-ID |
| `OnComponentSearch` | Suchen-Button | öffnet `component_search.SearchDialog` |
| `DirChange` | DirPicker | Pfade in `config.ini` speichern, Datei-Cache leeren |
| `m_checkBoxLocalLibOnCheckBox` | „Local Library“ | schaltet zwischen `${KICAD_3RD_PARTY}` und `${KIPRJMOD}` |
| `m_checkBoxSingleLibOnCheckBox` | „single lib name“ | alle Importe in eine Bibliothek zusammenführen |
| `on_close` | Fenster schließen | Hide/Stop/Cancel-Dialog, wenn Auto-Import läuft |

`FileDropTarget` ermöglicht Drag & Drop von `.zip`-Dateien direkt auf das Textfeld –
die Dateien gehen ohne Ordner-Monitoring durch dieselbe `_import_single_file`-Pipeline.

Die Funktion `check_library_import()` prüft nach jedem Import, ob die erzeugten
Bibliotheken in KiCads Tabellen eingetragen sind, und trägt sie bei aktiviertem
„auto KiCad setting“ automatisch nach.

### 4.2 `KiCadImport/` – die ZIP-Import-Pipeline

`LibImporter.import_all(zip_file, overwrite_if_exists)` ist der Hauptpfad:

```
1. identify_remote_type(zf)      → REMOTE_TYPES + Pfad-Dict {symbol, footprint, model, dcm}
2. load_symbol_lib(...)          → kiutils.SymbolLib (+ kicad-cli upgrade)
3. extract_footprint_to_file(...)→ <Lib>.pretty/<Name>.kicad_mod (+ fp upgrade)
4. load_model(...)               → 3D-Modell in ein tempdir extrahieren
5. update_symbol_properties(...) → Footprint-Property auf "<Lib>:<Footprint>" setzen
6. save_to_library(...)          → atomar in Ziel-Bibliothek schreiben
7. finally: alle tempdirs löschen
```

**Formaterkennung (`identify_remote_type`)** – heuristisch, in dieser Reihenfolge:

| Typ | Erkennungsmerkmal |
| --- | --- |
| `Octopart` | `device.lib` **und** `device.dcm` im Archiv |
| `Samacsys` | Verzeichnis `KiCad` (exakt so geschrieben) |
| `UltraLibrarian` | Verzeichnis `KiCAD` (abweichende Schreibweise!) |
| `Snapeda` | Fallback: irgendein `.kicad_sym` oder `.lib` vorhanden |
| `Partial` | nur ein 3D-Modell (`.step`/`.stp`/`.wrl`), keine Symbole |

Ohne verwertbare Dateien wird `ValueError` geworfen.

**Schreibsicherheit in `save_to_library`:**

- Vor dem Überschreiben wird eine `.backup`-Kopie angelegt (`backup_files`-Dict).
- Die Symbolbibliothek wird zuerst in `<Lib>.kicad_sym.tmp` geschrieben, dann
  **zurückgelesen und verifiziert** (nicht leer), erst dann per `rename()` ersetzt.
- Bei einer Exception werden alle Backups zurückgespielt (Rollback) und `*.tmp` gelöscht.
- Bei Erfolg werden die Backups gelöscht.

**Zielstruktur im Bibliotheksordner:**

```
<DEST_PATH>/
├── Samacsys.kicad_sym          # Symbole (alle Bauteile einer Quelle in einer Datei)
├── Samacsys.pretty/            # Footprints (.kicad_mod)
└── Samacsys.3dshapes/          # 3D-Modelle (.wrl / .step / .step.gz)
```

Bei aktivem „single lib name“ ersetzt der frei gewählte Name den Quellnamen
(`get_lib_name()`).

**3D-Modell-Verknüpfung** – `footprint_model_parser.py` manipuliert den
`(model ...)`-Block der `.kicad_mod`-Datei per Regex und setzt einen relativen Pfad:
`${KICAD_3RD_PARTY}/<Lib>.3dshapes/<Modell>` bzw. `${KIPRJMOD}/...` im lokalen Modus.

**Kompression** – ist `compress_models` aktiv, werden STEP-Dateien als `.step.gz`
(gzip, Level 9) abgelegt; das liest KiCad ab Version 6 nativ. WRL wird nicht komprimiert.

### 4.3 `impart_easyeda.py` – Online-Import per LCSC-Nummer

Kein ZIP-Umweg: `EasyEDAImporter.import_component("C2040")` lädt direkt von der
EasyEDA-API und nutzt die Exporter des `easyeda2kicad`-Submoduls:

```
EasyedaApi.get_cad_data_of_component(lcsc_id)
   ├─ EasyedaSymbolImporter    → ExporterSymbolKicad    → <Lib>.kicad_sym
   ├─ Easyeda3dModelImporter   → Exporter3dModelKicad   → <Lib>.3dshapes/*.wrl|.step[.gz]
   └─ EasyedaFootprintImporter → ExporterFootprintKicad → <Lib>.pretty/*.kicad_mod
```

Die Bauteil-ID muss mit `C` beginnen, sonst `ValueError`. Konfiguriert wird über das
Dataclass `ImportConfig(base_folder, lib_name, overwrite, lib_var, prefer_step,
compress_models)`.

Beim Laden wird der Modul-Cache bewusst bereinigt
(`del sys.modules["easyeda2kicad*"]`), damit ein eventuell global installiertes
`easyeda2kicad` nicht das mitgelieferte Submodul verdrängt.

### 4.4 `component_search.py` – JLCPCB-Bauteilsuche

Eigenständig lauffähig (`python plugins/component_search.py`) oder als `SearchDialog`
eingebettet. Bei Auswahl eines Treffers wird die LCSC-Nummer per Callback in das
Textfeld des Hauptdialogs geschrieben.

- Suche gegen die JLCPCB-Such-API (`EasyedaApi.search_jlcpcb_components`), Seitengröße 25.
- Alle Netzwerkzugriffe laufen in `threading.Thread`, Ergebnisse kommen per
  `wx.CallAfter` zurück; ein `_search_request_id`-Zähler verwirft veraltete Antworten.
- `DetailPanel` zeigt Produktbild sowie Symbol- und Footprint-**SVG-Vorschau**
  (`render_symbol_svg` / `render_footprint_svg` aus dem Submodul).
- Caches pro Sitzung: max. 50 Bilder, max. 30 CAD-Datensätze.
- `FilterDialog` filtert nach Marke, Package, Typ, Mindestbestand und Preis;
  Spaltenklick sortiert.

### 4.5 `KiCadSettingsPaths/` – KiCad-Erkennung

`KiCadApp(prefer_ipc=True, min_version="8.0.4")` ermittelt beim Start alles Nötige und
legt es als Attribute ab. Die Verbindungsstrategie ist dreistufig:

| `connection_type` | Quelle | Erkannt wird |
| --- | --- | --- |
| `"IPC"` | `kipy.KiCad()` | Version, offenes Projekt (PCB → sonst Schematic) |
| `"SWIG"` | `import pcbnew` | `SETTINGS_MANAGER().GetUserSettingsPath()`, `Version()` |
| `"FALLBACK"` | Pfad-Heuristik | nur `settings_path` über `KiCadSettingsPaths` |

Findet die IPC-API kein offenes Dokument, greift `_find_project_via_process_args()`:
die Argumentliste laufender KiCad-Prozesse wird gescannt (`/proc` unter Linux, `ps`
unter macOS, `psutil` unter Windows) und daraus `.kicad_pro` / `.kicad_pcb` /
`.kicad_sch` abgeleitet. `refresh_project_info()` erlaubt ein spätes Nachladen, falls
das Projekt erst nach Plugin-Start geöffnet wurde.

`KiCadSettingsPaths.find_actual_settings_path()` sucht plattformabhängig den
Konfigurationsordner (z. B. `%APPDATA%/kicad/<version>`, `~/.config/kicad/<version>`,
`~/Library/Preferences/kicad/<version>`).

### 4.6 `KiCad_Settings/` – Schreiben der KiCad-Konfiguration

Arbeitet direkt auf KiCads Konfigurationsdateien (über `kiutils.libraries.LibTable`
bzw. JSON):

| Datei | Funktionen |
| --- | --- |
| `sym-lib-table` | `get_sym_table`, `set_sym_table`, `sym_table_change_entry`, `check_symbollib` |
| `fp-lib-table` | `get_lib_table`, `set_lib_table_entry`, `check_footprintlib` |
| `kicad_common.json` | `get/set_kicad_common`, `get_kicad_GlobalVars`, `check_GlobalVar` |
| `kicad.json` | `get/set_kicad_json` |

Findet der Konstruktor im angegebenen Pfad keine `sym-lib-table`, sucht er automatisch
das höchste Versionsunterverzeichnis (z. B. `9.0/`).

Die `check_*`-Methoden geben Warntexte zurück und legen bei `add_if_possible=True`
fehlende Einträge an. Der Pfad-Präfix ist umschaltbar: `${KICAD_3RD_PARTY}` global
bzw. `${KIPRJMOD}` für projektlokale Bibliotheken.

### 4.7 `kicad_cli/` – Wrapper um `kicad-cli`

Sucht das Binary plattformabhängig (macOS: feste `/Applications/KiCad*`-Pfade, sonst
`shutil.which`) und kapselt `subprocess.run` mit:

- 30 s Timeout, erzwungenem `LANG=en_US.UTF-8` (parsebare Ausgabe),
- `CREATE_NO_WINDOW` unter Windows (kein aufblitzendes Konsolenfenster),
- strukturiertem `CommandResult(success, stdout, stderr, return_code, message)`.

Genutzt für `sym upgrade` (auch Konvertierung von altem `.lib` nach `.kicad_sym`) und
`fp upgrade`. Fehlt `kicad-cli`, läuft der Import ohne Upgrade weiter – bei `.lib`-
Dateien ist das jedoch ein harter Fehler, weil die Konvertierung nicht anders geht.

### 4.8 Kleine Helfer

- **`ConfigHandler`** – dünner `configparser`-Wrapper über `plugins/config.ini`.
  Legt fehlende Dateien mit Default-Sektion `[config]` an.
- **`FileHandler`** – merkt sich bereits gesehene Dateinamen in `known_files` und
  liefert über `get_new_files()` nur neue `.zip`-Dateien zwischen 1 KB und 50 MB.
  Beim Umschalten auf „overwrite“ wird `known_files` geleert, damit bekannte Dateien
  erneut verarbeitet werden.
- **`impart_gui.py`** – reines wxFormBuilder-Erzeugnis, **nicht von Hand editieren**;
  Änderungen gehören in `KiCad_Plugin_wxFormbuilder_dialog.fbp`.

---

## 5. Konfiguration und Persistenz

`plugins/config.ini`, Sektion `[config]`:

| Schlüssel | Bedeutung |
| --- | --- |
| `src_path` | Überwachter Download-Ordner |
| `dest_path` | Ziel-Bibliotheksordner (`${KICAD_3RD_PARTY}`) |
| `auto_import` | Dauerhafte Ordnerüberwachung |
| `overwrite_import` | Vorhandene Symbole/Footprints/Modelle überschreiben |
| `auto_lib` | KiCad-Bibliothekstabellen automatisch ergänzen |
| `local_lib` | Import ins Projektverzeichnis statt global |
| `single_lib` / `lib_name` | Alle Importe in eine benannte Bibliothek |
| `compress_models` | STEP als `.step.gz` speichern |

`metadata.json` schützt die Datei über `keep_on_update` vor dem Überschreiben durch
PCM-Updates:

```json
"keep_on_update": ["^/plugins/com_github_Steffen-W_impartGUI/config\\.ini$"]
```

**Logdateien** (im Plugin-Verzeichnis, werden pro neuer Instanz überschrieben):
`plugin.log` (IPC/Standalone) und `plugin_fallback.log` (pcbnew-Fallback).

---

## 6. KiCad-seitige Einrichtung

Damit importierte Bibliotheken nutzbar sind, muss KiCad sie kennen:

1. **Umgebungsvariable** – *Preferences → Configure Paths → Environment Variables*:
   `KICAD_3RD_PARTY` = Bibliotheksordner.
2. **Symbolbibliotheken** – *Manage Symbol Libraries → Global*:
   `${KICAD_3RD_PARTY}/<Name>.kicad_sym`
3. **Footprintbibliotheken** – *Manage Footprint Libraries → Global*:
   `${KICAD_3RD_PARTY}/<Name>.pretty`
4. **KiCad neu starten.**

Die Option „auto KiCad setting“ erledigt Schritte 1–3 über `KiCad_Settings`, arbeitet
laut README aber nicht in allen KiCad-Versionen zuverlässig.

---

## 7. CLI-Nutzung

```bash
cd plugins
python -m KiCadImport --lib-folder ~/KiCad --download-file part.zip
python -m KiCadImport --lib-folder ~/KiCad --download-folder ~/Downloads
python -m KiCadImport --lib-folder ~/KiCad --easyeda C2040
```

Weitere Schalter: `--overwrite-if-exists`, `--path-variable`, `--prefer-step`,
`--lib-name`. Quelle: `plugins/KiCadImport/__main__.py` → `KiCadImport.main()`.

---

## 8. Build und Release

`generate_zip.sh` erzeugt das PCM-taugliche ZIP:

1. Submodule prüfen/initialisieren; `git submodule update --remote --merge` wird
   übersprungen, wenn dort lokale Änderungen liegen (`--no-update` erzwingt das).
2. `metadata.json` → `versions[0].version` auf das heutige Datum setzen (via `jq`).
3. In ein temporäres Build-Verzeichnis kopieren: `metadata.json`, `resources/`,
   die Top-Level-Dateien aus `plugins/` und alle Unterordner **außer** den Submodulen.
4. Aus den Submodulen nur `kiutils/src/kiutils` und `easyeda2kicad/easyeda2kicad`
   (Tests, Docs, CI entfallen) – die Verzeichnisstruktur bleibt erhalten.
5. Aufräumen: versteckte Ordner, `__pycache__`, `*.pyc`, `*.log`, `*.fbp`, `*.svg`.
6. `Import-LIB-KiCad-Plugin.zip` schreiben, Inhalt und Größe ausgeben.

Ein `trap cleanup EXIT` stellt `metadata.json` wieder her und löscht das Tempverzeichnis.
Voraussetzungen: `jq` und `zip`.

**CI** (`.github/workflows/nightly.yml`): bei jedem Push auf `master` Checkout mit
`submodules: recursive`, Build mit `--no-update`, Löschen des alten `nightly`-Releases
und Neuanlage als Pre-Release mit dem ZIP als Asset.

---

## 9. Entwicklungs-Setup

```bash
git clone --recurse-submodules https://github.com/Steffen-W/Import-LIB-KiCad-Plugin.git
cd Import-LIB-KiCad-Plugin
git submodule update --init          # falls ohne --recurse-submodules geklont
./generate_zip.sh
```

Debuggen ohne KiCad: `.vscode/launch.json` startet das Modul `plugins.impart_action`
direkt (entspricht `python -m plugins.impart_action`).

**Qualitätswerkzeuge** – Submodule sind überall ausgenommen:

| Werkzeug | Konfiguration | Besonderheit |
| --- | --- | --- |
| ruff | `ruff.toml` | `E,W,F,I,UP`, line-length 100, `impart_gui.py` ausgenommen |
| mypy | `mypy.ini` | `check_untyped_defs`, `mypy_path` auf beide Submodule |
| pyright | `pyrightconfig.json` | `typeCheckingMode: basic` |

Alle Module verwenden `from __future__ import annotations` und Typannotationen, um
mit Python 3.9 kompatibel zu bleiben.

---

## 10. Wichtige Architekturentscheidungen

- **Doppelte Import-Pfade überall** (`from .X import Y` mit `except ImportError:
  from X import Y`) – dieselbe Datei muss als Paketmodul (KiCad) *und* als Skript
  (CLI, Standalone) funktionieren.
- **Submodule statt pip** – KiCads Python-Umgebung ist im Fallback-Modus nicht
  zuverlässig beschreibbar; `sys.path`-Manipulation vermeidet jede Installationsanforderung.
- **String-Buffer statt direkter GUI-Ausgabe** – entkoppelt Worker-Threads komplett
  vom wx-Mainloop; nur der Poll-Thread erzeugt wx-Events.
- **Port als Lock** – keine verwaisten Lockfiles nach Absturz, da das Betriebssystem
  den Port mit dem Prozess freigibt.
- **Atomares Schreiben mit Verifikation und Rollback** – ein fehlgeschlagener Import
  darf eine gewachsene Bibliothek niemals beschädigen.
- **`kicad-cli` für Formatmigration** – statt Formatversionen selbst nachzubauen,
  wird KiCads eigenes Upgrade-Werkzeug aufgerufen.

---

## 11. KiCad API-Dokumentation

### IPC-API (empfohlen)

- [IPC API – Übersicht (dev-docs)](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/)
- [APIs and Bindings – Einstiegsseite](https://dev-docs.kicad.org/en/apis-and-binding/)
- [kicad-python (`kipy`) API-Referenz](https://docs.kicad.org/kicad-python-main/)
- [kicad-python – Quellcode (GitLab)](https://gitlab.com/kicad/code/kicad-python)
- [kicad-python auf PyPI](https://pypi.org/project/kicad-python/)
- [Protobuf-Definitionen der API](https://gitlab.com/kicad/code/kicad/-/blob/master/api/proto)

In diesem Projekt genutzt in `plugins/KiCadSettingsPaths/__init__.py`
(`from kipy import KiCad, errors`, `DocumentType.DOCTYPE_PCB` / `DOCTYPE_SCHEMATIC`).

### SWIG / pcbnew (Fallback, veraltet)

- [pcbnew Python Bindings – Übersicht](https://dev-docs.kicad.org/en/apis-and-binding/pcbnew/)
- [pcbnew Python Doxygen-Referenz](https://docs.kicad.org/doxygen-python/)
- [pcbnew Python Doxygen – KiCad 8.0](https://docs.kicad.org/doxygen-python-8.0/)

Genutzt in `plugins/__init__.py` (`pcbnew.ActionPlugin`) und
`KiCadSettingsPaths._load_swig_properties()`.

### Addons, Manifeste und Dateiformate

- [Addon-Entwicklung / PCM-Paketformat](https://dev-docs.kicad.org/en/addons/)
- [PCM-Metadaten-Schema](https://go.kicad.org/pcm/schemas/v1) – für `metadata.json`
- [API-Plugin-Schema](https://go.kicad.org/api/schemas/v1) – für `plugins/plugin.json`
- [KiCad-Dateiformate (S-Expressions)](https://dev-docs.kicad.org/en/file-formats/)
- [kicad-cli Referenz](https://docs.kicad.org/9.0/en/cli/cli.html)

### Bibliotheken der Submodule

- [kiutils Dokumentation](https://kiutils.readthedocs.io/)
- [easyeda2kicad.py (Upstream)](https://github.com/uPesy/easyeda2kicad.py)

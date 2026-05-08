# disc-archiver

Archivfeste Sicherung von Verzeichnissen auf optische Medien (BD-R, BD-XL, M-Disc) mit PAR2-Vorwärtsfehlerkorrektur.

> **Hinweis zum Reifegrad:** Dieses Repo ist im Mai 2026 von `langzeitarchiv-manager` zu `disc-archiver` umbenannt worden. Die kanonische Spezifikation liegt unter [`Specs.md`](Specs.md) und ist der **North Star**. Der aktuell implementierte Funktionsumfang (`disc-archiver pack` mit TAR/ISO/DMG-Output und PAR2-Sidecars) ist **noch nicht** das, was die Specs beschreiben (DATA/MANIFEST/PAR2-Layout, Multi-Disc-Splitting, SQLite-Index, Replicas usw.). Phase 1 der Specs wird in den folgenden Releases umgesetzt – siehe Specs.md, Abschnitt 13 „Implementierungs-Roadmap". Solange ist der CLI-Befehl pragmatisch nutzbar, aber nicht spec-konform.

## Voraussetzungen

| Werkzeug | Zweck | Installation |
|---|---|---|
| `par2` / `par2cmdline` | PAR2-Redundanzdaten | `brew install par2` (macOS) · `apt install par2` (Debian/Ubuntu) |
| `hdiutil` | ISO- und DMG-Image-Erzeugung (`--format iso` / `--format dmg`) | nur auf macOS, eingebaut |

Python **3.12+** wird vorausgesetzt.

## Installation

```bash
pipx install kurmann-disc-archiver       # nach erstem PyPI-Release
# oder lokal aus dem Repo:
pipx install .
```

Registriert das CLI-Kommando `disc-archiver`.

## Verwendung

### `disc-archiver pack`

Packt ein Verzeichnis in ein Archiv und erzeugt PAR2-Redundanzdaten daneben.

```bash
disc-archiver pack <source_dir> [--format tar|iso|dmg] [--output <dir>] [--redundancy <percent>]
```

Beispiele:

```bash
# Unkomprimiertes TAR in ~/DiscArchive/staging/ mit 15 % PAR2-Redundanz
disc-archiver pack ~/Projects/Familie_2025

# ISO mit 20 % Redundanz in eigenem Output-Verzeichnis
disc-archiver pack ~/Projects/Familie_2025 --format iso --output /Volumes/Archive --redundancy 20

# DMG (nur macOS)
disc-archiver pack ~/Projects/MyApp --format dmg --output ~/Desktop/Archives
```

Was passiert:

1. Quellverzeichnis wird validiert (leer-Check, 0-Byte-Datei-Check).
2. Archiv wird im Output-Verzeichnis erstellt (`Familie_2025.tar`, `.iso` oder `.dmg`).
3. PAR2-Sidecar-Dateien werden neben dem Archiv erzeugt.
4. Summary-Tabelle wird ausgegeben.

> Spec-Hinweis: Dieser `pack`-Befehl entspricht im Geist dem One-Shot-Idiom aus [`Specs.md`](Specs.md) §6.3, **nicht aber** dem dort beschriebenen DATA/MANIFEST/PAR2-Disc-Layout. Migration auf das Spec-Layout folgt in 0.3.0+.

### `disc-archiver config`

Persistente Einstellungen in `~/.config/disc-archiver/config.toml`.

```bash
# Alle Werte anzeigen
disc-archiver config list

# Einzelnen Wert lesen
disc-archiver config get pack.redundancy_percent

# Werte setzen
disc-archiver config set pack.redundancy_percent 20
disc-archiver config set pack.output_dir /Volumes/Archive/staging
disc-archiver config set pack.default_format iso
```

Konfigurierbare Schlüssel:

| Schlüssel | Typ | Default | Bedeutung |
|---|---|---|---|
| `pack.redundancy_percent` | int | `15` | PAR2-Redundanz in % |
| `pack.par2_volumes` | int | `1` | Anzahl PAR2-Volume-Dateien |
| `pack.output_dir` | str | `~/DiscArchive/staging/` | Default-Output-Verzeichnis |
| `pack.default_format` | str | `tar` | Default-Archivformat |

## Entwicklung

```bash
# Editable install
pip install -e ".[dev]"

# Tests
pytest
```

## Änderungsverlauf

Siehe [`CHANGELOG.md`](CHANGELOG.md). Vorabversionen vor 0.2.0 liefen unter dem alten Namen `langzeitarchiv-manager` (LAM); die Repo-Historie ist erhalten.

## Lizenz

Lizenz noch nicht festgelegt – wird vor dem ersten PyPI-Release ergänzt.

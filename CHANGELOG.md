# Änderungsverlauf

Alle nennenswerten Änderungen am `disc-archiver`-Repo werden in dieser Datei festgehalten.

Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), die Versionierung [Semantic Versioning](https://semver.org/lang/de/).

## [0.2.0] – 2026-05-08

### Geändert

- **Repo umbenannt** von `langzeitarchiv-manager` zu `disc-archiver` (GitHub: `kurmann/disc-archiver`).
- **PyPI-Paketname** auf die kurmann-Konvention gehoben: `kurmann-disc-archiver`.
- **Python-Importname** `lam` → `disc_archiver`.
- **CLI-Kommando** `langzeitarchiv-manager` (und der Alias `lam`, der bereits in PR #10 entfernt wurde) → `disc-archiver`.
- **XDG-Config-Pfad** `~/.config/langzeitarchiv-manager/` → `~/.config/disc-archiver/`. Bestehende Konfigurationen müssen manuell migriert werden (Datei verschieben).
- **Default-Output-Pfad** `~/LAM/staging/` → `~/DiscArchive/staging/`.
- **README** auf Deutsch und auf die neue Identität umgestellt, mit klarer Spec-vs.-Implementierungs-Trennung.
- **Beschreibung in `pyproject.toml`** auf den neuen Bounded Context („Archivfeste Sicherung auf optische Medien mit PAR2") angepasst.

### Hinzugefügt

- `Specs.md` als North-Star-Spezifikation im Repo-Root (umgezogen aus dem [atelier](https://github.com/kurmann/atelier) – aus `atelier/projects/disc-archiver/Specs.md`). Beschreibt das Ziel-Verhalten in Phase 1–4: Plan/Prepare/Pack mit DATA/MANIFEST/PAR2-Layout, Multi-Disc-Splitting, SQLite-Index, Verify/Repair, Replicas. **Wichtig:** Der aktuell implementierte Funktionsumfang (`pack` mit TAR/ISO/DMG-Sidecar-Output) ist noch nicht spec-konform. Migration folgt in 0.3.0+.
- `CHANGELOG.md` (vorher nicht vorhanden – Vorabversionen ergeben sich aus dem Git-Verlauf).

### Entfernt

- `specification.md` (alte Langzeitarchiv-Manager-Produktspezifikation, ersetzt durch das neue `Specs.md`).

### Hintergrund

Die Umbenennung ist Teil einer Bounded-Context-Reorganisation im kurmann-Ökosystem. Der frühere `langzeitarchiv-manager` und der bisher nur im Atelier spezifizierte `disc-archiver` deckten überlappende Domänen ab (Verzeichnis → Archiv mit PAR2-Redundanz). Da `disc-archiver` die strukturiertere und ökosystem-anschlussfähige Spec ist, wird das bestehende Repo unter dem neuen Namen weitergeführt und stufenweise an die Spec heranentwickelt. Phase 1 der Specs.md ist der nächste Implementierungsfokus.

## Vorabversionen

Vor 0.2.0 lief dieses Repo unter dem Namen `langzeitarchiv-manager` (CLI-Kurzform `lam`) ohne CHANGELOG. Die Versionen `0.1.0` und `0.1.1` sind im Git-Log nachvollziehbar; sie haben den heutigen `pack`-Befehl mit TAR/ISO/DMG-Output etabliert. Für Migrations-Zwecke gelten sie als Pre-0.2.0-Stände.

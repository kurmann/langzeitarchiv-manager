# disc-archiver – Spezifikation

PyPI-Paketname: `kurmann-disc-archiver`
Python-Importname: `disc_archiver`
CLI-Kommando: `disc-archiver`
Initialversion: `0.1.0`

## 1. Zweck

`disc-archiver` ist eine CLI zur **archivfesten Sicherung von Verzeichnissen auf optische Medien** (BD-R, BD-XL, M-Disc) mit dateibasierter Vorwärtsfehlerkorrektur via PAR2. Das Werkzeug bereitet Disc-Sets vor, materialisiert sie als brennfertige Staging-Verzeichnisse, verifiziert und repariert beschädigte Datenträger und führt einen lokalen Index aller archivierten Volumes.

Optische Discs sind das primäre Zielmedium. Festplatten- und SSD-**Replicas** identischer Volumes werden als zweites Medium unterstützt, mit Wiederverwendung der bereits berechneten PAR2-Files.

## 2. Verbindliche Architektur-Konventionen

Das Projekt folgt strikt den kurmann-Skills:

- `kurmann-python-api` – Projektstruktur, Request/Result-Muster, RuntimeOptions, Event-Callbacks, Teiloperationen als Public API
- `kurmann-cli-und-config` – Typer-Adapter, stdout/stderr-Trennung, Subcommand-Struktur, XDG-Config
- `kurmann-projekt-setup` – pyproject.toml mit setuptools, UV-Workflow, Sprachkonventionen, Teststrategie
- `kurmann-versionierung` – SemVer, CHANGELOG.md, README-Pflege

Alle Architekturentscheidungen, Code-Konventionen und CLI-Verhalten folgen diesen Skills. Bei Widerspruch zwischen Skill und Specs.md gewinnt der Skill, ausser die Specs.md macht eine explizit abweichende Entscheidung mit Begründung.

**Sprachen:** Doku, README, CHANGELOG, Kommentare auf Deutsch. Code-Bezeichner auf Englisch. **Event-`stage_id`-Werte und StrEnum-Mitglieder sind Code-Bezeichner und damit englisch (snake_case).** Nur das `message`-Feld eines Events ist deutscher UI-Text.

## 3. Verzeichnisstruktur

```
kurmann-disc-archiver/
├── src/
│   └── disc_archiver/
│       ├── __init__.py
│       ├── core/
│       │   ├── planning.py        # Disc-Set-Splitting-Logik
│       │   ├── manifest.py        # SHA256-Manifest-Erzeugung und -Verifikation
│       │   ├── par2.py            # PAR2-Wrapper (par2cmdline-turbo)
│       │   ├── materialization.py # Hardlink/Copy-Logik
│       │   ├── disc_info.py       # disc-info.toml Lesen/Schreiben
│       │   └── index.py           # SQLite-Index-Operationen
│       ├── api/
│       │   ├── __init__.py        # Public API Re-Exports
│       │   ├── facade.py          # API-Funktionen
│       │   ├── models.py          # Request/Result-Dataclasses
│       │   ├── events.py          # Event-Modelle (StrEnum + Dataclasses)
│       │   └── runtime.py         # RuntimeOptions
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py            # Typer-App, Subcommand-Registrierung
│       │   ├── plan_cmd.py
│       │   ├── prepare_cmd.py
│       │   ├── verify_cmd.py
│       │   ├── repair_cmd.py
│       │   ├── replica_cmd.py
│       │   ├── index_cmd.py
│       │   ├── config_cmd.py
│       │   └── internal_config.py # XDG-Config-Lesen (CLI-intern)
│       ├── services/
│       │   ├── par2_service.py    # Subprozess-Aufruf par2 Binary
│       │   ├── filesystem.py      # FS-Abstraktion (für Tests)
│       │   └── sqlite_store.py    # SQLite-Adapter
│       └── models/
│           ├── disc.py            # Disc, DiscSet, FileEntry
│           ├── plan.py            # ArchivePlan
│           ├── replica.py         # Replica, MediumType
│           └── enums.py           # SplitStrategy, MaterializationMode etc.
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── LICENSE
```

## 4. Datenmodelle

### 4.1 Enums

```python
class MediumType(StrEnum):
    BD_R = "bd-r"               # 25 GB, organische Beschichtung
    BD_R_XL = "bd-r-xl"         # 50/100 GB
    BD_M_DISC = "bd-m-disc"     # 25/50/100 GB anorganisch, langzeitstabil
    HDD_REPLICA = "hdd-replica"
    SSD_REPLICA = "ssd-replica"

class SplitStrategy(StrEnum):
    BY_SIZE = "by-size"           # Greedy nach Grösse
    BY_FOLDER = "by-folder"       # Ganze Top-Level-Ordner zusammen halten
    BY_FILE = "by-file"           # Reine Dateiliste, keine Strukturberücksichtigung

class MaterializationMode(StrEnum):
    HARDLINK = "hardlink"
    COPY = "copy"

class ReplicaStatus(StrEnum):
    ACTIVE = "active"
    DEGRADED = "degraded"         # Verify hat Fehler gefunden
    LOST = "lost"                 # Disc unleserlich oder HDD-Pfad weg
```

### 4.2 Domänenobjekte

```python
@dataclass
class FileEntry:
    relative_path: Path
    size_bytes: int
    sha256: str
    mtime: datetime

@dataclass
class DiscSet:
    disc_number: int
    files: list[FileEntry]
    payload_bytes: int
    par2_bytes_estimated: int
    overhead_bytes_estimated: int  # UDF/ISO overhead
    total_bytes: int

@dataclass
class ArchivePlan:
    plan_id: str                   # ULID
    source_path: Path
    created_at: datetime
    discs: list[DiscSet]
    oversized_files: list[FileEntry]  # Einzeldatei > Disc-Kapazität
    par2_redundancy_percent: int
    disc_capacity_bytes: int
```

### 4.3 Requests / Results

```python
# plan_archive
@dataclass
class PlanArchiveRequest:
    source_path: Path
    files: list[Path] | None = None  # optional: explizite Dateiliste (relativ zu source_path). None = source_path scannen
    disc_capacity_bytes: int = 25_000_000_000
    par2_redundancy_percent: int = 15
    strategy: SplitStrategy = SplitStrategy.BY_SIZE
    reserve_bytes: int = 500_000_000  # Sicherheitsmarge UDF/Overhead
    excludes: list[str] = field(default_factory=list)  # Glob-Patterns; bei expliziter `files`-Liste ignoriert

@dataclass
class PlanArchiveResult:
    success: bool
    plan: ArchivePlan | None = None
    error_message: str | None = None

# pack_directory – One-Shot-Komfortfunktion: plan + prepare für Disc 1 in einem Schritt.
# Schlägt fehl, wenn der Inhalt grösser als eine Disc ist.
@dataclass
class PackDirectoryRequest:
    source_path: Path
    files: list[Path] | None = None
    output_dir: Path | None = None
    disc_capacity_bytes: int = 25_000_000_000
    par2_redundancy_percent: int = 15
    excludes: list[str] = field(default_factory=list)
    materialization: MaterializationMode | None = None
    strict_hardlinks: bool = False

@dataclass
class PackDirectoryResult:
    success: bool
    plan_id: str | None = None       # interner Plan, kann aber für spätere Operationen referenziert werden
    staging_dir: Path | None = None
    manifest_path: Path | None = None
    par2_index_path: Path | None = None
    disc_info_path: Path | None = None
    materialization_used: MaterializationMode | None = None
    error_message: str | None = None
    # Wenn der Inhalt nicht auf eine Disc passt:
    requires_multiple_discs: bool = False
    estimated_disc_count: int | None = None

# prepare_disc
@dataclass
class PrepareDiscRequest:
    plan_id: str
    disc_number: int
    output_dir: Path | None = None  # Default: XDG-Cache/disc-archiver/staging/<plan_id>/disc-N
    materialization: MaterializationMode | None = None  # None = auto (Hardlink mit Fallback)
    strict_hardlinks: bool = False  # True = Abbruch wenn Hardlink unmöglich

@dataclass
class PrepareDiscResult:
    success: bool
    staging_dir: Path | None = None
    manifest_path: Path | None = None
    par2_index_path: Path | None = None
    disc_info_path: Path | None = None
    materialization_used: MaterializationMode | None = None
    error_message: str | None = None

# verify_disc
@dataclass
class VerifyDiscRequest:
    target_path: Path  # Staging-Dir oder gemountete Disc
    use_par2: bool = True

@dataclass
class VerifyDiscResult:
    success: bool                  # True = alles OK
    files_checked: int = 0
    files_failed: int = 0
    failed_files: list[Path] = field(default_factory=list)
    par2_repairable: bool | None = None
    error_message: str | None = None

# repair_disc
@dataclass
class RepairDiscRequest:
    target_path: Path
    in_place: bool = False         # False = Reparatur in neues Verzeichnis
    output_dir: Path | None = None

@dataclass
class RepairDiscResult:
    success: bool
    repaired_files: list[Path] = field(default_factory=list)
    unrepairable_files: list[Path] = field(default_factory=list)
    output_dir: Path | None = None
    error_message: str | None = None

# replica_create
@dataclass
class CreateReplicaRequest:
    disc_id: str                   # Existierende Disc im Index
    target_path: Path              # z.B. /Volumes/Archive-HDD-1/BD-042
    medium_type: MediumType = MediumType.HDD_REPLICA
    source_staging_dir: Path | None = None  # Wenn Staging noch existiert
    source_disc_path: Path | None = None    # Alternativ: gemountete Original-Disc

@dataclass
class CreateReplicaResult:
    success: bool
    replica_id: str | None = None
    target_path: Path | None = None
    error_message: str | None = None

# Index-Operationen
@dataclass
class RegisterDiscRequest:
    staging_dir: Path
    label: str
    burned_on: date
    medium_type: MediumType = MediumType.BD_R
    notes: str = ""

@dataclass
class RegisterDiscResult:
    success: bool
    disc_id: str | None = None
    error_message: str | None = None

@dataclass
class QueryIndexRequest:
    paths: list[Path] | None = None       # Welche Files sind bereits archiviert?
    sha256_hashes: list[str] | None = None
    label_pattern: str | None = None      # Glob

@dataclass
class QueryIndexResult:
    success: bool
    matches: list[IndexMatch] = field(default_factory=list)
    error_message: str | None = None

@dataclass
class IndexMatch:
    disc_id: str
    label: str
    relative_path: Path
    sha256: str
    burned_on: date

@dataclass
class LocateFileRequest:
    sha256: str | None = None
    path_pattern: str | None = None

@dataclass
class LocateFileResult:
    success: bool
    locations: list[FileLocation] = field(default_factory=list)
    error_message: str | None = None

@dataclass
class FileLocation:
    disc_id: str
    disc_label: str
    relative_path: Path
    replicas: list[ReplicaInfo]

@dataclass
class ReplicaInfo:
    replica_id: str
    medium_type: MediumType
    location: str
    status: ReplicaStatus
    last_verified: datetime | None
```

### 4.4 RuntimeOptions

```python
@dataclass
class RuntimeOptions:
    par2_path: str = "par2"                      # par2cmdline-turbo via PATH
    par2_threads: int = 0                         # 0 = auto
    par2_volumes: int = 7                         # -n Parameter
    hash_algorithm: str = "sha256"
    index_db_path: Path | None = None             # Default: XDG-Data
    staging_root: Path | None = None              # Default: XDG-Cache
    temp_dir: Path | None = None
```

### 4.5 Events

Drei separate Event-Kanäle gemäss kurmann-python-api Punkt 5. Jede lang laufende API-Funktion bietet `on_event` (typisierte Events) und `on_output` (Roh-Output von par2 etc.).

```python
class PlanStage(StrEnum):
    SCAN_STARTED = "scan_started"
    HASHING_STARTED = "hashing_started"
    HASHED = "hashed"
    SPLITTING = "splitting"
    PLAN_READY = "plan_ready"

@dataclass
class PlanArchiveEvent:
    stage_id: str            # stabiler Code-Bezeichner, englisch
    message: str             # menschenlesbare Nachricht auf Deutsch
    current: int | None = None
    total: int | None = None

class PrepareStage(StrEnum):
    MATERIALIZATION_STARTED = "materialization_started"
    MATERIALIZATION_FALLBACK_TO_COPY = "materialization_fallback_to_copy"
    MATERIALIZATION_DONE = "materialization_done"
    MANIFEST_WRITTEN = "manifest_written"
    DISC_INFO_WRITTEN = "disc_info_written"
    PAR2_STARTED = "par2_started"
    PAR2_DONE = "par2_done"

@dataclass
class PrepareDiscEvent:
    stage_id: str
    message: str
    current: int | None = None
    total: int | None = None

# Analog VerifyDiscEvent, RepairDiscEvent, CreateReplicaEvent.
# Stage-IDs immer englisch (Code-Bezeichner).
# message-Feld immer Deutsch (Nutzer-UI).
```

## 5. Public API – Fassade

```python
# api/__init__.py
from .facade import (
    plan_archive,
    prepare_disc,
    pack_directory,
    verify_disc,
    repair_disc,
    create_replica,
    index_register,
    index_query,
    index_locate_file,
    index_list_discs,
    index_record_event,
)
from .models import (
    PlanArchiveRequest, PlanArchiveResult,
    PrepareDiscRequest, PrepareDiscResult,
    PackDirectoryRequest, PackDirectoryResult,
    VerifyDiscRequest, VerifyDiscResult,
    RepairDiscRequest, RepairDiscResult,
    CreateReplicaRequest, CreateReplicaResult,
    RegisterDiscRequest, RegisterDiscResult,
    QueryIndexRequest, QueryIndexResult,
    LocateFileRequest, LocateFileResult,
)
from .runtime import RuntimeOptions
from .events import (
    PlanArchiveEvent, PrepareDiscEvent, VerifyDiscEvent,
    RepairDiscEvent, CreateReplicaEvent,
)

__all__ = [
    "plan_archive", "prepare_disc", "pack_directory",
    "verify_disc", "repair_disc",
    "create_replica",
    "index_register", "index_query", "index_locate_file",
    "index_list_discs", "index_record_event",
    "RuntimeOptions",
    # Requests / Results / Events ...
]
```

Signaturen aller API-Funktionen:

```python
def plan_archive(
    request: PlanArchiveRequest,
    runtime: RuntimeOptions | None = None,
    on_event: Callable[[PlanArchiveEvent], None] | None = None,
) -> PlanArchiveResult: ...

def prepare_disc(
    request: PrepareDiscRequest,
    runtime: RuntimeOptions | None = None,
    on_event: Callable[[PrepareDiscEvent], None] | None = None,
    on_output: Callable[[str], None] | None = None,
) -> PrepareDiscResult: ...

def pack_directory(
    request: PackDirectoryRequest,
    runtime: RuntimeOptions | None = None,
    on_event: Callable[[PrepareDiscEvent], None] | None = None,
    on_output: Callable[[str], None] | None = None,
) -> PackDirectoryResult: ...

def verify_disc(
    request: VerifyDiscRequest,
    runtime: RuntimeOptions | None = None,
    on_event: Callable[[VerifyDiscEvent], None] | None = None,
    on_output: Callable[[str], None] | None = None,
) -> VerifyDiscResult: ...

def repair_disc(
    request: RepairDiscRequest,
    runtime: RuntimeOptions | None = None,
    on_event: Callable[[RepairDiscEvent], None] | None = None,
    on_output: Callable[[str], None] | None = None,
) -> RepairDiscResult: ...

def create_replica(
    request: CreateReplicaRequest,
    runtime: RuntimeOptions | None = None,
    on_event: Callable[[CreateReplicaEvent], None] | None = None,
) -> CreateReplicaResult: ...

def index_register(
    request: RegisterDiscRequest,
    runtime: RuntimeOptions | None = None,
) -> RegisterDiscResult: ...

def index_query(
    request: QueryIndexRequest,
    runtime: RuntimeOptions | None = None,
) -> QueryIndexResult: ...

def index_locate_file(
    request: LocateFileRequest,
    runtime: RuntimeOptions | None = None,
) -> LocateFileResult: ...
```

**Wichtig:** `plan_archive` und `prepare_disc` sind explizit als getrennte Teiloperationen verfügbar – damit eine Host-Applikation (z. B. `archive-manager`) den Plan prüfen, modifizieren oder verwerfen kann, bevor PAR2 berechnet wird. `pack_directory` ist die zulässige One-Shot-Komfortfunktion gemäss `kurmann-python-api` Punkt 7: Sie macht intern `plan_archive` + `prepare_disc` für Disc 1 in einem Schritt und verlangt, dass der Inhalt auf eine Disc passt. Wenn nicht, wird `requires_multiple_discs=True` mit der geschätzten Disc-Anzahl zurückgegeben, und der Nutzer wird auf den expliziten `plan` + `prepare`-Workflow verwiesen.

Pläne werden als JSON in `XDG_DATA_HOME/disc-archiver/plans/<plan-id>.json` persistiert. `prepare_disc(plan_id, ...)` lädt den Plan von dort. `pack_directory` schreibt seinen internen Plan ebenfalls dorthin, damit `verify`/`repair` später problemlos funktioniert.

## 6. CLI – Subcommand-Struktur

```
disc-archiver
├── plan <source-path>
├── prepare <plan-id> --disc <n>
├── pack <source-path> [--output-dir <path>]    # One-Shot: plan + prepare für Single-Disc-Inhalte
├── verify <target-path>
├── repair <target-path>
├── replica
│   ├── create <disc-id> --target <path>
│   ├── list <disc-id>
│   └── verify <replica-id>
├── index
│   ├── list
│   ├── show <disc-id>
│   ├── search <query>
│   ├── locate <sha256|path-pattern>
│   └── register <staging-dir> --label <label> --burned-on <date>
└── config
    ├── set <key> <value>
    ├── get <key>
    └── list
```

Top-Level-Struktur folgt zwingend `kurmann-cli-und-config` Punkt 5: `invoke_without_command=True`, `@app.callback()`, alle Commands mit explizitem `name=`.

### 6.1 Beispiel: plan-Command

```bash
disc-archiver plan /mnt/lyssach1/archiv/videoschnitt \
    --disc-size 25G \
    --par2-redundancy 15 \
    --strategy by-folder \
    --exclude "*/Cache/*" \
    --exclude ".DS_Store"
```

Ausgabe:
- **stdout:** `plan_id` als einzige Zeile (pipeline-fähig)
- **stderr:** Menschliche Übersicht (Anzahl Discs, Total-Grösse, Warnungen für oversized files)

### 6.2 Beispiel: prepare-Command

```bash
disc-archiver prepare 01HW8K3R9F7QXZ5B2N4M6P8VTC --disc 1 \
    --output-dir /Volumes/Archive-HDD-1/staging/BD-042
```

Ausgabe:
- **stdout:** Pfad zum Staging-Verzeichnis
- **stderr:** Fortschritt (Hash, Materialisierung, PAR2)

### 6.3 Beispiel: pack-Command

One-Shot für den Brenntool-Anwendungsfall: ein Verzeichnis, das auf eine Disc passt, wird mit PAR2 versehen und ist sofort brennfertig. Kein Index-Eintrag, kein Plan-Tracking aus Nutzersicht.

```bash
disc-archiver pack /Volumes/source/altes-projekt --output-dir /tmp/staging
```

Ausgabe:
- **stdout:** Pfad zum Staging-Verzeichnis
- **stderr:** Fortschritt (Hash, Materialisierung, PAR2)
- **Exit 6** (siehe 6.4): Inhalt passt nicht auf eine Disc, geschätzte Disc-Anzahl wird auf stderr ausgegeben mit Hinweis auf `plan` + `prepare`-Workflow.

Typischer Folge-Workflow:
```bash
STAGING=$(disc-archiver pack /Volumes/source/altes-projekt)
hdiutil burn "$STAGING"        # oder Brenntool deiner Wahl
disc-archiver verify /Volumes/altes-projekt   # nach dem Brennen
rm -rf "$STAGING"              # Staging aufräumen, wenn Disc reicht
```

### 6.4 Exit-Codes

| Code | Bedeutung |
|---|---|
| 0 | Erfolg |
| 1 | Allgemeiner Laufzeitfehler |
| 2 | Ungültige Argumente / Konfigurationsfehler |
| 3 | Verifikation hat Fehler gefunden, aber durch PAR2 reparierbar |
| 4 | Verifikation hat unrettbare Fehler gefunden |
| 5 | Hardlink unmöglich und `--strict-hardlinks` aktiv |
| 6 | `pack`: Inhalt passt nicht auf eine Disc (geschätzte Anzahl wird auf stderr genannt) |

### 6.5 --verbose-Verhalten

`--verbose` gibt zusätzlich auf stderr aus:
- Roh-Output von `par2` (über `on_output`-Callback)
- Feinere Events (z. B. jeden gehashten File einzeln)

`--verbose` verändert **niemals** stdout.

## 7. Disc-Layout

Jede Disc – egal ob optisch oder als HDD-Replica – hat folgende Struktur:

```
<volume-root>/
├── DATA/
│   └── <ursprungsstruktur erhalten>
├── MANIFEST/
│   ├── SHA256SUMS              # Format: <sha256>␣␣<relative-path>
│   └── disc-info.toml          # Disc-Eigenmetadaten
└── PAR2/
    ├── archiv.par2             # Index
    ├── archiv.vol000+01.par2
    ├── archiv.vol001+02.par2
    └── ... (insg. par2_volumes Volumes)
```

**SHA256SUMS** umfasst alle Files unter `DATA/`, Pfade relativ zu `DATA/`. Format kompatibel mit `sha256sum -c`.

**disc-info.toml** enthält die selbsterklärende Disc-Identität:

```toml
[disc]
id = "01HW8K3R9F7QXZ5B2N4M6P8VTC"
label = "BD-042"
burned_on = "2026-05-04"
medium_type = "BD-R"
capacity_gb = 25

[archive]
plan_id = "01HW8K2P5B3F9XQZ7N4M6V8TRD"
disc_number = 3
total_discs = 7
par2_redundancy_percent = 15
par2_volumes = 7
hash_algorithm = "sha256"

[creator]
tool = "disc-archiver"
tool_version = "0.1.0"
```

Disc-IDs sind ULIDs (zeitgeordnet, URL-safe, 26 Zeichen). Plan-IDs ebenfalls ULIDs.

## 8. PAR2-Integration

Externes Tool: `par2cmdline-turbo` (unter Linux/macOS via Homebrew/apt verfügbar). Aufruf als Subprozess.

### 8.1 Erzeugung

```
par2 create -r15 -n7 -- archiv.par2 <alle DATA-Files>
```

- `-r15` aus `request.par2_redundancy_percent`
- `-n7` aus `runtime.par2_volumes`
- Arbeitsverzeichnis: `<staging>/PAR2/`
- Pfade relativ zu `<staging>/` (Geschwister-Pfad nach `DATA/`)
- `--` Trenner gegen Pfad-Argumente die mit `-` beginnen

### 8.2 Verifikation

```
par2 verify -- archiv.par2
```

Exit-Codes von par2 mappen auf VerifyDiscResult:
- 0 → success
- 1 → reparable (par2_repairable=True)
- andere → unreparable

### 8.3 Reparatur

```
par2 repair -- archiv.par2
```

### 8.4 Output-Streaming

stdout/stderr von par2 werden zeilenweise abgegriffen und an `on_output`-Callback weitergereicht. Niemals direkt ans Terminal durchschleifen.

## 9. Materialisierung

`prepare_disc` materialisiert Files vom Quellpfad ins Staging-Verzeichnis. Standard: Hardlink-Versuch mit transparentem Fallback auf Kopie.

```python
def materialize_file(src: Path, dst: Path, runtime: RuntimeOptions, *, strict: bool) -> MaterializationMode:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
        return MaterializationMode.HARDLINK
    except OSError as e:
        # EXDEV: cross-device link not permitted; EPERM: dateisystem unterstützt kein link
        if strict:
            raise
        shutil.copy2(src, dst)
        return MaterializationMode.COPY
```

Bei Fallback wird **einmalig pro Disc** ein Event `MATERIALIZATION_FALLBACK_TO_COPY` ausgelöst (nicht für jede Datei). Die `message` des Events ist auf Deutsch (z. B. `"Hardlink nicht möglich – Wechsle auf Kopie."`).

## 10. SQLite-Index

**Speicherort:** `XDG_DATA_HOME/disc-archiver/catalog.sqlite` (Default: `~/.local/share/disc-archiver/catalog.sqlite`).

**Schema (Initialversion):**

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY
);
INSERT INTO schema_version (version) VALUES (1);

CREATE TABLE discs (
    disc_id TEXT PRIMARY KEY,           -- ULID
    label TEXT NOT NULL UNIQUE,
    plan_id TEXT NOT NULL,
    disc_number INTEGER NOT NULL,
    total_discs INTEGER NOT NULL,
    burned_on TEXT NOT NULL,            -- ISO-Date
    medium_type TEXT NOT NULL,
    capacity_bytes INTEGER NOT NULL,
    par2_redundancy_percent INTEGER NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL            -- ISO-Datetime
);

CREATE TABLE files (
    file_id TEXT PRIMARY KEY,           -- ULID
    disc_id TEXT NOT NULL REFERENCES discs(disc_id) ON DELETE CASCADE,
    relative_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    mtime TEXT NOT NULL                 -- ISO-Datetime
);

CREATE INDEX idx_files_sha256 ON files(sha256);
CREATE INDEX idx_files_disc ON files(disc_id);
CREATE INDEX idx_files_path ON files(relative_path);

CREATE TABLE replicas (
    replica_id TEXT PRIMARY KEY,        -- ULID
    disc_id TEXT NOT NULL REFERENCES discs(disc_id) ON DELETE CASCADE,
    medium_type TEXT NOT NULL,
    location TEXT NOT NULL,             -- Pfad oder Schrank-Position
    status TEXT NOT NULL,               -- ReplicaStatus
    created_on TEXT NOT NULL,
    last_verified TEXT                  -- nullable
);

CREATE TABLE events (
    event_id TEXT PRIMARY KEY,          -- ULID
    disc_id TEXT REFERENCES discs(disc_id) ON DELETE CASCADE,
    replica_id TEXT REFERENCES replicas(replica_id) ON DELETE CASCADE,
    kind TEXT NOT NULL,                 -- 'verify_ok', 'verify_failed', 'repair', 'replica_created'
    occurred_at TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);
```

**Schema-Versionierung:** Vor jedem DB-Zugriff `schema_version` lesen. Migrationen in `core/index_migrations.py` als nummerierte Funktionen (`migrate_v1_to_v2()` etc.). Phase 1 muss nur `v1` ausliefern.

**Query-Pattern:**
- `index_query(paths=[...])` → `WHERE relative_path IN (...)`
- `index_query(sha256_hashes=[...])` → `WHERE sha256 IN (...)` (für Dedup-Erkennung)
- `index_locate_file(sha256=...)` → JOIN über discs und replicas

**JSON-Export:** Optionaler Subcommand `disc-archiver index export <path>` schreibt vollständigen Index als formatiertes JSON. Nicht Teil der Phase-1-Implementierung, aber Schema soll dafür ausgelegt sein (alle Felder serialisierbar).

## 11. Konfigurationsschlüssel

XDG-Pfad: `~/.config/disc-archiver/config.toml`.

Konfigurierbare Schlüssel (alle optional, mit Defaults):

```toml
[par2]
path = "par2"                         # Werkzeug-Pfad
threads = 0                           # 0 = auto
volumes = 7                           # -n Parameter
default_redundancy_percent = 15

[storage]
index_db_path = ""                    # leer = XDG-Default
staging_root = ""                     # leer = XDG-Cache-Default

[defaults]
disc_capacity_gb = 25
medium_type = "bd-r"
reserve_bytes = 500000000             # UDF-Overhead-Reserve
hash_algorithm = "sha256"

[ulid]
# (keine Konfiguration nötig)
```

CLI: `disc-archiver config set par2.default_redundancy_percent 15` etc. Punkt-Notation für verschachtelte Schlüssel.

## 12. Was NICHT zum Scope gehört

Folgendes ist **explizit ausserhalb** des Scopes von `disc-archiver` und gehört in den späteren `archive-manager`:

- Quellverzeichnis-Policies (Mindestalter, Schwellen-Grössen, Excludes auf Profilebene)
- Inkrementelle Backups, Snapshots, Versionierung über die Zeit
- Live-Monitoring von Quellverzeichnissen
- Disc-Verschleiss-Vorhersage / proaktive Replica-Erneuerung
- Brennvorgang selbst (`hdiutil burn`, `growisofs` etc.) – nur Staging wird vorbereitet
- ISO-Bau – Phase 2 (siehe Roadmap)

Wenn ein Feature nur für HDD oder nur für eine bestimmte Quelle Sinn macht, gehört es nicht in dieses Tool.

## 13. Implementierungs-Roadmap

Bauplan in vier inkrementellen Phasen. Jede Phase endet mit einer release-fähigen Version inkl. CHANGELOG-Eintrag.

### Phase 1 → Version 0.1.0 – Plan, Prepare & Pack (Kernfunktion)
- Projekt-Skeleton, pyproject.toml, README, CHANGELOG
- Datenmodelle, Enums, Events, RuntimeOptions
- `core/planning.py` mit `BY_SIZE`-Strategie
- `PlanArchiveRequest.files` als optionaler Parameter (explizite Dateiliste statt Verzeichnis-Scan)
- `core/manifest.py` (SHA256-Berechnung und SHA256SUMS-Schreiben)
- `core/par2.py` und `services/par2_service.py`
- `core/materialization.py` (Hardlink-mit-Fallback)
- `core/disc_info.py`
- API-Funktionen `plan_archive`, `prepare_disc`, `pack_directory`
- CLI: `plan`, `prepare`, `pack`, `config`
- Plan-Persistenz als JSON (auch für intern erzeugte Pläne aus `pack_directory`)
- Unit-Tests für core, Integration-Test für CLI mit `tmp_path`

### Phase 2 → Version 0.2.0 – Verify & Repair
- `verify_disc`, `repair_disc` API-Funktionen
- CLI: `verify`, `repair`
- PAR2 verify/repair mit korrekter Exit-Code-Mappierung
- Manifest-Verifikation (Pre-PAR2-Check via SHA256)
- Tests mit künstlich beschädigten Files

### Phase 3 → Version 0.3.0 – Index
- SQLite-Schema und Migrations-Framework
- `core/index.py` und `services/sqlite_store.py`
- API-Funktionen `index_register`, `index_query`, `index_locate_file`, `index_list_discs`, `index_record_event`
- CLI: `index list/show/search/locate/register`
- Auto-Recording von Verify-Events: `verify` schreibt automatisch ein `events`-Eintrag
- `BY_FOLDER`-Strategie zusätzlich zu `BY_SIZE`

### Phase 4 → Version 0.4.0 – Replicas
- `create_replica` API
- CLI: `replica create/list/verify`
- Replica-Verifikation reuse `verify_disc`-Logik mit anderen Pfad
- `replica verify` updated `last_verified` und schreibt Event

### Phase 5+ (offen)
- ISO-Bau via `hdiutil`/`xorriso` als zusätzliche Output-Option
- JSON-Export des Index
- `BY_FILE`-Strategie
- `index export` und `index rebuild-from-discs` (Index aus disc-info.toml-Daten rekonstruieren)

Versionssprung auf `1.0.0` erst, wenn alle obigen Phasen integriert und produktiv erprobt sind.

## 14. Test-Strategie

Gemäss `kurmann-projekt-setup` Punkt 4: Kernfunktionen testen, kein 100%-Zwang.

Pflicht-Tests:
- `core/planning.py` – Splitting-Korrektheit, Edge Cases (oversized files, leeres Verzeichnis, einzelne Datei genau Disc-Grösse)
- `core/manifest.py` – Hash-Korrektheit, SHA256SUMS-Format, Round-Trip
- `core/par2.py` – Mock von par2-Subprozess, Exit-Code-Mapping
- `core/materialization.py` – Hardlink-Erfolg + Fallback (mit `unittest.mock` für `os.link`)
- `core/index.py` – CRUD-Operationen, Schema-Migration
- `api/facade.py` – Erfolgs- und Fehlerpfade je Funktion
- CLI: `typer.testing.CliRunner` mit `tmp_path` für jeden Subcommand

Mocks:
- `par2`-Binary nicht in CI ausführen → Subprocess-Mock
- Echte Disc nicht in CI mounten → Filesystem-Tests im `tmp_path`

## 15. Externe Abhängigkeiten

### 15.1 Python-Pakete

```toml
dependencies = [
    "typer>=0.12",
    "rich>=13",
    "python-ulid>=2.0",
    "tomli-w>=1.0",          # TOML schreiben (disc-info.toml, config.toml)
]
# tomllib ist ab Python 3.11 in der Standardbibliothek (nur Lesen).

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov>=5",
]
```

### 15.2 System-Werkzeuge

| Werkzeug | Zweck | Pflicht |
|---|---|---|
| `par2` (par2cmdline-turbo) | PAR2 erzeugen/verifizieren/reparieren | Ja |
| `sha256sum` | optional, intern via Python `hashlib` | Nein |

Im README unter «Voraussetzungen» dokumentieren mit Installations-Hinweisen für macOS (Homebrew) und Linux (apt).

## 16. Akzeptanzkriterien Phase 1 (für Claude Code)

Phase 1 gilt als abgeschlossen, wenn folgende Befehlsfolge auf einem realen Verzeichnis fehlerfrei läuft:

```bash
# Vorbereitung
mkdir -p /tmp/test-archiv/projekt-A /tmp/test-archiv/projekt-B
dd if=/dev/urandom of=/tmp/test-archiv/projekt-A/video1.mov bs=1M count=200
dd if=/dev/urandom of=/tmp/test-archiv/projekt-B/video2.mov bs=1M count=300

# Plan erstellen
PLAN_ID=$(disc-archiver plan /tmp/test-archiv --disc-size 1G --par2-redundancy 10)
echo "Plan: $PLAN_ID"

# Disc 1 vorbereiten
STAGING=$(disc-archiver prepare $PLAN_ID --disc 1 --output-dir /tmp/staging-1)
echo "Staging: $STAGING"

# Manuelle Prüfungen
test -f $STAGING/MANIFEST/SHA256SUMS
test -f $STAGING/MANIFEST/disc-info.toml
test -f $STAGING/PAR2/archiv.par2
ls $STAGING/PAR2/archiv.vol*.par2 | wc -l       # >= 1
sha256sum -c $STAGING/MANIFEST/SHA256SUMS       # alle OK

# Hardlink-Verifikation: Inode des Originals und im Staging identisch
ORIG_INODE=$(stat -f %i /tmp/test-archiv/projekt-A/video1.mov)
STAGING_INODE=$(stat -f %i $STAGING/DATA/projekt-A/video1.mov)
test "$ORIG_INODE" = "$STAGING_INODE"

# pack-Workflow für Single-Disc-Inhalte (One-Shot)
mkdir -p /tmp/small-archiv
dd if=/dev/urandom of=/tmp/small-archiv/datei.bin bs=1M count=10
PACK_STAGING=$(disc-archiver pack /tmp/small-archiv --output-dir /tmp/pack-staging)
test -f $PACK_STAGING/MANIFEST/SHA256SUMS
test -f $PACK_STAGING/PAR2/archiv.par2
sha256sum -c $PACK_STAGING/MANIFEST/SHA256SUMS

# pack mit zu grossem Inhalt: Exit-Code 6, kein Staging
disc-archiver pack /tmp/test-archiv --disc-size 10M
test $? -eq 6
```

Alle stdout-Ausgaben müssen pipeline-tauglich sein (nur die geforderten IDs/Pfade). Alle Statusmeldungen gehen auf stderr.

## 17. Erste konkrete Schritte für Claude Code

1. Repository initialisieren mit Verzeichnisstruktur aus Abschnitt 3
2. `pyproject.toml` aus `kurmann-projekt-setup` ableiten, Version `0.1.0`
3. `CHANGELOG.md` mit `## [0.1.0] – <heute>` und Initialeintrag
4. `README.md` mit Mindeststruktur (Voraussetzungen, Installation, Verwendung)
5. Datenmodelle und Enums anlegen (Abschnitt 4)
6. `core/`-Module Top-down implementieren: planning → manifest → materialization → par2 → disc_info
7. `api/facade.py` mit `plan_archive`, `prepare_disc`, `pack_directory` (`pack_directory` als dünner Wrapper)
8. CLI mit `plan`, `prepare`, `pack`, `config` (Stub mit Hilfeausgabe für Subcommands aus Phase 2+)
9. Tests
10. Phase 1 abschliessen mit Versions-Check und CHANGELOG-Eintrag gemäss `kurmann-versionierung`

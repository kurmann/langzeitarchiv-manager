# Design-Entscheidung: `mkisofs`/`xorriso` statt `hdiutil` für ISO-9660/UDF-Images

## Zusammenfassung

Für die Erstellung von **ISO-9660/UDF-Images** wird im LAM primär `xorriso -as mkisofs` (bzw. `mkisofs`) verwendet – **nicht** `hdiutil`. Diese Entscheidung basiert auf den Kernprinzipien des LAM: Plattformunabhängigkeit, Langzeitlesbarkeit, Reproduzierbarkeit und vollständige Kontrolle über die ISO/UDF-Optionen.

`hdiutil` bleibt für **DMG-Workflows** das Werkzeug der Wahl.

---

## Begründung im Detail

### 1. `hdiutil` ist macOS-spezifisch

`hdiutil` ist ein proprietäres Apple-Tool und ausschließlich unter macOS verfügbar. Es ist hervorragend für das Erstellen, Mounten und Verschlüsseln von DMG-Images geeignet – einem Apple-eigenen Format. Für ISO-9660/UDF-Images ist `hdiutil` jedoch nicht die optimale Wahl:

- Die ISO-Erstellung via `hdiutil` ist eine Sekundärfunktion; Parameter für ISO-Level, UDF-Versionen, Joliet oder Rock Ridge lassen sich kaum oder gar nicht gezielt steuern.
- Der erzeugte Output ist an das macOS-Ökosystem gebunden. Reproduzierbarkeit (Byte-identische Ergebnisse) ist nicht garantiert.
- Auf Linux oder Windows steht `hdiutil` grundsätzlich nicht zur Verfügung.

### 2. `mkisofs`/`xorriso` ist cross-platform und seit Jahrzehnten etabliert

`xorriso` (mit dem `mkisofs`-Kompatibilitätsmodus via `-as mkisofs`) und das klassische `mkisofs` sind:

- **Plattformübergreifend:** Verfügbar auf macOS (via Homebrew: `brew install xorriso`), Linux (via Paketmanager) und indirekt auf Windows (via WSL oder Cygwin).
- **Offen und dokumentiert:** Beides sind freie, quelloffene Werkzeuge mit umfangreicher Dokumentation, die seit Jahrzehnten in Distributions- und Archivierungskontexten eingesetzt werden (z. B. zum Mastern von Linux-Installationsmedien).
- **Reproduzierbar:** Über identische Parameter lassen sich byte-identische Images erzeugen – wichtig für die Verifikation und die Langzeitintegrität.

### 3. Vollständige Kontrolle über ISO/UDF-Optionen

`xorriso`/`mkisofs` bieten präzise Kontrolle über alle relevanten Parameter, die für Archivierungs-Images entscheidend sind:

| Parameter | Bedeutung |
|---|---|
| `-iso-level 3` | ISO-9660 Level 3 (Dateien > 2 GB, lange Dateinamen) |
| `-udf` / `-udf-version 2.01` | UDF-Dateisystem-Version (wichtig für Blu-ray) |
| `-J` (Joliet) | Kompatibilität mit Windows-Systemen |
| `-R` (Rock Ridge) | Unix-Metadaten (Berechtigungen, Symlinks) |
| `-V <Bezeichnung>` | Volume-Label des Images |
| `--hardlinks` | Harte Links im Image bewahren |

Dieses Kontrollniveau ist mit `hdiutil` für ISO-Images nicht erreichbar.

---

## Praktische Verwendung

### Image erstellen (xorriso im mkisofs-Modus)

```bash
xorriso -as mkisofs \
  -iso-level 3 \
  -udf \
  -J \
  -R \
  -V "ARCHIV_2025_01" \
  -o /pfad/zum/output.iso \
  /pfad/zur/quelldaten/
```

### Image verifizieren (Mounten und Prüfsumme)

```bash
# macOS
hdiutil attach /pfad/zum/output.iso -readonly -mountpoint /tmp/verify_mount

# Inhalt prüfen
sha256sum /tmp/verify_mount/wichtige_datei.mp4

# Aushängen
hdiutil detach /tmp/verify_mount
```

---

## Empfehlung: Welches Tool für welches Format?

| Anwendungsfall | Empfohlenes Tool |
|---|---|
| ISO-9660/UDF-Image erstellen | `xorriso -as mkisofs` |
| DMG erstellen / verschlüsseln | `hdiutil` |
| DMG mounten / verifizieren | `hdiutil` |
| ISO mounten (macOS) | `hdiutil attach` |

---

## Fazit

Die Kombination aus **Plattformunabhängigkeit**, **Langzeitlesbarkeit**, **Reproduzierbarkeit** und **vollständiger Parametersteuerung** macht `xorriso`/`mkisofs` zum richtigen Werkzeug für die ISO/UDF-Erstellung im LAM. `hdiutil` bleibt auf seine Kernkompetenz beschränkt: DMG-Workflows unter macOS.

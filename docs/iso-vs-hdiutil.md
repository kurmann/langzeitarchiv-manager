# Design-Entscheidung: `hdiutil makehybrid` fur ISO-9660/UDF-Images

## Zusammenfassung

Fur die Erstellung von **ISO-9660/UDF-Hybrid-Images** verwendet LAM `hdiutil makehybrid`. Diese Entscheidung basiert auf praktischen Tests: `xorriso` im `mkisofs`-Kompatibilitaetsmodus unterstuetzt das `-udf`-Flag nicht, was die Kernfunktion des LAM (UDF-basierte Langzeitarchivierung) verunmoeglicht.

`hdiutil` erzeugt standardkonforme ISO-9660 + UDF Hybrid-Images, die auf **allen Plattformen** lesbar sind. Die Plattformunabhaengigkeit betrifft das Ausgabeformat, nicht das Erstellungswerkzeug.

---

## Warum nicht xorriso?

Die urspruengliche Entscheidung fuer `xorriso -as mkisofs` basierte auf dem theoretischen Vorteil der plattformuebergreifenden Erstellung. In der Praxis scheitert dieser Ansatz:

```
xorriso : FAILURE : -as mkisofs: Unsupported option '-udf'
xorriso : WARNING : -volid text does not comply to ISO 9660 / ECMA 119 rules
```

**Problem 1:** Das `-udf`-Flag wird im mkisofs-Kompatibilitaetsmodus nicht unterstuetzt. UDF ist jedoch fuer Langzeitarchivierung essentiell (lange Dateinamen, Unicode, Dateien > 4 GB).

**Problem 2:** ISO 9660 / ECMA 119 erzwingt strenge Regeln fuer Volume-Labels (nur Grossbuchstaben A-Z, Ziffern 0-9, Underscore). Namen wie "Weihnachtsquiz Kurmann" sind nicht konform.

Der native xorriso-Modus (ohne `-as mkisofs`) bietet nur eingeschraenkte UDF-Unterstuetzung und ist erheblich komplexer zu konfigurieren.

---

## Warum hdiutil makehybrid?

### Bewaehrte Loesung

`hdiutil makehybrid` wird bereits erfolgreich im Schwesterprojekt **kamera-einleser** eingesetzt, wo hunderte ISO-Archive damit erstellt wurden.

### Standardkonforme Ausgabe

Der Befehl erzeugt ISO 9660 + UDF Hybrid-Images, die auf jedem Betriebssystem lesbar sind:
- **macOS:** Doppelklick zum Mounten
- **Windows:** Nativ unterstuetzt seit Windows 8
- **Linux:** `mount -o loop` oder Dateimanager

### Keine externen Abhaengigkeiten

`hdiutil` ist ein macOS-Systemwerkzeug. Keine Installation via Homebrew oder apt erforderlich.

### Keine Einschraenkungen bei Volume-Namen

Im Gegensatz zu xorriso/mkisofs gibt es keine Zeichenbeschraenkungen. Leerzeichen, Umlaute und beliebig lange Namen funktionieren.

---

## Praktische Verwendung

### ISO erstellen

```bash
hdiutil makehybrid -o /pfad/zum/output.iso /pfad/zur/quelldaten/ -udf -default-volume-name "Archiv 2025"
```

### ISO verifizieren

```bash
hdiutil attach /pfad/zum/output.iso -readonly -mountpoint /tmp/verify_mount
ls /tmp/verify_mount/
hdiutil detach /tmp/verify_mount
```

---

## Werkzeug-Zuordnung

| Anwendungsfall | Werkzeug |
|---|---|
| ISO-9660/UDF-Image erstellen | `hdiutil makehybrid` |
| DMG erstellen / verschluesseln | `hdiutil create` |
| ISO/DMG mounten (macOS) | `hdiutil attach` |

---

## Hinweis zur plattformuebergreifenden Erstellung

Falls in Zukunft ISO-Erstellung auf Linux benoetigt wird, waere `genisoimage` (der Debian-Fork von mkisofs) eine Option, da dieser im Gegensatz zu xorriso das `-udf`-Flag unterstuetzt. Fuer den aktuellen Einsatz auf macOS ist `hdiutil makehybrid` die pragmatische und bewaehrte Wahl.

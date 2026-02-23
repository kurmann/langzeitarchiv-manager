# Produktspezifikation: Langzeitarchiv-Manager (LAM)

**Rolle:** Product Owner

**Datum:** 27.01.2026

**Status:** Final Draft (Expanded)

**Autor:** Google Gemini 3.0 Pro auf detaillierte Anweisung und Feedback von Patrick Kurmann

## 1. Vision und Motivation

### 1.1 Das Problem: Die digitale Demenz und die Illusion der Sicherheit

Wir leben in einem Zeitalter der flüchtigen Daten. Während ein analoges Fotoalbum im Keller oder ein in Stein gemeißelter Text 50 oder 100 Jahre problemlos überdauert, sind digitale Daten einer ständigen, unsichtbaren Bedrohung ausgesetzt. Die Annahme, dass Daten sicher sind, nur weil sie auf einer Festplatte liegen, ist eine gefährliche Illusion.

Die Bedrohungen sind vielfältig und oft schleichend:

- **Bit-Rot (Silent Data Corruption):** Das schleichende Kippen von magnetischen oder elektrischen Ladungen auf Festplatten und SSDs. Ein einzelnes gekipptes Bit kann in modernen, hochkomprimierten Formaten (wie ZIP oder HEVC) dazu führen, dass eine Datei unwiederbringlich zerstört wird, ohne dass das Betriebssystem dies sofort bemerkt.
- **Software-Obsoleszenz:** Dateiformate, Container oder proprietäre Datenbanken, die in Zukunft nicht mehr geöffnet werden können, weil die Herstellerfirma nicht mehr existiert oder die Lizenzserver abgeschaltet wurden.
- **Hardware-Versagen:** Der plötzliche Tod von Festplatten-Controllern oder das mechanische Versagen von Lagerfetten in Festplatten, die zu lange ungenutzt gelagert wurden ("Stiction").
- **Menschliches Versagen & Systemfehler:** Unbeabsichtigtes Löschen, Überschreiben durch fehlerhafte Synchronisations-Skripte oder Ransomware-Angriffe in lebenden, schreibbaren Dateisystemen.

Bisherige Consumer-Lösungen verlassen sich oft auf proprietäre Datenbanken (die korrumpieren können), teure Cloud-Abos (die von Kreditkarten abhängen) oder reine Festplatten-Spiegelung (RAID ist kein Backup, sondern nur Verfügbarkeit). Keine dieser Lösungen bietet die Beständigkeit von "in Stein gemeißelten" Daten.

### 1.2 Die Lösung: Digitale Resilienz durch analoge Tugenden

Der **Langzeitarchiv-Manager (LAM)** ist eine CLI-Anwendung, die ein digitales Archiv nach den bewährten Prinzipien der analogen Welt aufbaut. Wir behandeln Daten nicht als flüchtigen Strom, sondern als **feste, unveränderliche Materie**. Wir bauen keine "Datenbank", sondern ein "digitales Fort Knox".

Unsere Strategie ruht auf drei fundamentalen Säulen:

1. **Physikalische Beständigkeit (Medium):** Wir setzen primär auf optische Medien, insbesondere die **M-Disc** (oder hochwertige HTL Blu-ray). Im Gegensatz zu Festplatten (Magnetismus) oder organischen DVDs (Farbstoffe) nutzen diese Medien anorganische, gesteinsähnliche Schichten. Daten werden physisch graviert. Sie sind immun gegen Magnetfelder, EMPs und chemischen Zerfall über Jahrzehnte hinweg.
2. **Mathematische Unsterblichkeit (Logik):** Wir akzeptieren, dass physische Medien altern und Kratzer bekommen können. Anstatt auf Perfektion zu hoffen, bauen wir Fehlertoleranz ein. Durch den Einsatz von **Reed-Solomon-Codes (PAR2)** fügen wir gezielt Redundanz hinzu. Dies ermöglicht es uns, Daten mathematisch zu rekonstruieren, selbst wenn Teile des physischen Trägers zerstört sind. Wir machen die Daten "selbstheilend".
3. **Unabhängigkeit (Zugriff):** Das Archiv muss in 50 Jahren lesbar sein, auch wenn es die Software "LAM", den ursprünglichen Computer oder das Betriebssystem nicht mehr gibt. Deshalb setzen wir radikal auf offene Standards: Dateisysteme (UDF/ExFAT), Textdateien (CSV) und Standard-Container. Ein Mensch muss in der Lage sein, das Archiv mit Standard-Werkzeugen zu verstehen ("Human Readable").

## 2. Fachliche Funktionsbereiche

Die Anwendung gliedert sich nicht nach Programmcode-Modulen, sondern nach funktionalen Kompetenzen, die sie dem Archivar zur Verfügung stellt. Sie agiert als intelligenter Assistent ("Der Manager"), der Fehler proaktiv verhindert.

### 2.1 Funktionsbereich: Ingest & Aufbereitung ("Das Labor")

Dies ist der Eintrittspunkt für alle Daten. Die Anwendung muss als strenger Gatekeeper fungieren und sicherstellen, dass nur valide, gesunde Daten ins Archiv gelangen. Müll rein, Müll raus – das gilt es zu verhindern.

- **Qualitäts-Gate (Validierung):**

    Bevor auch nur ein Byte archiviert wird, muss es geprüft werden.

    - **Integritäts-Check:** Die Anwendung muss defekte Dateien (0-Byte Größe) oder unvollständige Transfers erkennen.
    - **Format-Validierung:** Speziell für Videodateien (HEVC/H.264) und Bilder muss eine inhaltliche Prüfung erfolgen (z.B. mittels FFmpeg Decoding ins Leere). Wir müssen sicherstellen, dass der Datenstrom technisch abspielbar ist und keine "Glitch-Frames" enthält.
    - **Konsequenz:** Fehlerhafte Dateien führen zum sofortigen Abbruch des Prozesses mit einer klaren Fehlermeldung. Wir konservieren keine korrupten Daten.
- **Strategische Paketierung (Loose vs. Packed):**

    Die Anwendung muss intelligent entscheiden, wie Daten abgelegt werden, um den zukünftigen Zugriff zu optimieren:

    - *Medien (Standard-Modus):* Videodateien und Fotos sollen als **lose Dateien** ("Loose Files") im Archiv liegen. Dies ermöglicht den direkten Zugriff ("Random Access") ohne vorheriges, zeitaufwendiges Entpacken. Ein Abspielen direkt vom Archivmedium muss möglich sein. Die Verzeichnisstruktur der Quelle wird 1:1 übernommen.
    - *Projekte (Bundle-Modus):* Komplexe Verzeichnisstrukturen, die logisch untrennbar zusammengehören und oft aus tausenden kleinen Dateien bestehen (z.B. Final Cut Bundles, Logic Projekte, Software-Code-Repositories, virtuelle Maschinen), müssen in einen Container verpackt werden. Dies schützt die Integrität der Ordnerstruktur, der MacOS-spezifischen Metadaten (Extended Attributes) und entlastet das Dateisystem des Archivmediums. Als Container-Formate stehen **TAR**, **ISO** und **DMG** zur Wahl (siehe Abschnitt 4.6).
- **Das Atomare Paket:**

    Die wichtigste logische Einheit des Archivs ist das "Archiv-Paket". Ein Paket (z.B. der Ordner "2025_Weihnachten" oder das File "Projekt_Hausbau.tar") wird durch ein eigenes, dediziertes PAR2-Set geschützt. Die Anwendung muss sicherstellen, dass ein solches Paket **niemals** über mehrere physische Datenträger gesplittet wird (kein "Disc Spanning"). Ein Paket ist atomar: Ganz oder gar nicht. Dies garantiert, dass zur Wiederherstellung niemals mehrere Discs gleichzeitig benötigt werden.

- **Bin-Packing (Automatische Verteilung):**

    Wenn der Benutzer eine große Datenmenge (z.B. ein 200 GB Jahresarchiv an Fotos) archivieren möchte, muss die Anwendung diese Menge automatisch analysieren und in passende "Häppchen" aufteilen. Diese Häppchen müssen so berechnet werden, dass sie die Zielmedien (z.B. 25 GB Discs) optimal ausfüllen, ohne dabei die Atomarität der enthaltenen Unterordner zu verletzen. Die Anwendung übernimmt das "Tetris-Spielen" für den Benutzer.

### 2.2 Funktionsbereich: Panzerung & Schutz ("Die Versicherung")

Hier wird die mathematische Resilienz erzeugt. Dies ist der Schritt, der ein einfaches "Kopieren" von einer echten "Archivierung" unterscheidet.

- **Perimeter-Schutz:**

    Jedes Archiv-Paket erhält ein Set an PAR2-Dateien. Diese Dateien dienen als "Reparatur-Kit". Die Redundanz muss konfigurierbar sein, um dem Risiko des Mediums zu entsprechen (z.B. 15% für optische Medien aufgrund von Kratzerrisiko, 5% für Festplatten gegen Bit-Rot).

    - *Wichtig:* Die PAR2-Dateien liegen direkt *neben* den Daten ("Sidecar"), im selben Ordner. Damit ist die logische Zusammengehörigkeit auch ohne spezielle Software sofort erkennbar. Wer den Ordner kopiert, kopiert den Schutz automatisch mit.
- **Identifikation (Hashing):**

    Jede archivierte Datei wird mittels SHA-256 eindeutig identifiziert. Dieser Fingerabdruck dient der langfristigen Integritätsprüfung (Ist die Datei noch unverändert?) und der Erkennung von Dubletten über das gesamte Archiv hinweg.

### 2.3 Funktionsbereich: Physische Archivierung ("Der Bunker")

Die Anwendung steuert den Schreibvorgang auf optische Medien und eliminiert dabei menschliche Flüchtigkeitsfehler.

- **Medien-Agnostik:**

    Obwohl wir M-Disc für die Langzeitlagerung präferieren, muss die Software technisch mit jedem optischen Medium (BD-R, DVD, CD) umgehen können. Die Kapazitätsgrenzen müssen konfigurierbar sein, um z.B. auf 50 GB oder 100 GB BDXL Medien wechseln zu können, ohne den Code anzupassen.

- **Erzwungene Redundanz (3-2-1):**

    Der Archivierungsprozess gilt erst als abgeschlossen, wenn die Daten erfolgreich auf **zwei** physische Datenträger geschrieben wurden (Kopie A: M-Disc für das Offsite-Lager/Bankschließfach, Kopie B: Günstigere BD-R für den schnellen Zugriff im Büro). Die Anwendung muss den Benutzer aktiv dazu auffordern ("Bitte Medium 2 einlegen") und den Prozess steuern. Sie unterstützt dabei auch "Load-and-Go" Szenarien mit zwei parallel angeschlossenen Brennern.

- **Verifikation:**

    Nach dem Brennen darf nicht einfach "Fertig" gemeldet werden. Es muss zwingend ein physikalischer Lese-Test (Verify) erfolgen, um sicherzustellen, dass die Daten korrekt auf dem Medium gelandet sind und nicht nur im Cache des Brenners existierten.

### 2.4 Funktionsbereich: Backup-Management ("Das Außenlager")

Neben dem "kalten", unveränderlichen optischen Archiv verwaltet die Anwendung auch Backups auf externen Festplatten. Hier gelten andere Regeln als bei der optischen Archivierung, da Festplatten wiederbeschreibbar sind und andere Ausfallrisiken haben.

- **Intelligentes Routing (Smart Mapping):**

    Die Anwendung muss erkennen, welche externe Festplatte angeschlossen ist (z.B. anhand des Volume-Namens "ARCHIV_HDD_01") und automatisch wissen, welche Daten auf diese Platte gehören. Wir vermeiden "Split-Brain": Zusammengehörige Themenjahre sollen nicht willkürlich zerrissen werden, nur um Speicherplatz zu optimieren. Die logische Ordnung hat auf Festplatten Vorrang vor der Platzausnutzung.

- **Streaming-Transfer:**

    Beim Kopieren großer Datenmengen (Terabytes) auf externe Festplatten muss die Anwendung effizient arbeiten. Sie leitet die Daten direkt von der Quelle (NAS) zum Ziel (HDD) ("Streaming"), ohne den Umweg über die interne SSD des ausführenden Rechners zu nehmen. Dies schont die Schreibzyklen der SSD und beschleunigt den Vorgang. Die PAR2-Berechnung erfolgt dann direkt auf dem Zielmedium.

- **Inkrementelle Intelligenz (Smart Update):**

    Bei der Aktualisierung eines bestehenden Festplatten-Backups darf nicht das gesamte Archiv neu berechnet werden (das würde Tage dauern). Die Anwendung muss erkennen, welche Dateien sich geändert haben (z.B. durch Parsing von rsync-Logs) und nur für die betroffenen Archiv-Pakete die PAR2-Dateien neu berechnen ("Delta-Logik"). Unveränderte Ordner werden ignoriert.

- **Lücken-Analyse (Coverage Check):**

    Der Benutzer muss jederzeit abfragen können: "Gibt es Ordner auf meinem NAS, die noch keiner Backup-Festplatte zugewiesen sind?". Dies verhindert, dass Daten "vergessen" werden, nur weil man vergessen hat, einen Haken in der Backup-Software zu setzen.

### 2.5 Funktionsbereich: Indexierung & Wiederauffindbarkeit ("Das Gedächtnis")

Da die physischen Medien oft offline im Schrank liegen, benötigt der Benutzer einen digitalen Katalog, um Inhalte schnell zu finden.

- **Der Master-Index:**

    Ein zentrales Inhaltsverzeichnis (CSV-Datei) auf dem NAS speichert, welche Datei (Hash/Name) sich auf welchem Medium (Disc-ID) befindet.

- **Format-Wahl:**

    Der Index ist eine einfache Textdatei (CSV, UTF-8), keine binäre Datenbank.

    - *Grund:* In 50 Jahren kann jeder Texteditor eine CSV öffnen und durchsuchen. Eine SQL-Datenbank benötigt spezifische Software-Versionen, die es vielleicht nicht mehr gibt.
    - *Resilienz:* Wenn eine CSV-Datei beschädigt ist, sind meist nur wenige Zeilen betroffen. Eine beschädigte Datenbank ist oft totalverloren.

## 3. Technische Rahmenbedingungen

### 3.1 Plattform & Umgebung

- **System:** Die Anwendung läuft primär auf macOS (Apple Silicon M1+), muss aber grundsätzlich portierbar sein (Python).
- **Quell-System:** Ein Synology NAS dient als zentraler Datenspeicher ("Vault"). Es wird via Netzwerkfreigabe (SMB/NFS) eingebunden. Wichtig: Der Schreibzugriff auf das Archiv-Verzeichnis des NAS ist für den Benutzer im Alltag gesperrt (Read-Only), nur die Anwendung (via Admin-User oder dediziertem Prozess) darf dort schreiben, um versehentliches Löschen zu verhindern (WORM-Simulation).
- **Staging-Area:** Eine schnelle lokale SSD am Mac dient als temporärer Arbeitsplatz ("Labor") für die Erstellung der optischen Images und die PAR2-Berechnung vor dem Brennen.

### 3.2 Schnittstellen zu externen Tools

Die Anwendung erfindet das Rad nicht neu, sondern orchestriert bewährte, langlebige Standard-Tools:

- **ffmpeg:** Zur Validierung von Videostreams.
- **par2cmdline:** Zur Erstellung und Prüfung von Redundanzdaten.
- **rsync:** Für robuste, abbrechbare Datentransfers auf Festplatten.
- **drutil (macOS) / xorriso (Linux):** Zur direkten Steuerung der Brenn-Hardware.
- **tar:** Zum Erstellen von TAR-Containern (ausschließlich im unkomprimierten "Store"-Modus, um Bit-Rot-Ausbreitung zu minimieren).
- **hdiutil (macOS):** Zum Erstellen und Mounten von DMG-Images, inkl. Verschlüsselung (AES-256).
- **mkisofs / xorriso:** Zum Erstellen von ISO-9660/UDF-Images für plattformübergreifende Archiv-Container.

## 4. Abgrenzung & Entscheidungshistorie (Rationale)

Hier dokumentieren wir bewusst verworfene Alternativen und Design-Entscheidungen, um den Fokus der Anwendung zu wahren und "Feature Creep" zu verhindern.

### 4.1 Warum keine Datenbank (SQLite)?

Wir haben uns bewusst gegen SQLite entschieden. Zwar wäre die Suche Millisekunden schneller, aber die Langzeitstabilität ist geringer. Eine CSV-Datei ist menschenlesbar, mit simplen Unix-Tools (`grep`) durchsuchbar und extrem robust gegen leichte Beschädigungen. Langlebigkeit schlägt hier Performance.

### 4.2 Warum kein globales TAR für alles?

Ursprünglich wurde überlegt, alle Daten in TAR-Container zu packen. Wir haben dies verworfen. Für Videodateien ist der direkte Zugriff ("Random Access") essenziell. Ein 25 GB TAR zu entpacken, nur um einen Clip zu sehen, ist ineffizient und benutzerunfreundlich. Daher gilt die Hybrid-Regel: Lose Dateien für Medien, Container (TAR, ISO oder DMG) nur für technische Bundles, die ihre interne Struktur zwingend brauchen.

### 4.3 Warum keine Proxy-Verwaltung in dieser App?

Die Idee, Proxy-Dateien zu erstellen und mittels Tags mit dem Archiv zu verlinken, wurde als "Out of Scope" definiert. Diese Anwendung ist ein Bibliothekar, kein Produktions-Tool. Asset-Management gehört in die Schnittsoftware (Final Cut / DaVinci), nicht in die Backup-Software. Wir halten die Anwendung schlank, wartbar und fokussiert auf ihre Kernaufgabe: Sicherung.

### 4.4 Warum keine Cloud-Integration?

Cloud-Backups (z.B. zu Mega.nz) sind sinnvoll als temporärer Puffer während der Ingest-Phase (Schutz vor Hausbrand während der Bearbeitung), aber sie sind Infrastruktur-Aufgaben. Diese können durch separate Skripte oder Rclone-Dienste im Hintergrund gelöst werden. Die Kernanwendung kümmert sich um den physischen Besitz der Daten ("Cold Storage"), nicht um Miet-Speicher.

### 4.5 Warum "Smart Mapping" statt "Auto-Fill" auf HDDs?

Bei optischen Medien füllen wir den Platz maximal aus ("Bin-Packing"), da die Medien austauschbar und uniform sind. Bei Festplatten tun wir das nicht. Wir wollen nicht, dass ein logischer Jahrgang (z.B. 2025) über zwei Festplatten verstreut wird, nur um die letzten 10 GB einer Platte zu füllen. Die logische Zusammengehörigkeit und Auffindbarkeit auf der Festplatte hat Vorrang vor der maximalen Speicherplatz-Effizienz.

### 4.6 Warum ISO und DMG als Alternativen zu TAR?

Während TAR das klassische, bewährte Archivierungsformat für Unix-Systeme ist, haben ISO und DMG in bestimmten Anwendungsfällen klare Vorteile, die eine Unterstützung als gleichwertige Container-Optionen rechtfertigen.

**ISO (ISO-9660/UDF Image):**

- **Plattformunabhängigkeit:** ISO-Images sind ein offener, international normierter Standard (ISO 9660, ergänzt durch UDF), der auf praktisch jedem Betriebssystem – Windows, macOS, Linux, aber auch auf Embedded-Systemen und historischen Systemen – nativ unterstützt wird. Ein TAR hingegen ist primär ein Unix-Konstrukt und wird unter Windows ohne zusätzliche Software nicht nativ entpackt.
- **Kein Entpacken notwendig:** ISO-Images können direkt gemountet werden – sowohl als virtuelle Laufwerke auf einem Desktop-System als auch auf optische Medien gebrannt. Der Inhalt ist sofort zugänglich, ohne eine temporäre Kopie des gesamten Containers anlegen zu müssen. Dies ist besonders vorteilhaft bei großen Bundles (mehrere GB), wo ein TAR-Entpacken erhebliche Zeit und temporären Speicher beansprucht.
- **Weite Verbreitung und Langlebigkeit:** Das ISO-Format ist seit Jahrzehnten etabliert und wird es aller Voraussicht nach auch in Zukunft sein. Es bildet die Grundlage für nahezu alle optischen Medien (CD, DVD, Blu-ray) und ist damit eng mit der physischen Archivierungsstrategie des LAM verknüpft. Die Wahrscheinlichkeit, dass Werkzeuge zum Lesen von ISO-Images in 50 Jahren nicht mehr verfügbar sind, ist verschwindend gering.
- **Geeignet für:** Software-Bundles, Dokumentensammlungen, Projektarchive, bei denen plattformübergreifender Zugriff wichtig ist.

**DMG (Apple Disk Image):**

- **Native macOS-Integration:** Das DMG-Format ist das Standard-Disk-Image-Format von macOS und wird vom Betriebssystem ohne jegliche Drittsoftware vollständig unterstützt. Doppelklick genügt zum Mounten. Alle macOS-spezifischen Metadaten, Extended Attributes und Resource Forks werden korrekt und vollständig bewahrt – etwas, das mit TAR unter Umständen Konfigurationsaufwand erfordert und bei ISO gar nicht möglich ist.
- **Optionale Verschlüsselung (AES-256):** DMG-Images können nativ mit AES-128 oder AES-256 verschlüsselt werden (mittels `hdiutil`). Dies erlaubt es, sensitives Material (z.B. persönliche Dokumente, Passwörter, Steuerunterlagen) verschlüsselt im Archiv abzulegen, ohne auf externe Verschlüsselungstools angewiesen zu sein. TAR und ISO bieten diese Funktionalität nicht nativ.
- **Integrierte Prüfsummen:** `hdiutil` kann beim Erstellen und beim Verifizieren eines DMG automatisch Prüfsummen berechnen, was die Integritätsprüfung vereinfacht.
- **Geeignet für:** macOS-spezifische Anwendungsprojekte (Final Cut Bundles, Logic Projekte, Xcode-Projekte), sensitive Daten die verschlüsselt archiviert werden sollen, und alle Bundles, bei denen macOS-Metadaten-Treue oberste Priorität hat.

**Entscheidungshilfe: Welches Format wählen?**

| Kriterium | TAR | ISO | DMG |
|---|---|---|---|
| Plattformunabhängigkeit | Unix-zentrisch | ✅ Sehr hoch | macOS-zentrisch |
| Direktes Mounten (kein Entpacken) | ❌ | ✅ | ✅ |
| macOS-Metadaten (xattr, forks) | Eingeschränkt | ❌ | ✅ |
| Verschlüsselung (nativ) | ❌ | ❌ | ✅ (AES-256) |
| Werkzeug-Verfügbarkeit in 50 Jahren | Hoch | Sehr hoch | macOS-abhängig |
| Standardisierung | De-facto | ISO-Norm | Apple-proprietär |

Die Anwendung wählt das Container-Format nicht automatisch, sondern der Nutzer legt es beim Erstellen eines Bundles fest. Die Standardempfehlung ist **ISO** für maximale Portabilität und **DMG** wenn Verschlüsselung oder maximale macOS-Kompatibilität gewünscht sind. **TAR** bleibt als Option für einfache, Unix-lastige Bundles erhalten.

## 5. Zusammenfassung der User Experience

Der Nutzer interagiert mit der Anwendung über ein textbasiertes Interface (CLI/TUI), das ihn führt und schützt.

1. **Der Disponent (Start):** Beim Start analysiert die App die Umgebung. "Ich sehe zwei leere Blu-rays in den Brennern. Möchtest du den Ordner 'Familie_2025' aus dem Ingest archivieren?"
2. **Die Automatisierung (Prozess):** Der Nutzer bestätigt. Die App prüft die Datenqualität, erstellt Pakete, berechnet PAR2 und brennt parallel auf zwei Laufwerken.
3. **Der Abschluss (Finalisierung):** Nach erfolgreichem Brennen verschiebt die App die fertigen Daten in das "Vault"-Verzeichnis auf dem NAS und aktualisiert den Index.
4. **Das Backup (Sync):** Schließt der Nutzer eine externe Festplatte an, erkennt die App dies: "Das ist Festplatte 'ARCHIV_A'. Sie ist zuständig für die Jahre 2010-2020. Soll ich die neuen Daten synchronisieren?". Sie überträgt nur Änderungen und berechnet PAR2 nur dort neu, wo es nötig ist.

Das Ziel ist ein System, das dem Nutzer die kognitive Last ("Habe ich an alles gedacht? Sind die Daten wirklich sicher?") abnimmt und durch deterministische, mathematisch abgesicherte Prozesse ersetzt.

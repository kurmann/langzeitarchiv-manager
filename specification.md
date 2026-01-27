# Produktspezifikation: Langzeitarchiv-Manager (LAM)

**Rolle:** Product Owner

**Datum:** 27.01.2026

**Status:** Final Draft

**Autor:** Google Gemini 3.0 Pro auf detaillierte Anweisung und Feedback von Patrick Kurmann

## 1. Vision und Motivation

### 1.1 Das Problem: Die digitale Demenz

Wir leben in einem Zeitalter der flüchtigen Daten. Während ein analoges Fotoalbum im Keller 50 Jahre problemlos überdauert, sind digitale Daten einer ständigen Bedrohung ausgesetzt:

- **Bit-Rot:** Das schleichende Kippen von magnetischen oder elektrischen Ladungen auf Festplatten und SSDs.
- **Software-Obsoleszenz:** Dateiformate oder Container, die in Zukunft nicht mehr geöffnet werden können.
- **Hardware-Versagen:** Der plötzliche Tod von Festplatten-Controllern.
- **Menschliches Versagen:** Unbeabsichtigtes Löschen oder Überschreiben in lebenden Dateisystemen.

Bisherige Lösungen verlassen sich oft auf proprietäre Datenbanken, Cloud-Abos oder reine Festplatten-Spiegelung. Keine dieser Lösungen bietet die Beständigkeit von "in Stein gemeißelten" Daten.

### 1.2 Die Lösung: Digitale Resilienz durch analoge Tugenden

Der **Langzeitarchiv-Manager (LAM)** ist eine CLI-Anwendung, die ein digitales Archiv nach den Prinzipien der analogen Welt aufbaut. Wir behandeln Daten nicht als flüchtigen Strom, sondern als **feste Materie**.

Unsere Strategie ruht auf drei Säulen:

1. **Physikalische Beständigkeit:** Nutzung von optischen Medien (M-Disc/Blu-ray) mit anorganischen Schichten statt organischer Farbstoffe.
2. **Mathematische Unsterblichkeit:** Einsatz von Reed-Solomon-Codes (PAR2), um Daten selbst bei physischer Beschädigung des Trägers mathematisch rekonstruieren zu können.
3. **Unabhängigkeit:** Das Archiv muss in 50 Jahren lesbar sein, auch wenn es die Software "LAM" nicht mehr gibt. Deshalb setzen wir auf offene Standards (Dateisysteme, CSV, Standard-Container) statt auf Datenbanken.

## 2. Fachliche Funktionsbereiche

Die Anwendung gliedert sich nicht nach Programmcode-Modulen, sondern nach funktionalen Kompetenzen, die sie dem Archivar zur Verfügung stellt.

### 2.1 Funktionsbereich: Ingest & Aufbereitung ("Das Labor")

Dies ist der Eintrittspunkt für alle Daten. Die Anwendung muss sicherstellen, dass nur valide Daten ins Archiv gelangen.

- **Qualitäts-Gate (Validierung):**

    Bevor ein Byte archiviert wird, muss es geprüft werden. Die Anwendung muss defekte Dateien (0-Byte Größe) erkennen. Speziell für Videodateien (HEVC/H.264) muss eine Stream-Prüfung (z.B. mittels FFmpeg) erfolgen, um sicherzustellen, dass die Datei technisch abspielbar ist. Fehlerhafte Dateien führen zum Abbruch des Prozesses, damit kein "Datenmüll" konserviert wird.

- **Strategische Paketierung (Loose vs. Packed):**

    Die Anwendung muss intelligent entscheiden, wie Daten abgelegt werden:

    - *Medien (Standard):* Videodateien und Fotos sollen als **lose Dateien** ("Loose Files") im Archiv liegen. Dies ermöglicht den direkten Zugriff ("Random Access") ohne vorheriges Entpacken. Ein Abspielen direkt vom Archivmedium muss möglich sein.
    - *Projekte (Ausnahme):* Komplexe Verzeichnisstrukturen, die logisch zusammengehören und aus tausenden kleinen Dateien bestehen (z.B. Final Cut Bundles, Logic Projekte, Software-Code), müssen in einen Container (**TAR**) verpackt werden, um die Integrität der Ordnerstruktur und Metadaten zu wahren.
- **Das Atomare Paket:**

    Die wichtigste logische Einheit des Archivs ist das "Archiv-Paket". Ein Paket (z.B. "2025_Weihnachten") wird durch ein eigenes PAR2-Set geschützt. Die Anwendung muss sicherstellen, dass ein solches Paket **niemals** über mehrere physische Datenträger gesplittet wird. Ein Paket ist atomar: Ganz oder gar nicht.

- **Bin-Packing (Automatische Verteilung):**

    Wenn der Benutzer eine große Datenmenge (z.B. 200 GB Jahresarchiv) archivieren möchte, muss die Anwendung diese Menge automatisch in passende Häppchen aufteilen, die auf die Zielmedien (z.B. 25 GB Discs) passen, ohne dabei atomare Pakete zu zerreissen.

### 2.2 Funktionsbereich: Panzerung & Schutz ("Die Versicherung")

Hier wird die mathematische Resilienz erzeugt.

- **Perimeter-Schutz:**

    Jedes Archiv-Paket erhält ein Set an PAR2-Dateien. Diese Dateien dienen als "Reparatur-Kit". Die Redundanz muss konfigurierbar sein (z.B. 15% für optische Medien, 5% für Festplatten). Wichtig: Die PAR2-Dateien liegen direkt *neben* den Daten ("Sidecar"), um die logische Zusammengehörigkeit auch ohne Software sicherzustellen.

- **Identifikation (Hashing):**

    Jede archivierte Datei wird mittels SHA-256 eindeutig identifiziert. Dies dient der langfristigen Integritätsprüfung und der Erkennung von Dubletten.

### 2.3 Funktionsbereich: Physische Archivierung ("Der Bunker")

Die Anwendung steuert den Schreibvorgang auf optische Medien.

- **Medien-Agnostik:**

    Obwohl wir M-Disc präferieren, muss die Software mit jedem optischen Medium (BD-R, DVD) umgehen können. Die Kapazitätsgrenzen müssen konfigurierbar sein.

- **Erzwungene Redundanz (3-2-1):**

    Der Archivierungsprozess gilt erst als abgeschlossen, wenn die Daten erfolgreich auf **zwei** physische Datenträger (Kopie A: M-Disc/Offsite, Kopie B: BD-R/Onsite) geschrieben wurden. Die Anwendung muss den Benutzer aktiv dazu auffordern und den Prozess steuern ("Load-and-Go" bei zwei Brennern oder sequenziell).

- **Verifikation:**

    Nach dem Brennen muss zwingend ein Lese-Test erfolgen, um sicherzustellen, dass die Daten physikalisch korrekt auf dem Medium gelandet sind.

### 2.4 Funktionsbereich: Backup-Management ("Das Außenlager")

Neben dem "kalten" optischen Archiv verwaltet die Anwendung auch Backups auf externen Festplatten. Hier gelten andere Regeln als bei der optischen Archivierung.

- **Intelligentes Routing (Smart Mapping):**

    Die Anwendung muss erkennen, welche externe Festplatte angeschlossen ist (z.B. anhand des Volume-Namens) und automatisch wissen, welche Daten auf diese Platte gehören. Wir vermeiden "Split-Brain": Zusammengehörige Themenjahre sollen nicht willkürlich zerrissen werden, nur um Speicherplatz zu optimieren.

- **Streaming-Transfer:**

    Beim Kopieren großer Datenmengen auf Festplatten muss die Anwendung die Daten direkt von der Quelle (NAS) zum Ziel (HDD) leiten ("Streaming"), ohne den Umweg über die SSD des ausführenden Rechners zu nehmen. Dies schont die Hardware-Ressourcen.

- **Inkrementelle Intelligenz (Smart Update):**

    Bei der Aktualisierung eines bestehenden Festplatten-Backups darf nicht das gesamte Archiv neu berechnet werden. Die Anwendung muss erkennen, welche Dateien sich geändert haben (z.B. durch Parsing von rsync-Logs) und nur für die betroffenen Archiv-Pakete die PAR2-Dateien neu berechnen ("Delta-Logik").

- **Lücken-Analyse (Coverage Check):**

    Der Benutzer muss jederzeit abfragen können: "Gibt es Ordner auf meinem NAS, die noch keiner Backup-Festplatte zugewiesen sind?". Dies verhindert, dass Daten vergessen werden.

### 2.5 Funktionsbereich: Indexierung & Wiederauffindbarkeit ("Das Gedächtnis")

Da die physischen Medien im Schrank liegen ("Offline"), benötigt der Benutzer einen digitalen Katalog.

- **Der Master-Index:**

    Ein zentrales Inhaltsverzeichnis (CSV-Datei) auf dem NAS speichert, welche Datei (Hash/Name) sich auf welchem Medium (Disc-ID) befindet.

- **Format-Wahl:**

    Der Index ist eine einfache Textdatei (CSV, UTF-8), keine binäre Datenbank. Grund: In 50 Jahren kann jeder Texteditor eine CSV öffnen. Eine SQL-Datenbank benötigt spezifische Software, die es vielleicht nicht mehr gibt.

## 3. Technische Rahmenbedingungen

### 3.1 Plattform & Umgebung

- **System:** Die Anwendung läuft primär auf macOS (Apple Silicon M1+), muss aber portierbar sein (Python).
- **Quell-System:** Ein Synology NAS, eingebunden via Netzwerkfreigabe (SMB/NFS). Der Schreibzugriff auf das Archiv-Verzeichnis des NAS ist für den Benutzer im Alltag gesperrt (Read-Only), nur die Anwendung (Admin) darf schreiben.
- **Staging-Area:** Eine schnelle lokale SSD dient als temporärer Arbeitsplatz für die Erstellung der optischen Images.

### 3.2 Schnittstellen zu externen Tools

Die Anwendung erfindet das Rad nicht neu, sondern orchestriert bewährte Standard-Tools:

- **ffmpeg:** Zur Validierung von Videostreams.
- **par2cmdline:** Zur Erstellung von Redundanzdaten.
- **rsync:** Für robuste Datentransfers auf Festplatten.
- **drutil / xorriso:** Zur Steuerung der Brenn-Hardware.
- **tar:** Zum Erstellen von Containern (ausschließlich im unkomprimierten "Store"-Modus).

## 4. Abgrenzung & Entscheidungshistorie (Rationale)

Hier dokumentieren wir bewusst verworfene Alternativen und Design-Entscheidungen, um den Fokus der Anwendung zu wahren.

### 4.1 Warum keine Datenbank (SQLite)?

Wir haben uns gegen SQLite entschieden. Zwar wäre die Suche Millisekunden schneller, aber eine beschädigte Datenbankdatei ist oft totalverloren. Eine CSV-Datei ist robust, zeilenweise reparierbar und mit simplen Unix-Tools (`grep`) durchsuchbar. Langlebigkeit schlägt hier Performance.

### 4.2 Warum kein globales TAR für alles?

Ursprünglich wurde überlegt, alles in TAR-Container zu packen. Wir haben dies verworfen. Für Videodateien ist der direkte Zugriff ("Random Access") essenziell. Ein 25 GB TAR zu entpacken, nur um einen Clip zu sehen, ist ineffizient. Daher: Lose Dateien für Medien, TAR nur für technische Bundles.

### 4.3 Warum keine Proxy-Verwaltung in dieser App?

Die Idee, Proxy-Dateien zu erstellen und mit dem Archiv zu verlinken, wurde diskutiert und als "Out of Scope" definiert. Diese Anwendung ist ein Bibliothekar, kein Produktions-Tool. Asset-Management gehört in die Schnittsoftware (Final Cut / DaVinci), nicht in die Backup-Software. Wir halten die Anwendung schlank und fokussiert.

### 4.4 Warum keine Cloud-Integration?

Cloud-Backups (z.B. zu Mega.nz) sind sinnvoll als temporärer Puffer ("Ingest-Schutz"), aber sie sind Infrastruktur-Aufgaben. Diese können durch separate Skripte oder Rclone-Dienste gelöst werden. Die Kernanwendung kümmert sich um den physischen Besitz der Daten, nicht um Miet-Speicher.

### 4.5 Warum "Smart Mapping" statt "Auto-Fill" auf HDDs?

Bei optischen Medien füllen wir den Platz maximal aus ("Bin-Packing"), da die Medien austauschbar sind. Bei Festplatten tun wir das nicht. Wir wollen nicht, dass ein Jahrgang (2025) über zwei Festplatten verstreut wird, nur um 10 GB Platz zu sparen. Die logische Zusammengehörigkeit auf der Festplatte hat Vorrang vor der Speicherplatz-Effizienz.

## 5. Zusammenfassung der User Experience

Der Nutzer interagiert mit der Anwendung über ein textbasiertes Interface (CLI/TUI).

1. **Der Disponent:** Beim Start analysiert die App die Umgebung. "Ich sehe zwei leere Blu-rays. Möchtest du den Ordner 'Familie_2025' archivieren?"
2. **Die Automatisierung:** Der Nutzer bestätigt. Die App prüft, packt, berechnet PAR2 und brennt parallel auf zwei Laufwerken.
3. **Der Abschluss:** Die App verschiebt die fertigen Daten in das "Vault"-Verzeichnis auf dem NAS und aktualisiert den Index.
4. **Das Backup:** Schließt der Nutzer eine externe Festplatte an, erkennt die App dies: "Das ist Festplatte 'ARCHIV_A'. Soll ich die neuen Daten synchronisieren?". Sie überträgt nur Änderungen und berechnet PAR2 nur dort neu, wo es nötig ist.

Das Ziel ist ein System, das dem Nutzer die kognitive Last ("Habe ich an alles gedacht?") abnimmt und durch deterministische Prozesse ersetzt.

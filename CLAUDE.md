# Projektübersicht Rehrmann & Harms: Arbeitsanleitung für Claude

Diese Seite zeigt Kosten, Baudokumentation, Gewinnermittlung und Abschlussbericht der Fix-and-Flip-Projekte. Sie läuft über GitHub Pages. Das Repo ist öffentlich, deshalb liegen alle Daten und Fotos nur verschlüsselt im Repo.

Sprache: Deutsch. Keine Semikolons und keine Gedankenstriche als Satzzeichen. Kurze, sachliche Sätze.

## Aufbau

| Pfad | Inhalt |
| --- | --- |
| `index.html` | Die komplette Seite (HTML, CSS, JS). Entschlüsselt die Daten im Browser. |
| `daten/meta.json` | Salt und Iterationen für die Schlüsselableitung. Öffentlich, kein Geheimnis. |
| `daten/index.enc` | Verschlüsselt: Liste der Projekt-IDs, OneDrive-Wurzel, Stand der Daten. |
| `daten/pXX.enc` | Verschlüsselt: ein Projekt (Stammdaten, Plan, Kosten, Timeline). |
| `fotos/pXX/<foto-id>.enc` | Verschlüsselte Fotos, 1600 px. `_t.enc` ist die 480-px-Vorschau. |
| `werkzeuge/daten.py` | Ent- und Verschlüsseln, Fotos hinzufügen, Passwort ändern. |
| `klartext/` | Entschlüsselte Arbeitskopie. Steht in `.gitignore` und wird NIE committet. |

Über „Eckdaten bearbeiten“ erzeugt die Seite ohne GitHub-Schlüssel einen Text „Eckdaten in der Projektübersicht ändern, Projekt pXX …“ mit Zeilen „Feld: alt → neu“. Kommt dieser Text im Chat, die Änderungen genau so in `klartext/pXX.json` übernehmen (Zahlen im deutschen Format umrechnen, Datum als JJJJ-MM-TT, Status „Abgeschlossen“ setzt auch `status` und `verkauf`). Optional kann die Seite Eckdaten auch selbst speichern. Sie verschlüsselt im Browser und schreibt `daten/pXX.enc` über die GitHub-API. Dafür hinterlegen die Nutzer einmal pro Gerät einen GitHub-Schlüssel (Fine-grained Token, nur dieses Repo, Contents: Read and write). Die Seite setzt dabei `geaendert` im Projekt.

## Passwort

- Das Passwort steht nie im Repo, nie in einer Datei, nie in einer Commit-Nachricht.
- Es kommt aus dem Skill „Projektübersicht pflegen“ oder vom Nutzer im Chat.
- Nur als Umgebungsvariable nutzen: `PASSWORT='…' python3 werkzeuge/daten.py …`

## Ablauf jeder Änderung

0. `git pull origin main`. Die Seite speichert Eckdaten auch selbst (Knopf „Eckdaten bearbeiten“, Commit „Eckdaten aktualisiert“). Ohne Pull würden diese Änderungen überschrieben.
1. `python3 werkzeuge/daten.py entschluesseln`
2. JSON in `klartext/` bearbeiten.
3. `python3 werkzeuge/daten.py verschluesseln` (verschlüsselt nur Geänderte, setzt `aktualisiert` im Index).
4. `git status` prüfen: Es dürfen nur `daten/`, `fotos/` oder Code-Dateien geändert sein, nie `klartext/`.
5. Commit direkt auf `main` und pushen. So ist es mit den Nutzern vereinbart. Die Seite aktualisiert sich nach 1 bis 2 Minuten.
6. Commit-Nachrichten ohne Adressen, Namen und Beträge, zum Beispiel „Daten aktualisiert: 2 Belege“.

## Kostenkategorien (`bucket`)

| Schlüssel | Inhalt |
| --- | --- |
| `kaufpreis` | Kaufpreis |
| `knk` | Kaufnebenkosten: Notar, Grundbuch, Makler beim Ankauf, Grunderwerbsteuer |
| `finanzierung` | Nur Zinsen und Bearbeitungs- oder Bereitstellungsgebühr. Keine Tilgung. |
| `renovierung` | Renovierung mit Aufteilung `split: {material, arbeit}`. Weist die Rechnung beides nicht getrennt aus, `proxy: true` setzen. Bei pauschalen Abschlägen des Generalunternehmers 25 % Material und 75 % Arbeit vorschlagen, aber immer nachfragen. |
| `weiteres` | Alles andere: Hausgeld, Strom, Vermarktung, Homestaging, Fotograf, Inserate, Fahrten, Parken, Makler beim Verkauf |

Alle Beträge brutto. Eigenleistung nur als Text in der Timeline, nie als Kosten.

## Belege verarbeiten („Neue Belege verarbeiten“)

Gemeinsames OneDrive-Konto über den Microsoft-365-Connector. Wurzelordner `11_Projektdokumentation & Rechnungen`. IDs stehen in `klartext/index.json` unter `onedrive` und je Projekt unter `onedrive`.

1. Dateien in `00_Eingang` lesen. Rechnungen, die im Chat hochgeladen wurden, direkt lesen und nach „Belege aus dem Chat“ (unten) ins OneDrive bringen.
2. Je Datei ermitteln: Rechnungsdatum, Lieferant, Bruttobetrag, Projekt (meist über die Objektadresse), Kategorie, bei Renovierung Material und Arbeit.
3. Vorschlag als Tabelle zeigen, mit Zielordner und neuem Dateinamen. Erst nach Bestätigung handeln.
4. Nachfragen statt raten, wenn: kein Rechnungsdatum, Projekt unklar, mehrere Projekte auf einer Rechnung, Betrag unleserlich, Gutschrift, Abschlag mit unklarer Verrechnung.
5. Dateiname immer mit dem Werkzeug bilden, nie von Hand: `python3 werkzeuge/daten.py dateiname <JJJJ-MM-TT> <bucket> "<Lieferant>" "<Inhalt>" [endung]`. Ergebnis: `JJJJMMTT_Kategorie_Lieferant-Inhalt.pdf`.
   - Datum = Rechnungsdatum. Kategorie = einer der fünf Buckets (Kaufpreis, Kaufnebenkosten, Finanzierung, Renovierung, Weiteres).
   - Lieferant = Kurzname, unter dem man ihn sucht, höchstens 3 Wörter, ohne Rechtsform. Beispiele: `MP Bau`, `Notar Mueller`, `Finanzamt`, `Hausverwaltung Schmitz`. Denselben Lieferanten immer gleich schreiben, dazu vorher in den bisherigen Kosten des Projekts nachsehen.
   - Inhalt = was bezahlt wurde, 1 bis 4 Wörter, ohne Projekt (das Projekt steckt im Ordner). Beispiele: `Kaufvertrag`, `Grunderwerbsteuer`, `Zinsen Oktober`, `Parkett Eiche`, `Abschlag 1`, `Schlussrechnung`, `Hausgeld November`.
   - Gutschriften: Inhalt beginnt mit `Gutschrift`. Gibt es den Namen im Monatsordner schon, `_2`, `_3` anhängen.
   - Beispiel: `20261102_Renovierung_MP-Bau-Abschlag-1.pdf`
6. Datei in `<Projektordner>/<JJJJ>/<MM_Monat>` verschieben. Der Monat richtet sich nach dem Rechnungsdatum. Fehlt der Jahresordner, ihn mit `01_Januar` bis `12_Dezember` anlegen und die IDs ins Projekt schreiben.
7. Kostenposition anhängen: `{"id":"k001","datum":"JJJJ-MM-TT","lieferant":"…","text":"…","bucket":"…","betrag":0.00,"split":{…},"beleg":{"name":"…pdf","pfad":"…","url":"<webUrl>","itemId":"…"}}`. Ohne Beleg: `"beleg": false`.
8. Verschlüsseln, committen, pushen. Kurz bestätigen: Anzahl, Summe, je Kategorie.

### Belege aus dem Chat

Der Connector kann keine PDFs ins OneDrive hochladen. Deshalb läuft der Upload über das private Repo `rhIMMO/Belege-Eingang` und das Make-Szenario „Belege aus dem Chat ins OneDrive“.

1. Schritte 2 bis 5 wie oben: Daten ermitteln, Vorschlag zeigen, Bestätigung abwarten, Dateinamen mit dem Werkzeug bilden.
2. Repo `rhIMMO/Belege-Eingang` mit Schreibzugriff anhängen und klonen.
3. Jede Datei unter ihrem neuen Namen nach `eingang/` kopieren. Ein Commit für alle, Nachricht ohne Namen und Beträge, zum Beispiel „Belege: 2 Dateien“. Auf `main` pushen.
4. Make legt die Dateien nach etwa 30 bis 60 Sekunden unter demselben Namen in `00_Eingang` ab. Mit `read_resource` auf die Eingang-ID prüfen, bis zu 3 Minuten warten.
5. Weiter mit Schritt 6 bis 8 oben: verschieben, Kostenposition mit `url` und `itemId` anhängen, verschlüsseln, pushen.
6. Danach die Dateien in `Belege-Eingang` mit `git rm` aus `eingang/` löschen und pushen. Make ignoriert diesen Push.

Kommt nach 3 Minuten nichts an: Die Nutzer sollen in Make unter History den letzten Lauf ansehen. Nach einem Fehler schaltet Make das Szenario ab, dann wieder auf ON stellen. Dateien immer direkt in `eingang/` legen, nie in Unterordner. Sonst scheitert der Dateiname in OneDrive. Der GitHub-Schlüssel im Make-Modul „Datei von GitHub laden“ läuft etwa im November 2027 ab. Anleitung: https://claude.ai/artifact/Upo95ggdiUHCEAEUjf5jzg

## Timeline

Eintrag: `{"datum":"JJJJ-MM-TT","typ":"start|verlauf|abschluss","titel":"…","text":"…","fotos":[{"id":"f…","cap":"…","raum":"wohnen"}]}`

- Fotos mit `python3 werkzeuge/daten.py foto pXX <bild1> <bild2> …` einbinden. Das Werkzeug gibt die Foto-IDs aus.
- `start` = Besichtigung, `abschluss` = Fertigstellung. Bei diesen beiden Einträgen `raum` setzen (wohnen, kueche, bad, schlafen, flur, balkon). Der Abschlussbericht bildet daraus Vorher-Nachher-Paare.
- Statusbericht: 2 bis 5 Sätze, sachlich, nur was der Nutzer gesagt hat.

## Neues Projekt

- Nächste Nummer `pXX`, `nr` zweistellig. In `klartext/index.json` unter `projekte` ergänzen.
- Planwerte aus der Fix-and-Flip-Excel, Blatt „Kalkulation“: D16 Kaufpreis, D17 Wohnfläche, C18 Notar und Grundbuch, C19 Makler, C20 Grunderwerbsteuer, C25 Zinsmonate, C26 Finanzierungsanteil, C27 Zins, C28 Bearbeitungsgebühr, J7 Renovierung je m², H8 Puffer, H15 Projektdauer, I16 Hausgeld, I17 Strom und Heizung, O15 Homestaging, O9 und O10 Verkaufspreis je m² gering und hoch, C5 Energieklasse, C6 Heizung, E5 Baujahr. Positionen und Werte genau wie in der Excel.
- Alternativ kommt der Text aus dem Formular „Neues Projekt“ der Seite.
- OneDrive: in der Wurzel den Ordner `##_Straße_Hausnummer_PLZ_Ort` anlegen, darin den Jahresordner mit 12 Monatsordnern. IDs ins Projekt schreiben.
- `eigenkapital`: fester Betrag vom Nutzer. Fehlt der Wert, `null` lassen. Die Seite rechnet dann Plan-Gesamtkosten minus `plan.darlehen`.
- Alternativ `ekRegel: {"basis":16000,"knkTeile":{"notar":true,"makler":true,"grest":true},"knkVollstaendig":false}`: Eigenkapital = Basis plus die angehakten Teile der Kaufnebenkosten (notar = Notar und Grundbuch, makler = Makler, grest = Grunderwerbsteuer). Solange `knkVollstaendig` false ist, zählen die Planwerte, danach die Rechnungen. Sind Notar, Grundbuch, Makler und Grunderwerbsteuer erfasst, beim Nutzer nachfragen und dann `knkVollstaendig` auf true setzen. Die Nutzer können das auch selbst über „Eckdaten bearbeiten“ einstellen.
- Planpositionen der Kaufnebenkosten bekommen `teil` (notar, makler, grest). Kostenpositionen der Kategorie `knk` bekommen `knkTeil` mit demselben Wert. Grundbuchkosten zählen zu `notar`.

## Titelbild

Foto mit `werkzeuge/daten.py foto pXX <bild>` einbinden und als `titelbild: {"id":"f…","cap":"Außenansicht"}` ins Projekt schreiben. Die Projektkarte zeigt dann dieses Bild. Ohne Titelbild nimmt sie das erste Foto des neuesten Timeline-Eintrags. Nach Abschluss zeigt sie das erste Abschlussfoto.

## Projektabschluss

`verkauf: {"datum":"JJJJ-MM-TT","preis":0}`, `status: "abgeschlossen"`, `phase: "Abgeschlossen"`, Timeline-Eintrag `abschluss` mit Fotos.

## Rechenlogik (steht in `index.html`, Funktion `calc`)

- Gewinn vor Steuern = Verkaufspreis minus Summe der fünf Kategorien.
- Marge = Gewinn vor Steuern geteilt durch Summe Kosten.
- EK-Rendite = Gewinn vor Steuern geteilt durch Eigenkapital, p.a. linear hochgerechnet.
- Projektdauer = Beurkundung Ankauf bis Beurkundung Verkauf.
- Plan-Verkaufspreis = Szenario goldene Mitte aus der Excel.

## Testen vor dem Push

Nach Code-Änderungen lokal prüfen: `python3 -m http.server 8000` im Repo, Seite öffnen, Passwort eingeben, alle Tabs ansehen.

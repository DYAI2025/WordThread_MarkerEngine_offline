Ziel, Geltungsbereich, Nicht‑Ziele

Ziel
PROMATRA_INSYS nimmt Audio entgegen, extrahiert Prosodie und Voice‑Signale (inkl. Sprechererkennung/‑trennung), erzeugt ein zeitgestempeltes Transkript sowie Marker‑Annotationen und liefert daraus:

ein annotiertes Transkript (maschinenlesbar + optional menschenlesbare Vorschau),

einen normierten Handover für die Marker Engine mit Chunks und Ereignissen, falls --handover gesetzt ist.

DEV_PROMPT-promatra inc.1

Geltungsbereich

Audio zu Text via ASR mit Wort‑/Token‑Zeitstempeln.

Prosody‑Marker (Pitch/F0, Energie/Intensität, Pausen, Sprech‑Tempo etc.).

Voice‑Marker (Sprecher‑Diarisierung, Sprecher‑Embedding, Stimmqualitäts‑Proxys).

Diskrete EMO‑Events aus Paralinguistik als CLU*EMO*\* mit High‑Confidence‑Gates und Stabilitätsfenstern.

DEV_PROMPT-promatra inc.1

Nicht‑Ziele

Keine semantische Textanalyse, kein SEM‑Layer, kein inhaltliches Scoring. Das passiert nachgelagert in der Marker Engine. Vorversionen, die Text‑Only analysiert haben, werden hiermit ersetzt.

DEV_PROMPT-promatra inc.1

1. High‑Level‑Pipeline

Ingest

Eingänge: wav, flac, m4a, mp3. Normalisierung auf 16 kHz Mono für ASR; Original‑Samplerate für Prosodie optional zusätzlich behalten.

Preprocess

Lautheits‑Norm, DC‑Offset‑Fix, Bandpass optional. VAD für Sprachsegmente.

Diarization

Sprecherwechsel‑Detektion, Clustering, Zuweisung speaker_id=S1..Sn. Optional: Kanal‑Know‑how bei Mehrkanal.

ASR

Wortebene mit Zeitstempeln und Confidences. Ausgabe segment‑ und speaker‑synchron.

Prosodie & Voice

Pro Segment und Sprecher: F0‑Statistiken, Intensität/Energie, Pausen, Artikulations‑ und Sprechrate, Jitter/Shimmer‑Proxys, ZCR, Spektral‑Metriken; Sprecher‑Embeddings, Stimmqualitätsmarker.

Eventing

Regeln/Detektoren für Prosody‑Peaks und CLU*EMO*{ANGER,SADNESS,JOY} mit score ≥ 0.8 und Stabilitätsfenster 30–60 s. Konfliktauflösung: dominanteste Klasse. Telemetrie: Confirm/Retract.

DEV_PROMPT-promatra inc.1

Handover & Exporte

Annotated Transcript als JSONL.

Optional: menschenlesbare Vorschau (MD; PDF/DOCX ableitbar).

Bei --handover: 5.000‑Zeichen‑Chunking auf dem Transkript‑Text mit angehängten Prosody/Voice‑Annotationen + normierter handover/‑Ordner gemäß Struktur unten.

DEV_PROMPT-promatra inc.1

Validierungssatz nach jedem Schritt: 1–2 Sätze zur lokalen Plausibilisierung und Entscheidung Fortfahren/Korrigieren.

DEV_PROMPT-promatra inc.1

2. Ein-/Ausgaben und Modi
   Eingaben

Dateien: .wav .flac .m4a .mp3

Optionales Referenz‑Dokument (z. B. bestehender Chat‑Export .txt/.md), in das Transkriptblöcke an markierten Ankerpunkten eingefügt werden können.

Ausgaben

Primär: transcript_annotated.jsonl (maschinenlesbar, s. Schema).

Events: events_prosody.jsonl, events_clu.jsonl.

Optional Human Preview: transcript_preview.md (+ pdf/docx).

Bei --handover: chunks_5000.jsonl und manifest.json im handover/. Struktur unten.

DEV_PROMPT-promatra inc.1

Betriebsarten

Standalone: Kein Chunking; Fokus auf vollständiges annotiertes Transkript + optionale Vorschau.

Marker‑Engine‑Anbindung: Zusätzlich 5.000‑Zeichen‑Chunking und normierter Handover‑Ordner.

DEV_PROMPT-promatra inc.1

3. Datenmodell
   3.1 transcript_annotated.jsonl (eine Zeile pro Segment)
   {
   "job_id": "uuid",
   "segment_id": "seg_000123",
   "t0": 12.340,
   "t1": 16.880,
   "speaker_id": "S2",
   "channel": 0,
   "text": "… erkannter Text …",
   "words": [
   {"w":"…","t0":12.34,"t1":12.56,"conf":0.93},
   {"w":"…","t0":12.57,"t1":12.74,"conf":0.88}
   ],
   "prosody": {
   "f0_mean": 185.2,
   "f0_std": 24.1,
   "intensity_db_mean": -17.4,
   "speech_rate_syl_per_s": 4.6,
   "articulation_rate_syl_per_s": 5.2,
   "pause_count": 1,
   "pause_total_s": 0.42,
   "jitter_rel": 0.012,
   "shimmer_rel": 0.09,
   "zcr_mean": 0.08,
   "spectral_flux_mean": 0.21
   },
   "voice": {
   "embedding": "base64-…",
   "quality": {
   "roughness": 0.67,
   "breathiness": 0.31
   },
   "speaker_stability": 0.93
   },
   "markers": [
   {"label":"PROSODY_PEAK_ENERGY","score":0.87},
   {"label":"CLU_EMO_JOY","score":0.83,"stable_s":32.0}
   ]
   }

3.2 events_prosody.jsonl

Eine Zeile pro Event:

{"id":"evt_001","label":"PROSODY_PEAK_ENERGY","speaker_id":"S2","t0":12.3,"t1":13.1,"score":0.87}

3.3 events_clu.jsonl

Diskrete EMO‑Klassen gemäß CLU‑Schema (LD‑3.4), inkl. Stabilitätsfenster und High‑Confidence‑Gate.

DEV_PROMPT-promatra inc.1

3.4 speakers.json
{
"S1": {"embedding":"base64-…","segments":123,"dur_s":154.2},
"S2": {"embedding":"base64-…","segments":98,"dur_s":131.0}
}

3.5 Handover‑Ordner
handover/
chunks_5000.jsonl # Transkripttext + angehängte Marker, 5k Zeichen
events_ato.jsonl # Reserve (v1 optional)
events_sem.jsonl # Reserve (nicht genutzt in v1)
events_clu.jsonl # aus Prosodie/Voice abgeleitet
events_mema.jsonl # Reserve (v1 optional)
promatra_output.json # Meta-Index der obenstehenden Dateien
transcript_annotated.jsonl
speakers.json
manifest.json

Struktur angelehnt an die bereits beschriebene Übergabe.

DEV_PROMPT-promatra inc.1

4. Prosody‑ und Voice‑Detektion (Regeln)

Baseline‑Normalisierung je Sprecher:
Alle Schwellen als z‑Scores gegenüber Sprecher‑Baseline. Erst ab |z| ≥ 1.0 wird überhaupt markiert; harte Events ab |z| ≥ 1.8.

Prosody‑Marker (Beispiele):

PROSODY_PEAK_ENERGY: intensity_db_mean_z ≥ +1.8 innerhalb eines 3–6 s Fensters.

PROSODY_PEAK_PITCH: f0_mean_z ≥ +1.8 und f0_std_z ≥ +1.0.

PROSODY_FAST_RATE: articulation_rate_z ≥ +1.5.

PROSODY_LONG_PAUSE: Stille ≥ 0.75 s zwischen Wörtern.

PROSODY_ROUGH_VOICE: jitter_rel ≥ θ_j oder (jitter_rel_z ≥ +1.5 ∧ shimmer_rel_z ≥ +1.5).

Voice‑Marker:

SPEAKER_CHANGE: von Diarisierung emittiert.

SPEAKER_STABILITY_LOW: Häufige Fehlzuweisungen oder Embedding‑Drift > θ.

VOICE_QUALITY_ROUGHNESS/BREATHINESS: aus Jitter/Shimmer/Spektralindikatoren.

Diskrete EMO (paralinguistisch, textfrei):

CLU_EMO_ANGER: hohe Energie + hohe F0‑Varianz + raue Stimme, stabil ≥ 30 s, score ≥ 0.8.

CLU_EMO_SADNESS: niedrige Energie + tiefe F0 + verlangsamte Rate + längere Pausen.

CLU_EMO_JOY: erhöhte F0 + erhöhte Energie + beschleunigte Artikulation.
Emits nur wenn Stabilität und Score erfüllt; Konflikte via Dominanz. Telemetrie Confirm/Retract.

DEV_PROMPT-promatra inc.1

5. ASR‑Felder (Definition für Annotationskonsistenz)

Segmentebene: t0,t1, speaker_id, channel, text, words[].

Wortebene: {w, t0, t1, conf}.

Job‑Meta: sample_rate_in, sample_rate_proc, lang_hint, asr_model, diar_model, vad_model.
Diese Felder sind Grundlage für zeitgenaue Prosody‑Marker und den Einsatz der Stabilitätsfenster. (Vorversionen sprachen von Textformaten; hier wird explizit Audio→ASR→Marker festgelegt.)

DEV_PROMPT-promatra inc.1

6. Einfügen in Originaltexte (optional)

Wenn ein Originaltext bereitsteht (z. B. Chat‑Export .txt/.md), kann PROMATRA_INSYS Transkriptblöcke an Anker einfügen:

Ankerform: [[AUDIO_SEG:<segment_id>]] im Quelltext oder heuristisch per Zeit/Datum.

Ergebnis: doc_with_insertions.md, Blöcke enthalten Sprecher, Zeit, Text + Marker‑Kurzbadges.
Dies ist ein Komfortpfad für Menschen; für die Marker Engine zählt der JSON‑Handover.

DEV_PROMPT-promatra inc.1

7. API & CLI

HTTP

POST /audio/analyze?mode=standalone|engine&export=md,pdf,docx&handover=true|false
Body: Audiofile (+ optional Originaltext). Return: JSON mit Pfaden/URLs zu Artefakten.

GET /exports/{job_id} → Artefaktliste inkl. handover/manifest.json.

CLI

promatra audio --mode standalone --in ./call.m4a --export md
promatra audio --mode engine --in ./meeting.wav --handover --export md,pdf

(Beibehaltener Exportpfad und Handover‑Konzept aus der Vorversion, jetzt audio‑first.)

DEV_PROMPT-promatra inc.1

8. Fehlerbehandlung

INPUT_UNSUPPORTED_AUDIO (Format/Codec unlesbar)

ASR_FAILURE (Modellfehler/Timeout)

DIARIZATION_FAILURE

PROSODY_EXTRACTION_FAILURE

EXPORT_FAILURE
Antwortobjekt führt error String, sonst leer. Kein Silent‑Drop. (Validierungs‑Sätze geben die Kurzdiagnose aus.)

DEV_PROMPT-promatra inc.1

9. Telemetrie & Gates

Raten: Prosody‑Events pro Minute, CLU_EMO‑Confirm/Retract, Diar‑Purity.

Warnungen: zu viele Retracts, Ausfall von Prosody‑Kanälen, Embedding‑Drift.

Ziel: „Besser wenig, dafür valide Events.“

DEV_PROMPT-promatra inc.1

10. Sicherheit & Datenschutz

PII‑Redaktion optional: --redact pii=none|light|aggressive mit Span‑Markierung.

Keine Rohdaten in Logs. Keine verdeckten Uploads. Artefakte nur im Job‑Scope.

11. Validierungssätze (Beispiele)

Ingest: „Audio erkannt (48 kHz stereo, 23:14 min), VAD aktiv. Fortfahren.“

Diar: „3 Sprecher gefunden, Purity 0.91. Fortfahren.“

ASR: „WER 8.5 %, Wort‑Timestamps vollständig. Fortfahren.“

Prosody: „F0/Intensität pro Sprecher stabil; 12 Prosody‑Events. Fortfahren.“

CLU_EMO: „2 stabile JOY‑Events (≥30 s, score≥0.8), 0 Konflikte. Fortfahren.“

DEV_PROMPT-promatra inc.1

Handover: „handover/ erzeugt, 7 Dateien, Hashes ok. Fortfahren.“

DEV_PROMPT-promatra inc.1

12. Definition of Done (DoD)

Audio‑First: Mindestens eine reale Audiodatei wird zu einem annotierten Transkript verarbeitet; kein Text‑Only‑Pfad.

DEV_PROMPT-promatra inc.1

Prosody & Voice: Marker werden aus Audio‑Merkmalen abgeleitet und sind an Segmente/Wörter gebunden.

CLU_EMO: ANGER|SADNESS|JOY emittiert über paralinguistische Regeln mit High‑Confidence‑Gate und Stabilitätsfenster.

DEV_PROMPT-promatra inc.1

Handover: Bei --handover entsteht ein vollständiger handover/‑Ordner inkl. chunks_5000.jsonl, events_clu.jsonl, manifest.json.

DEV_PROMPT-promatra inc.1

Exports: Maschinenlesbar (transcript_annotated.jsonl, Events) und optional menschenlesbar (.md/.pdf/.docx).

DEV_PROMPT-promatra inc.1

Validierung: Nach jedem Pipeline‑Schritt liegt ein Validierungssatz im Log und im Manifest.

Fehlerbild: Eigene Fehlertypen setzen error deterministisch.

CI‑Tauglichkeit: Deterministische Dateinamen, Checksummen, reproduzierbare Builds, keine Mockups.

13. Beispielartefakte (gekürzt)
    13.1 transcript_annotated.jsonl (1 Zeile)
    {
    "job_id":"4c7c…",
    "segment_id":"seg_000045",
    "t0":62.41,"t1":66.93,
    "speaker_id":"S1","channel":0,
    "text":"Ich glaube, das passt.",
    "words":[
    {"w":"Ich","t0":62.41,"t1":62.61,"conf":0.94},
    {"w":"glaube,","t0":62.62,"t1":63.02,"conf":0.92},
    {"w":"das","t0":63.03,"t1":63.19,"conf":0.95},
    {"w":"passt.","t0":63.20,"t1":63.72,"conf":0.93}
    ],
    "prosody":{"f0_mean":142.7,"intensity_db_mean":-19.3,"speech_rate_syl_per_s":4.2,"pause_count":0},
    "voice":{"embedding":"base64-…","quality":{"roughness":0.22,"breathiness":0.28},"speaker_stability":0.96},
    "markers":[{"label":"PROSODY_PEAK_PITCH","score":0.82}]
    }

13.2 events_clu.jsonl (1 Zeile)
{"id":"evt_joy_002","class":"CLU_EMO_JOY","speaker_id":"S1","t0":120.0,"t1":152.0,"score":0.83,"stable_s":32.0,"confirm":1,"retract":0}

(Definitionen und Gates gemäß CLU‑Entscheidung. )

DEV_PROMPT-promatra inc.1

13.3 manifest.json (Auszug)
{
"job_id":"4c7c…",
"inputs":{"audio":["./in/call.m4a"]},
"models":{"asr":"asr_vX","diar":"diar_vY","prosody":"prosody_v1"},
"artifacts":[
"transcript_annotated.jsonl","events_prosody.jsonl","events_clu.jsonl",
"speakers.json","transcript_preview.md"
],
"handover":{"enabled":true,"files":["handover/chunks_5000.jsonl","handover/manifest.json"]},
"hashes":{"transcript_annotated.jsonl":"…"}
}

14. Implementierungshinweise

Determinismus: Keine zufälligen Seeds in Diar/ASR‑Postprocessing.

Zweistufige Prosody: Frame‑Features auf Segmentebene mitteln; Outlier‑Winsorisierung.

Sprecher‑Baseline: Rollierende Fenster für z‑Score‑Robustheit.

Chunking: Text aus ASR, 5.000‑Zeichen hart an Wortgrenzen; Marker am Chunkende replizieren, wenn Span überlappt.

Exports: MD als Quelle; PDF/DOCX aus MD. (Konzept bereits angelegt.)

DEV_PROMPT-promatra inc.1

Das ist die konsistente, audio‑first Fassung von PROMATRA_INSYS: Audio rein, Prosody/Voice messen, annotiertes Transkript und normierter Handover raus. Keine semantische Textanalyse in diesem Modul. Alles Weitere übernimmt die Marker Engine.

DEV_PROMPT-promatra inc.1

DEV_PROMPT-promatra inc.1

DEV_PROMPT-promatra inc.1

Quellen

pdf first, light als standard

ChatGPT kann Fehler machen. OpenAI verwendet keine Daten aus dem Arbeitsbereich DIYrigent GmbH zum Trainieren seiner Modelle.

Inkrement 1 — Audio→Transkript mit Prosody/Voice‑Basisschicht

Zweck: Von Sprachdatei zu einem annotierten, zeitgestempelten Transkript mit Prosody‑ und Voice‑Basismarkern, plus menschenlesbarer Vorschau. Kein 5k‑Chunking, kein SEM. Fokus: verlässliche Grundlagen, die direkt nutzbar sind.
Bezug zur Spezifikation: Nutzer erhält strukturiertes Dokument mit Originaltextnähe und Annotationen; Export mind. als Markdown, optional PDF/DOCX. Nach jedem Schritt Kurz‑Validierung.

DEV_PROMPT-promatra inc.1

Scope (muss enthalten sein)

Audio‑Ingest & Preprocess: WAV/FLAC/M4A/MP3, VAD, Normalisierung.

Diarisierung: Sprecher S1..Sn, Zeitsegmente.

ASR mit Wort‑Zeitstempeln: Grundlage für zeitgenaue Marker, menschenlesbare Vorschau. (Die Spez fordert sichtbare, annotierte Ergebnisse für Chat/Fließtext.)

DEV_PROMPT-promatra inc.1

Prosody‑Basismerkmale pro Segment & Sprecher: F0‑Mittel/Varianz, Intensität, Sprech‑ und Artikulationsrate, Pausen.

Basismarker (regelbasiert, textfrei):

PROSODY_PEAK_ENERGY, PROSODY_PEAK_PITCH, PROSODY_LONG_PAUSE, PROSODY_FAST_RATE.

Artefakte:

transcript_annotated.jsonl mit Segmenten, Wörtern, Prosody/Voice‑Feldern und Marker‑Hits.

events_prosody.jsonl (eine Zeile pro Event).

transcript_preview.md (+ optional pdf/docx), strukturiert wie gefordert.

DEV_PROMPT-promatra inc.1

Validierungssätze: Nach Ingest, Diar, ASR, Prosody, Export jeweils 1–2 Sätze Auto‑Plausibilisierung, wie in der Spez verlangt.

DEV_PROMPT-promatra inc.1

Nicht enthalten

5k‑Chunking und handover/‑Ordner. Das kommt in Inkrement 2, wie vorgesehen.

DEV_PROMPT-promatra inc.1

Schnittstellen

CLI:
promatra audio --mode standalone --in ./call.m4a --export md,pdf

HTTP:
POST /audio/analyze?mode=standalone&export=md,pdf

Akzeptanzkriterien (DoD)

Echter Output, keine Dummies: transcript_annotated.jsonl und transcript_preview.md existieren, sind befüllt und konsistent referenziert.

DEV_PROMPT-promatra inc.1

Sprecher‑Synchronität: Jede Zeile im Transkript hat t0/t1 und speaker_id, Wort‑Zeitstempel liegen innerhalb des Segmentfensters.

Marker‑Emission: Mindestens 3 Prosody‑Eventtypen werden korrekt emittiert und zeitlich referenziert.

Exportpflicht: Markdown vorhanden; PDF/DOCX optional, wie spezifiziert.

DEV_PROMPT-promatra inc.1

Validierungssätze: In Log/Manifest ersichtlich; „Fortfahren/Korrigieren“‑Entscheidung nach jedem Schritt.

DEV_PROMPT-promatra inc.1

Tests

Golden‑Audio (kurzer Two‑Speaker‑Call, 2–3 min): Erwartete Sprecherwechsel und 2–3 pausen‑/energiebedingte Events.

Property‑Checks: Wortzeitstempel sind monoton; keine Wort‑Überlappungen; Prosody‑Fenster decken ASR‑Spanne ab.

Visuelle Probe: transcript_preview.md zeigt Sprecherzeilen, Zeit, Text, Marker‑Badges in einer Zusatzspalte, wie gefordert.

DEV_PROMPT-promatra inc.1

Beispielauszug transcript_annotated.jsonl (1 Segment)
{"segment_id":"seg_0007","t0":12.34,"t1":16.88,"speaker_id":"S2",
"text":"…", "words":[{"w":"…","t0":12.34,"t1":12.56,"conf":0.93}],
"prosody":{"f0_mean":185.2,"intensity_db_mean":-17.4,"speech_rate_syl_per_s":4.6,"pause_count":1},
"voice":{"embedding":"base64-…","speaker_stability":0.93},
"markers":[{"label":"PROSODY_PEAK_ENERGY","score":0.86}]}

Mehrwert nach Inkrement 1: Du kannst heute schon Audio verarbeiten, Sprecher erkennen, Prosody messen, und ein prüfbares, lesbares Dokument plus maschinenlesbare Events ausspielen. Genau das fordert die Spez: sichtbarer Output für Nutzer, klare Annotationen.

DEV_PROMPT-promatra inc.1

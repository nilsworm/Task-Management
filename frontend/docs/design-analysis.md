# Design-Analyse: personal-data-dashboard

Quelle: `personal-data-dashboard/project/dashboard.html`
Analysiert am: 2026-04-24

---

## 1. Übersicht der Dateien

| Datei | Beschreibung |
|---|---|
| `README.md` | Claude-Design-Handoff-Hinweise |
| `project/dashboard.html` | Vollständige Single-File React-App (1909 Zeilen, Babel-Standalone, kein Build-Step) |

Kein separates CSS, keine Assets, keine weiteren Komponenten-Dateien.

---

## 2. Design-Tokens

### Farben (CSS-Variablen)

#### Dark Theme (Standard)
| Variable | Wert | Verwendung |
|---|---|---|
| `--bg` | `#0a0a0f` | Seiten-Hintergrund |
| `--bg1` | `#0f0f17` | Nav-Bar, Card-Header |
| `--bg2` | `#13131d` | Panel-Hintergrund |
| `--bg3` | `#181824` | Task-Cards, Tabellenzeilen-Hover |
| `--bg4` | `#1e1e2e` | Inputs, Stepper-Buttons |
| `--border` | `#2a2a3d` | Primäre Trennlinien |
| `--border2` | `#333350` | Hover-Borders, Input-Focus-Vorstufe |
| `--text` | `#e2e2f0` | Primärtext |
| `--text2` | `#9090b0` | Sekundärtext, Labels |
| `--text3` | `#5a5a7a` | Placeholder, Timestamps, Hints |

#### Light Theme (Overrides via `[data-theme="light"]`)
| Variable | Wert |
|---|---|
| `--bg` | `#f7f7fb` |
| `--bg1` | `#ffffff` |
| `--bg2` | `#ffffff` |
| `--bg3` | `#f2f2f7` |
| `--bg4` | `#e9e9f0` |
| `--border` | `#e2e2ec` |
| `--border2` | `#cfcfdc` |
| `--text` | `#1a1a28` |
| `--text2` | `#55556e` |
| `--text3` | `#8a8aa3` |

#### Akzentfarben (theme-unabhängig)
| Variable | Hex | Rolle |
|---|---|---|
| `--cyan` | `#00d4ff` | Primärer Akzent, aktive Zustände, Links |
| `--cyan-dim` | `rgba(0,212,255,0.15)` | Subtile Akzent-Flächen |
| `--cyan-glow` | `rgba(0,212,255,0.08)` | Sehr subtile Glow-Flächen |
| `--red` | `#ff4d6d` | Danger, High-Priorität, Overdue |
| `--red-dim` | `rgba(255,77,109,0.15)` | Danger-Backgrounds |
| `--yellow` | `#ffd166` | Medium-Priorität, Review, Warnungen |
| `--yellow-dim` | `rgba(255,209,102,0.15)` | Warning-Backgrounds |
| `--green` | `#06d6a0` | Done, Low-Priorität, Success |
| `--green-dim` | `rgba(6,214,160,0.15)` | Success-Backgrounds |
| `--purple` | `#a78bfa` | DevOps/Planning-Label, Monthly-Goals |
| `--orange` | `#fb923c` | Backend/Database-Label |

#### Status-Farben
| Status | Farbe | Hintergrund |
|---|---|---|
| Backlog | `#5a5a7a` | `rgba(90,90,122,0.18)` |
| In Progress | `#00d4ff` | `rgba(0,212,255,0.12)` |
| Review | `#ffd166` | `rgba(255,209,102,0.12)` |
| Done | `#06d6a0` | `rgba(6,214,160,0.12)` |

#### Prioritäts-Farben
| Priorität | Farbe | Hintergrund |
|---|---|---|
| High | `#ff4d6d` | `rgba(255,77,109,0.15)` |
| Medium | `#ffd166` | `rgba(255,209,102,0.15)` |
| Low | `#06d6a0` | `rgba(6,214,160,0.15)` |

#### Label-Farben (Tag-Farben)
| Label | Farbe |
|---|---|
| Frontend | `#ffd166` |
| Backend | `#fb923c` |
| DevOps | `#a78bfa` |
| Database | `#fb923c` |
| Testing | `#06d6a0` |
| Design | `#00d4ff` |
| Security | `#ff4d6d` |
| Planning | `#a78bfa` |

---

### Typografie

| Variable | Wert |
|---|---|
| `--sans` | `'Inter', sans-serif` |
| `--mono` | `'JetBrains Mono', monospace` |

**Verwendete Font-Gewichte:** 300, 400, 500, 600, 700, 800

**Größen-Skala (häufig genutzt):**
- 9–10px: Timestamps, Badge-Beschriftungen, Tabellen-Header
- 11px: Sekundäre Labels, Filter-Buttons, Monospace-Metadaten
- 12px: Primärer Body-Text, Task-Titel in Tabellen
- 13px: Wichtige Labels, Log-Editor-Text
- 14px: Hervorgehobener Body-Text
- 18px: Sprint-Titel, Mood-Picker-Icons
- 44px: Sprint-Fortschrittsprozent (großer numerischer Wert)
- 48–64px: Streak-Anzeige

**Font-Scale-Tweak:** Default 1.15× (wird auf `document.documentElement.style.fontSize` gesetzt)

---

### Spacing

- **Main Content Padding:** 12px rundum
- **Card Padding:** 10–16px (meistens `padding: 14px 16px`)
- **Card Gap:** 8–12px
- **Nav-Height:** 48px (flexShrink 0)
- **Scrollbar-Breite:** 4px
- **Inline-Grid-Gaps:** 6px (kleinere Elemente), 10–12px (Panels)

---

### Radien, Schatten, Borders

**Border-Radii:**
- 3px: Badges (Priority, Label, Status)
- 4px: Inputs, Buttons (Standard)
- 5px: Nav-Tab-Buttons, Task-Cards im Board
- 6px: Panels/Sections
- 8px: Modale
- 50%: Dot-Indikatoren

**Schatten:**
| Variable | Wert | Verwendung |
|---|---|---|
| `--shadow-strong` | `0 20px 60px rgba(0,0,0,0.6)` | Modale |
| `--shadow-med` | `0 8px 32px rgba(0,0,0,0.5)` | Schwebende Panels |
| `--shadow-card` | `0 4px 20px rgba(0,0,0,0.4)` | Task-Edit-Card |
| `--shadow-hover` | `0 2px 16px rgba(0,0,0,0.3)` | Hover-Zustand von Cards |

**Sonstige visuelle Details:**
- Glow-Effekte auf Akzent-Elementen: `box-shadow: 0 0 12px rgba(0,212,255,0.3)`
- Progress-Bars mit Glow: `box-shadow: 0 0 10px rgba(0,212,255,0.5)`
- Hintergrund-Radial-Gradient: `radial-gradient(ellipse at 20% 0%, rgba(0,212,255,0.03) 0%, transparent 50%)` — subtiler Cyan-Schimmer oben links
- Backdrop-Filter: `blur(8px)` auf Nav-Bar, `blur(4px)` auf Modal-Overlay
- Scrollbar: 4px, Thumb-Farbe `--border2`

---

## 3. Komponenten-Inventar

### Layout / Navigation
| Komponente | Beschreibung |
|---|---|
| **TopNav** | 48px horizontale Tab-Leiste; Logo links, 6 Tabs, Stats + ThemeToggle + Datum rechts |
| **Logo** | 24×24 Gradient-Box (`cyan → cyan/40%`), Monogramm "PD", Text "devflow" |
| **TabButton** | `display:flex`, Icon + Label, active: `cyan`-Farbe + `rgba(0,212,255,0.1)`-Hintergrund |
| **ThemeToggle** | 28×28 Icon-Button, Sun/Moon-SVG |
| **GlobalStats** | "X in progress · Y done" als Mono-Text mit Farb-Dots in der Nav |

### Badge-Komponenten
| Komponente | Props | Beschreibung |
|---|---|---|
| `StatusBadge` | `status` | Dot + Label, farbkodiert nach Status |
| `PriorityBadge` | `priority` | Uppercase Mono-Text, farbkodiert |
| `LabelTag` | `label, color` | Farbiger Text mit `color+'22'`-Background |

### Board Tab
| Komponente | Beschreibung |
|---|---|
| **KanbanColumn** | 4-spaltig, Drag&Drop (native HTML5), Spalten-Header mit Count-Badge |
| **KanbanCard** | Draggable, Title + Priority + Label + Datum + "Advance"-Button |
| **AddTaskForm** | Inline-Form in der Backlog-Spalte (Title, Priority, Label, Due Date) |

### Tasks Tab
| Komponente | Beschreibung |
|---|---|
| **FilterBar** | Status- und Prioritäts-Filter-Buttons + Task-Count |
| **TaskTable** | CSS-Grid-Tabelle: Checkbox / Title / Status / Priority / Due / Label |
| **TaskRow** | Klickbar zum Expandieren, zebra-striped |
| **TaskEditCard** | Inline im Table; TASK-ID-Badge, Title-Input, Status/Priority/Effort/Due-Grid, Label-Picker, Description-Textarea, "Mentioned in"-Log-Links |
| **Checkbox** | 16×16, grün wenn Done, border-radius 3px |

### Sprints Tab
| Komponente | Beschreibung |
|---|---|
| **SprintSidebar** | 260px, Sprint-Liste mit Mini-Progress-Bar + Datum, "New Sprint" Inline-Form |
| **SprintDetail** | Editierbarer Name/Datum, Sprint-Goal-Text, großes Progress-Prozent (44px Mono), Progress-Bar, Status-Breakdown-Pills, Sprint-Backlog-Liste |
| **SprintTaskRow** | Checkbox + Title + StatusBadge + PriorityBadge + Effort-Pill + Remove-Button |
| **AssignTaskPicker** | Modal mit Liste unassigned Tasks |

### Daily Log Tab *(NEU — kein Backend-Äquivalent)*
| Komponente | Beschreibung |
|---|---|
| **LogEditor** | Linkes Panel: Mood-Picker (4 Emoji), MentionTextarea, char/word Count, Save-Button |
| **LogHistory** | Rechtes Panel (320px): sortierte Einträge der letzten 7 Tage als klickbare Cards |
| **LogEntryModal** | Overlay mit editierbarem Volltext-Eintrag + Mood-Auswahl |
| **MentionTextarea** | Textarea mit `@TASK-xxx`-Autocomplete (Dropdown-Menü) |
| **MentionText** | Rendert `@TASK-xxx` als klickbare Cyan-Pills |

### Analytics Tab
| Komponente | Beschreibung |
|---|---|
| **BarChart** | SVG-Balkendiagramm (Inline-React, kein Recharts) |
| **LineChart** | SVG-Liniendiagramm mit Flächenfüllung |
| **DonutChart** | SVG-Donut mit Legende |
| **StreakWidget** | Riesige Zahl + 🔥-Emoji + "consecutive days" |
| **Widget** | Wrapper mit Title + Border + Padding |

### Goals Tab
| Komponente | Beschreibung |
|---|---|
| **GoalSection** | "Weekly Goals" / "Monthly Goals" mit Akzentbalken-Header |
| **GoalCard** | Titel, Category-Tag, Timeframe-Badge (WEEKLY/MONTHLY), Status-Badge, Progress-Bar + %-Anzeige, ±10-Stepper |

### Modale / Overlays
| Komponente | Beschreibung |
|---|---|
| **ModalOverlay** | `position:fixed, inset:0`, backdrop-blur, z-index 100 |
| **TweaksPanel** | Floating-Panel bottom-right: Theme-Toggle, 5 Akzentfarben, 5 Background-Farben, Font-Scale-Slider |

---

## 4. Layout-Architektur

Das Design nutzt eine **horizontale Top-Nav** (kein Sidebar) mit 6 Tabs:

```
┌─────────────────────────────────────────────────────────┐
│ Logo │ Board │ Tasks │ Sprints │ Daily Log │ Analytics │ Goals │ [stats] [theme] [date] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                  Tab Content (12px padding)             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Unsere App** hat dagegen eine **vertikale Sidebar** (240px) mit 5 Routen.

---

## 5. Mapping: Design → Unsere App

| Design-Tab | Unsere Route | Übereinstimmung | Bemerkung |
|---|---|---|---|
| **Board** | `/tasks` (Kanban-Ansicht) | Teilweise | Design zeigt alle Tasks sprints-unabhängig; unser Kanban ist sprint-spezifisch |
| **Tasks** | `/tasks` (Tabellen-Ansicht) | Gut | Gleiche Struktur; Design hat inline expandable Edit-Card statt Modal |
| **Sprints** | `/sprints` + `/sprints/:id` | Gut | Design: Sidebar+Detail statt Card-Grid+Detail-Page; Sprint-Goal-Textfeld fehlt in unserem Backend |
| **Daily Log** | — | **Kein Äquivalent** | Neues Feature, kein Backend-Support |
| **Analytics** | `/dashboard` | Teilweise | Design nutzt eigene SVG-Charts + Streak statt Recharts; Widgets ähnlich |
| **Goals** | `/goals` | Teilweise | Design: einfacher `progress`-Wert (0–100, Stepper ±10); unser Backend hat OKR (Objective + KeyResults) |

### Größte Design-Unterschiede zur bestehenden App

1. **Navigation:** Design → Top-Tab-Bar; App → Left-Sidebar. Strukturelle Änderung des Layouts.
2. **Goals-Datenmodell:** Design kennt nur `progress %` (manuell via Stepper). Unser Backend hat KeyResults, deren Werte den Fortschritt berechnen. Design ignoriert KeyResults komplett.
3. **Daily Log:** Vollständig neues Feature (Journaling + Mood + @mentions).
4. **Board-Tab vs. Sprint-Kanban:** Design hat einen globalen Board-Tab (alle Tasks). Unsere App hat kein globales Kanban — nur sprint-spezifisch.
5. **Inline-Edit vs. Modal:** Design klappt den Task-Edit-Row inline im Table aus. Unsere App öffnet ein Modal.
6. **Sprint hat `goal`-Textfeld:** Unser `Sprint`-Schema hat kein `goal`-Feld.
7. **Task hat `label` (single):** Unsere Tasks haben `tags: string[]`. Design hat ein einzelnes Label aus einer Festliste mit zugehöriger Farbe.

---

## 6. Entscheidungen (2026-04-24)

| # | Frage | Entscheidung |
|---|---|---|
| F1 | Daily Log | **Weglassen** — Backlog-Eintrag in PROGRESS.md |
| F2 | Sprint `goal`-Textfeld | **Backend erweitern** (Phase A) |
| F3 | Goals OKR vs. einfaches Progress % | **OKR-Struktur bleibt** — Card zeigt berechneten Progress, Detail zeigt KRs |
| F4 | Task `label` vs. `tags[]` | **Mapping** — erstes Tag als Label darstellen, Farb-Map aus Design |
| F5 | Globaler Board-Tab | **/tasks bekommt View-Switch** (Liste / Board), keine separate Route |
| D1 | Navigation Top-Nav vs. Sidebar | **Sidebar bleibt**, Design-Tokens der Top-Nav-Elemente auf Sidebar übertragen |
| D2 | Inline-Edit vs. Modal | **Inline-Expand** für Task-Rows übernehmen (Create bleibt Modal) |
| D3 | Chart-Bibliothek | **Recharts bleibt**, Farben/Glow ans Design angepasst |

**Design-Treue-Regel:** Alle visuellen Aspekte 1:1 umsetzen. Abweichungen nur bei Navigation (Sidebar), fehlenden Backend-Features (Daily Log) und nicht vorhandenen Feldern.

---

## 7. Offene Fragen

### Backend-Fehlende Features

**F1 — Daily Log:**
Das Design zeigt einen täglichen Tagebuch-Tab mit Mood-Tracking und @Task-Mentions. Unser Backend hat kein entsprechendes Modell.
→ **Entscheidung notwendig:** Weglassen (Scope-Disziplin) oder neues Backend-Feature (`DailyLog`-Entität)?

**F2 — Sprint `goal`-Feld:**
Das Sprint-Detail-Panel hat ein editierbares "Sprint goal" Textfeld (frei formulierter Satz). Unser `Sprint`-Schema hat nur `name`, `start_date`, `end_date`, `status`.
→ **Entscheidung notwendig:** Backend-Migration ergänzen oder Feld weglassen?

**F3 — Goals: OKR vs. einfaches Progress %:**
Das Design zeigt Goals mit einem einzigen `progress`-Wert (manuell ±10). Unser Backend berechnet den Goal-Fortschritt aus KeyResult-Werten.
→ **Empfehlung:** Unser OKR-Modell ist mächtiger. Im Design trotzdem die berechnete `progress_percent`-Summe der KRs anzeigen. Die Stepper-Buttons weglassen (wäre Workaround für fehlendes KR-UI). KR-Bearbeitung bleibt in der GoalDetailPage.

**F4 — Task `label` vs. `tags[]`:**
Design hat `label: string` (eines aus Festliste). Unser Backend hat `tags: string[]`.
→ **Empfehlung:** Beim Anzeigen das erste Tag als "Label" darstellen; die Label-Farbe aus einer Farb-Map ableiten wie im Design. Kein Backend-Change nötig.

**F5 — Global Board-Tab (alle Tasks cross-sprint):**
Design hat einen Board-Tab, der alle Tasks — unabhängig vom Sprint — in 4 Kanban-Spalten zeigt.
→ **Entscheidung notwendig:** Neuen globalen Board-View bauen, oder unseren `/tasks`-View um eine Kanban-Ansicht erweitern? Unser Backend unterstützt `GET /tasks` ohne Sprint-Filter, also kein Backend-Change nötig.

**F6 — @Mention-Cross-Links (Log ↔ Task):**
Das Design verknüpft Log-Einträge mit Tasks über `@TASK-xxx`-Tokens und zeigt in der Task-Detail-Card, welche Log-Einträge diesen Task erwähnen. Setzt F1 (Daily Log) voraus.

**F7 — Analytics: Productivity Streak:**
Der "Streak"-Widget zählt aufeinanderfolgende Tage, an denen eine Log-Eintragung oder ein Task als Done markiert wurde. Setzt F1 (Daily Log) voraus.

**F8 — Tweaks-Panel:**
Design hat einen schwebenden Tweaks-Panel (Accent-Color, Background, Font-Scale). Unser App hat nur Dark/Light-Toggle.
→ **Empfehlung:** Weglassen (Scope). Unser Theme-System (shadcn/Tailwind CSS-Variablen) ist mächtiger, aber ein Tweaks-Panel ist nice-to-have.

### Design-Entscheidungen

**D1 — Navigation-Umbau (Sidebar → Top-Nav):**
Das ist die tiefgreifendste strukturelle Änderung. Betrifft `AppLayout.tsx` + alle Routen.
→ **Entscheidung notwendig:** Vollständig auf Top-Nav umsteigen, oder nur das visuelle Design der Sidebar anpassen?

**D2 — Inline Edit vs. Modal:**
Design klappt Task-Edit inline im Table aus. Unser System nutzt Modals.
→ **Empfehlung:** Inline-Expand übernehmen für Tasks (präziserer Design-Match). Modal-Pattern für Create beibehalten.

**D3 — Chart-Bibliothek:**
Design nutzt handgeschriebene SVG-React-Komponenten (kein Recharts). Unser System nutzt Recharts.
→ **Empfehlung:** Recharts behalten — es ist bereits integriert und liefert bessere Interaktivität. Design-Optik (Farben, Glow) anpassen.

# Starters

Skeleton specs for every document in an engagement, from first contact to closeout. Each one has
the right sections in the right order, the right tables and columns, and the right component on
each slide, with the method written into the comments, speaker notes and `<angle-bracket prompts>`.
Every number in a starter is a placeholder: replace it, or bind it from a data file with `data:`.

```bash
sv new --list                                         # every starter, with its one-line description
sv new <Client> "<Name>" --type <starter> [--brand <id>]
sv build ~/Servantium-Work/<Client>/<slug>/deck.yaml  # decks; everything else is spec.yaml
```

`sv new` copies the starter into `~/Servantium-Work/<Client>/<slug>/` and replaces `{{NAME}}`,
`{{CLIENT}}` and `{{BRAND}}` (default `servantium`). Line 1 of each starter is the description
`--list` prints.

This repo is public: starters hold no client names or facts. Fill them in the workspace only.

## By stage

| Stage | Starter | Kind | What it is |
|---|---|---|---|
| 00 Company | `capabilities-deck` | deck | Who we are, what we deliver and how we work |
| | `org-chart` | mermaid | Leaders, departments with headcount, one team in full |
| | `rate-card` | workbook | Bill and cost rates by role and level, fixed-fee packages |
| 01 First contact | `first-call-notes` | document | What we heard, what they asked, first MEDDPICC read, next steps |
| | `nda` | document | Mutual non-disclosure agreement |
| | `opportunity-record` | workbook | The CRM deal: properties, MEDDPICC, contacts, line items, stages |
| | `prospect-walkthrough` | deck | Servantium deck co-branded for a prospect, on their own engagement |
| 02 Discovery | `discovery-notes` | document | Findings by meeting, open questions for the workshop |
| | `solution-workshop` | deck | Design workshop readout that feeds the estimate |
| | `process-flow` | mermaid | How work moves step by step, with decisions and loops |
| | `data-flow` | mermaid | Sources, system of record, checks and destinations |
| | `close-plan` | workbook | Mutual close plan with owners on both sides and a calendar |
| 03 Estimate | `rom-estimate` | workbook | Low, high and midpoint by phase, with what would move it |
| | `estimate` | workbook | Role x hours x rate by phase, live, with cost and margin floor |
| | `assumptions-log` | document | Every quantity the price depends on and what happens if it changes |
| | `deal-desk-approval` | document | Concessions, approval matrix checks, margin against the floor |
| 04 Proposal | `quote` | workbook | Recurring and services lines, term schedule, billing milestones |
| | `proposal-deck` | deck | Outcome, design, plan, team and commercials |
| | `bid-defense` | deck | A shortlisted bid answered question by question |
| 05 Contract | `msa` | document | Master services agreement with schedules |
| | `sow` | document | Scope, deliverables and acceptance, fees, rates, assumptions, change control |
| | `work-order` | document | Unit-priced order under an MSA with priced lines |
| | `order-form` | document | Subscription order: SKUs, fees by year, billing and renewal |
| | `purchase-order` | document | A PO to a supplier or subcontractor (or a customer PO in a demo) |
| 06 Handoff | `sales-to-delivery-handoff` | document | What was sold, why, what was promised, what to protect |
| | `requirements` | document | Numbered, testable, risk-classed requirements |
| | `raci` | workbook | RACI with a one-A check, plus the stakeholder register |
| | `raid-log` | workbook | Risks, assumptions, issues and decisions with scores and counts |
| | `communication-plan` | document | Meeting rhythm, reports, escalation, records, distribution |
| 07 Kickoff | `kickoff-deck` | deck | Plan, milestones, owners, governance, risks, first 30 days |
| | `project-charter` | document | Purpose, measures, scope, milestones, budget, decision rights |
| | `project-plan` | workbook | Live Gantt with phases, dependencies and milestones |
| | `resource-plan` | workbook | Hours by role by month, loaded cost, check against plan |
| 08 Delivery | `solution-design` | document | How the system is configured, versioned at the design gate |
| | `validation-plan` | document | Risk-based test and acceptance plan (IQ/OQ/PQ or UAT) |
| | `traceability-matrix` | workbook | Requirements to design and tests, with gaps and test status |
| | `training-plan` | document | Sessions by role, materials, training record before access |
| | `status-report` | document | RAG by area, milestones and billing, hours, RAID, decision needed |
| | `meeting-minutes` | document | Decisions, options weighed, actions with owners |
| | `steering-deck` | deck | Monthly steering built around one decision |
| | `change-order` | document | A priced change to the SOW, with impact and approvals |
| | `invoice` | document | Milestone, subscription or expense invoice |
| | `expense-report` | workbook | Expense form plus a tracker against the project cap |
| | `timesheet-summary` | workbook | Actual hours against plan by role and month, with causes |
| | `cutover-runbook` | workbook | Timed go-live steps, go/no-go criteria, rollback point, contacts |
| 09 Closeout | `acceptance-certificate` | document | Written acceptance of a milestone against its criteria |
| | `closeout-report` | document | Result against what was sold, hours and margin, lessons learned |
| | `qbr-deck` | deck | Results against the metrics sold, usage, support, renewal path |

## Writing a new starter

- Line 1 is `# <one-line description of the document and when to use it>`.
- Carry `brand: {{BRAND}}`, `client: {{CLIENT}}` and the kind key (`deck:`, `document:`,
  `workbook:`, `mermaid:`) with `{{NAME}}`.
- Placeholders are `<angle-bracket prompts>`. Inside `{...}` or `[...]`, put any prompt that
  holds a comma or `: ` in double quotes. In Mermaid labels write `#lt;` and `#gt;`.
- Decks follow the deck method: cover then a timed agenda, short one-line claim titles, a
  different shape on each slide, never two rows of boxes back to back, the talk in the notes.
- Build it with `sv new` and `sv build` before committing: 0 errors, and look at the pages.

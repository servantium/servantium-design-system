# Layout references

Where to look for slide compositions, and the patterns we plan to add as components.
We borrow layouts (grid, hierarchy), never another template's files, art or branding.
Researched 2026-10-06.

## Libraries

| Library | Use it for | Licence note |
|---|---|---|
| [SlideModel](https://slidemodel.com/templates/tag/consulting/) | Consulting diagram types: operating model, stage-gate, RACI, maturity | Paid; no redistribution |
| [Slideworks](https://slideworks.io/resources/best-templates-and-tools-for-strategy-presentations) / [Flevy](https://flevy.com/slides) | Strategy-firm storyline and action titles | Paid; no resale |
| [Deckary](https://deckary.com/blog/consulting-slide-templates) | Real strategy-firm decks to check composition against | Study only |
| [Pitch templates](https://pitch.com/templates/collections/Project-proposal) | Modern marketing polish for proposals and roadmaps | Platform-bound |
| [Dock sales-deck gallery](https://dock.us/library/sales-deck-examples) | Real B2B sales decks: logo walls, old/new world, use-case galleries | Study only |
| Slidesgo, SlidesCarnival, Figma Community | Visual mood | Attribution licences; never import files |

## Patterns to add (proposal, roadmap and vision decks)

| Pattern | Composition | Serves | Nearest component today |
|---|---|---|---|
| Phase x row approach matrix | Phase columns, gate diamonds between; rows for activities, deliverables, what we need from you | Methodology | **built: `approach`** |
| Value chain with layers | Chevron stages across; rows beneath for people, the record passed along, the system, the measure | End-to-end system flow (CRM to project) | **built: `approach` with `tone: record` / `ai` rows** |
| Team bios | 2-4 photos, name, role, two-line credential, one relevant engagement | Credibility | **built: `team` slide, `people` component** |
| Logo wall | 8-15 monochrome logos in a grid, grouped | Past implementations | `logos` (max 4) |
| Case study one-pager | Challenge, approach, result columns; one big result number; quote strip | Proof | `split` |
| Investment options | Three tiers, middle raised as recommended; scope, duration, fee | Commercials appendix | `panels` (2-up) |
| 2x2 prioritization | Value vs effort, labelled bubbles, a named start-here quadrant | Use-case portfolio | none |
| Use-case bento | Asymmetric grid, one hero tile and 4-5 small tiles with icon, title, outcome | Use-case portfolio | `tiles` |
| Maturity staircase | 4-5 rising steps with you-are-here and target | Transformation vision, access that widens step by step | **built: `staircase`** |
| Lifecycle ring | 5-6 stages on a circle, outcome in the center, today accented | One-system vision | none |
| Old world / new world | Tangled tools on the left, one clean system on the right | Before/after opener | `compare` |
| Stage-gate arrow | Phased arrow, decision diamonds, exit criteria under each | Phased roadmap | `chevrons`, `milestones` |
| RACI grid | Activities by Servantium / client / partner, R-A-C-I chips | Governance | `table` |

Not adopted: the situation-complication-resolution executive summary. It conflicts with the
no-summary-slide rule (LEARNINGS 2026-09-30).

Also built 2026-10-06, not from the libraries: `adoption` (Rogers' curve with Moore's chasm and a
"who is here" marker) and `zoom` (a process step magnified into a detail panel).
Built 2026-10-12: `questions` (a stop where the client talks: a "?" panel and two to four
questions, each with why we ask). Also `middleout` (a platform in the middle of a stack, built outward
to both sides, each item with when it lands).

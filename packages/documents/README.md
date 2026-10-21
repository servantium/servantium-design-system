# @servantium/documents

Decks (pptx), documents (docx), workbooks (xlsx) and diagrams (Mermaid, or a swimlane with an
editable .drawio), each with a PDF, generated from a checked YAML spec on branded templates.
**Any brand:** Servantium's (colours and fonts from `@servantium/verdant`, logos and company facts
from `@servantium/brand`), a prospect's co-brand, another company's brand imported from its
website, or a fictional demo company. Nothing is typed by hand.

## What it makes

| First key in the spec | Output | Format reference |
|---|---|---|
| `deck:` | .pptx + .pdf + contact sheet | `spec.py` docstring, `examples/torture-test.yaml` |
| `document:` | .docx + .pdf (contracts with numbered clauses, schedules, signatures; invoices, POs, change orders, acceptance forms; RAG tables) | `docs.py`, `examples/doc-*.yaml` |
| `workbook:` | .xlsx + .pdf (live formula tables, Gantt plans that move with their dates, invoice / PO / expense forms, summary tabs) | `sheets.py`, `examples/workbook-*.yaml` |
| `mermaid:` | .svg + .png + .pdf in the brand's theme | `mermaid.py`, `examples/mermaid-*.yaml` |
| `lanes:` + `steps:` | swimlane .pdf/.png/.svg + .drawio | `diagram.py` |

All of them: `sv build <spec>` then `sv publish <spec>`. Office files are built to open in
PowerPoint/Word/Excel, import into Google Slides/Docs/Sheets, and open in Keynote (see
LEARNINGS.md for every rule that keeps that true).

## Starting a document

```bash
sv new --list                                         # 48 starters, first contact to closeout
sv new Acme "Kickoff" --type kickoff-deck --brand avelle   # a starter, in a brand
```

Starters (`starters/*.yaml`, listed by stage in `starters/README.md`) carry the method: the right
sections in order, the right tables, guidance as prompts. Fill the angle-bracket prompts, then
`sv build`.

## Brands

A brand is a folder, `brands/<id>/brand.yaml` plus logos and fonts (format: `brands.py`). The
spec picks one with `brand: <id>`; without the key the active brand (`SV_BRAND`, default
`servantium`) applies. Built in: `servantium`, and the fictional demo companies `avelle`,
`lattica`, `merrow`.

```bash
sv brand list                                  # every brand the engine can see
sv brand show avelle                           # roles, fonts, logo files
sv brand import acme.com --client Acme       # a real company: logo (Brandfetch), colours and fonts (its site)
sv templates --all                             # Office templates for every brand (dist/<id>/)
sv fonts install                               # brand fonts for Keynote and LibreOffice
sv stylebook avelle --company company.yaml --docs index.yaml -o avelle.html   # one-file style guide
```

- **Co-branded:** `brand: servantium` + `prepared_for: {name: Acme, logo: acme.png}` puts the
  reader's logo on the cover beside ours.
- **White-label:** `brand: <their id>`. Nothing of Servantium's appears.
- **Imported brands live in the workspace** (`~/Servantium-Work/<Client>/_brand/<id>/`), templates
  included. Never copy one into this repo: Brandfetch forbids caching, and a customer's brand is
  not ours to publish.
- A brand states colour ROLES (primary, dark, tint, ink, on_dark, accents...). Renderers never
  name a hex; `tests/test_brands.py` fails if one names "Servantium".

## Shared numbers

`data: {co: ../company.yaml}` loads data files; `"{{ co.quote.total | money }}"` fills a string and
a bare `"{{ co.quote.lines }}"` binds the list itself. So the estimate, proposal, SOW, plan and
invoices print the same figure. Format and filters: `bind.py`.

## Where it publishes

`drive: {root: demo, folder: "04 Proposal"}` files into
`Shared drives/Everything/Demo Companies/<client>/04 Proposal/`. Without it, the client's folder
in `Customers/`. Demo files can never land in a customer folder.

**Status: Stage 1.** Works on one machine with one pilot; multi-brand and all four kinds as of 2026-10-20. Stage 2 (installable for
everyone) waits until the engine has absorbed the pilot's corrections.

## How a deck gets made

```
storyboard (titles only, agreed)  ->  spec (YAML)  ->  sv check  ->  sv build  ->  look  ->  sv publish
```

```bash
npm run setup                          # once: venv + editable install
.venv/bin/sv doctor                    # fonts, LibreOffice, template, Drive, Finder
.venv/bin/sv new Acme "Status Report"          # starts ~/Servantium-Work/Acme/status-report/deck.yaml
.venv/bin/sv storyboard <spec>         # the titles alone, in order
.venv/bin/sv check <spec>              # every rule, before anything renders
.venv/bin/sv build <spec>              # pptx + pdf + contact sheet in <spec dir>/out/
.venv/bin/sv publish <spec>            # into Shared drives/Everything/Customers/<client>/
.venv/bin/sv pull <client> [match]     # latest matching Office file, back into the workspace
```

The spec format and every component are documented in
[`src/servantium_documents/spec.py`](src/servantium_documents/spec.py). The worked example
that uses all of them is [`examples/torture-test.yaml`](examples/torture-test.yaml).

## Rules

- **Client work never enters this repo.** It is public. Specs and decks live in
  `~/Servantium-Work/<Client>/`; published specs go to the client's `_source` folder.
- **Never overwrite in Drive.** Every publish is a new versioned file. Replacing a file
  gives it a new Drive ID and breaks every link and comment on it.
- **Other companies' logos are never stored here** (Brandfetch forbids caching). Partner
  logos for a deck live in that deck's workspace folder.
- **Never hand-edit `src/servantium_documents/tokens.py`.** Change Verdant, run
  `npm run tokens`. Document-only values live in `scripts/sync_tokens.py` with a reason.
- **Every correction becomes a rule.** See [LEARNINGS.md](LEARNINGS.md).

## Google Drive, with no Google integration

macOS blocks this process from the Drive mount, so Finder does the copying and Drive for
Desktop does the syncing ([`drive.py`](src/servantium_documents/drive.py)). Native Google
files (`.gslides`, `.gdoc`) are only links on disk; read those through Claude's Drive
connector. To confirm a publish reached Google, list the folder by ID: Drive's title
search lags behind uploads.

## Templates

`sv templates` rebuilds `dist/`: the slides template (11 layouts on one master), the
document template and the workbook template, each as an editable file for Google and a
template file for Microsoft.

## Tests

```bash
npm test
```


## Diagrams on a canvas

`sv diagram <spec.yaml>` lays out a workflow (swimlanes, joint steps, optional detours,
loops, phase bands, time budgets, notes) and writes four files: a PDF and PNG printed from a
brand SVG by headless Chrome, the SVG itself, and an editable `.drawio` file with the same
shapes and live connectors for diagrams.net. The layout is ours, not an auto-layout: one
column per step, in the order it happens. Format: the docstring in `diagram.py`. Needs
`node` and `puppeteer` (set `SV_NODE_PATH` if it isn't found).

# Changelog: Grove Email

Each release is a git tag, `grove-email@<version>`, that matches `package.json`, and a GitHub release with the Postmark-ready bundle. Versions follow what a change means for the backend that sends these emails:

- **patch:** copy, layout or styling; no field changes
- **minor:** a new template, or a new optional field
- **major:** a removed or renamed template or field, or a field that becomes required

## 0.1.0 (2026-09-29)

The first release: 13 system emails, ready for Postmark.

- **Account:** `welcome`, `welcome-organization`, `password-reset`
- **Activity:** `task`, `notification`, `digest`
- **Support:** `support-received`, `support-reply`
- **Service:** `incident`, `incident-resolved`, `maintenance`
- **Product:** `release-notes` (broadcast stream)
- **Legal:** `regulatory-notice` (legal review pending)

Every image loads from a permanent, fingerprinted address at `assets.servantium.com`. The field contract ships as `contract.json` and as Python `TypedDict`s. [docs/templates.md](./docs/templates.md) lists every field.

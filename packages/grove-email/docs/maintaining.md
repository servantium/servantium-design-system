# Maintaining the emails

Every change starts as a pull request in this repo. Nothing is edited in Postmark.

## Releasing

| Step | What happens |
|---|---|
| Pull request | Build, tests, and a check that every image is live. The gallery is attached to the run. Review the rendered emails there. |
| Merge to `main` | The same checks, on `main`. |
| Tag `email-vX.Y.Z` | The same checks, then a GitHub release with the Postmark-ready templates and the contract. Engineering pushes that release into Postmark. |

```bash
git switch main && git pull
git tag email-v0.2.0
git push origin email-v0.2.0
```

Choose the version by what the change means for the backend:

| Change | Version |
|---|---|
| Copy, layout or styling; no field changes | patch: `email-v0.2.1` |
| A new template, or a new optional field | minor: `email-v0.3.0` |
| A removed or renamed template or field, or a field that becomes required | major: `email-v1.0.0`, after engineering has shipped their side |

Email tags are separate from the design system's `v*` package tags, and neither triggers the other. Tell engineering when a release is out; the release notes list what's in the bundle.

**Rolling back:** engineering pushes the previous release's bundle. Postmark keeps no template history of its own; the releases are the history.

## Everyday changes

**Change copy or layout.** Edit the master in `src/emails/`, run `npm run build` and `npm test`, check `dist/index.html`, open a pull request.

**Add a template.**

1. Create `src/emails/<alias>.mdx`. The file name is the Postmark alias: lower case, words joined by hyphens, and permanent once engineering uses it.
2. Write it by following [writing-an-email.md](./writing-an-email.md).
3. Add the alias to `ORDER` in `scripts/collect.tsx`, so the gallery lists it in a sensible place.
4. In the pull request, say which event should send it. Engineering wires the sending.

**Retire or rename a template.** The backend names templates by alias, so an alias can't simply disappear.

1. Add the new template (for a rename), and ship it.
2. Engineering switches the backend to the new alias, or stops sending the old one.
3. Delete the master here. A release doesn't delete anything in Postmark: engineering removes the old template from both servers by hand.

**Change a field.** The order matters more than the change. See [fields.md → Changing fields safely](./fields.md#changing-fields-safely).

## Monthly release notes

The help site is where release notes are written. The email is assembled from them, so the two never disagree.

```bash
node scripts/draft-release-notes.mjs \
  --from ../../../servantium-help/src/content/docs/help/release-notes \
  --month 2026-10 \
  --pick "Feature one,Feature two,Feature three,Feature four"
```

This rewrites `src/emails/release-notes.mdx` with a handful of highlights, a count of everything else, and a link to the full notes. Every feature you didn't pick is listed in a comment at the bottom, so you can swap one in. `upcoming-*` notes are skipped: they describe changes still in testing.

Edit the draft, open a pull request, then tag a release. There's one `release-notes` template, rewritten each month. It goes out on Postmark's broadcast stream, which skips anyone who has unsubscribed.

## Company facts and links

Edit [`packages/brand/company.json`](../../brand/company.json): the address, the footer links, help@, LinkedIn, the app and help center URLs. Every email picks the change up at the next release, and `CompanyLink` and `<Button to="…">` pick up URL changes too.

A footer link can be held back until it's real with `"live": false`. The Status link is held back this way: when the status page exists, set it to `true`.

Emails already delivered keep the links they were sent with. The address is baked in on purpose, because a legal footer should show the address as it was when the email was sent.

## Images

Images live in the asset library: [`packages/brand/assets/`](../../brand/assets/) in git, served from `assets.servantium.com` at permanent, fingerprinted addresses. [The asset library](../../brand/docs/asset-library.md) has the full rules. In short:

1. Edit the SVG master, or the art generator in `packages/brand/scripts/render.mjs`, and run `npm run render` in `packages/brand` for the PNG or JPG email clients need.
2. Run `npm run manifest` in `packages/brand`. The changed file gets a new fingerprint and so a new address.
3. Run `npm run publish` in `packages/brand` to upload it. New addresses can't affect anything already sent, so this is safe from a branch.
4. Rebuild the emails and open a pull request. The checks fail if an image isn't live yet.

Emails released after the change use the new image. Everything sent before keeps the old one, which stays online.

## Colours and fonts

They come from Verdant (`packages/verdant`). The build syncs them into `src/tokens.generated.ts`, and the tests recompute every contrast ratio. If a Verdant change makes a pair fail WCAG AA, the email tests fail, and the fix belongs in Verdant or in `src/theme.ts`.

## Components

Each lives in its own file in [`src/components/`](../src/components/).

- **To change one**, edit its file. It changes in every email that uses it, so check the whole gallery.
- **To add one**, create the file, export it from `src/components/index.ts` and add it to `mdxComponents` so masters can use it. Then add a sample to `src/stylesheet.ts`. The tests fail until the sample exists, and the build writes it into [style-guide.md](./style-guide.md).

## Never

- Edit a template in Postmark's own editor. The next push overwrites it.
- Type an address, footer link or colour into a master.
- Add a coloured bar down the side of anything.
- Put a field in the banner `title`.
- Hand-edit anything in `dist/`, `docs/style-guide.md`, `docs/templates.md` or `packages/brand/assets.manifest.json`. All are generated.
- Overwrite or delete a file in the asset library.

# Maintaining the emails

Every change starts as a pull request in this repo. Nothing is edited in Postmark.

## Releasing

| Step | What happens |
|---|---|
| Pull request | Build and tests run; the gallery is attached to the run. Review the rendered emails there. |
| Merge to `main` | Every template is pushed to the Postmark **QA** server. |
| Tag `email-vX.Y.Z` | Brand images sync to R2, then every template is pushed to Postmark **production**. |

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

Email tags are separate from the design system's `v*` package tags, and neither triggers the other.

**Rolling back:** revert the commit on `main` and tag again. Postmark keeps no template history of its own; git is the history.

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
3. Delete the master here. Deleting a file does **not** delete the template in Postmark: engineering removes it from both servers by hand.

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

The masters are SVGs in [`packages/brand/assets/`](../../brand/assets/). The banner art is drawn by `packages/brand/scripts/render.mjs`, seeded so a re-render is identical.

1. Edit the SVG, or the generator.
2. Run `npm run render` in `packages/brand`, which writes the PNG or JPG email clients need.
3. Commit both.

Images reach R2 on the production tag. Their addresses never change, so **a new image shows up in every email already sent**, not just new ones. Treat an image change like a production change and look at it in the gallery first.

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
- Hand-edit anything in `dist/` or `docs/style-guide.md`. Both are generated.

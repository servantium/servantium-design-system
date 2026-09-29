# Hosting brand images: `assets.servantium.com`

**Status: planned, not set up.** This is the plan for the Cloudflare R2 bucket that serves Servantium's brand images to email and anything else that loads images by URL.

## Why a bucket at all

An email can't bundle images. It's HTML that downloads its images from the internet each time it's opened, so every image needs a public address that never changes. Because the address never changes, replacing the file updates every email ever sent, including last year's.

| Option | Why not |
|---|---|
| `servantium.com/brand/` | Every response carries `Cross-Origin-Resource-Policy: same-site`, which tells browser engines (Apple Mail among them) to refuse the image anywhere else. It also ties brand images to website deploys. |
| Firebase Storage | That's the app's storage, which holds customer files. Keeping public brand images apart keeps the rule simple: this bucket never holds customer data. It would also tie design changes to engineering's project. |
| **R2 on a custom domain** | Public by exact URL, cached by Cloudflare, no egress fees, and it lives beside the servantium.com zone we already run. |

## The bucket

| Setting | Value | Why |
|---|---|---|
| Name | `servantium-assets` | One bucket for public brand files |
| Account | Servantium's Cloudflare account | A custom domain has to be in the same account as the `servantium.com` zone |
| Location | Automatic | Cloudflare's cache serves most requests anyway |
| Storage class | Standard | Infrequent Access charges for every read, and these are read constantly |
| Public access | Custom domain `assets.servantium.com` only | |
| `r2.dev` URL | Off | It's rate-limited and not meant for production |
| Listing | None | Public access serves a file by its exact address; nobody can list the bucket |
| CORS | None | Images in email don't need it |
| Versioning | Not used | Git is the history: every image's master is committed in this package |

## What goes in it

The `brand/` folder mirrors [`packages/brand/assets/`](../assets/), raster files only (email clients can't show SVG):

```
servantium-assets/
└── brand/
    ├── logo/
    │   ├── servantium-logo.png          on light backgrounds
    │   └── servantium-logo-white.png    on dark: the email banner
    ├── email/
    │   ├── header-standard.jpg          the banner art
    │   ├── header-hero.jpg              taller banner art, for when the mascot returns
    │   └── footer-bar.jpg               the bookend strip under every email
    ├── social/
    │   └── linkedin.png                 the footer icon
    └── astro/
        └── astro-<pose>.png             five mascot poses (unused while the mascot is off)
```

That's 11 files and about 210 KB. An address is `https://assets.servantium.com/brand/` plus the path, for example `https://assets.servantium.com/brand/email/footer-bar.jpg`.

### Rules

- **Public brand files only.** Never customer data, attachments, uploads, generated documents, or anything with a person's name or address in it.
- **Images only.** PNG and JPG (GIF if we ever need one). No HTML, scripts or SVG.
- **Addresses are permanent.** Never delete or rename anything under `brand/`: sent emails point at it. To change an image, upload over the same address. To retire one, leave it where it is.
- **The path is the source path.** `packages/brand/assets/email/footer-bar.jpg` is served at `brand/email/footer-bar.jpg`. Lower case, words joined by hyphens.
- **Only the workflow uploads**, on a production release. The one exception is the first seed during setup.

### Reserved for later: `content/`

When an email first needs an image of its own (a screenshot in a month's release notes, say), it goes under a dated path that's never overwritten:

```
content/release-notes/2026-10/secure-search.png
```

These can cache for a year (`public, max-age=31536000, immutable`), because they never change. Nothing uses this yet; build it with the first email that needs it.

## Headers

| Header | Value | Set by |
|---|---|---|
| `Content-Type` | `image/png` or `image/jpeg` | the upload (`--content-type`) |
| `Cache-Control` | `public, max-age=86400` | the upload (`--cache-control`) |
| `Cross-Origin-Resource-Policy` | absent, or `cross-origin`. **Never `same-site`.** | Check after setup. If one appears, a Response Header Transform Rule on `assets.servantium.com` sets `cross-origin`. |

A day's cache means a replaced image can take up to a day to show, unless the URL is purged in the Cloudflare dashboard. Gmail and Outlook also keep their own copies through their image proxies, which we don't control.

## Access

| Who | Can |
|---|---|
| Anyone | Read a file by its exact address |
| The workflow's production job | Write objects to this bucket only, with an R2 token scoped to `servantium-assets` (Object Read & Write). It's stored as `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` in the repo's `production` environment, which requires a reviewer. |
| People | The Cloudflare dashboard, as today |

The existing local wrangler token can't reach R2: listing buckets returned an authentication error on 2026-09-29. Setup needs the dashboard, or a new token.

## Cost

Within R2's free tier: 10 GB of storage, a million writes and ten million reads a month, and no egress fees. We store about 210 KB and write 11 files per release. Each opened email fetches four images, and Cloudflare's cache answers most of those without touching the bucket.

## Setting it up

Not done yet. It needs a go-ahead, because it creates public infrastructure.

1. **Create the bucket.** Cloudflare dashboard → R2 → Create bucket: `servantium-assets`, automatic location, Standard.
2. **Connect the domain.** Bucket → Settings → Custom Domains → `assets.servantium.com`. Cloudflare adds the DNS record and the certificate. Leave the `r2.dev` URL disabled.
3. **Seed it once.** Build the email package, then upload `packages/verdant-email/dist/assets/**` to `brand/` with the content types and cache header above.
4. **Check it.** For each file, `curl -sI https://assets.servantium.com/brand/logo/servantium-logo-white.png` should return `200`, the right `content-type` and `cache-control`, and no `cross-origin-resource-policy: same-site`.
5. **Make the upload token.** R2 → Manage API tokens → Object Read & Write, limited to `servantium-assets`. Engineering adds it to the repo's `production` environment. On the first production run, confirm wrangler accepts a bucket-scoped token. If it doesn't, switch the sync step to R2's S3 API using the same token's access keys.
6. **Point the defaults at it.** Set `DEFAULT_ASSET_BASE` in [`src/index.ts`](../src/index.ts) to `https://assets.servantium.com/brand`, so every consumer, not just email, uses the hosted files.

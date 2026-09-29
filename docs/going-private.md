# Making this repo private

**Status: a plan, not started.** Nothing needs to change while the repo is public. This is what would have to happen first if it ever goes private, and why the change is worth making anyway.

## What would break today

The website and the help center don't install the design system as packages. Their builds clone this repo anonymously, check out the version in their `.design-system-ref` file, and install Verdant and Grove from the clone with `file:` paths:

```yaml
# website and servantium-help: .github/workflows/build.yml (their Cloudflare Pages builds do the same)
git clone https://github.com/servantium/servantium-design-system.git vendor/design-system
```

An anonymous clone only works on a public repo. Make it private and both sites stop building, in GitHub Actions and in Cloudflare Pages.

Nothing else depends on the repo being public:

| Thing | If private |
|---|---|
| `assets.servantium.com` | Unaffected. It's served from R2, not from GitHub. |
| Email releases | Downloading one needs a GitHub login: `gh release download` inside the org, or a token in engineering's pipeline. |
| This repo's workflows | Keep working. Private repos use Actions minutes; the Team plan includes 3,000 a month. |
| Deployment environments with required reviewers | Private repos need GitHub Enterprise for required reviewers. No workflow here uses one today. |

## The better way to build it

Consume the design system as versioned packages from the registry it already publishes to, rather than cloning git.

`publish.yml` already publishes `@servantium/verdant` and `@servantium/grove` to GitHub Packages on every `v*` tag. The sites just don't install from there yet. Switching them over fixes the private-repo problem, and it's a better setup regardless:

- **Real versions.** `"@servantium/grove": "^0.6.0"` in `package.json` replaces a git ref in a side file, and npm resolves it.
- **Update pull requests for free.** Dependabot or Renovate opens a pull request when a new version is published. That replaces the dispatch workflow that's currently disabled.
- **No clone at build time.** Builds get faster and more cacheable, and never depend on GitHub's git endpoint.

## Steps

1. **Here.**
   - Point `publish.yml` at the per-package tags the repo now uses (`grove@*`, `verdant@*`). It runs on any tag starting with `v`, which catches `verdant@…` but not `grove@…`, so the last publish was at `verdant@0.5.0` in April 2026.
   - Publish every package a site uses: add `@servantium/brand` to `publish.yml` if the sites start importing it.
   - Give each package a `publishConfig` for `npm.pkg.github.com`.
   - In each package's settings on GitHub, grant the `website` and `servantium-help` repositories read access, so their `GITHUB_TOKEN` can install it.
2. **In each site's repo.**
   - Add an `.npmrc`:
     ```
     @servantium:registry=https://npm.pkg.github.com
     //npm.pkg.github.com/:_authToken=${NODE_AUTH_TOKEN}
     ```
   - Replace the `file:./vendor/design-system/...` dependencies with versions.
   - Delete the clone step and `.design-system-ref`.
   - In GitHub Actions, set `NODE_AUTH_TOKEN` from `GITHUB_TOKEN`, with `packages: read`.
3. **In Cloudflare Pages.** Give each site's build a `NODE_AUTH_TOKEN` that can read packages: a fine-grained token or a GitHub App installation token, stored as an encrypted build variable.
4. **Updates.** Turn on Dependabot for npm in each site, scoped to `@servantium/*`.
5. **Then flip the repo to private** and confirm both sites build.

Steps 1 to 4 can happen while the repo is still public, one site at a time. Only step 5 is the switch.

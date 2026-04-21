# @servantium/verdant

Design tokens for the Servantium product and marketing surfaces.

## Install

```bash
npm install @servantium/verdant
```

## Usage

Import once at your app root:

```js
import '@servantium/verdant/tokens.css';
import '@servantium/verdant/base.css';  // optional
```

Then reference tokens anywhere:

```css
.my-button {
  background: var(--color-green);
  padding: var(--v-space-sm) var(--v-space-md);
  font-family: var(--font-body);
}
```

## Tokens

See [`tokens.css`](./tokens.css) for the full list. Primary groups:

- **Colors:** brand greens, inks, accents (coral/amber/slate-blue/deep-teal)
- **Typography:** `--font-display` (Playfair Display), `--font-body` (Source Sans 3)
- **Spacing:** `--v-space-xs` through `--v-space-3xl`
- **Easing:** `--ease-out`, `--ease-spring`, `--ease-bounce`

## Tailwind v4 consumers

Tokens are defined inside an `@theme` block, so Tailwind v4 picks them up automatically. Use `bg-green`, `text-ink`, `font-display` directly.

# Legacy images

Archived 2026-05-27 during the v1.0 visual refresh.

## v1.0 hero and architecture refresh

Three originals (`hero.png`, `architecture.png`, `before-after.png`) told the v0.x "push markdown into Google Docs" story. v1.0 expanded scope to the full ten-service Workspace surface plus fourteen named workflows, so the visual story was redone from scratch using a StoryBrand structure. The new images live one level up in `docs/images/`.

Files in this folder -

- `hero.png` - original v0.x hero (SCRIBE wordmark + glowing orb shooting markdown chars into a Doc icon)

- `hero-v1.png` - first v1.0 hero generation. Operator was standing beside the laptop rather than actually using it, and the service-icon constellation duplicated several services. Superseded same-day by the second-pass hero now in `docs/images/hero.png`.

- `architecture.png` - original v0.x architecture diagram. Showed three layers but with stale `/scribe-auth-init` slash command syntax (since corrected to `/scribe:auth-init`) and only four of the ten Workspace service icons (since expanded to all ten).

- `before-after.png` - generic cartoon "stressed vs calm" composition. Replaced by `the-problem.png` (one half) and `the-success.png` (the other half), both reshot as photorealistic editorial pieces.

## Brand mark redesign - feather replaces orb-and-hashtag

The original Scribe brand mark was a warm orange orb containing a white hashtag glyph. The hashtag referenced markdown (the v0.x core capability of pushing markdown into Google Docs). v1.0 expanded the plugin to orchestrate ten Workspace services through fourteen named workflows, making the hashtag-as-markdown association too narrow.

The new mark is a bold orange feather silhouette on the same deep navy background, with a thin electric-blue rim-highlight along its left edge and a small white-hot dot-trail in the lower-right suggesting freshly-dropped ink from the quill tip. The feather is the universal historical scribe symbol - it speaks directly to the plugin's name without needing the wordmark beside it. It is also significantly more distinctive at favicon size than the previous orb design, which read as a featureless orange disc at 32px.

The brand mark redesign considered seven alternative directions (constellation inside the orb, S inside the orb, dissolving quill inside the orb, S sweep without orb, hub-and-satellites, S portal, person silhouette) plus seven iterations on the two finalists (the orbed feather and a quill-S hybrid). The feather without the orb won the size-test comparison decisively - both finalists worked at 1024px but only the feather survived 32px with full distinctiveness.

Files in `icon-old-2026-05/` -

- `icon-1024.png` - original master at 1024 by 1024

- `icon-512.png`, `icon-256.png`, `icon-128.png`, `icon-64.png`, `icon-32.png` - the auto-generated variants from the original master

- `icon.png` - marketplace alias (was a copy of `icon-256.png`)

The new icon family was generated from a fresh `icon-1024.png` (the feather) via `make icons`. The same filenames now contain the new feather mark at each resolution.

## Disposal note

Kept here for reference and so existing forks or in-flight branches can still resolve historical image links if needed. Safe to delete once nothing external still links to these paths.

---
name: bayside-saas-redesign
description: Redesign a Vue 3 app's UI into a polished modern SaaS interface with a fixed vertical sidebar on the left (replacing the top nav bar), a consistent spacing scale, and a distinct 1990s "Saved by the Bell" (Bayside High) visual identity. Use this skill whenever the user asks to restyle, reskin, modernize, or redesign a Vue app's look and feel, move navigation from a top bar to a left sidebar, add a SaaS dashboard shell, apply a retro/90s/Saved-by-the-Bell/Memphis theme, or make the UI "more polished and professional", even if they don't say "Saved by the Bell" or "sidebar" explicitly.
---

# Bayside SaaS Redesign

Turn a Vue 3 app into a modern SaaS shell (left sidebar + content area) whose personality is early-90s Bayside High: Memphis geometry, saturated teal/purple/pink/yellow accents, chunky offset shadows, and a Saturday-morning-sitcom title-card feel. The goal is "professional product with a wink", not a costume. Data-dense screens (tables, charts, forms) must stay readable, so the retro voice lives in the chrome (sidebar, headers, badges, buttons, dividers) and the content surfaces stay clean.

## Workflow

1. **Survey before touching anything.** Read the app shell (usually `App.vue`), the router, any filter/toolbar component, and skim two or three views. Note: where the top nav lives, how routes map to nav labels (including i18n keys), what global state the shell owns (modals, profile menu, language switcher), and which CSS is global versus scoped. Also read the project's CLAUDE.md files; they can impose rules (for example "no emojis", "delegate .vue edits to a subagent", a mandated palette). Project rules win over this skill's defaults, and where they conflict with the theme, adapt the theme (see "Constraints that beat the theme").
2. **Establish tokens first.** Create the design tokens (colors, spacing, radius, shadow, type) as CSS custom properties in the global stylesheet or the shell's unscoped `<style>`, using `references/design-tokens.md`. Everything later consumes tokens, which is what makes spacing consistent and lets the theme be tuned in one place.
3. **Build the shell.** Replace the top nav with a sidebar using `assets/Sidebar.template.vue` as a starting point. Keep every existing route, i18n key, and shell-owned feature (language switcher, profile menu, modals) working; move them, don't drop them.
4. **Restyle shared components.** Filter bars, modals, buttons, inputs, cards, badges, tables. Fix these before individual views, because views inherit them.
5. **Sweep the views.** Replace hard-coded colors, ad-hoc paddings, and one-off shadows with tokens. Don't rewrite view logic or templates beyond what the style change needs; this is a visual change, so data flow, computed properties, and API calls stay untouched.
6. **Recolor charts.** Sweeping `<style>` blocks misses colors written inline in templates or scripts, so charts keep their old blue/gray. Grep for hex colors and `fill=`/`stroke=` in the views and swap fills for tokens. Change only color values, never geometry, scales or labels. Keep series distinguishable (for example revenue in ink, cost in pink) and keep white bar labels on a dark enough fill (purple-700, not purple-500).
7. **Verify visually.** Start the dev server (look for project-local tools such as `.tools/` if `node` or `uv` aren't on PATH), load every route at desktop (1440px) and mobile (390px), and look at screenshots. Open the mobile drawer. Check the console for errors. Run the production build to catch template or style errors. Then run the overflow check below.

## Layout rules

- Sidebar: fixed, full height, 248px wide (72px collapsed icon-less rail is optional; skip unless asked). Brand block at top, nav in the middle, utilities (language switcher, profile) pinned at the bottom.
- Content: `margin-left` equals the sidebar width; a sticky page header strip can hold the filter bar. Max content width 1280px, centered within the remaining space.
- Under 900px the sidebar becomes an off-canvas drawer opened by a hamburger button in a slim top bar, with a scrim. Use `v-model`-style local state in the shell; close on route change.
- Spacing comes only from the 4px-based scale (`--space-1` to `--space-8`). Cards use `--space-5` padding, grids use `--space-5` gaps, sections are separated by `--space-6`. Mixing arbitrary values like 13px or 22px is the main thing that makes a UI look unpolished, so grep for stray pixel values at the end.
- Accessibility: nav is a `<nav aria-label="Primary">`, active link gets `aria-current="page"`, focus rings are visible (a thick offset outline suits the theme), and text on colored backgrounds meets 4.5:1 contrast. The bright accents are for fills, borders, and shadows; body text stays dark ink on light surfaces.

## Mobile overflow check (do not skip)

Fixed-width charts, `minmax(450px, 1fr)` grids, wide tables and fixed-width search boxes are what break phones, and screenshots can hide it because the page just scrolls sideways. At 390px, for every route, evaluate `document.documentElement.scrollWidth` and compare with `clientWidth`. If they differ, list elements whose `getBoundingClientRect().right` exceeds the viewport and that have no scrolling ancestor, then fix at the source:

- Wide tables: wrap in a container with `overflow-x: auto`.
- Chart cards: `min-width: 0; overflow-x: auto` on mobile, which scrolls the chart without touching its geometry.
- Grids: `minmax(min(450px, 100%), 1fr)` so one column fits.
- Header rows with a search box: allow `flex-wrap` and drop the box's `min-width`.
- The sticky filter bar eats a third of a phone screen, so make it `position: static` under 900px.
- Drawer: the mobile top bar sits above the drawer so the hamburger stays reachable, therefore give the drawer `padding-top: calc(var(--topbar-height) + var(--space-4))` or the brand block hides under the bar.

## Intensity tiers

Default is the baseline described below. If the user asks to turn it up ("more rad", "more 90s", "punchier"), step up about 20% rather than rewriting: more saturated accents (teal #00d4bd, purple #a15bff, pink #ff3d9a, yellow #ffd60a; verify ink text stays at 4.5:1 or better), 5px shadows with a two-color double shadow on the active nav item and primary buttons only, a pink zigzag plus slanted teal block under every page title, a top stripe on cards cycling teal/purple/pink/yellow with `:nth-child(4n+x)`, extra Memphis shapes and a faint diagonal texture in the sidebar, a hover slide with a colored bar on nav items, and a `prefers-reduced-motion` guard on all added motion. If the user asks to tone it down, remove the stripes, double shadows and texture first. Re-run the overflow check after any turn-up, since stripes, shadows and margins can clip.

## The Saved by the Bell vibe (how to do it tastefully)

Lean on these motifs, a few per screen rather than all at once:

- **Bayside palette**: deep ink navy for text and the sidebar, a teal/aqua as the primary action color, with purple, hot pink, and sunny yellow as accents. Warm off-white page background so cards pop.
- **Memphis confetti**: squiggles, dots, triangles, and zigzags built from CSS (gradients, `clip-path`, inline SVG). Use them in the sidebar brand block, empty states, and as a thin zigzag divider under page headers. Keep them low-density and never behind data.
- **Chunky offset shadows**: hard 4px 4px 0 shadows in ink on cards, buttons, and active nav items instead of soft blur. Buttons "press" on hover/active by shifting the shadow away. This is the single most recognizable move and costs almost nothing.
- **Title-card typography**: headings in a bold geometric or rounded display face (see tokens), uppercase small labels with letter-spacing, body in a clean sans. Load fonts from Google Fonts only if the project allows external requests; otherwise use the system fallbacks in the tokens.
- **Brand block as a title card**: name the product area like a show logo, with a slanted color-block behind it. Pull the product name from the existing i18n/nav strings rather than inventing one.
- **Copy stays untouched.** No catchphrases, character names, or show logos. The reference is a visual mood from the era, not the show's IP, and changing UI text risks breaking i18n and tests.

## Constraints that beat the theme

- **No emojis in UI** if the project says so (many do). Build icons from inline SVG or CSS shapes. A small set of 20x20 stroke icons in `assets/Sidebar.template.vue` covers typical nav entries.
- **Project palette rules**: if the project mandates a base palette (e.g. slate/gray), keep that as the structural neutral for text, borders, and surfaces, and apply the Bayside colors as accents and status colors only. Status semantics (green/blue/yellow/red) must remain recognizable, so keep success=green, warning=yellow, danger=red even if the brand teal is nearby.
- **Charts**: recolor via tokens but don't change geometry, scales, or labels.
- **Delegation rules**: if the project requires `.vue` changes to go through a specific subagent (this repo's CLAUDE.md does, for `vue-expert`), brief that subagent with the survey findings, the token file, and the sidebar template rather than editing the files yourself.
- **Scoped styles**: don't fight them. Prefer changing tokens and shared components; when a view has a hard-coded color, swap it for the token in place.

## Output

When finished, report: files changed, the token file location, how to tune the theme (which variables), screenshots checked (routes and widths), and anything intentionally left alone. Mention any view you couldn't verify.

## Reference files

- `references/design-tokens.md`: the palette, spacing scale, type, shadow, and Memphis snippets. Read this at step 2.
- `assets/Sidebar.template.vue`: sidebar + mobile drawer starting point with inline SVG icons. Adapt routes, labels, and slots to the app; don't paste it unchanged.

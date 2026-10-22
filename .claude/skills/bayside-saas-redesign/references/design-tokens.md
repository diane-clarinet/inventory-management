# Design tokens

Drop these into the global stylesheet (or the shell's unscoped `<style>`). Tune values here, not in components.

## Table of contents
- Color
- Spacing, radius, shadow
- Typography
- Component recipes
- Memphis snippets

## Color

```css
:root {
  /* Structure (neutral) */
  --ink-900: #0f172a;      /* text, sidebar background */
  --ink-700: #334155;
  --ink-500: #64748b;      /* secondary text */
  --ink-200: #e2e8f0;      /* borders */
  --paper: #fffaf0;        /* page background, warm off-white */
  --surface: #ffffff;      /* cards */

  /* Bayside accents */
  --teal-500: #14b8a6;     /* primary action */
  --teal-600: #0d9488;
  --purple-500: #8b5cf6;
  --pink-500: #ec4899;
  --yellow-400: #facc15;

  /* Status (keep semantics intact) */
  --success: #16a34a;
  --info: #2563eb;
  --warning: #eab308;
  --danger: #dc2626;
}

@media (prefers-color-scheme: dark) { /* optional: only if the app already supports dark mode */ }
```

Text on `--teal-500` and `--yellow-400` fills should be `--ink-900`. White text works on `--ink-900`, `--purple-500` (large text only), `--teal-600`, and `--danger`.

## Spacing, radius, shadow

```css
:root {
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
  --space-5: 24px; --space-6: 32px; --space-7: 48px; --space-8: 64px;

  --radius-sm: 6px; --radius-md: 10px; --radius-lg: 16px;

  --shadow-pop: 4px 4px 0 var(--ink-900);        /* cards, buttons */
  --shadow-pop-sm: 2px 2px 0 var(--ink-900);     /* pressed state, small chips */
  --border-pop: 2px solid var(--ink-900);

  --sidebar-width: 248px;
  --focus-ring: 3px solid var(--purple-500);
}
```

## Typography

```css
:root {
  --font-display: "Poppins", "Avenir Next", "Trebuchet MS", system-ui, sans-serif;
  --font-body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --text-xs: 12px; --text-sm: 14px; --text-md: 16px; --text-lg: 20px; --text-xl: 28px;
}
h1, h2, h3 { font-family: var(--font-display); font-weight: 800; letter-spacing: -0.01em; }
.eyebrow { font-size: var(--text-xs); text-transform: uppercase; letter-spacing: 0.12em; font-weight: 700; color: var(--ink-500); }
```

Fonts are optional; the fallbacks are chosen to look right without any network request.

## Component recipes

```css
.card {
  background: var(--surface); border: var(--border-pop); border-radius: var(--radius-md);
  box-shadow: var(--shadow-pop); padding: var(--space-5);
}
.btn {
  background: var(--teal-500); color: var(--ink-900); font-weight: 700;
  border: var(--border-pop); border-radius: var(--radius-sm); padding: var(--space-2) var(--space-4);
  box-shadow: var(--shadow-pop-sm); transition: transform .08s, box-shadow .08s; cursor: pointer;
}
.btn:hover  { transform: translate(-1px, -1px); box-shadow: var(--shadow-pop); }
.btn:active { transform: translate(2px, 2px);   box-shadow: 0 0 0 var(--ink-900); }
:focus-visible { outline: var(--focus-ring); outline-offset: 2px; }
.badge { font-size: var(--text-xs); font-weight: 700; padding: 2px var(--space-2); border: var(--border-pop); border-radius: 999px; }
```

Tables: no pop shadow on rows. Use a 2px ink header underline, zebra with `--paper`, and `--space-3` cell padding.

## Memphis snippets

Zigzag divider (under page headers):

```css
.zigzag {
  height: 10px;
  background:
    linear-gradient(135deg, var(--pink-500) 25%, transparent 25%) -10px 0,
    linear-gradient(225deg, var(--pink-500) 25%, transparent 25%) -10px 0;
  background-size: 20px 20px;
}
```

Confetti dots (sidebar brand block):

```css
.confetti {
  background-image:
    radial-gradient(var(--yellow-400) 3px, transparent 3.5px),
    radial-gradient(var(--pink-500) 2px, transparent 2.5px);
  background-size: 28px 28px, 44px 44px;
  background-position: 0 0, 14px 18px;
}
```

Color-block slash behind the brand name: a `::before` with `transform: skewX(-12deg)` and `background: var(--teal-500)`.

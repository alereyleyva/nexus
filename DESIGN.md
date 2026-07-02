---
version: alpha
name: Acme
description: Visual identity for Acme — powerful, ethical software. Calm ocean blues, soft teals, and a single confident green.
colors:
  # Core
  primary: "#0C4A6E"          # brand-blue — deep ocean ink
  secondary: "#006591"        # brand-lightblue — wordmark, links, accents
  tertiary: "#57BC90"         # brand-green — primary call-to-action
  accent: "#F6E05E"           # warm yellow — secondary highlight
  # Brand teals / greens
  teal: "#7DBFBB"             # brand-darkgreen — section covers, brand panels
  teal-soft: "#91CAC4"        # brand-gray — muted teal
  green-deep: "#31A07F"       # brand-mutedgreen — logo gradient terminus
  motif: "#90C9C5"            # ambient pebble decoration tint
  # Surfaces
  background: "#EBF5F6"       # brand-lightgray — default page background
  surface: "#FFFFFF"          # card surface
  surface-muted: "#F8FAFC"    # brand-slate — partner pills, insets
  surface-tint: "#DBEDED"     # brand-darkgray — dividers, tints
  surface-washed: "#ECF5F5"   # brand-washedwhite — padded blocks
  # Text
  text: "#334155"             # brand-blueslate — body copy
  text-muted: "#61657C"       # brand-mutedblue — captions, metadata
  text-subtle: "#595959"      # brand-muted — fine print
  # On-color (foregrounds)
  on-primary: "#FFFFFF"
  on-tertiary: "#FFFFFF"
  on-accent: "#4A5568"
  on-secondary: "#FFFFFF"
typography:
  display:
    fontFamily: Foco
    fontSize: 3.25rem
    fontWeight: 900
    lineHeight: 1
    letterSpacing: -0.03em
  h1:
    fontFamily: Inter
    fontSize: 3.75rem
    fontWeight: 800
    lineHeight: 1.02
    letterSpacing: -0.03em
  h2:
    fontFamily: Inter
    fontSize: 2.125rem
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: -0.02em
  h3:
    fontFamily: Inter
    fontSize: 1.5rem
    fontWeight: 600
    lineHeight: 1.3
  quote:
    fontFamily: Inter
    fontSize: 1.375rem
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: -0.01em
  body:
    fontFamily: Inter
    fontSize: 1.0625rem
    fontWeight: 400
    lineHeight: 1.55
  body-strong:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 700
    lineHeight: 1.4
  label-caps:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: 0.12em
  button:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 500
    lineHeight: 1.2
rounded:
  base: 4px
  md: 6px
  lg: 8px
  xl: 12px
  card: 16px
  pill: 20px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  section: 72px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 11px 24px
  button-primary-hover:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.on-primary}"
  button-cta:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-tertiary}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 11px 24px
  button-accent:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 11px 24px
  button-secondary:
    backgroundColor: "{colors.surface-tint}"
    textColor: "{colors.text}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 11px 24px
  nav-item:
    textColor: "{colors.text}"
    typography: "{typography.label-caps}"
    rounded: "{rounded.base}"
    padding: 8px 18px
  nav-item-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.base}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.card}"
    padding: 32px
  panel-brand:
    backgroundColor: "{colors.teal}"
    textColor: "{colors.primary}"
    rounded: "{rounded.card}"
    padding: 44px
  panel-dark:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.card}"
    padding: 44px
  pill:
    backgroundColor: "{colors.surface-muted}"
    rounded: "{rounded.pill}"
    padding: 16px
    height: 150px
    width: 300px
  stat-value:
    textColor: "{colors.primary}"
    typography: "{typography.h2}"
  stat-label:
    textColor: "{colors.secondary}"
    typography: "{typography.body}"
  chip:
    backgroundColor: "{colors.background}"
    textColor: "{colors.text}"
    typography: "{typography.body-strong}"
    rounded: "{rounded.xl}"
    padding: 14px 18px
---

## Overview

Acme builds custom, high-quality software. The identity has to read as **trustworthy,
calm and competent** — never loud. Think of a quiet engineering studio with a
conscience: precise, warm, and human.

The system is anchored by two deep blues and a family of soft teals, lifted by a
single confident green that carries every primary action. Backgrounds are tinted
toward a cool, pale teal-white rather than pure white, giving the whole product a
soft, low-glare, "matte" feel. The recurring visual signature is the **logomark's
interlocking-arrow motif**, echoed as ambient organic pebble shapes that drift
behind coloured section covers.

Design with restraint. Generous whitespace, large rounded surfaces, one accent
per view. When in doubt, remove rather than add.

## Colors

The palette is built from high-contrast blue ink, a teal-green mid-range, and warm
near-white surfaces.

- **Primary `#0C4A6E`** — Deep ocean blue. Headlines, primary buttons, dark panels,
  and the dominant ink colour. The most authoritative voice in the system.
- **Secondary `#006591`** — Lighter ocean blue. The wordmark, links, accent text,
  and the primary-button hover state.
- **Tertiary `#57BC90`** — The brand green. Reserved almost exclusively for primary
  calls-to-action and positive emphasis. Use it sparingly so it always reads as "go".
- **Accent `#F6E05E`** — Warm yellow. A rare secondary highlight; pairs with the
  slate ink `on-accent #4A5568`, never white.
- **Teal `#7DBFBB`** & **Teal-soft `#91CAC4`** — The brand's soft middle register.
  Full-bleed section covers, brand panels, and supporting surfaces.
- **Green-deep `#31A07F`** — The green terminus of the logomark gradient
  (`#006591 → #7CBFBB` primary, `#31A07F → #7CBFBB` secondary pass).
- **Motif `#90C9C5`** — One step lighter than the teal cover; used only for the
  ambient pebble decorations so they stay low-contrast.
- **Surfaces** — `background #EBF5F6` is the default page tint (cool, pale, never
  pure white). `surface #FFFFFF` for cards, `surface-muted #F8FAFC` for partner
  pills and insets, `surface-tint #DBEDED` for dividers, `surface-washed #ECF5F5`
  for padded blocks.
- **Text** — `text #334155` for body, `text-muted #61657C` for captions and
  metadata, `text-subtle #595959` for fine print. Headings use Primary.

Primary on white reads at ~10:1; white on Primary at ~10:1 — both comfortably pass
WCAG AA. The green CTA carries white text; the yellow accent carries slate ink.

## Typography

Two families do all the work.

- **Foco** — the brand display face, used for the **wordmark and key brand moments
  only**. Weight 900, tight tracking. It is a licensed face served from Acme's
  CDN; fall back to a humanist sans (`sans-serif`) where unavailable.
- **Inter** — the workhorse for every heading, paragraph, button and label. Ranges
  from 400 body to 800 hero weights.

Scale highlights: hero headlines set in Inter 800 at ~60px with -3% tracking;
section titles at ~34px/700; sub-heads at ~24px/600. Testimonials are set in
**italic Inter 500** — the one place italics appear. Body copy is 17px/400 at a
relaxed 1.55 line-height. Labels and eyebrows are uppercase Inter 700 at 12px with
wide +0.12em tracking.

Headings are always Primary blue (or white on dark). Body is `text`. Keep line
lengths generous and let headings breathe with negative letter-spacing.

## Layout

Content sits in a centred column capped around **1100px** with roomy 8% side
gutters. Vertical rhythm is driven by the spacing scale — `section: 72px` between
major bands, `xl: 40px` inside hero blocks, `lg: 24px` between cards, `md: 16px`
for component internals.

Cards and panels are arranged on responsive grids (`1fr` / two-column / auto-fill
minmax) with explicit `gap`, never bare margins. Full-width coloured **section
covers** alternate with white content bands to create rhythm; a cover typically
carries the teal background plus one or two ambient pebble shapes bleeding off the
edges. Stats and capability chips lay out in compact 2×2 or stacked grids.

## Elevation & Depth

Depth is soft and layered, never harsh. Four shadow steps, all low-opacity black:

- **sm** — `0 1px 3px rgba(0,0,0,.1), 0 1px 2px rgba(0,0,0,.06)` — default for cards
  and resting buttons.
- **md** — `0 4px 6px -1px rgba(0,0,0,.1), 0 2px 4px -1px rgba(0,0,0,.06)`.
- **lg** — `0 10px 15px -3px rgba(0,0,0,.1), 0 4px 6px -2px rgba(0,0,0,.05)`.
- **xl** — `0 20px 25px -5px rgba(0,0,0,.1), 0 10px 10px -5px rgba(0,0,0,.04)`.

Most of the UI lives at **sm**. Reserve higher steps for overlays and hover lift.
Buttons rise ~1px on hover over a 0.3s ease-in-out — the single signature
transition timing across the system.

## Shapes

Everything is rounded; nothing is sharp.

- **base 4px** — nav items, small chips.
- **md 6px** — buttons (the canonical Acme button radius).
- **lg 8px / xl 12px** — inner elements, capability chips, swatches.
- **card 16px** — content cards and coloured panels.
- **pill 20px** — partner-logo pills (fixed 300×150 on `surface-muted`).
- **full 9999px** — eyebrow badges and avatar/round elements.

The **signature motif** is the organic pebble: a rounded arc shape (one squared
corner, three heavily-rounded corners, e.g. `border-radius: 140px 140px 24px 140px`)
echoing the curves of the logomark. Pebbles appear in the `motif` tint behind
coloured covers, low-contrast and ambient — decoration, never content.

## Components

- **button-primary** — Primary-blue fill, white text, 6px radius, soft `sm` shadow,
  weight 500. Hover shifts to Secondary blue and lifts 1px. The default action
  across the site (e.g. "Book a call").
- **button-cta** — Green fill, white text. Reserved for the strongest positive
  action; never more than one per view.
- **button-accent** — Yellow fill with slate ink. A rare secondary highlight.
- **button-secondary** — `surface-tint` fill with `text` ink for low-emphasis
  actions. Sizes step down via padding: default `11px 24px`, medium `8px 16px`,
  small `6px 8px` at 0.75rem.
- **nav-item / nav-item-active** — Uppercase label-caps with a 4px hover wash; the
  active item carries the Primary fill.
- **card** — White, 16px radius, 32px padding, `sm` shadow. The universal container.
- **panel-brand / panel-dark** — Full-bleed teal or Primary-blue panels at 16px
  radius with ambient pebbles; used for testimonials and brand moments.
- **pill** — Fixed 300×150 partner-logo tile on `surface-muted` at 20px radius;
  logos scroll in an infinite marquee.
- **stat-value / stat-label** — Large Primary-blue number over a Secondary-blue
  caption; arranged in compact grids.
- **chip** — Capability tag: an icon tile plus bold label on a `background` wash at
  12px radius.

## Do's and Don'ts

**Do**
- Tint backgrounds toward `#EBF5F6` — soft, cool, low-glare. Avoid pure white fields.
- Keep the green for action only; one CTA per view.
- Use Foco strictly for the wordmark and brand flourishes; Inter for everything else.
- Lean on generous whitespace, large radii, and the `sm` shadow as defaults.
- Let pebble motifs stay faint and ambient behind coloured covers.

**Don't**
- Don't introduce new hues — the palette is deliberately narrow. No gradients beyond
  the logomark's own blue→teal→green.
- Don't set body copy in Foco, and don't use italics outside testimonials.
- Don't pile up shadows or use hard, square corners.
- Don't let the yellow accent touch white text, or the green stray into decoration.
- Don't crowd sections — rhythm comes from space, not density.

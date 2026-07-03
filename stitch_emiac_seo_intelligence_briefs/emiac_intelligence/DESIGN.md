---
name: EMIAC Intelligence
colors:
  surface: '#f9f9f9'
  surface-dim: '#dadada'
  surface-bright: '#f9f9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f3'
  surface-container: '#eeeeee'
  surface-container-high: '#e8e8e8'
  surface-container-highest: '#e2e2e2'
  on-surface: '#1b1b1b'
  on-surface-variant: '#3f4943'
  inverse-surface: '#303030'
  inverse-on-surface: '#f1f1f1'
  outline: '#6f7a72'
  outline-variant: '#bec9c1'
  surface-tint: '#F3F6F3'
  primary: '#004931'
  on-primary: '#ffffff'
  primary-container: '#006344'
  on-primary-container: '#8cdcb5'
  inverse-primary: '#86d7b0'
  secondary: '#5e5e5c'
  on-secondary: '#ffffff'
  secondary-container: '#e1dfdc'
  on-secondary-container: '#636360'
  tertiary: '#3c403e'
  on-tertiary: '#ffffff'
  tertiary-container: '#535755'
  on-tertiary-container: '#c9cdca'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#a2f3cb'
  primary-fixed-dim: '#86d7b0'
  on-primary-fixed: '#002114'
  on-primary-fixed-variant: '#005137'
  secondary-fixed: '#e4e2df'
  secondary-fixed-dim: '#c8c6c3'
  on-secondary-fixed: '#1b1c1a'
  on-secondary-fixed-variant: '#474745'
  tertiary-fixed: '#e0e3e0'
  tertiary-fixed-dim: '#c4c7c5'
  on-tertiary-fixed: '#181c1b'
  on-tertiary-fixed-variant: '#444846'
  background: '#f9f9f9'
  on-background: '#1b1b1b'
  surface-variant: '#e2e2e2'
  surface-paper: '#F6F4F1'
  brand-deep: '#004D35'
  white: '#FFFFFF'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: DM Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: DM Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: DM Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: DM Sans
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: DM Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1440px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
  section-gap: 80px
---

## Brand & Style

The design system is built on a "Strategic Precision" narrative, reflecting a high-end SEO and digital marketing agency that balances data-heavy intelligence with a bespoke, human-centric touch. It avoids generic SaaS tropes in favor of a sophisticated, editorial aesthetic that feels both authoritative and innovative.

The visual style is **Corporate / Modern** with a lean toward **Minimalism**. It utilizes high-quality typography, generous whitespace, and a restrained but impactful use of the signature "Forest Green" to guide the user's focus. The interface should feel like a premium consultancy report: clean, structured, and profoundly legible, ensuring that complex SEO data is presented with clarity and elegance.

## Colors

This color palette is anchored by the signature brand green, used purposefully for primary actions, branding elements, and key data highlights. To achieve a high-end agency feel, the system moves away from clinical grays, instead using "Surface Paper" (`#F6F4F1`) and "Surface Tint" (`#F3F6F3`) for backgrounds. This off-white, warm-neutral approach reduces eye strain and provides a sophisticated, tactile quality to the dashboard.

Pure Black (`#000000`) is reserved for high-contrast typography and iconography to ensure maximum readability. White is used sparingly as a "highlighter" for card surfaces or active input fields to create subtle depth against the off-white backgrounds.

## Typography

The typography strategy leverages two distinct geometric sans-serifs to create a professional hierarchy. 

**Plus Jakarta Sans** is used for headlines and display text. Its slightly wider apertures and modern construction convey innovation and friendliness, making large data titles feel accessible.

**DM Sans** is utilized for body copy and UI labels. It is chosen for its exceptional legibility at smaller sizes and its neutral, systematic character, which is essential for data-heavy SEO tables and reporting modules. 

Text should generally be set in Black or the "Brand Deep" green for secondary headings. Use "Label SM" in uppercase for metadata or technical categories to create a clear visual distinction from narrative content.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy for desktop dashboards to ensure data density remains manageable and consistent, while transitioning to a fluid model for mobile.

- **Desktop (1440px+):** A 12-column grid with 24px gutters and 40px outer margins. Content is housed in "intelligence modules" (cards) that align to the grid.
- **Tablet (768px - 1439px):** A 6-column grid with 20px gutters. Sidebars collapse into a compact icon rail or a hamburger menu.
- **Mobile (Under 768px):** A 2-column fluid grid. Vertical stacking is mandatory for data visualizations.

The spacing rhythm is based on an 8px baseline. Use generous "Section Gaps" (80px) between major dashboard blocks to maintain the "high-end agency" feel, preventing the interface from feeling cluttered or overwhelming.

## Elevation & Depth

This design system uses **Tonal Layers** and **Low-contrast outlines** rather than heavy shadows to convey depth. This approach maintains a modern, flat aesthetic that feels like high-quality print media.

- **Surface Level 0:** The main background (`#F6F4F1`).
- **Surface Level 1 (Modules/Cards):** White (`#FFFFFF`) surfaces with a very thin, 1px border in a slightly darker version of the "Surface Tint" (`#E0E5E0`).
- **Surface Level 2 (Popovers/Modals):** White surfaces with a soft, ambient shadow (10% opacity of the Brand Green) to indicate interactivity and focus.

Interactive elements should not "float" aggressively; they should feel seated within the grid, using subtle color shifts on hover rather than physical lifts.

## Shapes

The shape language is **Soft** and professional. A standard radius of 4px (`roundedness: 1`) is applied to buttons, input fields, and small UI components. This provides a hint of approachability without sacrificing the crisp, technical feel required for an SEO intelligence platform.

Larger containers and cards may use 8px or 12px radii to create a clearer distinction between the "infrastructure" of the site and the "content" of the modules. Data visualizations (bars in charts) should remain sharp or have minimal rounding to emphasize precision.

## Components

### Buttons
- **Primary:** Solid Forest Green (`#006344`) with white text. 4px border radius.
- **Secondary:** Transparent background with a 1px Forest Green border and Green text.
- **Ghost:** No border, text-only in Green or Black, used for low-priority actions.

### Input Fields
Inputs should use a White background with a 1px border in a neutral gray. Focus states should switch the border to Forest Green with a subtle 2px outer glow in a transparent version of the same green.

### Cards & Modules
The core of the dashboard. Use a White background, Soft (1px) border, and ensure internal padding is consistent at 24px. Headers within cards should use "Headline SM" in Plus Jakarta Sans.

### Chips & Tags
Used for SEO status (e.g., "Crawled," "Error," "Optimized"). Use a "Surface Tint" (`#F3F6F3`) background with Forest Green text for positive states, and a muted red/amber for warnings, keeping the saturation low to match the brand's sophisticated palette.

### Lists & Data Tables
Tables are the primary data vehicle. Remove vertical borders; use only light horizontal dividers. The header row should have a subtle "Surface Tint" background with "Label SM" typography for titles.
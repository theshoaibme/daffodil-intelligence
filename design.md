---
name: Stitch Light System
colors:
  surface: '#fcf8f9'
  surface-dim: '#dcd9da'
  surface-bright: '#fcf8f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f4'
  surface-container: '#f0edee'
  surface-container-high: '#eae7e8'
  surface-container-highest: '#e5e2e3'
  on-surface: '#1c1b1c'
  on-surface-variant: '#424750'
  inverse-surface: '#313031'
  inverse-on-surface: '#f3f0f1'
  outline: '#737781'
  outline-variant: '#c3c6d1'
  surface-tint: '#315f9d'
  primary: '#315f9d'
  on-primary: '#ffffff'
  primary-container: '#8ab4f8'
  on-primary-container: '#0d4582'
  inverse-primary: '#a8c8ff'
  secondary: '#5c5f5e'
  on-secondary: '#ffffff'
  secondary-container: '#e1e3e1'
  on-secondary-container: '#626564'
  tertiary: '#5e5e64'
  on-tertiary: '#ffffff'
  tertiary-container: '#b3b2b9'
  on-tertiary-container: '#44454a'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a8c8ff'
  on-primary-fixed: '#001b3c'
  on-primary-fixed-variant: '#114784'
  secondary-fixed: '#e1e3e1'
  secondary-fixed-dim: '#c5c7c5'
  on-secondary-fixed: '#191c1b'
  on-secondary-fixed-variant: '#444746'
  tertiary-fixed: '#e3e2e9'
  tertiary-fixed-dim: '#c7c6cd'
  on-tertiary-fixed: '#1a1b20'
  on-tertiary-fixed-variant: '#46464c'
  background: '#fcf8f9'
  on-background: '#1c1b1c'
  surface-variant: '#e5e2e3'
typography:
  display-lg:
    fontFamily: Roboto Flex
    fontSize: 57px
    fontWeight: '400'
    lineHeight: 64px
    letterSpacing: -0.25px
  headline-lg:
    fontFamily: Roboto Flex
    fontSize: 32px
    fontWeight: '400'
    lineHeight: 40px
  headline-md:
    fontFamily: Roboto Flex
    fontSize: 28px
    fontWeight: '400'
    lineHeight: 36px
  title-lg:
    fontFamily: Roboto Flex
    fontSize: 22px
    fontWeight: '500'
    lineHeight: 28px
  title-md:
    fontFamily: Roboto Flex
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
    letterSpacing: 0.15px
  body-lg:
    fontFamily: Roboto Flex
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0.5px
  body-md:
    fontFamily: Roboto Flex
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0.25px
  label-lg:
    fontFamily: Roboto Flex
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.1px
  label-sm:
    fontFamily: Roboto Flex
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.5px
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 24px
---

## Brand & Style

This design system embodies the "Modern Google" aesthetic: a sophisticated, light-themed interface designed for high-stakes productivity and data-dense environments. The brand personality is clinical, reliable, and unobtrusive, prioritizing content and user workflow over decorative elements. 

The design style is **Corporate / Modern**, heavily influenced by Material Design 3 (Material You) but refined for desktop-class productivity. It leverages large border radii, subtle tonal shifts, and a restrained color palette to create a focused, high-clarity environment. The goal is to evoke a sense of "quiet intelligence"—where the UI recedes and the user's data becomes the primary focus.

## Colors

The color strategy centers on a clean, light foundation to maximize readability and provide a professional, open workspace.

- **Primary (#8ab4f8):** A soft, functional blue used for high-importance actions, active states, and focus indicators. 
- **Neutral/Background (#fdf8ff):** The core canvas color. It is a crisp, bright surface that ensures maximum contrast for text and data.
- **Surface/Secondary (#f1edf4):** Used for container backgrounds (cards, sidebars) to create subtle tonal separation from the main background.
- **Border (#c5c6d0):** A light-grey used for structural lines and separators, ensuring boundaries are visible without being distracting.
- **Typography:** Primary text uses a deep charcoal (#1b1b1f) for readability, while secondary metadata uses a muted grey (#44474e).

## Typography

This system utilizes **Roboto Flex** (the closest available systematic alternative to Google Sans) to provide a clean, highly legible typographic hierarchy. 

The scale follows a mathematical progression designed for information-dense applications. **Title** and **Label** roles utilize medium weights (500) to ensure clarity against light backgrounds, while **Body** text remains at a regular weight (400) for comfortable long-form reading. For mobile devices, Display and Headline sizes should be reduced by approximately 20% to maintain a balanced layout.

## Layout & Spacing

The layout employs a **Fluid Grid** system that optimizes for both high-density data and generous whitespace where appropriate.

- **Grid:** A 12-column grid is used for desktop (1440px+), transitioning to an 8-column grid for tablets and a 4-column grid for mobile.
- **Rhythm:** An 8px base unit (with a 4px sub-step) governs all margins, padding, and component heights. 
- **Density:** In productivity views (e.g., data tables), vertical padding is reduced to `8px` (sm). In editorial or dashboard views, padding is increased to `24px` (lg) to allow the content to "breathe."
- **Margins:** Page margins are fixed at `24px` on desktop and `16px` on mobile to ensure content doesn't bleed into the bezel.

## Elevation & Depth

Visual hierarchy is achieved through **Tonal Layering** and soft, natural shadows. In this light theme, elevation is represented by subtly darker surface colors or light shadows:

1.  **Level 0 (Base):** Background (#fdf8ff).
2.  **Level 1 (Cards/Sheets):** Surface (#f1edf4) with a subtle #c5c6d0 border.
3.  **Level 2 (Modals/Popovers):** Surface (#ffffff) with a soft, diffused ambient shadow (0px 4px 12px rgba(0,0,0,0.08)).

Interactive elements use a "halo" focus state: a 2px outer stroke of the Primary Blue (#8ab4f8) when focused or active. Avoid heavy blurs; use thin, 1px borders (#c5c6d0) to define boundaries between adjacent containers.

## Shapes

The shape language is defined by highly organic, **Pill-shaped** forms that soften the clinical nature of the productivity tool.

- **Standard Components:** Buttons, input fields, and small cards use a **16px** (rounded-sm) to **32px** (rounded-md) radius, creating a friendly, approachable aesthetic.
- **Large Containers:** Main content areas, large cards, and dialogs use a **48px** (rounded-lg) radius to achieve the signature Material You container look.
- **Full Rounded:** Chips and search bars use a **pill-shape** (9999px) to distinguish them from structural layout elements.

## Components

- **Buttons:** Primary buttons are filled with Primary Blue (#8ab4f8) and dark text (#131314). Secondary buttons use a tonal grey background (#f1edf4) or a simple outline (#c5c6d0) with Primary Blue text.
- **Input Fields:** Fields are outlined with #c5c6d0 and utilize a highly rounded (16px+) radius. Upon focus, the border transitions to #8ab4f8 with a 2px thickness. Labels sit above the field in `label-sm` style.
- **Chips:** Used for filtering and tags. They feature a 1px border (#c5c6d0) and a pill-shaped radius. When selected, they fill with a low-opacity Primary Blue (approx. 12% alpha).
- **Cards:** Background set to #f1edf4 with a 1px border of #c5c6d0. No shadow is required unless the card is draggable or floating.
- **Lists:** High-density list items should have a minimum height of 48px, utilizing `body-md` for primary text and `label-sm` for secondary metadata.
- **Checkboxes & Radios:** Use the Primary Blue (#8ab4f8) for the "selected" state. The "unselected" state is a simple #c5c6d0 outline.

---
name: Professional Dark Design System
colors:
  surface: '#141313'
  surface-dim: '#141313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353434'
  on-surface: '#e5e2e1'
  on-surface-variant: '#c4c7c8'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#8e9192'
  outline-variant: '#444748'
  surface-tint: '#c6c6c7'
  primary: '#ffffff'
  on-primary: '#2f3131'
  primary-container: '#e2e2e2'
  on-primary-container: '#636565'
  inverse-primary: '#5d5f5f'
  secondary: '#c4c7ca'
  on-secondary: '#2d3134'
  secondary-container: '#464a4d'
  on-secondary-container: '#b5b9bc'
  tertiary: '#ffffff'
  on-tertiary: '#313032'
  tertiary-container: '#e5e1e4'
  on-tertiary-container: '#656466'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e2e2e2'
  primary-fixed-dim: '#c6c6c7'
  on-primary-fixed: '#1a1c1c'
  on-primary-fixed-variant: '#454747'
  secondary-fixed: '#e0e3e6'
  secondary-fixed-dim: '#c4c7ca'
  on-secondary-fixed: '#181c1f'
  on-secondary-fixed-variant: '#43474a'
  tertiary-fixed: '#e5e1e4'
  tertiary-fixed-dim: '#c8c6c8'
  on-tertiary-fixed: '#1b1b1d'
  on-tertiary-fixed-variant: '#474649'
  background: '#141313'
  on-background: '#e5e2e1'
  surface-variant: '#353434'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
    letterSpacing: 0em
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0.01em
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: 0.01em
  label-caps:
    fontFamily: Hanken Grotesk
    fontSize: 11px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.08em
  mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.4'
    letterSpacing: 0em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  margin-desktop: 32px
  gutter-desktop: 24px
---

## Brand & Style

This design system is engineered for professional creative environments where the interface must recede to let the user's work take center stage. The aesthetic is a fusion of **High-Fidelity Minimalism** and **Technical Sophistication**, now softened by a pill-shaped geometry that bridges the gap between precision tools and modern approachable software.

The brand personality is authoritative yet quiet, characterized by expansive layouts and an obsessive focus on precision. It targets high-end designers and engineers who value clarity and "air" in their workspace. The emotional goal is to evoke a sense of limitless digital space, reducing cognitive load through ultra-refined details and a monochromatic, high-contrast palette. By avoiding heavy fills and opting for fine-line geometry with generous rounding, the system feels like a high-precision instrument that is ergonomic and fluid.

## Colors

The palette is strictly functional, utilizing a "void-like" base to minimize screen glare during long working sessions.

- **Base Layer:** The deepest charcoal (#0E0E10) is used for the primary application canvas.
- **Surface Layer:** Subtle shifts to #161618 designate floating panels or sidebars.
- **High Contrast:** Pure white (#FFFFFF) is reserved exclusively for typography and primary action icons, ensuring maximum legibility.
- **Slate Accents:** #3C4043 serves as the "workhorse" color for dividers, inactive states, and structural borders, providing definition without visual noise.

## Typography

This design system utilizes **Hanken Grotesk** for its geometric clarity and contemporary proportions, mirroring a clean, technical aesthetic.

Hierarchy is established through weight and tracking rather than color. Larger headlines use tight tracking and heavy weights for a tectonic feel, while labels and small UI text employ generous letter-spacing (0.08em) to maintain legibility against dark backgrounds. 

For technical data or coordinate inputs common in design tools, **JetBrains Mono** is introduced as a secondary utility font to provide a rhythmic, tabular layout for numbers.

## Layout & Spacing

The layout philosophy follows a **Fixed-Fluid Hybrid** model. Toolbars and property inspectors are fixed-width (typically 240px to 320px) to provide a stable ergonomic environment, while the central workspace is entirely fluid.

A strict **4px baseline grid** governs all internal spacing. To achieve the "expansive" feel, the design system mandates a "minimum breathing room" policy—panels should never feel cramped; the default internal padding for containers starts at `lg` (24px).

**Breakpoints:**
- **Desktop (1440px+):** 12-column grid, 32px margins.
- **Tablet (768px-1439px):** 8-column grid, 24px margins, sidebars collapse into drawers.
- **Mobile (<767px):** 4-column grid, 16px margins, focus on single-column utility.

## Elevation & Depth

This system rejects heavy fills for depth, relying instead on **Subtle Outlines** and **Soft Ambient Shadows**.

1.  **Level 0 (Canvas):** #0E0E10. No shadow.
2.  **Level 1 (Sidebars/Panels):** Separated by a 1px solid border (#3C4043) or a subtle shift to #161618. 
3.  **Level 2 (Dropdowns/Modals):** These use a sophisticated shadow: `0px 8px 32px rgba(0, 0, 0, 0.5)`. The border remains 1px but becomes slightly brighter (`rgba(255, 255, 255, 0.15)`) to simulate a rim-light effect.

Depth is also communicated through **Backdrop Blurs**. Any element floating over the main canvas should utilize a 12px-20px Gaussian blur to maintain the sense of layers without needing opaque backgrounds.

## Shapes

The shape language is "Fluid-Technical." Elements use a **16px (1rem)** base radius to appear modern, friendly, and ergonomic, moving away from strict rectangular forms toward pill-shaped containers.

- **Standard Buttons/Inputs:** 16px radius (Pill-shaped).
- **Cards/Main Panels:** 32px (2rem) radius.
- **Contextual Overlays:** 48px (3rem) radius.

This generous rounding creates a highly distinctive "capsule" aesthetic that softens the monochromatic high-contrast palette, ensuring the professional environment feels contemporary and accessible.

## Components

- **Buttons:** Primary buttons are #FFFFFF with #0E0E10 text, utilizing a full pill-shape (16px+ radius). Secondary buttons are ghost-style with 1px #3C4043 borders and the same rounding. Hover states should use a very subtle white opacity overlay (4%).
- **Inputs:** Dark backgrounds (#0E0E10) with 1px #3C4043 borders and a 16px radius. On focus, the border brightens to pure white. Labels should always be in the `label-caps` typography style, positioned above the field.
- **Chips:** Highly refined and fully pill-shaped with 1px borders. Use them for layer tags or status indicators. No background fill unless active.
- **Lists:** High-density with 1px dividers. Selection states use a subtle 4% white tint across the entire row, with rounded selection indicators (8px).
- **Cards:** Defined by 32px rounded corners and borders rather than shadows. Shadows are reserved for elements that "break" the layout (like tooltips or modals).
- **Property Inspectors:** Use tight vertical spacing for controls, utilizing the `mono-sm` font for all numeric input fields to ensure alignment of decimal points. Controls within inspectors retain the 16px rounding.

---
trigger: always_on
---

---
name: Stitch Light System
colors:
  surface: '#fbf8ff'
  surface-dim: '#dad9e6'
  surface-bright: '#fbf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f2ff'
  surface-container: '#eeecfa'
  surface-container-high: '#e8e7f5'
  surface-container-highest: '#e2e1ef'
  on-surface: '#1a1b24'
  on-surface-variant: '#444656'
  inverse-surface: '#2f303a'
  inverse-on-surface: '#f1effd'
  outline: '#757688'
  outline-variant: '#c5c5d9'
  surface-tint: '#2e46ef'
  primary: '#213be7'
  on-primary: '#ffffff'
  primary-container: '#4259ff'
  on-primary-container: '#f1f0ff'
  inverse-primary: '#bcc2ff'
  secondary: '#4e58a2'
  on-secondary: '#ffffff'
  secondary-container: '#a4aefe'
  on-secondary-container: '#343e87'
  tertiary: '#973500'
  on-tertiary: '#ffffff'
  tertiary-container: '#c04500'
  on-tertiary-container: '#ffeee8'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dfe0ff'
  primary-fixed-dim: '#bcc2ff'
  on-primary-fixed: '#000c62'
  on-primary-fixed-variant: '#0026d6'
  secondary-fixed: '#dfe0ff'
  secondary-fixed-dim: '#bcc2ff'
  on-secondary-fixed: '#030e5d'
  on-secondary-fixed-variant: '#364089'
  tertiary-fixed: '#ffdbce'
  tertiary-fixed-dim: '#ffb599'
  on-tertiary-fixed: '#370e00'
  on-tertiary-fixed-variant: '#7f2b00'
  background: '#fbf8ff'
  on-background: '#1a1b24'
  surface-variant: '#e2e1ef'
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

- **Primary (#4259ff):** A vibrant, functional blue used for high-importance actions, active states, and focus indicators. 
- **Secondary (#6771bd):** A muted indigo used for secondary actions and tonal accents, providing depth without competing with the primary blue.
- **Tertiary (#c04500):** A punchy burnt orange used sparingly for call-outs, status changes, or highlighting specific data points.
- **Neutral/Background (#fcf8f9):** The core canvas color. It is a crisp, bright surface that ensures maximum contrast for text and data.
- **Border (#767682):** A balanced grey used for structural lines and separators, ensuring boundaries are visible without being distracting.
- **Typography:** Primary text uses a deep charcoal for readability, while secondary metadata uses a muted grey (#767682).

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

1.  **Level 0 (Base):** Background (#fcf8f9).
2.  **Level 1 (Cards/Sheets):** Surface-container (#f0edee) with a subtle #767682 border.
3.  **Level 2 (Modals/Popovers):** Surface-container-lowest (#ffffff) with a soft, diffused ambient shadow (0px 4px 12px rgba(0,0,0,0.08)).

Interactive elements use a "halo" focus state: a 2px outer stroke of the Primary Blue (#4259ff) when focused or active. Avoid heavy blurs; use thin, 1px borders (#767682) to define boundaries between adjacent containers.

## Shapes

The shape language is defined by highly organic, **Pill-shaped** forms that soften the clinical nature of the productivity tool.

- **Standard Components:** Buttons, input fields, and small cards use a **16px** (rounded-sm) to **32px** (rounded-md) radius, creating a friendly, approachable aesthetic.
- **Large Containers:** Main content areas, large cards, and dialogs use a **48px** (rounded-lg) radius to achieve the signature Material You container look.
- **Full Rounded:** Chips and search bars use a **pill-shape** (9999px) to distinguish them from structural layout elements.

## Components

- **Buttons:** Primary buttons are filled with Primary Blue (#4259ff) and white text (#ffffff). Secondary buttons use a tonal indigo background (#6771bd) or a simple outline (#767682) with Primary Blue text.
- **Input Fields:** Fields are outlined with #767682 and utilize a highly rounded (16px+) radius. Upon focus, the border transitions to #4259ff with a 2px thickness. Labels sit above the field in `label-sm` style.
- **Chips:** Used for filtering and tags. They feature a 1px border (#767682) and a pill-shaped radius. When selected, they fill with a low-opacity Primary Blue.
- **Cards:** Background set to #f0edee with a 1px border of #767682. No shadow is required unless the card is draggable or floating.
- **Lists:** High-density list items should have a minimum height of 48px, utilizing `body-md` for primary text and `label-sm` for secondary metadata.
- **Checkboxes & Radios:** Use the Primary Blue (#4259ff) for the "selected" state. The "unselected" state is a simple #767682 outline.
```
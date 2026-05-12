---
name: Stitch Light System
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

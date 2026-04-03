# Design System Strategy: The Kinetic Edge

## 1. Overview & Creative North Star
This design system is built on the Creative North Star of **"The Kinetic Edge."** In the world of high-stakes poker and automated video production, precision isn't just a preference—it’s a requirement. This system moves away from the "template" look of standard SaaS platforms, instead favoring a high-end editorial aesthetic that feels like a premium broadcast suite.

We achieve this through **Intentional Asymmetry** and **Tonal Depth**. By breaking the rigid 12-column grid with overlapping glass layers and hyper-focused typography scales, we create a UI that feels "automated" yet "organic." The goal is to make the user feel like they are operating a sophisticated piece of machinery where every pixel serves a tactical purpose.

## 2. Colors
Our palette is rooted in the deep shadows of the poker room, punctuated by the electric energy of automated precision.

*   **Core Tones:**
    *   **Background:** `#121315` (The void. Everything emerges from here.)
    *   **Primary (Neon Green):** `#2ae500` (The pulse. Use for active states and "Success" automation.)
    *   **Secondary (Poker Red):** `#d20220` (The heat. Use for critical actions and high-stakes highlights.)
    *   **Surface Tiers:** Use `surface_container_lowest` (`#0d0e10`) through `surface_container_highest` (`#343537`) to define hierarchy.

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders to section off parts of the interface. Separation must be achieved through background color shifts. A `surface_container_low` section sitting on a `surface` background is the only way to define boundaries. This creates a seamless, sophisticated environment rather than a "boxed-in" feel.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. 
*   **Layer 1 (The Base):** `surface` (`#121315`).
*   **Layer 2 (The Deck):** `surface_container_low` (`#1b1c1e`).
*   **Layer 3 (The Card):** `surface_container` (`#1f2022`).
By nesting these, you create depth without visual clutter.

### The "Glass & Gradient" Rule
Floating elements (modals, dropdowns, floating toolbars) must utilize Glassmorphism. Use `surface_variant` (`#343537`) at 60% opacity with a `20px` backdrop-blur. For primary CTAs, apply a subtle linear gradient from `primary` (`#efffe3`) to `primary_container` (`#39ff14`) to provide a "glow" that feels powered by the software itself.

## 3. Typography
We utilize a dual-font system to balance "High-Tech" with "Editorial Clarity."

*   **Display & Headlines (Space Grotesk):** This is our "Precision" font. Use `display-lg` (3.5rem) and `headline-lg` (2rem) for data points and section titles. Its geometric nature reflects the automated aspect of the suite.
*   **Body & Titles (Manrope):** This is our "Human" font. It provides high readability for poker hand histories and tool descriptions. Use `body-lg` (1rem) for general content and `title-md` (1.125rem) for sub-headers.
*   **Labels (Inter):** For the smallest details—timestamps, frame counts, and micro-data—use `label-md` (0.75rem).

**Hierarchy Tip:** Contrast a `display-sm` headline in `Space Grotesk` with a `label-md` in `Inter` right next to it. This "Big-Small" contrast is a hallmark of high-end editorial design.

## 4. Elevation & Depth
Depth in this system is achieved through **Tonal Layering** rather than structural lines or heavy shadows.

*   **The Layering Principle:** Place a `surface_container_highest` element on top of a `surface_container_low` background to create an immediate, natural lift.
*   **Ambient Shadows:** If an element must float (like a video preview or a floating action menu), use a shadow with a 32px blur at 8% opacity, tinted with the `surface_tint` (`#2ae500`). This mimics the ambient light of a high-tech screen.
*   **The "Ghost Border" Fallback:** If accessibility requires a container boundary, use the `outline_variant` (`#3c4b35`) at **15% opacity**. This "Ghost Border" provides a hint of structure without breaking the "No-Line" rule.
*   **Backdrop Blurs:** Any element using `surface_container_highest` should implement a subtle backdrop-blur (4px to 8px) to soften the content beneath it, making the UI feel like a stack of semi-transparent glass panes.

## 5. Components

### Buttons
*   **Primary:** Background `primary_container` (`#39ff14`), Label `on_primary` (`#053900`). Use `md` (0.375rem) roundedness. 
*   **Secondary:** Glassmorphic. `surface_variant` at 40% opacity with a "Ghost Border."
*   **States:** On hover, increase the `surface_tint` glow. On active, scale the button down to 98% to simulate a tactile mechanical switch.

### Cards & Lists
*   **Rule:** Forbid divider lines. 
*   **Implementation:** Use `8` (1.75rem) or `10` (2.25rem) spacing from the scale to separate list items. For cards, use `surface_container_high` (`#292a2c`) with `xl` (0.75rem) corner radius.

### Input Fields
*   **Style:** Minimalist. Background is `surface_container_lowest`. No border, just a bottom-aligned `primary_fixed_dim` line (2px) that animates from the center outward when the field is focused.

### Specialized Component: The "Timeline Scrub"
*   For video editing, use `primary_fixed` (`#79ff5b`) for the playhead. Use `secondary` (`#ffb3ad`) to highlight "poker heat maps" or "all-in" moments on the timeline.

## 6. Do's and Don'ts

*   **DO:** Use intentional white space. Let the `surface` background breathe.
*   **DO:** Use the `20` (4.5rem) and `24` (5.5rem) spacing tokens for large section offsets to create an editorial feel.
*   **DON'T:** Use 100% opaque, high-contrast borders. It kills the "Kinetic Edge" aesthetic.
*   **DON'T:** Use generic grey shadows. Always tint your shadows with the primary or surface-tint color.
*   **DO:** Align data points (like pot odds or hand strength) using `Space Grotesk` in `headline-sm` to make them feel like a digital readout.
*   **DON'T:** Overuse the Poker Red (`secondary`). It is a high-alert color. Reserve it for "Bust" moments, errors, or "Delete" actions.

This system is about the tension between the dark, quiet surface and the vibrant, neon precision of the data. Keep it clean, keep it layered, and keep it sharp.
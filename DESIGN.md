# Bon Laundry Station — Service Ledger Interface

## Product expression

Bon Laundry is a live service operation. Its interface should feel like the front desk of a considered, well-run business: attentive, legible, and calm under pressure. It is not a generic analytics dashboard and it is not a marketing-led SaaS product.

The central visual object is the **service ledger**. A booking, queue place, machine assignment, payment, and order status are all records moving through one service system. That makes the next action, the assigned machine, and the current state more important than decorative containers or decorative data.

## Operating principles

1. Put the current service record and its next decision before supporting detail.
2. Treat records, timers, assignments, and checkout as the primary visual material.
3. Use warm paper, deep service ink, crisp rules, and one confident blue action color—not decorative dashboard styling.
4. Keep controls conventional and obvious. There are no decorative controls or movement for its own sake.
5. Treat dense operational data as first-class content: aligned columns, tabular numbers, predictable row actions, and accessible focus states.

## Foundations

| Token | Value | Use |
|---|---:|---|
| Service ink | `#132531` | Primary text and operations navigation |
| Service blue | `#0D6D9B` | Primary action and selected control |
| Ledger | `#F6F4EF` | Application background |
| Paper | `#FFFEFA` | Forms, tables, and intentional groups |
| Rule | `#D9D9D2` | Structural dividers and input boundaries |
| Ready | `#18785E` | Completed and available states |
| Attention | `#A86518` | Waiting, active wash, and review states |
| Error | `#B43B40` | Validation and failed states |

## Typography

- **Archivo** is the application face for headings, controls, and body copy. It is compact, legible, and does not create a marketing/editorial split inside an operational product.
- **Roboto Mono** is reserved for values that benefit from alignment: queue numbers, order IDs, prices, timers, and tabular numeric data.
- Page titles are 24–30px, section titles 18–20px, body copy 14–15px, labels 11–12px. Labels never substitute for meaningful titles.

## Components

- **Navigation:** deep service-ink navigation for staff/manager. The active item is a paper insert that reads like the current ledger tab. Customer navigation remains simple and content-led.
- **Buttons:** 5px radius; one service-blue primary button per decision area. Secondary actions use a bordered neutral style. No gradients or glow shadows.
- **Inputs:** white, 1px border, 6px radius; aqua focus ring. Validation messages describe both the issue and recovery.
- **Tables:** tinted header, compact 11px labels, 13px body, horizontal row dividers, tabular numeric values. Use rows rather than card grids for repeatable operational data.
- **Surfaces:** paper sheets and controlled work panels have 5–8px corners. Most page regions are flat and separated with whitespace or rules. Shadows are avoided.
- **Status:** status is always conveyed through text plus color, never color alone. Pills are small and reserved for a short state.
- **Empty/loading/error:** retain the existing live data hooks. Their visual treatment is concise, in-place, and never blocks related actions.

## Role-specific hierarchy

- **Customer:** the active order or queue state, then booking, availability, and appointment history.
- **Staff:** POS details, selected machine, amount and confirmation, then queue progression.
- **Manager:** one continuous operational readout, live activity and load risk, then configuration and audit tables.

## Responsive behavior

- The desktop operations sidebar becomes a simple overlay drawer on mobile.
- Tables retain their structure and scroll horizontally when needed; controls do not shrink below usable touch targets.
- Customer booking stacks into one explicit sequence: schedule, service, confirmation.
- Motion is limited to live-state feedback and is disabled under reduced-motion preferences.

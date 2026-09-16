# Design Notes

## Product name

**DR Review Workspace**
Descriptor: **Screening Support POC**

The name identifies the disease area and the human-review purpose without implying diagnosis, autonomy, or clinical clearance.

## Information architecture

The interface is divided by user role instead of exposing every technical feature in one dashboard.

| Area | Page | Primary question |
|---|---|---|
| Review workspace | Overview | What should I do next? |
| Review workspace | Screening | What is visible in this ROI, and what decision should I record? |
| Review workspace | Review queue | Which uncertain cases still need human resolution? |
| Model lab | Explainability | What image regions influenced this one model output? |
| Model lab | Model comparison | Which cases improved, regressed, or changed between two versions? |
| System | Integrations | How are the UI, Label Studio, bridge, and model API connected? |

## Nuxt UI design reference

The redesign follows the official Nuxt UI dashboard template patterns without copying its product content:

- persistent grouped sidebar;
- compact page navbar;
- low-contrast borders and neutral surfaces;
- master-detail review layout;
- segmented controls for alternate views;
- restrained badges and one dominant action per page;
- responsive mobile navigation.

The package remains plain HTML, CSS, and JavaScript so it can be opened offline and handed to stakeholders as a ZIP. A production Vue/Nuxt implementation can map these patterns directly to `UDashboardGroup`, `UDashboardSidebar`, `UDashboardPanel`, `UDashboardNavbar`, `UNavigationMenu`, `UTabs`, `UBadge`, `UButton`, `UModal`, and `UTable`.

## Explainability design

The explainability page is case-first rather than metric-first:

1. select a task;
2. compare original, attention, and ROI views;
3. inspect ranked relative evidence regions;
4. check agreement with the reviewer-selected ROI;
5. read the explicit interpretation boundary.

Attention is presented as model aggregation evidence. It is never labeled as a lesion mask or validated localization.

## Model comparison and error analysis

The model comparison page is designed around changed cases rather than a generic analytics dashboard:

1. select Model A, Model B, and an evaluation set;
2. separate improved, regressed, changed, and unchanged cases;
3. filter the case table;
4. inspect the exact prediction transition;
5. group repeated failures into reviewable clusters.

No real performance metric is displayed until a versioned evaluation set and live model outputs are connected.

## Visual system

- Public Sans for the primary interface and IBM Plex Mono for identifiers.
- Institutional brick red `#A73B24` as a restrained primary accent.
- White surfaces, zinc-toned borders, and minimal shadow.
- Lucide-compatible icons only.
- No university logo, gradient branding, glass cards, or decorative metric tiles.

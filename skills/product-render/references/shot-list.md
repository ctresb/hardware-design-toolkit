# Shot list

A product story needs a few images, each answering one question a buyer or investor has. Pick 3–6 from this
list using the brief. Every shot must pass `realism-checklist.md`.

| # | Shot | Question it answers | Recipe / view | Notes |
|---|---|---|---|---|
| 1 | **Hero** | What is it? | `dark-studio` or `hero-float`, `--view hero` | front 3/4, LED on if it has one; vertical 4K for mobile pages, horizontal for desktop |
| 2 | **In context** | Where does it live? | `tabletop-hdri`, `three-quarter` | on the desk or bench, next to the objects it is used with (keyboard, phone, plant) |
| 3 | **On the body / in the hand** | How big is it, and how is it worn? | real rigged hand or body scan + `dark-studio` | only with a convincing hand; otherwise use a scale object |
| 4 | **Dark, LED on** | What does it look like when it works? | `dark-studio`, `--emit` | the LED is subtle; the product shape is drawn by strips |
| 5 | **Exploded** | What is inside? Is it real engineering? | `dark-studio` or `white-seamless` | parts spread along the assembly axis in build order; same light as the hero |
| 6 | **Close-up of internals** | Is the board real? | `dark-studio`, `macro`, f/11–f/16 | shows solder fillets, markings, the battery label |
| 7 | **Colorway lineup** | What can I buy? | `white-seamless` or `dark-studio` | all colors at the same angle; one image or a sheet |
| 8 | **Detail** | What is the material or finish? | `tabletop-hdri`, macro | engraving, contacts, texture, cord |
| 9 | **Back / charging** | How does it charge? | `three-quarter-right` or `back` | the one shot where the back faces the camera |

## Layouts that work

- **Vertical triptych** (three 4K vertical images side by side), each telling one part:
  - left: the product on a desk (context);
  - center: dark studio, LED on (hero);
  - right: exploded (the inside).
  Use the same camera height and focal length in all three, so they read as a set.
- **Hero + 3 details:** one large image and three small ones (material, inside, in use).
- **Lineup strip:** colorways in a row, same light.

## Exploded view rules

- Move whole groups rigidly along the assembly axis, in assembly order. The gaps are larger between groups
  than inside a group.
- Keep each part's orientation. Do not rotate parts to "show them better", because the viewer then
  cannot see how they fit.
- Small parts (screws, magnets, contacts) stay near where they go.
- A vector exploded view for quotes is another deliverable, made by `technical-drawing`.

## Before the final batch

1. Render every shot at `--format preview`.
2. Put them on one contact sheet.
3. Show the sheet, and adjust angles and colorways once.
4. Render the finals in one batch, on a GPU.

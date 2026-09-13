# Slide-Out Pan Commode - Manufacturer Brief (Rev B, concept design - REAR slide-out)

## What it is
A standard folding aluminium bedside commode (1" tube frame, telescoping legs, round 440 mm PP seat/lid, padded backrest, armrests)
fitted with a **rear slide-out pan module**. The pan rides on two full-extension ball-bearing drawer
slides that run front-to-back under the seat, on angle rails clamped to the existing front and rear cross bars.
A caregiver standing **behind the chair** pulls the handle, the pan slides ~20" (508 mm) out the back
**while the user remains seated**, is lifted straight out
of its carrier by its two end grips, emptied, dropped back in and pushed home where a catch holds it.

## How it works (see Sheet 1 and renders)
1. Two 40x40x3 mm aluminium angle rails (SP-06, 508 mm long) run front-to-back under the seat at
   +/-200 mm from centre, each held by a rubber-lined tube clamp (SP-04) on the front and rear cross bar -
   four clamps total, no welding or drilling of the chair frame; the module is a retrofit kit.
2. A 20" (508 mm) full-extension slide bolts to the web of each rail. A carrier plate (SP-01, 375 mm wide x
   400 mm long) with down-turned side flanges is bolted to the moving members of both slides. It has a
   320 mm dia round cutout, concentric with the seat aperture, and a D-pull handle on its rear edge.
3. The round pan (SP-02, 310 mm rim dia) hangs by its 15 mm flange in the cutout, directly under the seat aperture. Its rim top
   sits 22 mm below the seat underside. Pan bottom is 276 mm above the floor - clears the lower side brace.
4. At full extension the pan is entirely behind the rear legs (110 mm clearance past the rear leg) so it
   lifts vertically out. The rear cross bar sits above the rails and the backrest pad is above the pan path,
   so nothing obstructs travel. A snap-on splash lid (SP-03) is fitted before carrying.
5. Padded backrest (SP-05, 460 x 200 x 45 mm foam/vinyl) straps to the FRONT face of the rear back-bar so a
   user leaning back contacts padding, never the tube.
6. A magnetic catch / spring detent holds the carrier in the closed position; bump stops at full travel.

## Key dimensions
| Item | mm | in |
|---|---|---|
| Overall width / depth | 585 x 455 | 23.0 x 17.9 |
| Seat height (nominal, adjustable) | 470 (420-570) | 18.5 (16.5-22.5) |
| Slide travel | 508 | 20.0 |
| Carrier plate, W x L (round cutout 320 dia) | 375 x 400 x 6 | 14.75 x 15.75 x 0.24 |
| Angle rails (2), 40x40x3, centre spacing | 508 long, 400 c/c | 20.0 long, 15.75 c/c |
| Pan overhang behind rear leg at full extension | 450 | 17.7 |
| Pan rim dia / flange O/A dia / base dia | 310 / 340 / 250 | 12.2 / 13.4 / 9.8 |
| Pan depth | 152 | 6.0 |
| Pan capacity (working / brim) | 6.7 L / 9.3 L | 7 qt / 9.8 qt |
| Design load | 136 kg seated, 15 kg in pan | 300 lb / 33 lb |

## Files
| File | Purpose |
|---|---|
| `commode_slide_pan_closed.step` / `.stl` | Full 3D assembly, pan closed (STEP opens in AutoCAD, SolidWorks, Fusion, FreeCAD) |
| `commode_slide_pan_extended.step` / `.stl` | Full 3D assembly, pan at full extension |
| `part_carrier.step/.stl`, `part_pan.step/.stl`, `part_slides.step/.stl`, `part_backrest.step/.stl` | Individual new parts |
| `sheet1_general_assembly.pdf/.dxf` | GA drawing: front, side, top views, overall dims, notes |
| `sheet2_carrier_plate.pdf/.dxf` | Carrier plate detail + section |
| `sheet3_pan.pdf/.dxf` | Pan detail + section, draft, fill line |
| `sheet4_bracket_bom.pdf/.dxf` | Clamp bracket detail + full Bill of Materials |
| `render_01..06.png` | Shaded renders for quoting / marketing |
| `model.py`, `drawings.py`, `render.py` | Parametric source (CadQuery) - change any dimension and regenerate |

## Questions for the manufacturer / decisions still open
- Material choice for carrier (HDPE vs 304 SS) and pan (moulded PP vs drawn SS) - tooling cost vs volume.
- Pan exits to the REAR (caregiver behind user) - no left/right handedness. Confirm the caregiver has
  ~18" of clear floor space behind the chair in the intended use setting (e.g. not pushed against a wall).
- Slide spec: confirm 100 lb/pair, corrosion-resistant (stainless or zinc + sealed bearings) and washable.
- Whether the base chair is bought-in (retrofit kit) or the manufacturer supplies the whole chair.
- Optional: splash lid that closes automatically as the pan slides out (hinged flap on carrier) - not in Rev A.

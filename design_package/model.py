"""Parametric model: folding commode chair with side-sliding removable pan.
Units: mm.  X = side-to-side (+X = caregiver / slide-out side), Y = front(-)/back(+), Z = up.
"""
import cadquery as cq

# ---------------- Parameters ----------------
TUBE_OD = 25.4        # 1" aluminum frame tube
TUBE_WALL = 1.5
LEG_X = 280.0         # leg centre half-width  (overall width ~ 585 mm / 23")
LEG_Y = 215.0         # leg centre half-depth  (overall depth ~ 455 mm / 18")
SEAT_H = 470.0        # seat top height (18.5", mid range of 16.5-22.5")
CROSSBAR_Z = 440.0    # front / rear cross bar centre height
ARM_Z = 700.0         # armrest tube centre height
BACK_Z = 640.0        # rear back-bar centre height
BRACE_Z = 180.0       # lower side brace centre height
INNER_LEG_OD = 22.0
INNER_LEG_LEN = 260.0
FOOT_H = 30.0

SEAT_W, SEAT_D, SEAT_T = 480.0, 420.0, 22.0   # legacy envelope
SEAT_DIA = 440.0                              # round seat
SEAT_HOLE_W, SEAT_HOLE_D = 300.0, 220.0
LID_T = 15.0
LID_ANGLE = 100.0
BACKPAD_W, BACKPAD_H, BACKPAD_T = 460.0, 200.0, 45.0   # padded backrest on FRONT face of back bar

SLIDE_LEN = 508.0     # 20" full-extension ball-bearing drawer slide
SLIDE_H = 45.0
SLIDE_T = 12.7        # thickness per slide (closed)
SLIDE_Z = 375.0       # slide bottom
TRAVEL = 508.0

CARRIER_X = 400.0
CARRIER_Y = 2 * (LEG_Y - TUBE_OD / 2 - SLIDE_T)  # fits between the slides  (~354)
CARRIER_T = 6.0
CARRIER_Z = SLIDE_Z + SLIDE_H                     # plate bottom sits on slide top (420)
CUTOUT_DIA = 320.0                                # round cutout in carrier
CUTOUT_X = CUTOUT_Y = CUTOUT_DIA

PAN_DIA = 310.0                                   # round pan, rim dia (fits through cutout, 5 mm/side)
PAN_BOT_DIA = 250.0
PAN_TOP_X = PAN_TOP_Y = PAN_DIA
PAN_BOT_X = PAN_BOT_Y = PAN_BOT_DIA
PAN_DEPTH = 150.0
PAN_FLANGE = 15.0                                 # flange OD 340 < carrier inner width 351
PAN_WALL = 2.5
HANDLE_W = 120.0

SEAT_Z = SEAT_H - SEAT_T                          # seat underside (448) -> 22 mm above carrier top


def tube(p1, p2, od=TUBE_OD):
    v = cq.Vector(*p2) - cq.Vector(*p1)
    L = v.Length
    return (cq.Workplane(cq.Plane(origin=p1, normal=v.normalized()))
            .circle(od / 2).extrude(L))


def rounded_box(x, y, z, r):
    return cq.Workplane("XY").box(x, y, z).edges("|Z").fillet(r)


def frame():
    parts = []
    for sx in (-1, 1):
        x = sx * LEG_X
        # inverted-U side frame: front leg -> armrest -> rear leg
        parts.append(tube((x, -LEG_Y, INNER_LEG_LEN), (x, -LEG_Y, ARM_Z)))
        parts.append(tube((x, LEG_Y, INNER_LEG_LEN), (x, LEG_Y, ARM_Z)))
        parts.append(tube((x, -LEG_Y, ARM_Z), (x, LEG_Y, ARM_Z)))
        # lower side brace
        parts.append(tube((x, -LEG_Y, BRACE_Z), (x, LEG_Y, BRACE_Z)))
        # telescoping inner legs + feet
        for y in (-LEG_Y, LEG_Y):
            parts.append(tube((x, y, FOOT_H), (x, y, INNER_LEG_LEN + 80), INNER_LEG_OD))
            parts.append(cq.Workplane("XY").workplane(offset=0).center(x, y)
                         .circle(20).extrude(FOOT_H))
        # armrest pad
        parts.append(cq.Workplane("XY").workplane(offset=ARM_Z + 5).center(x, 0)
                     .rect(50, 280).extrude(28).edges("|Z").fillet(20))
    # cross bars (front, rear, rear back-bar)
    for y in (-LEG_Y, LEG_Y):
        parts.append(tube((-LEG_X, y, CROSSBAR_Z), (LEG_X, y, CROSSBAR_Z)))
    parts.append(tube((-LEG_X, LEG_Y, BACK_Z), (LEG_X, LEG_Y, BACK_Z)))
    solid = parts[0]
    for p in parts[1:]:
        solid = solid.union(p)
    return solid


def seat():
    s = (cq.Workplane("XY").workplane(offset=SEAT_Z).circle(SEAT_DIA / 2).extrude(SEAT_T)
         .edges(">Z").fillet(8))
    hole = cq.Workplane("XY").ellipse(SEAT_HOLE_W / 2, SEAT_HOLE_D / 2).extrude(100).translate((0, 0, SEAT_Z - 10))
    return s.cut(hole)


def lid():
    d = SEAT_DIA - 20
    l = cq.Workplane("XY").circle(d / 2).extrude(LID_T).edges(">Z").fillet(6)
    # hinge along the rear edge: lid lies toward -Y, then swings up/back
    l = l.translate((0, -d / 2, 0))
    l = l.rotate((0, 0, 0), (1, 0, 0), -LID_ANGLE)
    return l.translate((0, SEAT_DIA / 2 - 10, SEAT_H))


def backrest():
    """Padded backrest strapped to the front face of the rear back-bar so the
    user's back contacts foam, never the tube.  Wraps 12 mm over the bar top/bottom."""
    pad = rounded_box(BACKPAD_W, BACKPAD_T, BACKPAD_H, 18)
    y = LEG_Y - TUBE_OD / 2 - BACKPAD_T / 2 + 6     # 6 mm of pad wraps the bar
    pad = pad.translate((0, y, BACK_Z))
    # rear shell wrapping around the bar
    shell = (cq.Workplane("XY").workplane(offset=BACK_Z - BACKPAD_H / 2)
             .center(0, LEG_Y).rect(BACKPAD_W - 40, TUBE_OD + 12).extrude(BACKPAD_H)
             .edges("|Z").fillet(10))
    return pad.union(shell)


def slide_pair(ext):
    """Two full-extension slides on front/rear cross bars; ext = drawer travel (0..TRAVEL)."""
    parts = []
    for sy in (-1, 1):
        y_in = sy * (LEG_Y - TUBE_OD / 2)           # inner face of cross bar tube
        # cabinet member (fixed)  - hugs the tube, thickness SLIDE_T/2
        yc = y_in - sy * SLIDE_T / 4
        parts.append(cq.Workplane("XY").box(SLIDE_LEN, SLIDE_T / 2, SLIDE_H)
                     .translate((0, yc, SLIDE_Z + SLIDE_H / 2)))
        # drawer member (moving)
        yd = y_in - sy * 3 * SLIDE_T / 4
        parts.append(cq.Workplane("XY").box(SLIDE_LEN, SLIDE_T / 2, SLIDE_H - 6)
                     .translate((ext, yd, SLIDE_Z + SLIDE_H / 2)))
        # tube clamp brackets (3 per bar)
        for x in (-180, 0, 180):
            clamp = (cq.Workplane("YZ").center(sy * LEG_Y, CROSSBAR_Z)
                     .circle(TUBE_OD / 2 + 3).extrude(30).translate((x - 15, 0, 0)))
            bore = tube((x - 16, sy * LEG_Y, CROSSBAR_Z), (x + 16, sy * LEG_Y, CROSSBAR_Z))
            clamp = clamp.cut(bore)
            # tab down to slide
            tab = cq.Workplane("XY").box(30, 6, CROSSBAR_Z - SLIDE_Z).translate(
                (x, y_in - sy * 3, (CROSSBAR_Z + SLIDE_Z) / 2))
            parts.append(clamp.union(tab))
    solid = parts[0]
    for p in parts[1:]:
        solid = solid.union(p)
    return solid


def carrier(ext):
    plate = rounded_box(CARRIER_X, CARRIER_Y, CARRIER_T, 60)
    cut = cq.Workplane("XY").circle(CUTOUT_DIA / 2).extrude(50).translate((0, 0, -25))
    plate = plate.cut(cut)
    # front/rear down-turned flanges bolted to slide drawer members
    for sy in (-1, 1):
        fl = cq.Workplane("XY").box(SLIDE_LEN - 20, 3, SLIDE_H - 10).translate(
            (0, sy * (CARRIER_Y / 2 - 1.5), -(SLIDE_H - 10) / 2 + CARRIER_T / 2))
        plate = plate.union(fl)
    # D pull handle on the +X end
    h = (cq.Workplane("XY").box(12, HANDLE_W, 12).translate((CARRIER_X / 2 + 40, 0, 0)))
    for sy in (-1, 1):
        h = h.union(cq.Workplane("XY").box(40, 12, 12).translate((CARRIER_X / 2 + 20, sy * (HANDLE_W / 2 - 6), 0)))
    plate = plate.union(h.edges().fillet(3))
    return plate.translate((ext, 0, CARRIER_Z + CARRIER_T / 2))


def pan(ext):
    top_z = CARRIER_Z + CARRIER_T
    import math
    taper = math.degrees(math.atan((PAN_TOP_X - PAN_BOT_X) / 2 / PAN_DEPTH))  # draft angle

    def tapered(dia, ztop, h):
        # round bucket: extrude downward from the rim with a positive taper (narrowing)
        return (cq.Workplane("XY").workplane(offset=ztop)
                .circle(dia / 2).extrude(-h, taper=taper))
    outer = tapered(PAN_DIA, top_z, PAN_DEPTH)
    inner = tapered(PAN_DIA - 2 * PAN_WALL, top_z + 1, PAN_DEPTH - PAN_WALL + 1)
    body = outer.cut(inner)
    flange = (cq.Workplane("XY").circle(PAN_DIA / 2 + PAN_FLANGE).circle(PAN_DIA / 2 - PAN_WALL)
              .extrude(PAN_WALL).translate((0, 0, top_z)))
    body = body.union(flange)
    # bail-style lift grips on flange (both X ends)
    for sx in (-1, 1):
        g = cq.Workplane("XY").box(30, 90, 8).edges("|Z").fillet(3).translate(
            (sx * (PAN_DIA / 2 + PAN_FLANGE + 8), 0, top_z + 4))
        body = body.union(g)
    return body.translate((ext, 0, 0))


def build(ext=0.0):
    return {
        "frame": frame(),
        "seat": seat(),
        "lid": lid(),
        "backrest": backrest(),
        "slides": slide_pair(ext),
        "carrier": carrier(ext),
        "pan": pan(ext),
    }


COLORS = {
    "frame": (0.75, 0.76, 0.78),
    "seat": (0.86, 0.90, 0.90),
    "lid": (0.86, 0.90, 0.90),
    "backrest": (0.20, 0.22, 0.28),
    "slides": (0.35, 0.36, 0.40),
    "carrier": (0.20, 0.45, 0.75),
    "pan": (0.80, 0.86, 0.86),
}

if __name__ == "__main__":
    import os
    out = os.path.dirname(os.path.abspath(__file__)) + "/out"
    os.makedirs(out, exist_ok=True)
    for name, ext in (("closed", 0.0), ("extended", TRAVEL)):
        parts = build(ext)
        asm = cq.Assembly(name=f"commode_slide_pan_{name}")
        for k, v in parts.items():
            asm.add(v, name=k, color=cq.Color(*COLORS[k]))
        asm.save(f"{out}/commode_slide_pan_{name}.step")
        comp = cq.Compound.makeCompound([v.val() for v in parts.values()])
        cq.exporters.export(cq.Workplane().add(comp), f"{out}/commode_slide_pan_{name}.stl", tolerance=0.5)
        print("exported", name)
    # individual new parts for the manufacturer
    parts = build(0.0)
    for k in ("carrier", "pan", "slides", "backrest"):
        cq.exporters.export(parts[k], f"{out}/part_{k}.step")
        cq.exporters.export(parts[k], f"{out}/part_{k}.stl", tolerance=0.3)
    print("done")

"""Dimensioned 2D manufacturing drawings (PDF + DXF) generated from model.py parameters."""
import os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Ellipse, FancyBboxPatch, Polygon
import ezdxf
from ezdxf.enums import TextEntityAlignment
import model as M

OUT = os.path.dirname(os.path.abspath(__file__)) + "/out"
IN = 25.4


def fmt(mm):
    return f'{mm:.0f} mm [{mm / IN:.2f}"]'


class Sheet:
    """Records 2D primitives and emits them to matplotlib (PDF) and ezdxf (DXF)."""

    def __init__(self, title, size=(17, 11)):
        self.title = title
        self.fig, self.ax = plt.subplots(figsize=size)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.doc = ezdxf.new("R2010", setup=True)
        self.doc.units = ezdxf.units.MM
        self.msp = self.doc.modelspace()
        for name, color in (("OUTLINE", 7), ("HIDDEN", 8), ("DIM", 1), ("TEXT", 3), ("CENTER", 4)):
            self.doc.layers.add(name, color=color)
        self.doc.layers.get("HIDDEN").dxf.linetype = "DASHED"
        self.doc.layers.get("CENTER").dxf.linetype = "CENTER"

    # ---- primitives ----
    def line(self, p1, p2, hidden=False, lw=1.0, color="k"):
        ls = "--" if hidden else "-"
        self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], ls, lw=lw, color=color)
        self.msp.add_line(p1, p2, dxfattribs={"layer": "HIDDEN" if hidden else "OUTLINE"})

    def rect(self, x, y, w, h, r=0, hidden=False, lw=1.0):
        if r > 0:
            self.ax.add_patch(FancyBboxPatch((x + r, y + r), w - 2 * r, h - 2 * r,
                                             boxstyle=f"round,pad={r}", fill=False, lw=lw,
                                             ls="--" if hidden else "-"))
            pts = []
            for cx, cy, a0 in ((x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180), (x + w - r, y + r, 270)):
                for i in range(0, 91, 15):
                    a = math.radians(a0 + i)
                    pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            self.msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "HIDDEN" if hidden else "OUTLINE"})
        else:
            self.ax.add_patch(Rectangle((x, y), w, h, fill=False, lw=lw, ls="--" if hidden else "-"))
            self.msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], close=True,
                                    dxfattribs={"layer": "HIDDEN" if hidden else "OUTLINE"})

    def circle(self, c, r, hidden=False):
        self.ax.add_patch(Circle(c, r, fill=False, lw=1.0, ls="--" if hidden else "-"))
        self.msp.add_circle(c, r, dxfattribs={"layer": "HIDDEN" if hidden else "OUTLINE"})

    def ellipse(self, c, rx, ry):
        self.ax.add_patch(Ellipse(c, 2 * rx, 2 * ry, fill=False, lw=1.0))
        self.msp.add_ellipse(c, major_axis=(rx, 0), ratio=ry / rx, dxfattribs={"layer": "OUTLINE"})

    def centerline(self, p1, p2):
        self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], "-.", lw=0.6, color="0.4")
        self.msp.add_line(p1, p2, dxfattribs={"layer": "CENTER"})

    def text(self, p, s, size=9, ha="left", weight="normal"):
        self.ax.text(p[0], p[1], s, fontsize=size, ha=ha, va="bottom", weight=weight, family="DejaVu Sans")
        h = size * 1.8
        align = {"left": TextEntityAlignment.LEFT, "center": TextEntityAlignment.CENTER,
                 "right": TextEntityAlignment.RIGHT}[ha]
        for i, ln in enumerate(s.split("\n")):
            self.msp.add_text(ln, height=h, dxfattribs={"layer": "TEXT"}).set_placement(
                (p[0], p[1] - i * h * 1.6), align=align)

    def dim(self, p1, p2, offset, text=None, vertical=False):
        """Linear dimension between p1 and p2 with extension lines, offset perpendicular."""
        x1, y1 = p1
        x2, y2 = p2
        if vertical:
            xd = x1 + offset
            self.ax.plot([x1, xd + (5 if offset > 0 else -5)], [y1, y1], lw=0.5, color="r")
            self.ax.plot([x2, xd + (5 if offset > 0 else -5)], [y2, y2], lw=0.5, color="r")
            self.ax.annotate("", (xd, y1), (xd, y2), arrowprops=dict(arrowstyle="<->", lw=0.7, color="r"))
            t = text or fmt(abs(y2 - y1))
            self.ax.text(xd + 4, (y1 + y2) / 2, t, fontsize=7.5, color="r", rotation=90, ha="left", va="center")
            self.msp.add_linear_dim(base=(xd, (y1 + y2) / 2), p1=(x1, y1), p2=(x2, y2), angle=90,
                                    text=t, dxfattribs={"layer": "DIM"}).render()
        else:
            yd = y1 + offset
            self.ax.plot([x1, x1], [y1, yd + (5 if offset > 0 else -5)], lw=0.5, color="r")
            self.ax.plot([x2, x2], [y2, yd + (5 if offset > 0 else -5)], lw=0.5, color="r")
            self.ax.annotate("", (x1, yd), (x2, yd), arrowprops=dict(arrowstyle="<->", lw=0.7, color="r"))
            t = text or fmt(abs(x2 - x1))
            self.ax.text((x1 + x2) / 2, yd + 4, t, fontsize=7.5, color="r", ha="center", va="bottom")
            self.msp.add_linear_dim(base=((x1 + x2) / 2, yd), p1=(x1, y1), p2=(x2, y2),
                                    text=t, dxfattribs={"layer": "DIM"}).render()

    def note(self, p, s, size=7.5):
        self.text(p, s, size=size)

    def finish(self, fname_base, notes_xy=None):
        self.ax.set_title(self.title, fontsize=14, weight="bold", loc="left")
        self.ax.relim(); self.ax.autoscale_view()
        lo, hi = self.ax.get_ylim()
        self.ax.set_ylim(lo, hi + 0.06 * (hi - lo))
        self.fig.tight_layout()
        self.fig.savefig(f"{OUT}/{fname_base}.pdf")
        self.fig.savefig(f"{OUT}/{fname_base}.png", dpi=170)
        plt.close(self.fig)
        self.doc.saveas(f"{OUT}/{fname_base}.dxf")
        print("wrote", fname_base)


# =====================================================================================
def sheet_assembly():
    s = Sheet("SHEET 1 - GENERAL ASSEMBLY: Folding commode with side slide-out pan (units mm [in], scale 1:1 in DXF)")
    R = M.TUBE_OD / 2
    OW = 2 * M.LEG_X + M.TUBE_OD   # overall width
    OD = 2 * M.LEG_Y + M.TUBE_OD   # overall depth

    # ---------- FRONT VIEW (X-Z) at origin ----------
    ox, oz = 0, 0
    s.text((ox - OW / 2, oz + M.ARM_Z + 90), "FRONT VIEW (caregiver / slide-out side on RIGHT)", size=10, weight="bold")
    for sx in (-1, 1):
        x = ox + sx * M.LEG_X
        s.rect(x - R, oz + M.INNER_LEG_LEN, M.TUBE_OD, M.ARM_Z - M.INNER_LEG_LEN + R)          # outer leg
        s.rect(x - M.INNER_LEG_OD / 2, oz + M.FOOT_H, M.INNER_LEG_OD, M.INNER_LEG_LEN + 80)   # inner leg
        s.rect(x - 20, oz, 40, M.FOOT_H)                                                        # foot
        s.rect(x - 25, oz + M.ARM_Z + 5, 50, 28, r=6)                                           # arm pad
        for i in range(5):                                                                       # height-adjust holes
            s.circle((x, oz + M.INNER_LEG_LEN + 10 + i * 25), 4)
    s.rect(ox - M.LEG_X, oz + M.CROSSBAR_Z - R, 2 * M.LEG_X, M.TUBE_OD)                          # front cross bar
    s.rect(ox - M.LEG_X, oz + M.BACK_Z - R, 2 * M.LEG_X, M.TUBE_OD, hidden=True)                # back bar
    s.rect(ox - M.BACKPAD_W / 2, oz + M.BACK_Z - M.BACKPAD_H / 2, M.BACKPAD_W, M.BACKPAD_H, r=18)  # backrest pad (in front of bar)
    s.rect(ox - M.SEAT_DIA / 2, oz + M.SEAT_Z, M.SEAT_DIA, M.SEAT_T, r=8)                       # round seat (dia)
    s.rect(ox - M.SLIDE_LEN / 2, oz + M.SLIDE_Z, M.SLIDE_LEN, M.SLIDE_H)                         # slide (closed)
    s.rect(ox - M.CARRIER_X / 2, oz + M.CARRIER_Z, M.CARRIER_X, M.CARRIER_T)                     # carrier
    s.rect(ox + M.CARRIER_X / 2 + 8, oz + M.CARRIER_Z - 3, 44, 12, r=3)                          # handle
    pan_top = M.CARRIER_Z + M.CARRIER_T
    s.line((ox - M.PAN_TOP_X / 2, oz + pan_top), (ox - M.PAN_BOT_X / 2, oz + pan_top - M.PAN_DEPTH))
    s.line((ox + M.PAN_TOP_X / 2, oz + pan_top), (ox + M.PAN_BOT_X / 2, oz + pan_top - M.PAN_DEPTH))
    s.line((ox - M.PAN_BOT_X / 2, oz + pan_top - M.PAN_DEPTH), (ox + M.PAN_BOT_X / 2, oz + pan_top - M.PAN_DEPTH))
    s.rect(ox - M.PAN_TOP_X / 2 - M.PAN_FLANGE, oz + pan_top, M.PAN_TOP_X + 2 * M.PAN_FLANGE, M.PAN_WALL)
    # extended pan ghost
    ex = M.TRAVEL
    s.line((ox + ex - M.PAN_TOP_X / 2, oz + pan_top), (ox + ex - M.PAN_BOT_X / 2, oz + pan_top - M.PAN_DEPTH), hidden=True)
    s.line((ox + ex + M.PAN_TOP_X / 2, oz + pan_top), (ox + ex + M.PAN_BOT_X / 2, oz + pan_top - M.PAN_DEPTH), hidden=True)
    s.line((ox + ex - M.PAN_BOT_X / 2, oz + pan_top - M.PAN_DEPTH), (ox + ex + M.PAN_BOT_X / 2, oz + pan_top - M.PAN_DEPTH), hidden=True)
    s.rect(ox + ex - M.CARRIER_X / 2, oz + M.CARRIER_Z, M.CARRIER_X, M.CARRIER_T, hidden=True)
    s.rect(ox + ex - M.SLIDE_LEN / 2, oz + M.SLIDE_Z + 3, M.SLIDE_LEN, M.SLIDE_H - 6, hidden=True)
    s.text((ox + ex + 40, oz + pan_top - M.PAN_DEPTH - 40), "PAN SHOWN EXTENDED (dashed)\nfully clears legs -> lift straight up", size=7.5)
    # dims
    s.dim((ox - M.LEG_X - R, oz), (ox + M.LEG_X + R, oz), -70, text="OVERALL WIDTH " + fmt(OW))
    s.dim((ox - M.LEG_X, oz), (ox + M.LEG_X, oz), -40, text="LEG C/C " + fmt(2 * M.LEG_X))
    s.dim((ox + M.LEG_X + R + 30, oz), (ox + M.LEG_X + R + 30, oz + M.SEAT_H), 0, text="SEAT HEIGHT " + fmt(M.SEAT_H) + ' (adj. 16.5"-22.5")', vertical=True)
    s.dim((ox + M.LEG_X + R + 150, oz), (ox + M.LEG_X + R + 210, oz + M.ARM_Z + 33), 0, text="OVERALL HEIGHT " + fmt(M.ARM_Z + 33), vertical=True)
    s.dim((ox - M.LEG_X - R - 40, oz), (ox - M.LEG_X - R - 40, oz + pan_top - M.PAN_DEPTH), 0, text="PAN CLEARANCE TO FLOOR " + fmt(pan_top - M.PAN_DEPTH), vertical=True)
    s.dim((ox - M.LEG_X - R - 150, oz), (ox - M.LEG_X - R - 150, oz + M.SLIDE_Z), 0, text="SLIDE UNDERSIDE " + fmt(M.SLIDE_Z), vertical=True)
    s.dim((ox, oz + M.ARM_Z + 60), (ox + ex, oz + M.ARM_Z + 60), 0, text="SLIDE TRAVEL " + fmt(ex))

    # ---------- SIDE VIEW (Y-Z) to the right ----------
    sx0 = ox + OW / 2 + ex + 520
    s.text((sx0 - OD / 2, oz + M.ARM_Z + 90), "SIDE VIEW (from slide-out side)", size=10, weight="bold")
    for sy in (-1, 1):
        y = sx0 + sy * M.LEG_Y
        s.rect(y - R, oz + M.INNER_LEG_LEN, M.TUBE_OD, M.ARM_Z - M.INNER_LEG_LEN + R)
        s.rect(y - M.INNER_LEG_OD / 2, oz + M.FOOT_H, M.INNER_LEG_OD, M.INNER_LEG_LEN + 80)
        s.rect(y - 20, oz, 40, M.FOOT_H)
    s.rect(sx0 - M.LEG_Y, oz + M.ARM_Z - R, 2 * M.LEG_Y, M.TUBE_OD)      # armrest tube
    s.rect(sx0 - 140, oz + M.ARM_Z + 5, 280, 28, r=6)
    s.rect(sx0 - M.LEG_Y, oz + M.BRACE_Z - R, 2 * M.LEG_Y, M.TUBE_OD)    # lower brace
    for sy in (-1, 1):                                                    # cross bar ends + slide + clamp
        y = sx0 + sy * M.LEG_Y
        s.circle((y, oz + M.CROSSBAR_Z), R)
        s.circle((y, oz + M.CROSSBAR_Z), R + 3)
        yi = y - sy * R
        s.rect(min(yi, yi - sy * M.SLIDE_T), oz + M.SLIDE_Z, M.SLIDE_T, M.SLIDE_H)
        s.rect(min(yi, yi - sy * 6), oz + M.SLIDE_Z, 6, M.CROSSBAR_Z - M.SLIDE_Z)
    s.circle((sx0 + M.LEG_Y, oz + M.BACK_Z), R)
    py = sx0 + M.LEG_Y - R - M.BACKPAD_T + 6
    s.rect(py, oz + M.BACK_Z - M.BACKPAD_H / 2, M.BACKPAD_T, M.BACKPAD_H, r=10)                  # backrest pad, front of bar
    s.text((py - 150, oz + M.BACK_Z - M.BACKPAD_H / 2 - 40), "BACKREST PAD SP-05\n(in FRONT of back bar)", size=6.5)
    s.rect(sx0 - M.SEAT_DIA / 2, oz + M.SEAT_Z, M.SEAT_DIA, M.SEAT_T, r=8)
    s.rect(sx0 - M.CARRIER_Y / 2, oz + M.CARRIER_Z, M.CARRIER_Y, M.CARRIER_T)
    s.line((sx0 - M.PAN_TOP_Y / 2, oz + pan_top), (sx0 - M.PAN_BOT_Y / 2, oz + pan_top - M.PAN_DEPTH))
    s.line((sx0 + M.PAN_TOP_Y / 2, oz + pan_top), (sx0 + M.PAN_BOT_Y / 2, oz + pan_top - M.PAN_DEPTH))
    s.line((sx0 - M.PAN_BOT_Y / 2, oz + pan_top - M.PAN_DEPTH), (sx0 + M.PAN_BOT_Y / 2, oz + pan_top - M.PAN_DEPTH))
    s.rect(sx0 - M.PAN_TOP_Y / 2 - M.PAN_FLANGE, oz + pan_top, M.PAN_TOP_Y + 2 * M.PAN_FLANGE, M.PAN_WALL)
    # lid open
    lid_len = M.SEAT_DIA - 20
    a = math.radians(180 - M.LID_ANGLE)
    hx, hz = sx0 + M.SEAT_DIA / 2 - 10, oz + M.SEAT_H
    s.line((hx, hz), (hx + lid_len * math.cos(a), hz + lid_len * math.sin(a)))
    s.line((hx - M.LID_T * math.sin(a), hz + M.LID_T * math.cos(a)),
           (hx + lid_len * math.cos(a) - M.LID_T * math.sin(a), hz + lid_len * math.sin(a) + M.LID_T * math.cos(a)))
    s.dim((sx0 - M.LEG_Y - R, oz), (sx0 + M.LEG_Y + R, oz), -70, text="OVERALL DEPTH " + fmt(OD))
    s.dim((sx0 - M.LEG_Y, oz), (sx0 + M.LEG_Y, oz), -40, text="LEG C/C " + fmt(2 * M.LEG_Y))
    s.dim((sx0 - M.CARRIER_Y / 2, oz + M.CARRIER_Z + 60), (sx0 + M.CARRIER_Y / 2, oz + M.CARRIER_Z + 60), 0, text="CARRIER WIDTH " + fmt(M.CARRIER_Y))
    s.dim((sx0 + M.LEG_Y + R + 30, oz), (sx0 + M.LEG_Y + R + 30, oz + M.CROSSBAR_Z), 0, text="CROSS BAR C/L " + fmt(M.CROSSBAR_Z), vertical=True)
    s.dim((sx0 + M.LEG_Y + R + 100, oz), (sx0 + M.LEG_Y + R + 100, oz + M.BRACE_Z), 0, text="SIDE BRACE C/L " + fmt(M.BRACE_Z), vertical=True)
    s.dim((sx0 - M.LEG_Y - R - 40, oz + pan_top), (sx0 - M.LEG_Y - R - 40, oz + M.SEAT_Z), 0, text="GAP " + fmt(M.SEAT_Z - pan_top), vertical=True)

    # ---------- TOP VIEW (X-Y) below ----------
    ty = oz - 420 - OD / 2
    s.text((ox - OW / 2, ty + OD / 2 + 130), "TOP VIEW (seat & lid removed) - pan closed, extended position dashed", size=10, weight="bold")
    for sx in (-1, 1):
        for sy in (-1, 1):
            s.circle((ox + sx * M.LEG_X, ty + sy * M.LEG_Y), R)
            s.circle((ox + sx * M.LEG_X, ty + sy * M.LEG_Y), M.INNER_LEG_OD / 2)
        s.rect(ox + sx * M.LEG_X - R, ty - M.LEG_Y, M.TUBE_OD, 2 * M.LEG_Y)             # armrest tubes
    for sy in (-1, 1):
        s.rect(ox - M.LEG_X, ty + sy * M.LEG_Y - R, 2 * M.LEG_X, M.TUBE_OD)               # cross bars
        yi = ty + sy * (M.LEG_Y - R)
        s.rect(ox - M.SLIDE_LEN / 2, min(yi, yi - sy * M.SLIDE_T), M.SLIDE_LEN, M.SLIDE_T)  # slides
        for x in (-180, 0, 180):
            s.rect(ox + x - 15, ty + sy * M.LEG_Y - R - 3, 30, M.TUBE_OD + 6)              # clamps
    s.rect(ox - M.CARRIER_X / 2, ty - M.CARRIER_Y / 2, M.CARRIER_X, M.CARRIER_Y, r=60)
    s.circle((ox, ty), M.CUTOUT_DIA / 2)
    s.circle((ox, ty), M.PAN_DIA / 2 + M.PAN_FLANGE)
    s.rect(ox + M.CARRIER_X / 2, ty - M.HANDLE_W / 2, 46, M.HANDLE_W, r=5)
    s.ellipse((ox, ty), M.SEAT_HOLE_W / 2, M.SEAT_HOLE_D / 2)
    s.text((ox - 60, ty + M.SEAT_HOLE_D / 2 + 8), "seat aperture (ref.)", size=7)
    s.circle((ox, ty), M.SEAT_DIA / 2, hidden=True)
    s.text((ox - M.SEAT_DIA / 2 + 10, ty + M.SEAT_DIA / 2 - 30), f"ROUND SEAT dia {M.SEAT_DIA:.0f} mm [{M.SEAT_DIA/25.4:.2f}\"] (dashed, ref.)", size=7)
    s.rect(ox + ex - M.CARRIER_X / 2, ty - M.CARRIER_Y / 2, M.CARRIER_X, M.CARRIER_Y, r=60, hidden=True)
    s.circle((ox + ex, ty), M.PAN_DIA / 2 + M.PAN_FLANGE, hidden=True)
    s.circle((ox + ex, ty), M.PAN_BOT_DIA / 2, hidden=True)
    s.centerline((ox - OW / 2 - 60, ty), (ox + ex + M.CARRIER_X / 2 + 100, ty))
    s.dim((ox - M.SLIDE_LEN / 2, ty - OD / 2 - 20), (ox + M.SLIDE_LEN / 2, ty - OD / 2 - 20), -30, text="SLIDE LENGTH " + fmt(M.SLIDE_LEN) + " (20 in full-extension, 100 lb/pair)")
    s.dim((ox - M.CARRIER_X / 2, ty + OD / 2 + 10), (ox + M.CARRIER_X / 2, ty + OD / 2 + 10), 30, text="CARRIER LENGTH " + fmt(M.CARRIER_X))
    s.dim((ox + ex + M.PAN_TOP_X / 2 + M.PAN_FLANGE, ty - OD / 2 - 20), (ox + M.LEG_X + R, ty - OD / 2 - 20), -75,
          text="pan overhang past leg " + fmt(ex + M.PAN_TOP_X / 2 + M.PAN_FLANGE - M.LEG_X - R))
    s.dim((ox + ex - M.PAN_TOP_X / 2 - M.PAN_FLANGE, ty + OD / 2 + 10), (ox + M.LEG_X - R, ty + OD / 2 + 10), 75,
          text="lift-out clearance " + fmt(ex - M.PAN_TOP_X / 2 - M.PAN_FLANGE - M.LEG_X + R))

    s.note((ox + OW / 2 + ex + 100, ty + OD / 2),
           "NOTES\n"
           "1. Base chair: standard folding aluminium commode, 1\" (25.4 mm) x 1.5 mm wall tube, telescoping legs, 5-position height adjust.\n"
           "2. Slide-out pan module attaches to existing front & rear cross bars with 6x tube clamps (3 per bar) - no welding, retrofit-able.\n"
           "3. Two 20\" full-extension ball-bearing drawer slides, 45 mm x 12.7 mm, stainless or zinc-plated, min. 100 lb (45 kg) rated per pair, with soft-close/detent.\n"
           "4. Carrier plate (blue) rides on slides; pan hangs by its rim in the carrier cutout and lifts straight out when extended.\n"
           "5. Pan slides out to the RIGHT of the seated user (caregiver side). Mirror assembly for left-hand version.\n"
           "6. Spring latch / magnetic catch holds carrier in CLOSED position; positive stop at full extension.\n"
           "7. All edges deburred. Static load: 300 lb (136 kg) user. Materials in Sheet 4 BOM.")
    s.finish("sheet1_general_assembly")


def sheet_carrier():
    s = Sheet("SHEET 2 - CARRIER PLATE (P/N SP-01) - 6 mm HDPE or 2.0 mm 304 SS  (units mm [in])")
    X, Y, T = M.CARRIER_X, M.CARRIER_Y, M.CARRIER_T
    FH = M.SLIDE_H - 10
    # top view
    s.text((-X / 2, Y / 2 + 110), "TOP VIEW", size=10, weight="bold")
    s.rect(-X / 2, -Y / 2, X, Y, r=60)
    s.circle((0, 0), M.CUTOUT_DIA / 2)
    s.centerline((-X / 2 - 40, 0), (X / 2 + 100, 0))
    s.centerline((0, -Y / 2 - 40), (0, Y / 2 + 40))
    # handle
    s.rect(X / 2, -M.HANDLE_W / 2, 52, M.HANDLE_W, r=6)
    s.rect(X / 2 + 12, -M.HANDLE_W / 2 + 12, 28, M.HANDLE_W - 24, r=4)
    # flange fastener holes (M4 x 6 per flange, shown as hidden circles at flange line)
    for sy in (-1, 1):
        for x in (-180, -110, -40, 40, 110, 180):
            s.circle((x, sy * (Y / 2 - 1.5)), 2.2, hidden=True)
    # dims
    s.dim((-X / 2, -Y / 2), (X / 2, -Y / 2), -50, text=fmt(X))
    s.dim((-M.CUTOUT_X / 2, -Y / 2), (M.CUTOUT_X / 2, -Y / 2), -25, text="CUTOUT dia " + fmt(M.CUTOUT_DIA))
    s.dim((-X / 2, -Y / 2), (-X / 2, Y / 2), -40, text=fmt(Y), vertical=True)

    s.dim((X / 2, Y / 2), (X / 2 + 52, Y / 2), 30, text="HANDLE " + fmt(52))
    s.dim((X / 2 + 60, -M.HANDLE_W / 2), (X / 2 + 60, M.HANDLE_W / 2), 0, text=fmt(M.HANDLE_W), vertical=True)
    s.dim((-180, Y / 2), (180, Y / 2), 40, text="M4 hole pattern 6x @ 70 mm pitch, both flanges " + fmt(360))
    s.text((-M.CUTOUT_X / 2 + 40, -M.CUTOUT_Y / 2 + 20), "round cutout, concentric with seat aperture\nR60 corners (outer)", size=7.5)

    # section A-A (side profile) below
    oy = -Y / 2 - 260
    s.text((-X / 2, oy + 60), "SECTION A-A  (through Y=0, looking from +X)  -  flanges bolt to slide drawer members", size=10, weight="bold")
    s.rect(-Y / 2, oy, Y, T)
    for sy in (-1, 1):
        s.rect(min(sy * (Y / 2), sy * (Y / 2) - sy * 3), oy - FH, 3, FH)
        # slide drawer member + cabinet member ghost
        yi = sy * (Y / 2)
        s.rect(min(yi, yi + sy * M.SLIDE_T / 2), oy - FH - 5, M.SLIDE_T / 2, M.SLIDE_H - 6, hidden=True)
        s.rect(min(yi + sy * M.SLIDE_T / 2, yi + sy * M.SLIDE_T), oy - FH - 5, M.SLIDE_T / 2, M.SLIDE_H, hidden=True)
        s.circle((yi + sy * (M.SLIDE_T + M.TUBE_OD / 2), oy + 15), M.TUBE_OD / 2, hidden=True)
    s.dim((-Y / 2, oy), (-Y / 2, oy - FH), -60, text="FLANGE " + fmt(FH), vertical=True)
    s.dim((Y / 2 + 60, oy), (Y / 2 + 60, oy + T), 0, text="t=" + fmt(T), vertical=True)
    s.text((-Y / 2 - 5, oy - FH - 70), "dashed: drawer slide & cross-bar tube (ref.)", size=7.5)
    s.note((-X / 2, oy - FH - 150),
           "NOTES\n"
           "1. Material option A: 6 mm HDPE (FDA, white) - flanges are separate 3 mm SS angle riveted on.   Option B: 2.0 mm 304 SS, flanges formed, edges hemmed.\n"
           "2. Handle: 12 mm dia SS D-pull or moulded HDPE, 120 mm wide, 40 mm stand-off from plate edge.\n"
           "3. Pan flange rests on plate around cutout - keep cutout edge smooth (R>=1 mm) so pan can be lifted out.\n"
           "4. Latch keeper (magnetic catch or spring detent) on -X end; strike on frame clamp.  Bump stop at full extension.\n"
           "5. Tolerance: +/-0.5 mm cutout, +/-1.0 mm outer, flatness 1.0 mm.")
    s.finish("sheet2_carrier_plate")


def sheet_pan():
    s = Sheet("SHEET 3 - REMOVABLE ROUND PAN (P/N SP-02)\nmoulded PP or 0.8 mm 304 SS drawn  (units mm [in])")
    TX, TY, BX, BY, D, F, W = M.PAN_TOP_X, M.PAN_TOP_Y, M.PAN_BOT_X, M.PAN_BOT_Y, M.PAN_DEPTH, M.PAN_FLANGE, M.PAN_WALL
    s.text((-TX / 2 - F, TY / 2 + F + 60), "TOP VIEW", size=10, weight="bold")
    s.text((TX / 2 + F + 60, TY / 2), "Concentric with 440 mm round seat;\nrim surrounds 300 x 220 seat aperture.", size=7.5)
    s.circle((0, 0), TX / 2 + F)
    s.circle((0, 0), TX / 2)
    s.circle((0, 0), TX / 2 - W)
    s.circle((0, 0), BX / 2, hidden=True)
    for sx in (-1, 1):
        s.rect(sx * (TX / 2 + F + 8) - 15, -45, 30, 90, r=3)
    s.centerline((-TX / 2 - F - 60, 0), (TX / 2 + F + 60, 0))
    s.centerline((0, -TY / 2 - F - 40), (0, TY / 2 + F + 40))
    s.dim((-TX / 2 - F, -TY / 2 - F), (TX / 2 + F, -TY / 2 - F), -50, text="FLANGE O/A dia " + fmt(TX + 2 * F))
    s.dim((-TX / 2, -TY / 2 - F), (TX / 2, -TY / 2 - F), -25, text="RIM dia " + fmt(TX))
    s.dim((-TX / 2 - F - 27, -45), (-TX / 2 - F - 27, 45), -60, text="grip " + fmt(90), vertical=True)
    s.text((-BX / 2 + 10, -BY / 2 + 10), "dashed: base dia " + fmt(BX), size=7.5)

    oy = -TY / 2 - F - 300
    s.text((-TX / 2 - F, oy + 50), "SECTION B-B (long axis)", size=10, weight="bold")
    # outer profile
    pts_outer = [(-TX / 2 - F, oy), (-TX / 2 - F, oy + W), (-TX / 2 + W, oy + W), (-BX / 2 + W, oy - D + W),
                 (BX / 2 - W, oy - D + W), (TX / 2 - W, oy + W), (TX / 2 + F, oy + W), (TX / 2 + F, oy),
                 (TX / 2, oy), (BX / 2, oy - D), (-BX / 2, oy - D), (-TX / 2, oy)]
    for i in range(len(pts_outer)):
        s.line(pts_outer[i], pts_outer[(i + 1) % len(pts_outer)])
    # fill line 7 qt
    fill_z = oy - D + 115
    s.line((-BX / 2 - 10, fill_z), (BX / 2 + 10, fill_z), hidden=True)
    s.text((TX / 2 + F + 90, fill_z - 4), "MAX FILL line (moulded), 7 qt / 6.7 L", size=7.5)
    s.dim((TX / 2 + F + 40, oy - D), (TX / 2 + F + 40, oy + W), 0, text="DEPTH " + fmt(D + W), vertical=True)
    s.dim((-BX / 2, oy - D), (BX / 2, oy - D), -40, text="BASE dia " + fmt(BX))
    s.dim((-TX / 2, oy - D), (-TX / 2 - F, oy - D), -70, text="FLANGE " + fmt(F))
    taper = math.degrees(math.atan((TX - BX) / 2 / D))
    s.note((-TX / 2 - F, oy - D - 120),
           "NOTES\n"
           f"0. Round (revolved) pan.  Draft angle {taper:.1f} deg.  Wall {W:.1f} mm nominal.  Base corner R15 inside.\n"
           "1. Capacity: ~9.3 L brim-full; 7 qt (6.7 L) working capacity at moulded MAX FILL line 115 mm above base.\n"
           "   Concentric with the 440 mm round seat and its 300 x 220 aperture (pan rim 310 dia fully surrounds aperture).\n"
           "2. Flange rests on carrier plate cutout (Sheet 2). Two moulded end grips for lift-out.\n"
           "3. Supply with snap-on splash lid (P/N SP-03, same rim profile) - lid fitted once pan is extended before carrying.\n"
           "4. Material: polypropylene copolymer, min. 2.5 mm wall, autoclavable / dishwasher-safe. Alt: 0.8 mm 304 SS deep-drawn, polished.\n"
           "5. Tolerance +/-1.0 mm; rim must pass freely through carrier cutout (5 mm radial clearance); flange OD 340 clears carrier flanges (351 inside).")
    s.finish("sheet3_pan")


def sheet_bracket_bom():
    s = Sheet("SHEET 4 - TUBE CLAMP BRACKET (P/N SP-04) & BILL OF MATERIALS  (units mm [in])")
    R = M.TUBE_OD / 2
    H = M.CROSSBAR_Z - M.SLIDE_Z
    # bracket end view
    s.text((-60, 60), "CLAMP BRACKET - END VIEW (2-piece saddle, 30 mm long)", size=10, weight="bold")
    s.circle((0, 0), R + 3)
    s.circle((0, 0), R, hidden=True)
    s.line((-R - 3, 0), (R + 3, 0))                           # split line
    s.rect(R + 3 - 6, -H, 6, H)                                 # tab down to slide
    s.rect(R + 3, -H, M.SLIDE_T / 2, M.SLIDE_H, hidden=True)    # slide cabinet member (ref.)
    for z in (-H + 10, -H + 35):
        s.circle((R + 3 + 3, z), 2.2)
    for x in (-R - 3 + 6, R + 3 - 6):
        s.circle((x, 0), 2.5)
    s.dim((-R - 3, -H - 20), (R + 3, -H - 20), -20, text="O/D " + fmt(2 * R + 6))
    s.dim((R + 40, -H), (R + 40, 0), 0, text="TAB " + fmt(H) + " (bar C/L to slide bottom)", vertical=True)
    s.dim((R + 90, -R), (R + 90, R), 0, text="bore " + fmt(2 * R) + " (1 in tube)", vertical=True)
    s.text((-60, -H - 90),
           "Material: 6061-T6 aluminium or glass-filled nylon.\n"
           "2x M5 clamp screws (split line), 2x M4 screws into\n"
           "slide cabinet member. Rubber liner 1 mm inside bore\n"
           "to protect powder-coat & prevent slip.\n"
           "Qty 6 (3 per cross bar at X = -180, 0, +180 mm).", size=8)

    # BOM table
    bx, by = 320, -20
    rows = [
        ("ITEM", "P/N", "DESCRIPTION", "MATERIAL", "QTY"),
        ("1", "BASE", "Folding commode chair, 1\" alu frame, seat, lid, arms (existing / purchased)", "Aluminium / PP", "1"),
        ("2", "SLD-20", "Full-extension ball-bearing drawer slide, 20\" (508 mm), 45 mm, 100 lb/pair, detent", "Zinc-plated or SS", "2"),
        ("3", "SP-01", "Carrier plate with formed flanges & cutout (Sheet 2)", "6 mm HDPE or 2 mm 304 SS", "1"),
        ("4", "SP-02", "Removable pan, flanged rim, end grips (Sheet 3)", "PP copolymer / 304 SS", "1"),
        ("5", "SP-03", "Snap-on splash lid for SP-02", "PP copolymer", "1"),
        ("6", "SP-04", "Tube clamp bracket, 1\" saddle with tab (this sheet)", "6061-T6 or GF nylon", "6"),
        ("7", "HDL-120", "D-pull handle 120 mm, 12 mm dia", "304 SS", "1"),
        ("8", "LTCH", "Magnetic catch 5 kg (or spring ball detent) + strike", "SS / nylon", "1"),
        ("9", "HW", "M4x10 SS button-head screws + nyloc (slide to carrier flange)", "A2 SS", "12"),
        ("10", "HW", "M5x20 SS screws + nyloc (clamp halves)", "A2 SS", "12"),
        ("11", "HW", "M4x8 SS screws (clamp tab to slide cabinet member)", "A2 SS", "12"),
        ("12", "STOP", "Rubber bump stop 15 mm (full-extension stop on slide)", "EPDM", "2"),
        ("13", "SP-05", "Backrest pad 460x200x45, wraps FRONT of back-bar, rear shell w/ 2 hook-&-loop straps", "PU foam / vinyl, PP shell", "1"),
    ]
    colw = [40, 60, 420, 150, 35]
    rh = 22
    for i, row in enumerate(rows):
        y = by - i * rh
        x = bx
        for j, cell in enumerate(row):
            s.rect(x, y - rh, colw[j], rh)
            s.text((x + 4, y - rh + 6), cell, size=7 if i else 8, weight="bold" if i == 0 else "normal")
            x += colw[j]
    s.text((bx, by + 15), "BILL OF MATERIALS - slide-out pan module", size=10, weight="bold")
    s.note((bx, by - len(rows) * rh - 140),
           "GENERAL\n"
           "- Dimensions in mm [inches]. Untoleranced +/-1.0 mm. Break all edges 0.5 mm.\n"
           "- Frame contact parts must not damage powder-coat: use rubber-lined clamps.\n"
           "- Slide rails to be mounted parallel within 0.5 mm over 508 mm; check free travel with 20 kg in pan.\n"
           "- Design load: 136 kg (300 lb) seated user on base chair; 15 kg in pan on slides at full extension.\n"
           "- Finish: pan & carrier smooth, non-porous, cleanable with hospital disinfectants.\n"
           "- Handedness: drawing shows right-hand (caregiver's right when facing user). Mirror for LH.")
    s.finish("sheet4_bracket_bom")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sheet_assembly()
    sheet_carrier()
    sheet_pan()
    sheet_bracket_bom()

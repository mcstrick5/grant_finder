"""One-page Request for Quote cover letter (PDF + Markdown) for the rear slide-out pan commode."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

TITLE = "REQUEST FOR QUOTE - Rear Slide-Out Pan Bedside Commode (Rev B)"

SECTIONS = [
    ("Date", "________________"),
    ("Project", "Retrofit module for a standard folding aluminium bedside commode that lets a caregiver empty the waste pan\n"
                "while the user remains seated. The round pan slides 20\" (508 mm) straight out the BACK of the chair on two\n"
                "ball-bearing drawer slides, lifts out for emptying, and slides back to a latched position under the seat."),
    ("Scope of quote",
     "Please quote the following, priced separately:\n"
     "  A. Prototype: 1 complete working unit (module fitted to a base chair) for fit and function testing.\n"
     "  B. Pilot run: 10 units.\n"
     "  C. Production: 100 and 500 units (unit price, tooling, lead time).\n"
     "For each, state whether you supply the base chair or fit the module to a chair we supply."),
    ("Parts to be made / sourced (see Sheet 4 BOM for full list)",
     "  SP-01  Carrier plate 375 x 400 x 6 mm, 320 mm round cutout, side flanges, rear D-handle  (Sheet 2)\n"
     "  SP-02  Round pan, 310 mm rim / 340 mm flange / 250 mm base, 152 mm deep, 7 qt working  (Sheet 3)\n"
     "  SP-03  Snap-on splash lid for pan\n"
     "  SP-04  Tube clamp bracket, 1\" saddle with foot, rubber-lined, qty 4  (Sheet 4)\n"
     "  SP-05  Padded backrest 460 x 200 x 45 mm, mounts in FRONT of the rear bar\n"
     "  SP-06  Angle rail 40 x 40 x 3 mm x 508 mm, 6061-T6, qty 2  (Sheet 4)\n"
     "  Bought-in: 2x 20\" full-extension slides (100 lb/pair, corrosion resistant), D-handle, magnetic catch,\n"
     "  bump stops, stainless fasteners."),
    ("Key requirements",
     "  - Retrofit: clamps to the existing frame, no welding or drilling of the chair.\n"
     "  - Pan and carrier concentric with the 440 mm round seat; pan must lift freely out of the carrier at full extension.\n"
     "  - Design load 300 lb (136 kg) seated user; 15 kg in pan at full extension; no tipping with pan extended.\n"
     "  - Pan, lid and carrier smooth, non-porous, dishwasher/disinfectant safe (PP or 304 SS).\n"
     "  - Slides and hardware stainless or zinc-plated with sealed bearings; washable.\n"
     "  - Tolerances per drawings (+/-1.0 mm untoleranced); all edges deburred."),
    ("Supplier to confirm / advise",
     "  1. Material recommendation for carrier (HDPE vs 304 SS) and pan (moulded PP vs drawn SS) at each volume.\n"
     "  2. Engineering review of slide/rail loading and tip stability with the pan extended; propose changes if needed.\n"
     "  3. Whether the design fits your standard commode frame, or dimensions that must change.\n"
     "  4. Lead time for prototype, pilot and production; tooling costs and ownership; MOQ."),
    ("US market / regulatory requirements (product ships to the United States)",
     "  - FDA: commode is a Class I medical device (21 CFR 890.3100/890.3110, 510(k)-exempt). Manufacturer must hold\n"
     "    FDA Establishment Registration and Device Listing and follow 21 CFR 820 QMS (or ISO 13485). Provide evidence.\n"
     "  - Testing: static load and stability per ISO 17966 (assistive products for personal hygiene) and/or RESNA;\n"
     "    supply test reports for 300 lb (136 kg) rated user load with pan extended.\n"
     "  - Materials: skin-contact parts biocompatible (ISO 10993-5/-10); pan/lid plastics food-grade PP. Vinyl, foam and\n"
     "    plastics to meet California Prop 65 and CPSIA/16 CFR limits for lead, cadmium and phthalates; RoHS declaration.\n"
     "  - Corrosion: salt-spray / cleaning-agent resistance test on slides, rails, clamps and fasteners (e.g. ASTM B117).\n"
     "  - Labeling: permanent label with model, rated load, manufacturer, country of origin (19 CFR 134 'Made in China'),\n"
     "    English instructions for use and cleaning; UDI/labeling per 21 CFR 801 as applicable.\n"
     "  - Quality: ISO 9001 certificate; pre-shipment inspection (AQL) report; packaging drop test (ISTA/ASTM D4169).\n"
     "  - Supplier to state the HTS code and confirm any US import tariff applicable to their quote."),
    ("Files provided",
     "  README_manufacturer_brief.md (start here)  |  sheet1-4 PDF + DXF drawings and BOM\n"
     "  commode_slide_pan_closed / _extended .STEP + .STL (full assembly)  |  part_*.step (individual parts)\n"
     "  render_01-06.png (how it works)  |  model.py / drawings.py / render.py (parametric source)"),
    ("Note", "This is a concept design based on standard commode dimensions and has not been physically tested.\n"
             "Fit to the actual base chair and all structural/safety validation are to be performed by the supplier."),
]


def write_pdf():
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    y = 0.955
    ax.text(0.06, y, TITLE, fontsize=13.5, weight="bold", va="top")
    y -= 0.035
    for head, body in SECTIONS:
        ax.text(0.06, y, head.upper(), fontsize=8.5, weight="bold", va="top", color="#333")
        y -= 0.017
        ax.text(0.06, y, body, fontsize=7.6, va="top", family="DejaVu Sans", linespacing=1.3)
        y -= 0.0133 * (body.count("\n") + 1) + 0.011
    ax.text(0.06, 0.03, "Please reply with your quotation and any design comments. Thank you.", fontsize=8.5, va="bottom")
    fig.savefig(f"{OUT}/RFQ_cover_letter.pdf")
    fig.savefig(f"{OUT}/RFQ_cover_letter.png", dpi=150)
    plt.close(fig)


def write_md():
    lines = [f"# {TITLE}", ""]
    for head, body in SECTIONS:
        lines += [f"## {head}", "```" if body.startswith("  ") else "", body, "```" if body.startswith("  ") else "", ""]
    lines.append("Please reply with your quotation and any design comments. Thank you.")
    with open(f"{OUT}/RFQ_cover_letter.md", "w") as f:
        f.write("\n".join(l for l in lines if l is not None))


if __name__ == "__main__":
    write_pdf(); write_md(); print("wrote RFQ_cover_letter.pdf/.png/.md")

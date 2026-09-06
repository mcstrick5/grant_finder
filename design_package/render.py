import os
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
import model

OUT = os.path.dirname(os.path.abspath(__file__)) + "/out"


def to_polydata(shape, tol=0.5):
    verts, tris = shape.val().tessellate(tol, 0.2)
    pts = vtk.vtkPoints()
    pts.SetData(numpy_to_vtk(np.array([[p.x, p.y, p.z] for p in verts]), deep=True))
    t = np.array(tris, dtype=np.int64)
    cells = np.hstack([np.full((len(t), 1), 3, dtype=np.int64), t]).ravel()
    ca = vtk.vtkCellArray()
    ca.SetCells(len(t), numpy_to_vtkIdTypeArray(cells, deep=True))
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetPolys(ca)
    n = vtk.vtkPolyDataNormals()
    n.SetInputData(pd)
    n.SetFeatureAngle(60)
    n.Update()
    return n.GetOutput()


def render(parts, fname, cam_dir=(1.0, -1.3, 0.75), title="", size=(1800, 1400), label=None, transparent=()):
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.SetSize(*size)
    rw.SetMultiSamples(0)
    rw.AddRenderer(ren)
    for name, shape in parts.items():
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(to_polydata(shape))
        a = vtk.vtkActor()
        a.SetMapper(m)
        p = a.GetProperty()
        p.SetColor(*model.COLORS[name])
        p.SetSpecular(0.35)
        p.SetSpecularPower(25)
        p.SetAmbient(0.15)
        if name in transparent:
            p.SetOpacity(0.35)
        ren.AddActor(a)
    if title:
        t = vtk.vtkTextActor()
        t.SetInput(title)
        tp = t.GetTextProperty()
        tp.SetFontSize(34)
        tp.SetColor(0.1, 0.1, 0.1)
        tp.SetJustificationToCentered()
        t.SetDisplayPosition(size[0] // 2, size[1] - 60)
        ren.AddActor2D(t)
    for txt, pos in (label or []):
        t = vtk.vtkTextActor()
        t.SetInput(txt)
        tp = t.GetTextProperty()
        tp.SetFontSize(24)
        tp.SetColor(0.1, 0.1, 0.1)
        t.SetDisplayPosition(*pos)
        ren.AddActor2D(t)
    cam = ren.GetActiveCamera()
    d = np.array(cam_dir, dtype=float)
    d /= np.linalg.norm(d)
    cam.SetFocalPoint(0, 0, 350)
    cam.SetPosition(*(np.array([0, 0, 350]) + d * 3000))
    cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()
    cam.Zoom(1.3)
    ren.SetTwoSidedLighting(True)
    ren.AutomaticLightCreationOn()
    rw.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()
    wr = vtk.vtkPNGWriter()
    wr.SetFileName(fname)
    wr.SetInputConnection(w2i.GetOutputPort())
    wr.Write()
    print("wrote", fname)


if __name__ == "__main__":
    closed = model.build(0)
    ext = model.build(model.TRAVEL)
    render(closed, f"{OUT}/render_01_closed_iso.png",
           title="Folding commode with slide-out pan  -  CLOSED (pan latched under seat)")
    render(ext, f"{OUT}/render_02_extended_iso.png",
           title="Pan slid out to caregiver side  -  FULL EXTENSION (20 in / 508 mm)")
    render(ext, f"{OUT}/render_03_extended_front.png", cam_dir=(0.15, -1, 0.12),
           title="Front view  -  pan extended, clears right-hand legs for lift-out")
    render(ext, f"{OUT}/render_04_extended_seat_ghosted.png", cam_dir=(1.0, -0.9, 1.1), transparent=("seat", "lid"),
           title="Seat/lid ghosted  -  ball-bearing slides, carrier plate (blue), pan")
    render({k: closed[k] for k in ("frame", "slides", "carrier", "pan")}, f"{OUT}/render_05_closed_underside.png",
           cam_dir=(1.0, -1.0, -0.7), title="Underside  -  closed position, slide clamps on front/rear cross bars")
    render({k: ext[k] for k in ("slides", "carrier", "pan")}, f"{OUT}/render_06_slide_assembly.png",
           cam_dir=(1.0, -1.2, 0.9), title="Slide-pan sub-assembly (new parts only)")

import pdb
import json

from OCC.Bnd import Bnd_Box
from OCC.BRepMesh import BRepMesh_IncrementalMesh
from OCC.BRepBndLib import brepbndlib_Add
from OCC.GProp import GProp_GProps
from OCC.BRepGProp import brepgprop_VolumeProperties
from OCC.TColStd import TColStd_SequenceOfAsciiString
from OCC.STEPControl import STEPControl_Reader
from OCC.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity

def bnd_box_volume(bbox):
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    return (xmax - xmin) * (ymax - ymin) * (zmax - zmin)

step_reader = STEPControl_Reader()
status = step_reader.ReadFile('./demo.stp')

if status == IFSelect_RetDone:  # check status
    ok = step_reader.TransferRoot(1)
    _nbs = step_reader.NbShapes()
    aResShape = step_reader.Shape(1)

    # Units
    length = TColStd_SequenceOfAsciiString()
    angles = TColStd_SequenceOfAsciiString()
    solid_angles = TColStd_SequenceOfAsciiString()
    step_reader.FileUnits(length, angles, solid_angles)
    print("length units:", length.First().ToCString())

    # bounding box
    bbox = Bnd_Box()
    deflection = 0.01
    BRepMesh_IncrementalMesh(aResShape, deflection)

    brepbndlib_Add(aResShape, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    print("xmin", xmin)
    print("ymin", ymin)
    print("zmin", zmin)
    print("xmax", xmax)
    print("ymax", ymax)
    print("zmax", zmax)
    print("Bounding Box Volume:", bnd_box_volume(bbox))

    # pdb.set_trace()

    # Volume of solid
    props = GProp_GProps()
    brepgprop_VolumeProperties(aResShape, props)
    print("Volume: ", props.Mass())

    result = {'bounding_box_volume': bnd_box_volume(bbox),
            'solid_volume': props.Mass(),
            'units': length.First().ToCString()}

    print(json.dumps(result))

else:
    print("Error: can't read file.")
    sys.exit(0)


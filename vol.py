import pdb
import json

from OCC.Bnd import Bnd_Box
from OCC.BRepMesh import *
from OCC.BRepBndLib import *
from OCC.GProp import *
from OCC.BRepGProp import *
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
    length = OCC.TColStd.TColStd_SequenceOfAsciiString()
    angles = OCC.TColStd.TColStd_SequenceOfAsciiString()
    solid_angles = OCC.TColStd.TColStd_SequenceOfAsciiString()
    step_reader.FileUnits(length, angles, solid_angles)
    print("length units:", length.First().ToCString())

    # bounding box
    bbox = OCC.Bnd.Bnd_Box()
    deflection = 0.01
    OCC.BRepMesh.BRepMesh_IncrementalMesh(aResShape, deflection)

    OCC.BRepBndLib.brepbndlib_Add(aResShape, bbox)
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
    props = OCC.GProp.GProp_GProps()
    OCC.BRepGProp.brepgprop_VolumeProperties(aResShape, props)
    print("Volume: ", props.Mass())

    result = {'bounding_box_volume': bnd_box_volume(bbox),
            'solid_volume': props.Mass(),
            'units': length.First().ToCString()}

    print(json.dumps(result))

else:
    print("Error: can't read file.")
    sys.exit(0)


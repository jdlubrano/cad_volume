import getopt
import json
import pdb
import sys

from OCC.Bnd import Bnd_Box
from OCC.BRepMesh import BRepMesh_IncrementalMesh
from OCC.BRepBndLib import brepbndlib_Add
from OCC.GProp import GProp_GProps
from OCC.BRepGProp import brepgprop_VolumeProperties
from OCC.TColStd import TColStd_SequenceOfAsciiString
from OCC.STEPControl import STEPControl_Reader
from OCC.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity

def calculate_bnd_box(bbox):
  xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
  x = xmax - xmin
  y = ymax - ymin
  z = zmax - zmin
  return {
    'volume': x * y * z,
    'x_length': x,
    'y_length': y,
    'z_length': z
  }

def analyze_file(filename):
  step_reader = STEPControl_Reader()
  status = step_reader.ReadFile(filename)
  result = None

  if status == IFSelect_RetDone:  # check status
    number_of_roots = step_reader.NbRootsForTransfer()
    ok = step_reader.TransferRoot(1)
    number_of_shapes = step_reader.NbShapes()
    if (number_of_roots > 1) or (number_of_shapes > 1):
      return { 'error': 'Cannot handle more than one shape in a file' }

    aResShape = step_reader.Shape(1)

    # Units
    length = TColStd_SequenceOfAsciiString()
    angles = TColStd_SequenceOfAsciiString()
    solid_angles = TColStd_SequenceOfAsciiString()
    step_reader.FileUnits(length, angles, solid_angles)
    pdb.set_trace()

    # bounding box
    bbox = Bnd_Box()
    deflection = 0.01
    BRepMesh_IncrementalMesh(aResShape, deflection)

    brepbndlib_Add(aResShape, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

    # pdb.set_trace()

    # Volume of solid
    props = GProp_GProps()
    brepgprop_VolumeProperties(aResShape, props)

    bounding_box = calculate_bnd_box(bbox)

    result = {'bounding_box_volume': bounding_box['volume'],
              'mesh_volume': props.Mass(),
              'mesh_surface_area': None,
              'cylinder_volume': None,
              'convex_hull_volume': None,
              'euler_number': None,
              'units': length.First().ToCString()}

  else:
    result = { 'error': 'Cannot read file' }

  return result

def usage():
  print 'volume.py -f <inputfile>'
  sys.exit(0)

def main(argv):
  try:
    opts, args = getopt.getopt(argv, "hf:", ["file="])
  except getopt.GetoptError:
    usage()

  filename = None
  for opt, arg in opts:
    if opt in ("-f", "--file"):
      filename = arg

  if filename != None:
    result = analyze_file(filename)
    print(json.dumps(result))
  else:
    result = { 'error': 'No filename provided' }
    print(json.dumps(result))

  sys.exit(0)

if __name__ == '__main__':
  main(sys.argv[1:])


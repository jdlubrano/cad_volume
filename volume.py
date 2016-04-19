import getopt
import json
import math
import pdb
import sys

from OCC.Bnd import Bnd_Box
from OCC.BRepMesh import BRepMesh_IncrementalMesh
from OCC.BRepBndLib import brepbndlib_Add
from OCC.GProp import GProp_GProps
from OCC.gp import *
from OCC.BRepGProp import brepgprop_VolumeProperties
from OCC.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCC.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.TColStd import TColStd_SequenceOfAsciiString
from OCC.STEPControl import STEPControl_Reader
from OCC.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Display.SimpleGui import init_display

def calculate_bnd_box(bbox):
  xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
  x = xmax - xmin
  y = ymax - ymin
  z = zmax - zmin
  return {
    'volume': x * y * z,
    'x_length': x,
    'y_length': y,
    'z_length': z,
    'x_min': xmin,
    'x_max': xmax,
    'y_min': ymin,
    'y_max': ymax,
    'z_min': zmin,
    'z_max': zmax
  }

def orient_cylinder(bounding_box):
  lengths = [ i for i in bounding_box.keys() if i.endswith('length') ]
  lengths_only = { key: bounding_box[key] for key in lengths }
  longest = max(lengths_only.values())
  longest_dimension = lengths_only.keys()[lengths_only.values().index(longest)]

  axis_direction = None
  if longest_dimension == 'x_length':
    axis_direction = gp_Dir(gp_XYZ(1,0,0))
    axis_origin = gp_Pnt(
      bounding_box['x_min'],
      (bounding_box['y_min'] + bounding_box['y_max']) / 2,
      (bounding_box['z_min'] + bounding_box['z_max']) / 2
    )
  elif longest_dimension == 'y_length':
    axis_direction = gp_Dir(gp_XYZ(0,1,0))
    axis_origin = gp_Pnt(
      (bounding_box['x_min'] + bounding_box['x_max']) / 2,
      bounding_box['y_min'],
      (bounding_box['z_min'] + bounding_box['z_max']) / 2
    )
  else:
    axis_direction = gp_Dir(gp_XYZ(0,0,1))
    axis_origin = gp_Pnt(
      (bounding_box['x_min'] + bounding_box['x_max']) / 2,
      (bounding_box['y_min'] + bounding_box['y_max']) / 2,
      bounding_box['z_min']
    )

  axis = gp_Ax2(axis_origin, axis_direction)

  # radius as the diagonal of bounding box
  dimensions = lengths_only.values()
  dimensions.sort()
  short_dimensions = dimensions[0:2]
  diag = math.sqrt(sum([i ** 2 for i in short_dimensions]))
  return axis, diag / 2, longest

def calculate_bnd_cyl(shape, bounding_box):
  # cylinder with diagonal of smaller face of bounding box
  axis, radius, height = orient_cylinder(bounding_box)
  cylinder = BRepPrimAPI_MakeCylinder(axis, radius, height)
  display, start_display, add_menu, add_function_to_menu = init_display()
  display.DisplayShape(shape, update=True)
  display.DisplayShape(cylinder.Shape(), update=True)
  start_display()
  pdb.set_trace()
  cut = BRepAlgoAPI_Cut(shape, cylinder)

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

    bounding_cylinder = calculate_bnd_cyl(aResShape, bounding_box)

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


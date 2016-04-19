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

def display_shapes(shapes):
  from OCC.Display.SimpleGui import init_display
  display, start_display, add_menu, add_function_to_menu = init_display()
  [display.DisplayShape(shape, update=True) for shape in shapes]
  start_display()

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

def pick_lengths(bounding_box):
  lengths = [ i for i in bounding_box.keys() if i.endswith('length') ]
  return { key: bounding_box[key] for key in lengths }

def get_longest_dimension(bounding_box):
  lengths_only = pick_lengths(bounding_box)
  longest = max(pick_lengths(bounding_box).values())
  return longest, lengths_only.keys()[lengths_only.values().index(longest)]

def second_longest_dimension(bounding_box):
  lengths_only = pick_lengths(bounding_box)
  lengths = lengths_only.values()
  lengths.sort()
  return lengths[1]

def determine_axis(bounding_box):
  l, longest_dimension = get_longest_dimension(bounding_box)
  axis_origin = None
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

  return gp_Ax2(axis_origin, axis_direction)

def orient_cylinder(bounding_box):
  # radius as the diagonal of bounding box
  height = get_longest_dimension(bounding_box)
  dimensions = lengths_only.values()
  dimensions.sort()
  short_dimensions = dimensions[0:2]
  diag = math.sqrt(sum([i ** 2 for i in short_dimensions]))
  return axis, longest

def cylinder_volume(axis, radius, height):
  return calculate_volume(cylinder.Shape()), calculate_volume(cut.Shape())

def cylinder_cut_excess_volume(shape, cylinder):
  cut = BRepAlgoAPI_Cut(shape, cylinder.Shape())
  return calculate_volume(cut.Shape())

def calculate_bounding_cylinder(shape, bounding_box):
  # cylinder with diagonal of smaller face of bounding box
  axis = determine_axis(bounding_box)
  height, longest_dimension = get_longest_dimension(bounding_box)

  cylinder = None
  cylinder_vol = 0
  cut_vol = 1
  radius = second_longest_dimension(bounding_box) / 2

  while cut_vol > 0.0:
    cylinder = BRepPrimAPI_MakeCylinder(axis, radius, height)
    cylinder_vol = calculate_volume(cylinder.Shape())
    cut_vol = cylinder_cut_excess_volume(shape, cylinder)
    radius = radius + 0.1

  return cylinder

def calculate_volume(shape):
  props = GProp_GProps()
  brepgprop_VolumeProperties(shape, props)
  return props.Mass()

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

    bounding_box = calculate_bnd_box(bbox)

    bounding_cylinder = calculate_bounding_cylinder(aResShape, bounding_box)

    result = {'bounding_box_volume': bounding_box['volume'],
              'mesh_volume': calculate_volume(aResShape),
              'mesh_surface_area': None,
              'cylinder_volume': calculate_volume(bounding_cylinder.Shape()),
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


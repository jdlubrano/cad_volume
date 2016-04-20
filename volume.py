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
  longest_length = lengths_only.keys()[lengths_only.values().index(longest)]
  return longest, longest_length[0]

def x_axis(bounding_box):
  axis_direction = gp_Dir(gp_XYZ(1,0,0))
  axis_origin = gp_Pnt(
    bounding_box['x_min'],
    (bounding_box['y_min'] + bounding_box['y_max']) / 2,
    (bounding_box['z_min'] + bounding_box['z_max']) / 2
  )
  return gp_Ax2(axis_origin, axis_direction)

def y_axis(bounding_box):
  axis_direction = gp_Dir(gp_XYZ(0,1,0))
  axis_origin = gp_Pnt(
    (bounding_box['x_min'] + bounding_box['x_max']) / 2,
    bounding_box['y_min'],
    (bounding_box['z_min'] + bounding_box['z_max']) / 2
  )
  return gp_Ax2(axis_origin, axis_direction)

def z_axis(bounding_box):
  axis_direction = gp_Dir(gp_XYZ(0,0,1))
  axis_origin = gp_Pnt(
    (bounding_box['x_min'] + bounding_box['x_max']) / 2,
    (bounding_box['y_min'] + bounding_box['y_max']) / 2,
    bounding_box['z_min']
  )
  return gp_Ax2(axis_origin, axis_direction)

def determine_axis(bounding_box):
  l, longest_dimension = get_longest_dimension(bounding_box)
  axis = None
  if longest_dimension == 'x_length':
    axis = x_axis(bounding_box)
  elif longest_dimension == 'y_length':
    axis = y_axis(bounding_box)
  else:
    axis = z_axis(bounding_box)

  return axis

def get_axis(dimension, bounding_box):
  axis_fn = dimension + '_axis'
  return globals()[axis_fn](bounding_box)

def cylinder_dict(cylinder, cut, radius, height):
  return {
      'radius': radius,
      'height': height,
      'cylinder_volume': calculate_volume(cylinder.Shape()),
      'cylinder': cylinder,
      'cut': cut,
      'cut_vol': calculate_volume(cut.Shape())
      }

def min_cylinder(height_dimension, shape, bounding_box):
  axis = get_axis(height_dimension, bounding_box)
  lengths = pick_lengths(bounding_box)
  height_length = height_dimension + '_length'
  height = bounding_box[height_length]
  radius = max([ value for key, value in lengths.iteritems() if key != height_length ]) / 2
  cylinder = BRepPrimAPI_MakeCylinder(axis, radius, height)
  cut = BRepAlgoAPI_Cut(shape, cylinder.Shape())
  return cylinder_dict(cylinder, cut, radius, height)

def try_min_cylinders(shape, bounding_box):
  x = min_cylinder('x', shape, bounding_box)
  y = min_cylinder('y', shape, bounding_box)
  z = min_cylinder('z', shape, bounding_box)

  bounding = [ i for i in [x,y,z] if i['cut_vol'] == 0.0 ]

  if bounding:
    min_volume = min([ i['cylinder_volume'] for i in bounding ])
    min_bounding = [ i for i in bounding if i['cylinder_volume'] == min_volume ]
    return min_bounding[0]
  else:
    return None

def smallest_max_cylinder(shape, bounding_box):
  # cylinder with diagonal of smaller face of bounding box
  height, longest_dimension = get_longest_dimension(bounding_box)
  longest_length = longest_dimension + '_length'

  lengths = pick_lengths(bounding_box)
  face_sides = [ value for key, value in lengths.iteritems() if key != longest_length ]
  radius = math.sqrt(sum([i ** 2 for i in face_sides])) / 2 # diagonal / 2

  axis = get_axis(longest_dimension, bounding_box)
  cylinder = BRepPrimAPI_MakeCylinder(axis, radius, height)
  cut = BRepAlgoAPI_Cut(shape, cylinder.Shape())
  return cylinder_dict(cylinder, cut, radius, height)

def calculate_bounding_cylinder(shape, bounding_box):
  cylinder = try_min_cylinders(shape, bounding_box)
  if cylinder:
    return cylinder
  else:
    return smallest_max_cylinder(shape, bounding_box)

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

    result = {'bounding_box': bounding_box,
              'bounding_box_volume': bounding_box['volume'],
              'mesh_volume': calculate_volume(aResShape),
              'mesh_surface_area': None,
              'bounding_cylinder': {
                'volume': bounding_cylinder['cylinder_volume'],
                'radius': bounding_cylinder['radius'],
                'height': bounding_cylinder['height']
              },
              'cylinder_volume': bounding_cylinder['cylinder_volume'],
              'convex_hull_volume': None,
              'euler_number': None,
              'units': length.First().ToCString().lower()}

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


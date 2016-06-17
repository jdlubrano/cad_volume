import getopt
import os
import sys

from OCC.StlAPI import StlAPI_Writer
from OCC.STEPControl import STEPControl_Reader
from OCC.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity

def usage():
  print('step_to_stl.py -i source -o dest')
  sys.exit(2)

def convert(source, dest):
  step_reader = STEPControl_Reader()
  status = step_reader.ReadFile(source)

  if status == IFSelect_RetDone:
    i = 1
    ok = False
    number_of_roots = step_reader.NbRootsForTransfer()

    while i <= number_of_roots and not ok:
      ok = step_reader.TransferRoot(i)
      i += 1

    if (not ok):
      return { 'error': 'Failed to find a suitable root for the STEP file' }

    shape = step_reader.Shape(1)
    output = os.path.abspath(dest)
    stl_ascii = False
    stl_writer = StlAPI_Writer()
    stl_writer.SetASCIIMode(stl_ascii)
    stl_writer.Write(shape, output)
    print "STL FILE: %s" % output

  else:
      print "Error, can't read file: %s" % './demo.stp'

def main(argv):
  try:
    opts, args = getopt.getopt(argv, "hi:o:", ["infile=", "outfile="])
  except getopt.GetoptError:
    usage()

  source = None
  dest = None
  for opt, arg in opts:
    if opt in ("-i", "--infile"):
      source = arg
    if opt in ("-o", "--outfile"):
      dest = arg

  if source != None and dest != None:
    convert(source, dest)
  else:
    usage()

  sys.exit(0)

if __name__ == '__main__':
  main(sys.argv[1:])


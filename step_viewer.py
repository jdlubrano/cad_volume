#! /Users/joel/miniconda2/bin/python

import sys

from OCC.STEPControl import STEPControl_Reader
from OCC.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Display.SimpleGui import init_display

def main(argv):
  step_reader = STEPControl_Reader()
  status = step_reader.ReadFile(argv[0])

  if status == IFSelect_RetDone:  # check status
      failsonly = False
      step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
      step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)

      number_of_roots = step_reader.NbRootsForTransfer()

      ok = False
      i = 1

      while not ok and i <= number_of_roots:
        ok = step_reader.TransferRoot(i)
        i += 1

      _nbs = step_reader.NbShapes()
      aResShape = step_reader.Shape(1)
  else:
      print("Error: can't read file.")
      sys.exit(0)

  display, start_display, add_menu, add_function_to_menu = init_display()
  display.DisplayShape(aResShape, update=True)
  start_display()

if __name__ == '__main__':
  main(sys.argv[1:])


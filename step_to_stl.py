import os
from OCC.StlAPI import StlAPI_Writer
from OCC.STEPControl import STEPControl_Reader
from OCC.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity

step_reader = STEPControl_Reader()
status = step_reader.ReadFile('./demo.stp')

if status == IFSelect_RetDone:
    ok = step_reader.TransferRoot(1)
    shape = step_reader.Shape(1)
    working_dir = os.path.split(__name__)[0]
    output_dir = os.path.abspath(working_dir)
    output = os.path.join(output_dir, 'demo.stl')
    stl_ascii = False
    stl_writer = StlAPI_Writer()
    stl_writer.SetASCIIMode(stl_ascii)
    stl_writer.Write(shape, output)
    print "STL FILE: %s" % output

else:
    print "Error, can't read file: %s" % './demo.stp'
    sys.exit(1)


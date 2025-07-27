import sys, pathlib
sys.path.append((pathlib.Path(__file__).parent).as_posix())

from main import airplane_sol

file = (pathlib.Path(__file__).parent.parent / "schematics" / "design.step").resolve().as_posix()
airplane_sol.export_cadquery_geometry(file, minimum_airfoil_TE_thickness = 0.001)

#!/bin/env python
import os
import argparse
import shutil
import pdb
import subprocess
import re

from pymatgen import Structure
from pymatgen.io.vasp.sets import MPStaticSet

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--structure', dest='structure',
                      help='POSCAR file of the structure.')
  args = parser.parse_args()

  struc = Structure.from_file(args.structure)
  # Prepare the vasp working directory
  working_path = os.getcwd()

  vasp_path = os.path.join(working_path, 'vasp_tmp')
  if not os.path.exists(vasp_path):
    os.makedirs(vasp_path)
  else:
    shutil.rmtree(vasp_path)
    os.makedirs(vasp_path)

  staticset = MPStaticSet(struc, force_gamma=True,
                          user_incar_settings={"ICHARG": 2})
  staticset.write_input(vasp_path)
  # chdir to vasp running directory
  os.chdir(vasp_path)
  subprocess.call("mpirun -np 10 vasp5.2-openmpi", shell=True)

if __name__ == "__main__":
  main()

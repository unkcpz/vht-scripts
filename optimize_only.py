#!/bin/env python

import argparse
import os
import shutil
import subprocess

from pymatgen import Structure
from pymatgen.io.vasp.sets import MPRelaxSet

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--structure', dest='structure',
                      help='POSCAR file of the structure.')
  args = parser.parse_args()

  struc = Structure.from_file(args.structure)
  working_path = os.getcwd()
  import random 
  import string
  rd_suffix = ''.join(random.choices(string.ascii_uppercase
                                     + string.digits, k=4))
  vasp_path = os.path.join(working_path, 'vasp_tmp_{0:}'.format(rd_suffix))
  if not os.path.exists(vasp_path):
    os.makedirs(vasp_path)
  else:
    shutil.rmtree(vasp_path)
    os.makedirs(vasp_path)

  relaxset = MPRelaxSet(struc, force_gamma=True,
                        user_incar_settings={"ISMEAR": 1, "SIGMA": 0.2})
  relaxset.write_input(vasp_path)
  os.chdir(vasp_path)
  subprocess.call("mpirun -np 10 vasp5.2-openmpi", shell=True)

  contcar = os.path.join(vasp_path, 'CONTCAR')
  dst = os.path.join(working_path, 'POSCAR_optimized')
  shutil.copyfile(contcar, dst)

if __name__ == "__main__":
  main()

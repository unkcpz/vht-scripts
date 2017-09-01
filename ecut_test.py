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

  l_ecut = list(range(400, 710, 10))
  toten = []
  for ecut in l_ecut:
    vasp_path = os.path.join(working_path, 'vasp_tmp')
    if not os.path.exists(vasp_path):
      os.makedirs(vasp_path)
    else:
      shutil.rmtree(vasp_path)
      os.makedirs(vasp_path)

    staticset = MPStaticSet(struc, force_gamma=True,
                            user_incar_settings={"ENCUT": ecut, "ISPIN": 1,
                                                 "LWAVE": 'FALSE', "ICHARG": 2,
                                                 "LVHAR": 'FALSE',
                                                 "LREAL": 'FALSE', "ISMEAR": 1, "SIGMA": 0.2},
                            user_kpoints_settings={"reciprocal_density": 64})
    staticset.write_input(vasp_path)
    # chdir to vasp running directory
    os.chdir(vasp_path)
    subprocess.call("mpirun -np 10 vasp5.2-openmpi", shell=True)

    # find energy total lines and the total energy
    regex = re.compile("energy\s+without\s+entropy\s*=\s*(\S+)\s+energy\(sigma->0\)\s+=\s+(\S+)")

    with open(os.path.join(vasp_path, 'OUTCAR')) as f:
      for line in f:
        found = regex.search(line)
        if found is not None:
          result = found.group(1)
    
    toten.append(float(result))
    # print("The energy for ENCUT = {0:4d} is {1:0.6f}\n\n\n".format(ecut, float(result)))

  # print to the stdout
  for ecut, energy in zip(l_ecut, toten):
    print("The energy for ENCUT = {0:4d} is {1:0.6f}".format(ecut, energy))
    
  # draw convert line using matplotlib
  import matplotlib
  matplotlib.use('Agg')
  import matplotlib.pyplot as plt
  fig = plt.figure()
  ax = fig.gca()
  ax.plot(l_ecut, toten)
  ax.grid()
  ax.set_ylabel('Total Energy (eV)')
  ax.set_xlabel('ENCUT (eV)')
  fig.savefig(os.path.join(working_path, 'conv_test_ENCUT.png'))

if __name__ == "__main__":
  main()

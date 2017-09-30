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

  stru = Structure.from_file(args.structure)
  # Prepare the vasp working directory
  working_path = os.getcwd()

  l_kp = range(20, 100, 10)
  toten = []
  for kp in l_kp:
    vasp_path = os.path.join(working_path, 'vasp_tmp')
    if not os.path.exists(vasp_path):
      os.makedirs(vasp_path)
    else:
      shutil.rmtree(vasp_path)
      os.makedirs(vasp_path)

    staticset = MPStaticSet(stru, force_gamma=True,
                            user_incar_settings={"ENCUT": 500, "ISPIN": 1,
                                                 "LWAVE": 'FALSE', "ICHARG": 2,
                                                 "LREAL": 'FALSE', "ISMEAR":0,
                                                 "EDIFF": 0.001, "NPAR": 5},
                            user_kpoints_settings={"reciprocal_density": kp})
    staticset.config_dict['POTCAR']['Cu'] = 'Cu'
    staticset.config_dict['POTCAR']['Si'] = 'Si'
    staticset.write_input(vasp_path)
    # chdir to vasp running directory
    os.chdir(vasp_path)
    subprocess.call("mpirun -np 10 vasp5.4.1-std", shell=True)

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
  for kp, energy in zip(l_kp, toten):
    print("The energy for K_Density = {0:4d} is {1:0.6f}".format(kp, energy))
    
  # draw convert line using matplotlib
  import matplotlib
  matplotlib.use('Agg')
  import matplotlib.pyplot as plt
  fig = plt.figure()
  ax = fig.gca()
  ax.plot(l_kp, toten)
  ax.grid()
  ax.set_ylabel('Total Energy (eV)')
  ax.set_xlabel('Reciprocal Density p/A^-3')
  fig.savefig(os.path.join(working_path, 'conv_test_KPOINT.png'))

if __name__ == "__main__":
  main()

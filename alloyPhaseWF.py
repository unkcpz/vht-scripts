#!/bin/env python

import argparse
import os
import shutil
import subprocess
import gzip
import time

from pymatgen import Structure
from pymatgen.io.vasp.sets import MPRelaxSet, MPStaticSet
from pymatgen.io.vasp.outputs import Vasprun

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--structure', dest='structure',
                      help='POSCAR file of the structure.')
  parser.add_argument('-c', '--comment-file-name', dest='comment',
                      help='File name of comment')
  args = parser.parse_args()

  struc = Structure.from_file(args.structure)
  working_path = os.getcwd()

  # comment file stay in the working path and 
  # initiat file with head if not exist
  comment_file = os.path.join(working_path, args.comment)
  if not os.path.isfile(comment_file):
    f = open(comment_file, 'w')
    f.write('POSCAR_FILE, formular, ion_conv, ele_conv, final_energy, out_dir\n')
    f.close()

  import random 
  import string
  rd_suffix = ''.join(random.choices(string.ascii_uppercase
                                     + string.digits, k=6))
  vasp_path = os.path.join(working_path, 'vasp_tmp_{0:}'.format(rd_suffix))
  if not os.path.exists(vasp_path):
    os.makedirs(vasp_path)
  else:
    shutil.rmtree(vasp_path)
    os.makedirs(vasp_path)

  vasp_relax_path = os.path.join(vasp_path, 'relax')
  relaxset = MPRelaxSet(struc, force_gamma=True,
      user_incar_settings={"ISMEAR": 0, "SIGMA": 0.05, "NPAR": 4, "NSW": 60,
                           "ISPIN": 1, "LREAL": ".FALSE.", "PREC": "NORMAL",
                           "KSPACING": 0.4, "EDIFF": 0.0001, "ENCUT": 300})
  relaxset.config_dict['POTCAR']['Cu'] = 'Cu'
  relaxset.config_dict['POTCAR']['Ti'] = 'Ti'
  relaxset.config_dict['POTCAR']['V'] = 'V'
  relaxset.write_input(vasp_relax_path)
  os.chdir(vasp_relax_path)
  kfile = os.path.join(vasp_relax_path, "KPOINTS")
  os.remove(kfile)
  subprocess.call("mpirun -np 20 vasp5.4.1-std", shell=True)
  time.sleep(10)

  # Extract the output information
  vasprun_relax = os.path.join(vasp_relax_path, 'vasprun.xml')
  out_relax = Vasprun(vasprun_relax)

  # RECORD THE INPUT FILE AND IS IONIC CONVERGED
  fn = args.structure
  ion_conv = out_relax.converged_ionic
  # if not converged also put energy
  energy = out_relax.final_energy

  print("fn is {0:}, ion_conv is {1:}".format(fn, ion_conv))

  ###########################################
  # Done: add all files to compress
  ###########################################
  f_list = os.listdir(vasp_relax_path)
  for f in f_list:
    fname = os.path.join(vasp_relax_path, f)
    with open(fname, 'rb') as f_in:
      with gzip.open("{}{}".format(fname, '.relax.gz'), 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
        os.remove(fname)
  

  ###########################################
  # CALCULATING THE STATIC ENERGY
  ###########################################
  vasp_static_path = os.path.join(vasp_path, 'static')
  stru_static = out_relax.final_structure
  staticset = MPStaticSet(struc_static, force_gamma=True,                                            
      user_incar_settings={"ICHARG": 2, "NPAR": 4, "NELM": 40, "LREAL": ".FALSE.", 
                           "ISPIN": 1, "KSPACING":0.4, "EDIFF": 0.0001,
                           "ENCUT": 350, "ISMEAR": 0, "SIGMA": 0.05})                                  
  staticset.write_input(vasp_static_path)
  staticset.config_dict['POTCAR']['Cu'] = 'Cu'
  staticset.config_dict['POTCAR']['Ti'] = 'Ti'
  staticset.config_dict['POTCAR']['V'] = 'V'
  os.chdir(vasp_static_path)
  kfile = os.path.join(vasp_static_path, "KPOINTS")
  os.remove(kfile)
  subprocess.call("mpirun -np 20 vasp5.4.1-std", shell=True)
  time.sleep(10)
  
  vasprun_static = os.path.join(vasp_static_path, 'vasprun.xml')
  out_static = Vasprun(vasprun_static)

  formula = out_static.final_structure.formula
  elec_conv = out_static.converged_electronic
  energy = out_static.final_energy
 
  with open(comment_file, 'a') as f:
    f.write("{0:}, {1:}, {2:}, {3:}, {4:5f}, {5:}\n".format(fn, formula, ion_conv,
                                                            elec_conv, energy, vasp_path))

  ###########################################
  # Done: add all files to compress
  ###########################################
  f_list = os.listdir(vasp_static_path)
  for f in f_list:
    fname = os.path.join(vasp_static_path, f)
    with open(fname, 'rb') as f_in:
      with gzip.open("{}{}".format(fname, '.static.gz'), 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
        os.remove(fname)


if __name__ == "__main__":
  main()

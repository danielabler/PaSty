import os
from pasty.parametric_study import ParametricStudy
from pasty import config
import pandas as pd

ps = ParametricStudy(config.test_folder_structure_dir)
ps.reload_state()
#ps.collect_results(verbose=True)
#ps.create_summary_doc()

experiment = {"D_WM":      {'range' : [0.05,0.20], "stepsize" : 0.01},
              "rho_WM":    {'range' : [0.02,0.20], "stepsize" : 0.01},
              "coupling":  {'range' : [0.02,0.20], "stepsize" : 0.01}}


# new combinations
new_D_WM     = [0.18, 0.2, 0.22, 0.24, 0.26, 0.30]
new_rho_WM   = [0.18, 0.2, 0.22, 0.24, 0.26, 0.30]
new_coupling = [0.18, 0.2, 0.22, 0.24, 0.26, 0.30]
param_values = [new_D_WM, new_rho_WM, new_coupling]
param_names  = ["D_WM", "rho_WM", "coupling"]


ps.extend_study(param_names, param_values, generate_folders=True)

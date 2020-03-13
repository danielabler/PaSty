import os
from pasty.parametric_study import ParametricStudy
from pasty import config

experiment = {"D_WM":      {'range' : [0.05,0.20], "stepsize" : 0.1},
              "rho_WM":    {'range' : [0.02,0.20], "stepsize" : 0.1},
              "coupling":  {'range' : [0.02,0.20], "stepsize" : 0.1}}

ps = ParametricStudy(config.test_folder_structure_dir, experiment)
ps.create_parameter_table()
ps.generate_simulation_folder_structure(with_param_files=True,
                                        with_template_files=False,
                                        exist_ok=True, verbose=True)
ps.save_state()
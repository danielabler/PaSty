import os
from pasty.parametric_study import ParametricStudy
from pasty import config


experiment = {"D_WM":      {'range' : [0.05,0.20], "stepsize" : 0.05},
              "rho_WM":    {'range' : [0.02,0.20], "stepsize" : 0.04},
              "coupling":  {'range' : [0.02,0.20], "stepsize" : 0.04}}

path_glimslib = '/glimslib'
path_code_experiment = '/code'
max_cpu_time = "10:00:00"
path_singularity = '/singularity/fenics'

replacement_dict = {'VAR_MAX_CPU_TIME' : max_cpu_time,
                    'VAR_PATH_CODE_MAIN' : path_glimslib,
                    'VAR_PATH_CODE_EXPERIMENT' : path_code_experiment,
                    'VAR_PATH_SINGULARITY_IMAGE' : path_singularity,
}


ps = ParametricStudy(config.test_folder_structure_dir, experiment)
ps.config['name'] = 'test_study'
ps.create_parameter_table()
ps.generate_simulation_folder_structure(with_param_files=True,
                                        with_template_files=False,
                                        exist_ok=True, verbose=True)
ps.submit_job(config.path_to_slurm_test_template, job_params=replacement_dict)
ps.save_state()

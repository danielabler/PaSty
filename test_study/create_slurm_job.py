from pasty import slurm_interface as si
from pasty import config
import os

path_to_job_file = os.path.join(config.output_dir, 'job.sh')

job_name   = 'job_array'
path_code_experiment = '/code'
experiment_base_dir = '/sim/experiment'
max_cpu_time = "10:00:00"
path_singularity = '/singularity/fenics'

replacement_dict = {'VAR_MAX_CPU_TIME' : '10:00:00',
                    'VAR_SUBMISSION_NAME' : job_name,
                    'VAR_JOB_ARRAY_RANGE' : '1-10',
                    'VAR_SLURM_ERROR_OUT' : os.path.join(experiment_base_dir, 'slurm_output_error.out'),
                    'VAR_SLURM_OUT' : os.path.join(experiment_base_dir, 'slurm_output.out'),
                    'VAR_PATH_CODE_MAIN' : '/path_to_code',
                    'VAR_PATH_CODE_EXPERIMENT' : path_code_experiment,
                    'VAR_SIM_BASE_DIR' : experiment_base_dir,
                    'VAR_PATH_SINGULARITY_IMAGE' : path_singularity,
}

si.create_jobfile_from_template(replacement_dict, config.path_to_slurm_test_template, path_to_job_file)
si.submit_job(path_to_job_file)
"""Provides path settings for PaSty"""

import os

base_path = os.path.join(os.path.dirname(__file__), '..')

output_dir                              = os.path.join(base_path,  'output')
if not os.path.exists(output_dir):
    os.mkdir(output_dir)
test_folder_structure_dir               = os.path.join(output_dir, 'test_folder_structure')

test_study_dir                          = os.path.join(base_path, 'test_study')
slurm_template_dir                      = os.path.join(test_study_dir, 'slurm_template')
path_to_slurm_test_template             = os.path.join(slurm_template_dir, 'slurm_array_job_test_template.sh')
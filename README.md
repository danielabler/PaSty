# PaSty 

PaSty is a library for parametric simulation studies.
It provides a class and simple helper functions that support the following workflow steps:

- Initialization:
    - Generation of parameter combinations from user-defined parameters and ranges.
    - Creation of folder structure, with `simulation` subfolders for each parameter combination.
    - Generation and submission of [slurm](https://slurm.schedmd.com) *array job* from custom job-template.
- Postprocessing:
    - Generation and submission of additional jobs.
    - Resubmission of computations for parameter combinations with missing results.
- Analysis:
    - Report generation by redefining `ParametricStudy.latex_experiment_summary`, see this [example](https://github.com/danielabler/PaSty/blob/master/test_study/analyse_parametric_study.py).
    - Collection of analysis results for each parameter combination.

Since all functionalities are independent of the actual computations to be performed, 
this should be fairly flexible and able to provide a scaffold for a large range of usage scenarios.
 
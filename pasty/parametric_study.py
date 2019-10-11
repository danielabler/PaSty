import numpy as np
import itertools
import pandas as pd
import pathlib as pl
import pickle
import json
import shutil
from datetime import datetime
import os

from pasty import slurm_interface as si
from pasty import images_to_latex as itl

class ParametricStudy():

    def __init__(self, base_path, problem=None, config=None):
        """
        Expects dictionaries such as:

        (1) problem

                 problem = {"param_1": {'range' : [0,10], "steps" : 4},
                            "param_2": [1,4,5,2],
                            "param_3": {'range' : [0,10], "stepsize" : 4}}

            possible specifications: {range, steps}, {range, stepsize}, [list]
        """
        self.base_dir = base_path
        self.config =   {'base_dir'     : base_path,
                         'name'         : 'parametric_study',
                         'sim_dir'      : 'simulations',
                         'analysis_dir' : 'analysis',
                         'jobs_dir'     : 'slurm_jobs',
                         'exp_name_pre' : 'sim',
                         'exp_name_post': None,
                         'id_format'    : '%03d',
                         'param_file_name' : 'params.py',
                         'template_source_folder' : None,
                         'template_target_folder' : 'all',
                         'results_file_name' : os.path.join('summary', 'simulation_parameterset_summary.pkl'),
                         'results_table_file_name': 'results_summary',
                         'parameter_table_file_name': 'parameter_summary',
                         'jobs_table_file_name': 'slurm_jobs_summary',
                         'summary_doc_dir' : "summary_doc"}

        self.path_to_state_file = pl.Path(base_path).joinpath('experiment_state.pkl')

        if config:
            self.config.update(config)
        if problem:
            self.problem_orig = problem
            self._expand_problem()
        if self.path_to_state_file.exists():
            print("-- Statefile discovered in '%s'---\n" %self.path_to_state_file.parent)
            print("   You can reload the status of this experiment by calling 'ps.reload_state()'")

    def save_state(self):
        state_dict = {'problem_orig' : self.problem_orig,
                      'problem' : self.problem,
                      'config' : self.config,
                      'parameter_table' : self.parameter_table}
        if hasattr(self, 'results_table'):
            state_dict['results_table'] = self.results_table
        if hasattr(self, 'job_table'):
            state_dict['job_table'] = self.job_table
        with self.path_to_state_file.open(mode='wb') as handle:
            pickle.dump(state_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print("-- Saved current state to '%s'"%self.path_to_state_file)

    def reload_state(self):
        if self.path_to_state_file.exists():
            state_dict = pickle.load(self.path_to_state_file.open(mode='rb'))
            for name, item in state_dict.items():
                setattr(self, name, item)
            print("-- Reloaded statem from '%s'."%self.path_to_state_file)
        else:
            print("-- Statefile does not exist. Cannot reload")

    def _expand_problem(self):
        exp_problem_dict = {}
        for param, spec in self.problem_orig.items():
            spec_dict = {}
            if isinstance(spec, list) or isinstance(spec, np.ndarray):
                values = np.array(spec)
            elif isinstance(spec, dict):
                values = self._range_to_sample_points(spec)
                spec_dict.update(spec)
            else:
                print("Cannot work with input of type '%s'"%type(spec))
                values = np.ones(1)*np.nan
            spec_dict['values'] = values
            exp_problem_dict[param] = spec_dict
        self.problem = exp_problem_dict

    def _range_to_sample_points(self, spec_dict):
        values = np.ones(1)*np.nan
        if 'range' in spec_dict.keys() and 'steps' in spec_dict.keys():
            values = np.linspace(spec_dict['range'][0], spec_dict['range'][1], spec_dict['steps'])
        elif 'range' in spec_dict.keys() and 'stepsize' in spec_dict.keys():
            values = np.arange(spec_dict['range'][0], spec_dict['range'][1], spec_dict['stepsize'])
        else:
            print("Requires keywords 'range' and 'steps'/'stepsize'")
        return values

    def create_parameter_table(self):
        param_names = self.problem.keys()
        param_values= [ param_dict['values'] for param_dict in self.problem.values()]

        cart_prod_values = itertools.product(*param_values)
        param_df = pd.DataFrame(columns=param_names)
        for i, vars in enumerate(cart_prod_values):
            param_df.loc[i] = vars
        self.parameter_table = param_df
        # -- save
        p_analysis = self.create_analysis_dir_path()
        p_parameter_summary_file = p_analysis.joinpath(self.config['parameter_table_file_name'])
        self.save_table(param_df, p_parameter_summary_file)
        return param_df

    def create_path(self, exp_id=None, path_type='simulation', create=False, exist_ok=False):
        if path_type == 'simulation':
            subpath = self.config['sim_dir']
        elif path_type == 'analysis':
            subpath = self.config['analysis_dir']
        elif path_type == 'jobs':
            subpath = self.config['jobs_dir']
        p = pl.Path(self.base_dir).joinpath(subpath)

        if exp_id is not None:
            exp_name = self.config['id_format'] % exp_id
            if self.config['exp_name_pre'] is not None:
                exp_name = self.config['exp_name_pre'] + '_' + exp_name
            if self.config['exp_name_post'] is not None:
                exp_name = exp_name + '_' + self.config['exp_name_post']
            p = p.joinpath(exp_name)

        if create:
            p.mkdir(parents=True, exist_ok=exist_ok)
        return p

    def generate_simulation_folder_structure(self, with_param_files=True,
                                                   with_template_files=True,
                                                   exist_ok=False, verbose=False):
        print("-- Generating simulation file structure in '%s'"%self.base_dir )
        if not hasattr(self, 'parameter_table'):
            self.create_parameter_table()
        print(self.parameter_table)
        for idx, row in self.parameter_table.iterrows():
            # create dir
            p = self.create_path(exp_id=idx, path_type='simulation', create=True, exist_ok=exist_ok)
            if verbose:
                print("  - ID %03d: Creating folder '%s'"%(idx, p))
            # add path to parameter_table
            self.parameter_table.loc[idx,'simulation_path'] = p.as_posix()
            # write parameter files
            if with_param_files:
                path_param_json = p.joinpath(self.config['param_file_name'])
                self.write_parameter_file(idx, path_param_json)
            # copy content of template folder
            if self.config['template_source_folder'] and with_template_files:
                if self.config['template_target_folder'] =='all':
                    if verbose:
                        print("  - ID %03d: Copying files from '%s'" % (idx, self.config['template_source_folder']))
                    p_template = pl.Path(self.config['template_source_folder'])
                    self.copy_files(p_template, p)
        if self.config['template_source_folder'] and self.config['template_target_folder'] != 'all' and with_template_files:
            p_template_source = pl.Path(self.config['template_source_folder'])
            p_template_target = pl.Path(self.config['template_target_folder'])
            if verbose:
                print("  - Copying files from '%s' to '%s'" % (p_template_source, p_template_target))
            self.copy_files(p_template_source, p_template_target)


    def get_parameters(self, exp_id):
        params = self.parameter_table.loc[exp_id, self.problem.keys()]
        return params

    def write_parameter_file(self, exp_id, path):
        params = self.get_parameters(exp_id)
        # write as json
        path.write_text(params.to_json())

    def create_path_parameter_file(self, exp_id):
        p = self.create_path(exp_id, path_type='simulation').joinpath(self.config['param_file_name'])
        return p

    def get_parameters_from_parameter_file(self, exp_id):
        p = self.create_path_parameter_file(exp_id)
        param_dict = json.loads(p.read_text())
        return param_dict

    def copy_files(self, source_dir, target_dir, pattern='*'):
        for file in source_dir.glob(pattern):
            print(file)
            shutil.copy(str(file), str(target_dir))

    def create_path_results_file(self, exp_id):
        p = self.create_path(exp_id, path_type='simulation').joinpath(self.config['results_file_name'])
        return p

    def create_analysis_dir_path(self):
        p_analysis = pl.Path(self.base_dir).joinpath(self.config['analysis_dir'])
        p_analysis.mkdir(parents=True, exist_ok=True)
        return p_analysis

    def save_table(self, dataframe, base_path):
        path_pkl = str(base_path)+'.pkl'
        path_xls = str(base_path) + '.xls'
        path_csv = str(base_path) + '.csv'
        dataframe.to_excel(path_xls)
        dataframe.to_pickle(path_pkl)
        dataframe.to_csv(path_csv)
        print("-- Saving table '%s'"%path_xls)

    def extend_study(self, param_names, params_values, generate_folders=False):
        cart_prod_values = itertools.product(*params_values)
        param_df_new = pd.DataFrame(columns=param_names)
        for i, vars in enumerate(cart_prod_values):
            param_df_new.loc[i] = vars
        # merge existing with new
        param_df_merged = self.parameter_table.merge(param_df_new, on=param_names, how="outer", suffixes=('', '_tmp'))
        #param_df_merged = param_df_merged.drop('simulation_path_tmp', axis=1)
        # assign to self.parameter_table & save
        print("Updating parameter table")
        self.parameter_table = param_df_merged
        p_analysis = self.create_analysis_dir_path()
        p_parameter_summary_file = p_analysis.joinpath(self.config['parameter_table_file_name'])
        self.save_table(param_df_merged, p_parameter_summary_file)

        if generate_folders:
            self.generate_simulation_folder_structure(exist_ok=True, verbose=True)
        self.save_state()

    def collect_results(self, verbose=False):
        print("-- Trying to assemble results.")
        results_df = pd.DataFrame()
        for idx, row in self.parameter_table.iterrows():
            p_results_file = self.create_path_results_file(idx)
            if p_results_file.exists():
                if verbose:
                    print("  - id %04d: exists"%idx)
                try:
                    results_dict = pickle.load(p_results_file.open(mode='rb'))
                    results_dict['sim_name'] = 'sim_%04d'%idx
                    results_series = pd.Series(results_dict, name=idx)
                    results_df = results_df.append(results_series)
                except:
                    print(p_results_file.as_posix())
                    results_df_tmp = pd.read_pickle(p_results_file.as_posix())
                    results_df_tmp['sim_name'] = 'sim_%04d'%idx
                    results_df = results_df.append(results_df_tmp, ignore_index=True)
            else:
                if verbose:
                    print("  - id %03d: missing (%s)" % (idx,p_results_file))
                results_series = pd.Series(name=idx)
                results_series['sim_name'] = 'sim_%04d'%idx
                results_df = results_df.append(results_series)
        self.results_table = results_df
        #-- save
        p_analysis = self.create_path(path_type='analysis', create=True, exist_ok=True)
        p_results_summary_file = p_analysis.joinpath(self.config['results_table_file_name'])
        self.save_table(results_df, p_results_summary_file)

    def create_datetime_stamped_path(self, basepath, filename, file_ext):
        date_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        name = filename + '_' + date_time_str + file_ext
        p = pl.Path(basepath).joinpath(name)
        return p

    def submit_job(self, path_to_template, job_params=None):
        sim_dir = self.create_path(path_type='simulation')
        jobs_dir= self.create_path(path_type='jobs', create=True, exist_ok=True)
        params = {'VAR_SIM_BASE_DIR' : sim_dir,
                   'VAR_SLURM_ERROR_OUT': jobs_dir.joinpath('slurm_output_error.out').as_posix(),
                   'VAR_SLURM_OUT': jobs_dir.joinpath('slurm_output.out').as_posix(),
                   'VAR_SUBMISSION_NAME': self.config['name']}
        if job_params is not None:
            params.update(job_params)
        # create job file
        p_job_file = self.create_datetime_stamped_path(self.create_path(path_type='jobs'),'job','.sh')
        si.create_jobfile_from_template(params, pl.Path(path_to_template).as_posix(), p_job_file.as_posix())
        # submit job
        job_id = si.submit_job(p_job_file.as_posix(), ['submit', 'ppx'])
        # append to job submission dict
        submission_dict = {'submission_time' : datetime.now(), 'job_file' : p_job_file, 'job_id' : job_id}
        if not hasattr(self, 'job_table'):
            self.job_table = pd.DataFrame()
        self.job_table = self.job_table.append(submission_dict, ignore_index=True)
        p_jobs_file = jobs_dir.joinpath(self.config['jobs_table_file_name'])
        self.save_table(self.job_table, p_jobs_file)
        return job_id

    def submit_array_job(self, path_to_template, job_params=None, array_range='all', n_concurrent=None):
        if array_range=='all':
            n_start = self.parameter_table.index[0]
            n_end = self.parameter_table.index[-1]
            array_range = "%i-%i"%(n_start, n_end)
        if n_concurrent is not None:
            concurrency_str = "%%%i"%n_concurrent
            array_range = array_range+concurrency_str
        jobs_dir = self.create_path(path_type='jobs', create=True, exist_ok=True)
        params = {"VAR_JOB_ARRAY_RANGE" : array_range,
                  'VAR_SLURM_OUT': jobs_dir.joinpath('slurm_output_%A_%a.out').as_posix(),
                  'VAR_SLURM_ERROR_OUT': jobs_dir.joinpath('slurm_output_error_%A_%a.out').as_posix()
                  }
        if job_params is not None:
            params.update(job_params)
        job_id = self.submit_job(path_to_template, params)
        return job_id

    def submit_array_job_missing(self, path_to_template, job_params=None, n_concurrent=None,
                                 results_col_name='relative_error_D_WM', batch_size=100):
        results = self.results_table
        if results_col_name is not None:
            if results_col_name in results.columns:
                no_results = results[results[results_col_name].isna()]
            else:
                no_results = results
            indices = [str(index) for index in no_results.index]
            if len(indices)==0:
                print("Nothing to submit")
                job_id = None
            else:
                while len(indices) > 0:
                    if len(indices) > batch_size:
                        batch = indices[:batch_size]
                        indices = indices[batch_size:]
                    else:
                        batch = indices
                        indices = []
                    array_range = ",".join(batch)
                    job_id = self.submit_array_job(path_to_template, job_params, array_range=array_range, n_concurrent=n_concurrent)
        else:
            job_id = self.submit_array_job(path_to_template, job_params, array_range='all', n_concurrent=n_concurrent)
        return job_id

    def latex_experiment_summary(self, doc, exp_id, results):
        doc.addLine("%========================================== \n")
        doc.addLine("\\begin{frame} \n")
        doc.addLine("\\frametitle{Configuration %03d} \n" % (exp_id))
        doc.addLine("\\centering \n")
        #self.addImage(path_to_image, image_options)
        doc.addLine("This is a template...")
        doc.addLine("Define report by overwriting this function for specific experiment.")
        doc.addLine("\\end{frame} \n")
        doc.addLine("%========================================== \n")

    def latex_study_information(self, doc, **kwargs):
        doc.addLine("%========================================== \n")
        doc.addLine("\\begin{frame} \n")
        doc.addLine("\\frametitle{Study Overview} \n")
        doc.addLine("\\centering \n")
        doc.addLine("This is a template...")
        doc.addLine("Define report by overwriting this function for specific experiment.")
        doc.addLine("\\end{frame} \n")
        doc.addLine("%========================================== \n")

    def create_summary_doc(self, summary_creation_function=None, summary_type=None, **kwargs):
        if not hasattr(self, 'results_table'):
            self.collect_results()
        p_doc = self.create_path(exp_id=None, path_type='analysis', create=True, exist_ok=True)
        p_doc = p_doc.joinpath(self.config['summary_doc_dir'], 'summary.tex')

        doc_properties = {"title"    : self.config['name'].replace("_", " "),
                          "subtitle" : "Summary",
                          "author"   : "",
                          "date"     : "\\today",
                          "institute": ""}
        doc = itl.LatexDoc(doc_properties)
        doc.addTitlePage()
        self.latex_study_information(doc, **kwargs)
        for idx, row in self.results_table.iterrows():
            doc.addLine("\\section{Configuration %03d} \n" % (idx))
            if summary_creation_function is not None:
                summary_creation_function(doc, idx, row, **kwargs)
            else:
                self.latex_experiment_summary(doc, idx, row, summary_type, **kwargs)

        doc.writeDoc(p_doc)
        doc.compile(n_times=3)

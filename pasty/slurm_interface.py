import subprocess, shlex
import socket
import pandas as pd

def replaceTextInFile(replacement_dict, path_to_input_file, path_to_output_file):
    with open(path_to_input_file) as infile, open(path_to_output_file, 'w') as outfile:
        for line in infile:
            for src, target in replacement_dict.items():
                line = line.replace(src, target)
            outfile.write(line)

def create_jobfile_from_template(replacement_dict, template_file, output_file):
    replacement_dict_str = {name : str(value) for name, value in replacement_dict.items()}
    replaceTextInFile(replacement_dict_str, template_file, output_file)
    return output_file

def submit_job(path_to_job_file, expected_hostname='submit'):
    hostname = socket.gethostname()
    if isinstance(expected_hostname, list):
        bool_list = [hostname.startswith(name) for name in expected_hostname]
        can_submit = any(bool_list)
    else:
        can_submit = hostname.startswith(expected_hostname)
    if can_submit:
        output = subprocess.check_output(['sbatch', path_to_job_file])
        job_id = output.split()[3]
    else:
        print("Cannot submit job on host '%s'" % hostname)
        job_id = 'dummy_id'
    print("Submitted file '%s' as job '%s'" % (path_to_job_file, job_id))
    return job_id

def cml_output_to_pandas(output, header=None):
    table = [line.strip().split() for line in output]
    if header == None:
        header = map(str.lower, table.pop(0))
    if not len(table) == 0:
        if len(table[0]) > 0:
            table_pd = pd.DataFrame(table, columns=header).dropna(axis=0)
        else:
            table_pd = pd.DataFrame(columns=header)
    else:
        table_pd = pd.DataFrame(columns=header)
    return table_pd

def check_jobs(user):
    command_string = 'squeue --user=%s' % user
    args = shlex.split(command_string)
    output = subprocess.check_output(args)
    table_pd = cml_output_to_pandas(output.split('\n'))
    return table_pd

def check_job_jobid_running(job_id):
    command_string = 'scontrol show jobid %s' % str(job_id)
    args = shlex.split(command_string)
    try:
        output = subprocess.check_output(args)
        job_stat_dict = {item.split('=')[0]: item.split('=')[1] for item in output.split()}
        return job_stat_dict
    except:
        print("Process id='%s' seems to have finished." % str(job_id))
        return {'JobState': 'invalid'}

def check_jobs_past(start_time, end_time=None):
    if end_time is None:
        command_string = 'sacct --starttime=%s' % str(start_time.date())
    else:
        command_string = 'sacct --starttime=%s --endtime=%s' % str(start_time.date(), end_time.date())
    args = shlex.split(command_string)
    try:
        output = subprocess.check_output(args).split('\n')
        output_filtered = [line for line in output if not '.ba+' in line]
        table_pd = cml_output_to_pandas(output_filtered)
        return table_pd
    except:
        print("Cannot process output'")

#!/bin/sh
#================================================================
#  QUEUE SETTINGS
#================================================================
#--- EMAIL ADDRESS
#SBATCH --mail-user=name@org.org
#SBATCH --mail-type=end,fail
#--- Mandatory resources (h_cpu=hh:mm:ss)
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=5G
#SBATCH --tmp=2G
#SBATCH --time=VAR_MAX_CPU_TIME
#--- JOB
#SBATCH --job-name=VAR_SUBMISSION_NAME
#SBATCH --array=VAR_JOB_ARRAY_RANGE
#SBATCH --error=VAR_SLURM_ERROR_OUT
#SBATCH --output=VAR_SLURM_OUT

#================================================================
#  GENERAL PATH SETTINGS
#================================================================
$SIMULATION_DIR=VAR_SIM_BASE_DIR
TASK_ARRAY_ID_INT=$(($SLURM_ARRAY_TASK_ID+0))
SIMULATION_SUB_DIR=$(printf "sim_%03d" $TASK_ARRAY_ID_INT)
PATH_SIM_DIR=$SIMULATION_DIR/$SIMULATION_SUB_DIR

$PATH_CODE_MAIN=VAR_PATH_CODE_MAIN
$PATH_CODE_EXPERIMENT=VAR_PATH_CODE_EXPERIMENT
$PATH_SINGULARITY_IMAGE=VAR_PATH_SINGULARITY_IMAGE

#================================================================
#  ENVIRONMENT VARIABLES --  SINGULARITY
#================================================================
export SINGULARITYENV_PATH_SIM_DIR=$PATH_SIM_DIR


#================================================================
#  RUN
#================================================================
cd $PATH_CODE_MAIN
echo "==== Step 1"
singularity exec -e $PATH_SINGULARITY_IMAGE python3 $PATH_CODE_EXPERIMENT/sim_01.py
echo "==== Step 2"
singularity exec -e $PATH_SINGULARITY_IMAGE python3 $PATH_CODE_EXPERIMENT/sim_02.py

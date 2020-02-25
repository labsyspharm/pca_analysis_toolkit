#!/bin/bash
#SBATCH --job-name=crop
#SBATCH -n 1                # Number of cores
#SBATCH -N 1                # Ensure that all cores are on one machine
#SBATCH -t 0-00:30          # Runtime in D-HH:MM, minimum of 10 minutes
#SBATCH -p short   # Partition to submit to
#SBATCH --mem 64G           # Memory pool for all cores (see also --mem-per-cpu)
#SBATCH -o out.txt  # File to which STDOUT will be written, %j inserts jobid
#SBATCH -e error.txt  # File to which STDERR will be written, %j inserts jobid

module load gcc/6.2.0 python/3.7.4
source ../virtualenv/bin/activate
python main.py

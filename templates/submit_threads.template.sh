#/bin/bash
#PBS -l select=1
#PBS -l walltime={walltime}
#PBS -A {project}
#PBS -q {queue}
#PBS -l filesystems={filesystems}
#PBS -N {job_name}


NUM_NODES=$(cat $PBS_NODEFILE | wc -l)
RANKS_PER_NODE=1
NRANKS=$(( $NUM_NODES * $RANKS_PER_NODE ))
echo [$SECONDS] running $NRANKS ranks on $NUM_NODES nodes
THREADS={threads}
RANKS={ranks}
echo [$SECONDS] passed threads=$THREADS  ranks=$RANKS

{executable}


#/bin/bash
#PBS -l select={num_nodes:d}
#PBS -l walltime={walltime}
#PBS -A {project}
#PBS -q {queue}
#PBS -l filesystems={filesystems}
#PBS -N {job_name}

cd $PBS_O_WORKDIR

NUM_NODES=$(cat $PBS_NODEFILE | wc -l)
RANKS_PER_NODE={ranks_per_node:d}
NRANKS=$(( $NUM_NODES * $RANKS_PER_NODE ))
echo [$SECONDS] running $NRANKS ranks on $NUM_NODES nodes
echo [$SECONDS] passed threads={threads:d}  ranks={ranks:d}
echo [$SECONDS] PWD=$PWD


KOKKOS_VERSION=3.7.02
KOKKOS_ARCH=Kokkos_ARCH_AMPERE80
KOKKOS_BUILD=Release

KOKKOS_STRING=kokkos-$KOKKOS_VERSION/$KOKKOS_ARCH/$KOKKOS_BUILD

PROJ_PATH=/lus/grand/projects/datascience/parton
KOKKOS_PATH=$PROJ_PATH/kokkos/$KOKKOS_STRING
PEPPER_PATH=/home/parton/git/pepper/build/$KOKKOS_STRING

source $KOKKOS_PATH/setup.sh
module load cray-hdf5-parallel

export PEPPER_DATA_PATH=$PROJ_PATH/pepper_data

cat << EOF > pepper_config.ini
[main]
process = {process}
batch_size = {threads:d}
n_batches = {n_batches:d}
seed = 12345
collision_energy = 14000
verbosity = info

[phase_space]
use_cached_results = true
cache_path = $PROJ_PATH/pepper_cache
# integrator = Chili

[phase_space.chili]
num_s_channels   = 99
start_vegas_bins = 100
max_vegas_bins   = 100

[cuts]
jets.pt_min = 0.01
jets.nu_max = 5
jets.dR_min = 0.4
ll.m_min    = 66
ll.m_max    = 116

[events]
output_path = event_data.hdf5

[dev]
diagnostic_output_enabled = true
EOF

cat << EOF > parallel_config.json
{{
   "N Ranks": $NRANKS,
   "Ranks per Node": $RANKS_PER_NODE,
   "N Nodes": $NUM_NODES
}}
EOF

echo [$SECONDS] pepper start
mpiexec -n $NRANKS --ppn $RANKS_PER_NODE --hostfile $PBS_NODEFILE $PEPPER_PATH/{executable} pepper_config.ini
echo [$SECONDS] pepper done

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import glob
import os
import json
import configparser
import h5py as hp
import subprocess

def main():
   parser = argparse.ArgumentParser(description='Plotting script for scaling tests.')
   parser.add_argument('-i', '--input-path', required=True, help='Path to base scaling output data.')
   # parser.add_argument('-f', '--function', required=True, help='User-provided function to extract data from files')
   parser.add_argument('-n', '--name', required=True, help='Name of the figure of merit for plot labels')
   parser.add_argument('-o', '--output-basename', required=True, help='output plot filename base, possibly including path.',default='')

   parser.add_argument('--overwrite', action='store_true', help='reread input files and write out CSV files',default=False)
   args = parser.parse_args()

   # Dynamically import the user-provided function
   # module_name, function_name = args.function.rsplit('.', 1)
   # module = __import__(module_name, fromlist=[function_name])
   # extraction_function = getattr(module, function_name)

   fn_base = args.output_basename
   if not fn_base.endswith('/') and not fn_base.endswith('.') and not fn_base.endswith('_'):
      fn_base = fn_base + '.'

   threads_base = os.path.join(args.input_path,'threads')
   if os.path.exists(threads_base):
      if args.overwrite:
         threads_df = extraction_function(threads_base)
      else:
         threads_df = pd.read_csv(fn_base + 'threads.csv.gz',index_col=0)
      title = "Thread Scaling for " + threads_df["Process"].loc[0]
      plot_scaling_loglog(threads_df,"Batch Size","Number of Threads",args.name,args.name,title,fn_base+"thread_scaling.png",norm=False)
      plot_scaling_loglog(threads_df,"Batch Size","Number of Threads",args.name,args.name + " (norm)",title,fn_base+"thread_scaling_norm.png",norm=True)
      if args.overwrite:
         threads_df.to_csv(fn_base + 'threads.csv.gz',compression='gzip')

   ranks_base = os.path.join(args.input_path,'ranks')
   if os.path.exists(ranks_base):
      if args.overwrite:
         ranks_df = extraction_function(ranks_base)
      else:
         ranks_df = pd.read_csv(fn_base + 'ranks.csv.gz',index_col=0)
      title = "Rank Scaling for " + ranks_df["Process"].loc[0]
      ranks_df = ranks_df.sort_values(by="N Ranks")
      plot_scaling_loglog(ranks_df,"N Ranks","Number of Ranks",args.name,args.name,title,fn_base+"rank_scaling.png",norm=False)
      plot_scaling_loglog(ranks_df,"N Ranks","Number of Ranks",args.name,args.name + " (norm)",title,fn_base+"rank_scaling_norm.png",norm=True)
      plot_runtime_breakdown(ranks_df,fn_base)
      create_two_plot_figure(ranks_df,"N Ranks",fn_base+"runtime_to_bash_ratio.png")
      plot_and_ratio(ranks_df,"N Ranks","Total Runtime",fn_base+"runtime.png")
      plot_and_ratio(ranks_df,"N Ranks","Event Rate",fn_base+"event_rate.png")
      if args.overwrite:
         ranks_df.to_csv(fn_base + 'ranks.csv.gz',compression='gzip')

   # Assuming the extraction function returns a dataframe
   # df_list = [extraction_function(file) for file in sorted(glob.glob(data_glob))]
   # df = pd.concat(df_list, ignore_index=True)

   # df.sort_values(by='threads',inplace=True)
   # df.sort_values(by='ranks',inplace=True)
   # print(df)

   # figure_of_merit_name = args.name
   # plot_thread_scaling(df, figure_of_merit_name)
   # plot_rank_scaling(df, figure_of_merit_name)

def plot_runtime_breakdown(df,output_basename):

   # Define the groups of columns
   top_level_columns = ['Event Generation Runtime', 'Optimisation Runtime',
                        'Initialisation Runtime', 'HDF5 Close Runtime',
                        'Unweighting Setup Runtime']

   event_generation_columns = ['EG Recursion','EG Output',
                               'EG PDF and AlphaS evaluation','EG Phase space']

   recursion_columns = ["EG-R Calculate currents","EG-R Momenta preparation",
                        "EG-R Currents preparation","EG-R IP reset",
                        "EG-R ME update",
                        "EG-R ME2 update",
                        "EG-R ME reset","EG-R IC reset"]


   # Function to create the plot
   def create_plot(df, columns, total_column, xlabel, output_filename):
      # Calculate the fractions
      fractions = df[columns].div(df[total_column], axis=0)
      fractions[xlabel] = df[xlabel]
      
      plt.figure(dpi=240)
      # Plot the data
      fractions.plot(x=xlabel, kind='bar', stacked=True, ax=plt.gca())
      plt.ylim(0, 1)
      plt.ylabel('Fraction of Total Runtime')
      plt.title('Fraction of Total Runtime per Component')
      plt.grid(axis='y')
      
      plt.tight_layout()
      plt.savefig(output_filename)
      plt.close("all")
      
   # Create the plots
   create_plot(df, top_level_columns, 'Total Runtime', 'N Ranks',output_basename + 'total_runtime.png')
   create_plot(df, event_generation_columns, 'Event Generation Runtime', 'N Ranks',output_basename + 'eg_runtime.png')
   create_plot(df, recursion_columns, 'EG Recursion', 'N Ranks',output_basename + 'recursion_runtime.png')

# Function to create a figure with two plots
def create_two_plot_figure(df, x_label,output_filename):
   # Create a figure with specified grid spec
   fig = plt.figure(figsize=(8, 6))
   spec = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[3, 1], hspace=0.0)
   
   # Top plot (75% of the space)
   ax1 = fig.add_subplot(spec[0])
   df.plot(x=x_label, y=['Total Runtime', 'Bash Runtime'], ax=ax1)
   ax1.set_ylabel('Runtime')
   ax1.set_title('Total and Bash Runtimes')
   
   # Remove x-axis label and ticks from the top plot
   ax1.set_xlabel('')
   ax1.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
   
   # Bottom plot (25% of the space)
   ax2 = fig.add_subplot(spec[1], sharex=ax1)
   ratio = (df['Bash Runtime'] / df['Total Runtime'])
   ax2.plot(df[x_label],ratio, color='red')
   ax2.set_ylabel('Ratio')
   ax2.set_xlabel(x_label)
   # ax2.set_title('Ratio of Bash Runtime to Total Runtime') 
   
   # Set the x-ticks and labels to match the top plot
   # ax2.set_xticks(df.index)
   # ax2.set_xticklabels(df[x_label].tolist(), rotation=45)
   
   # Adjust the layout so that plots do not overlap
   fig.tight_layout()
   
   fig.savefig(output_filename)
   plt.close("all")


def plot_and_ratio(df,x_col,y_col,output_filename):
   # Extract data
   x_data = df[x_col].values
   y_data = df[y_col].values

   # Create main plot
   fig, ax = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1], 'hspace': 0}, sharex=True)
   
   ax[0].plot(x_data, y_data, marker='o', linestyle='-')
   ax[0].set_ylabel(y_col)
   # ax[0].set_title("Total Runtime vs. N Ranks")
   ax[0].grid(axis='y')

   # Create normalized plot at the bottom
   min_y_data = y_data[x_data == x_data.min()][0]  # Get y_data for smallest rank
   normalized_y_data = y_data / min_y_data
   ax[1].plot(x_data, normalized_y_data, marker='o', linestyle='-', color='r')
   ax[1].set_xlabel(x_col)
   ax[1].set_ylabel("Normalized " + y_col)
   ax[1].grid(axis='y')

   fig.tight_layout()
   fig.savefig(output_filename)
   plt.close("all")

def plot_scaling_loglog(df, x_key, x_label, y_key, y_label, title, output_filename, norm=False):
   df = df.sort_values(by=x_key)
   plt.figure(dpi=240)
   x = df[x_key]
   y = df[y_key]
   if norm:
      y = y / df[y_key].loc[0]
   plt.loglog(x, y, 'o-')

   plt.xlabel(x_label)
   plt.ylabel(y_label)
   plt.grid(which='major', linestyle='-', alpha=0.7)
   plt.grid(which='minor', linestyle=':', alpha=0.5)
   # plt.legend()
   plt.title(title)
   plt.tight_layout()
   plt.savefig(output_filename)
   plt.close("all")



def extraction_function(base_path):
   # filename: "/path/to/output/{threads,ranks}/"
   subdirs = sorted(glob.glob(base_path + '/*',recursive=False))
   # print(subdirs)
   rows = []
   for subdir in subdirs:
      csv_dict = extract_timers_csv(subdir)
      ini_dict = extract_ini(subdir)
      csv_dict.update(ini_dict)
      xs_dict = extract_final_xs_hdf5(subdir)
      csv_dict.update(xs_dict)
      run_time = extract_log_data(subdir)
      csv_dict.update(run_time)
      parallel_dict = extract_parallel_config(subdir)
      csv_dict.update(parallel_dict)
      if csv_dict['Process'] == '' and csv_dict['Batch Size'] == 0:
         continue
      # print(csv_dict)
      rows.append(csv_dict)
   df = pd.DataFrame(rows)
   df['Batch Size'] = df['Batch Size'].astype(int)
   df['N Batches'] = df['N Batches'].astype(int)
   df['Event Period'] = df['Event Generation Runtime'] / df['Batch Size'] / df['N Batches']
   df['Event Rate'] = 1. / df['Event Period']

   return df


def extract_log_data(base_path):
   # base_path: "/path/to/output/{threads,ranks}/<num>-threads_<num>-ranks/"
   filenames = sorted(glob.glob(os.path.join(base_path,'pepper_scaling.o*')))
   duration = 0
   filename = 'None'
   if len(filenames) > 0:
      filename = filenames[-1]
      cmd = 'grep "pepper start" %s' % filename
      result = subprocess.run(cmd, capture_output=True, shell=True, text=True)
      start_str = str(result.stdout)
      start_time = int(start_str.split(']')[0].replace('[',''))

      cmd = 'grep "pepper done" %s' % filename
      result = subprocess.run(cmd, capture_output=True, shell=True, text=True)
      stop_str = str(result.stdout)
      if len(stop_str) > 1:
         stop_time = int(stop_str.split(']')[0].replace('[',''))
         duration = stop_time - start_time
   return {
      "Bash Runtime": duration,
      "Log Filename": filename,
   }


def extract_final_xs_hdf5(base_path):
   # base_path: "/path/to/output/{threads,ranks}/<num>-threads_<num>-ranks/"
   filename = os.path.join(base_path,'event_data.hdf5')
   xs_mean = 0.
   xs_sigma = 0.
   if os.path.exists(filename):
      try:
         data = hp.File(filename)
         xs_mean = data['generatedResult'][0]
         xs_sigma = data['generatedResult'][1]
      except:
         print('failed to open file: ',filename)
   return {
      'xs_mean': xs_mean,
      'xs_sigma': xs_sigma,
      "HDF5 Filename": filename,
   }

def extract_ini(base_path):
   # base_path: "/path/to/output/{threads,ranks}/<num>-threads_<num>-ranks/"
   config_ini_fn = os.path.join(base_path,'pepper_config.ini')
   batch_size = 0
   n_batches = 0
   process = ''
   if os.path.exists(config_ini_fn):
      config = configparser.ConfigParser()
      config.read(config_ini_fn)
      batch_size = config['main']['batch_size']
      n_batches = config['main']['n_batches']
      process = config['main']['process']
   return {
      "Batch Size":batch_size,
      "N Batches": n_batches,
      "Process": process,
      "Config Filename": config_ini_fn,
   }


def extract_parallel_config(base_path):
   # base_path: "/path/to/output/{threads,ranks}/<num>-threads_<num>-ranks/"
   config_json_fn = os.path.join(base_path,'parallel_config.json')
   nnodes = 0
   ranks_per_node = 0
   nranks = 0
   if os.path.exists(config_json_fn):
      config = json.load(open(config_json_fn))
      nnodes = config['N Nodes']
      ranks_per_node = config['Ranks per Node']
      nranks = config['N Ranks']
   return {
      'N Nodes':nnodes,
      'Ranks per Node': ranks_per_node,
      'N Ranks': nranks,
      'Parallel Config Filename': config_json_fn
   }

def extract_timers_csv(base_path):
   # base_path: "/path/to/output/{threads,ranks}/<num>-threads_<num>-ranks/"
   timers_csv_fn = glob.glob(base_path + '/pepper_diagnostics/*/timers.csv')
   if len(timers_csv_fn) == 1:
      timers_csv_fn = timers_csv_fn[0]
      timers = pd.read_csv(timers_csv_fn)
      timers['Task'] = timers['Task'].apply(lambda x: x.strip())
      # Remove padding from column names
      timers.columns = timers.columns.str.strip()
      return {
         'Total Runtime':                 timers.loc[timers['Task'] == 'Total','Duration [s]'].iloc[0],
         'Event Generation Runtime':      timers.loc[timers['Task'] == 'Event generation','Duration [s]'].iloc[0],
         'Optimisation Runtime':          timers.loc[timers['Task'] == 'Optimisation','Duration [s]'].iloc[0],
         'Initialisation Runtime':        timers.loc[timers['Task'] == 'Initialisation','Duration [s]'].iloc[0],
         'HDF5 Close Runtime':            timers.loc[timers['Task'] == 'HDF5 close','Duration [s]'].iloc[0],
         'Unweighting Setup Runtime':     timers.loc[timers['Task'] == 'Unweighting setup','Duration [s]'].iloc[0],
         'EG Recursion':                  timers.loc[timers['Task'] == 'Recursion','Duration [s]'].iloc[0],
         'EG Output':                     timers.loc[timers['Task'] == 'Output','Duration [s]'].iloc[0],
         'EG PDF and AlphaS evaluation':  timers.loc[timers['Task'] == 'PDF and AlphaS evaluation','Duration [s]'].iloc[0],
         'EG Phase space':                timers.loc[timers['Task'] == 'Phase space','Duration [s]'].iloc[0],
         'EG Output':                     timers.loc[timers['Task'] == 'Output','Duration [s]'].iloc[0],
         'EG-R Calculate currents':       timers.loc[timers['Task'] == 'Calculate currents','Duration [s]'].iloc[0],
         'EG-R Momenta preparation':      timers.loc[timers['Task'] == 'Momenta preparation','Duration [s]'].iloc[0],
         'EG-R Currents preparation':     timers.loc[timers['Task'] == 'Currents preparation','Duration [s]'].iloc[0],
         'EG-R IP reset':                 timers.loc[timers['Task'] == 'Internal particle information reset','Duration [s]'].iloc[0],
         'EG-R ME update':                timers.loc[timers['Task'] == 'ME update','Duration [s]'].iloc[0],
         'EG-R ME2 update':               timers.loc[timers['Task'] == 'ME2 update','Duration [s]'].iloc[0],
         'EG-R ME reset':                 timers.loc[timers['Task'] == 'ME reset','Duration [s]'].iloc[0],
         'EG-R IC reset':                 timers.loc[timers['Task'] == 'Internal currents reset','Duration [s]'].iloc[0],
         'CSV Timer Filename':            timers_csv_fn,
      }
   
   return {}


if __name__ == "__main__":
   main()

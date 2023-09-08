from .sched_base import Scheduler
import subprocess
import logging
import os
logger = logging.getLogger(__name__)


class PBS(Scheduler):

   def submit(self, config,
              threads: int,
              ranks: int,
              job_working_path: str = os.getcwd(),
              no_sub: bool = False):
      
      
      # open PBS script template
      self.SUBMIT_SCRIPT = self.get_script(config['script_template_file'])
      logging.debug("script template:\n%s",self.SUBMIT_SCRIPT)

      # Create the PBS script
      opts = config['script_template_opts']
      opts['threads'] = threads
      opts['ranks'] = ranks
      opts['num_nodes'] = int(ranks / opts['ranks_per_node'])
      script_content = self.SUBMIT_SCRIPT.format(**opts)
      logging.debug("script file:\n%s",script_content)

      # make sure output path exists
      os.makedirs(job_working_path,exist_ok=True)

      script_name = f"{threads:06d}-threads_{ranks:05d}-ranks.pbs.sh"
      script_path = os.path.join(job_working_path,script_name)
      with open(script_path, 'w') as f:
         f.write(script_content)

      # Submit the job
      cmd = f"{self.SUBMIT} {script_name}"
      logger.debug("submit command: %s",cmd)
      if not no_sub:
         result = subprocess.run(cmd, capture_output=True, shell=True, text=True,cwd=job_working_path)

         if result.returncode != 0:
            open(os.path.join(job_working_path,script_name + '.output.txt'),'w').write(result.stdout)
            open(os.path.join(job_working_path,script_name + '.error.txt'),'w').write(result.stderr)

         # Extract job ID from the result (assuming the format is "1234.servername")
         job_id = result.stdout.split('.')[0]
         return job_id
      else:
         return 0
   
   def get_script(self,script_template_file):
      return open(script_template_file).read()

   def status(self, job_id):
      cmd = f"{self.STATUS} {job_id}"
      result = subprocess.run(cmd, capture_output=True, shell=True, text=True)
      return job_id in result.stdout

   def delete(self, job_id):
      cmd = f"{self.DELETE} {job_id}"
      result = subprocess.run(cmd, capture_output=True, shell=True, text=True)
      return result.returncode == 0

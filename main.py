import json
from scheduler import PBS  # Import other schedulers as you implement them
import logging
import argparse
import os
import time
logger = logging.getLogger(__name__)

def get_scheduler(name):
    if name == "PBS":
        return PBS()
    # Add more schedulers as needed
    # elif name == "SLURM":
    #     return SLURM()
    else:
        raise ValueError(f"Unsupported scheduler: {name}")

def run_with_threads(scheduler, config, no_sub=False, single_queue=False):
    for threads in config["range"]:
        ranks = config['fixed_value']
        job_working_path = os.path.join(config['output_path'],'threads', f'{threads:06d}-threads_{ranks:05d}-ranks')
        job_id = scheduler.submit(config,threads,ranks,job_working_path,no_sub)

        if single_queue and not no_sub:
            logger.info('waiting for job %s with %d threads %d ranks',job_id,threads,ranks)
            while scheduler.status(job_id):
                logger.debug('waiting for job %s',job_id)
                time.sleep(30)  # Check every 30 seconds


def run_with_ranks(scheduler, config, no_sub=False, single_queue=False):
    for ranks in config["range"]:
        threads = config["fixed_value"]
        job_working_path = os.path.join(config['output_path'],'ranks', f'{threads:06d}-threads_{ranks:05d}-ranks')
        job_id = scheduler.submit(config,threads,ranks,job_working_path,no_sub)

        if single_queue and not no_sub:
            logger.info('waiting for job %s with %d threads %d ranks',job_id,threads,ranks)
            while scheduler.status(job_id):
                logger.debug('waiting for job %s',job_id)
                time.sleep(30)  # Check every 30 seconds

def main(config_file,no_sub=False, single_queue=False):
    with open(config_file, 'r') as f:
        config = json.load(f)

    scheduler = get_scheduler(config["scheduler"])

    if config["run_type"] == "threads":
        run_with_threads(scheduler, config, no_sub, single_queue)
    elif config["run_type"] == "ranks":
        run_with_ranks(scheduler, config, no_sub, single_queue)
    else:
        print(f"Invalid run_type: {config['run_type']}")

if __name__ == "__main__":
   ''' Scaler framework for running tests. '''
   logging_format = '%(asctime)s %(levelname)s:%(name)s:%(message)s'
   logging_datefmt = '%Y-%m-%d %H:%M:%S'
   logging_level = logging.INFO
   
   parser = argparse.ArgumentParser(description='')
   parser.add_argument('-c','--config',help='Input config file in json format',required=True)

   parser.add_argument('--no-sub', default=False, action='store_true', help="For debugging, disable subprocess calls")
   parser.add_argument('--single-queue', default=False, action='store_true', help="Ensure only one job is in the queue at a time")


   parser.add_argument('--debug', default=False, action='store_true', help="Set Logger to DEBUG")
   parser.add_argument('--error', default=False, action='store_true', help="Set Logger to ERROR")
   parser.add_argument('--warning', default=False, action='store_true', help="Set Logger to ERROR")
   parser.add_argument('--logfilename',default=None,help='if set, logging information will go to file')
   args = parser.parse_args()

   if args.debug and not args.error and not args.warning:
      logging_level = logging.DEBUG
   elif not args.debug and args.error and not args.warning:
      logging_level = logging.ERROR
   elif not args.debug and not args.error and args.warning:
      logging_level = logging.WARNING

   logging.basicConfig(level=logging_level,
                       format=logging_format,
                       datefmt=logging_datefmt,
                       filename=args.logfilename)
   
   main(args.config,args.no_sub, single_queue=args.single_queue)

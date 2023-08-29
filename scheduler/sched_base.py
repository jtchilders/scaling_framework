class Scheduler:
   SUBMIT_SCRIPT = ''
   SUBMIT = 'qsub'
   STATUS = 'qstat'
   DELETE = 'qdel'

   def __init__(self):
      pass

   def submit(self):
      raise NotImplementedError("submit function is not defined for this scheduler")

   def status(self):
      raise NotImplementedError("status function is not defined for this scheduler")

   def delete(self):
      raise NotImplementedError("delete function is not defined for this scheduler")
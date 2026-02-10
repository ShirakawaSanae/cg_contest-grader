from pygrading import Job

job = Job()

job.verdict("Accept")
job.score(100)
job.comment("Hello World")

job.print()

hostname = "rig.mit.edu"
https = True

if https is True:
    prefix = "https"
else:
    prefix = "http"

ET_ROOT = "{prefix}://{hostname}/et/".format(
    prefix=prefix, hostname=hostname
)

ET_PROJECTS = ET_ROOT + "projects/{repo}"

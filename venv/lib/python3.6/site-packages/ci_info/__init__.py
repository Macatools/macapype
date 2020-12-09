from builtins import str  # remove this once Py2 is dropped
import json
import os


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

_here = os.path.dirname(__file__)
with open(os.path.join(_here, 'vendors.json')) as fp:
    vendors = json.load(fp)

THISENV = os.environ
ENVINFO = None
for vendor in vendors:
    vendor_env = vendor.get('env')
    if isinstance(vendor_env, list):
        if all((ev in THISENV for ev in vendor_env)):
            ENVINFO = vendor
            break
    elif isinstance(vendor_env, dict):
        for ev, val in vendor_env.items():
            if ev in THISENV and THISENV[ev] == val:
                ENVINFO = vendor
                break
    elif isinstance(vendor_env, str):
        if vendor.get('env') in THISENV:
            ENVINFO = vendor
            break

if ENVINFO is None:
    # no matches
    ENVINFO = {}


def name():
    """
    Returns a string containing name of the CI server the code is running on.
    If CI server is not detected, returns None.
    """
    return ENVINFO.get('name')


def is_ci():
    """
    Returns a boolean. Will be `True` if the code is running on a CI server,
    otherwise `False`.
    """
    return bool(name())


def is_pr():
    """
    Returns a boolean if PR detection is supported for the current CI server.
    Will be `True` if a PR is being tested, otherwise `False`. If PR detection
    is not supported for the current CI server, the value will be `None`.
    """
    if ENVINFO.get('pr') is None:
        return

    pr_info = ENVINFO['pr']
    if isinstance(pr_info, dict):
        # "pr": { "env": "BUILDKITE_PULL_REQUEST", "ne": "false" }
        if pr_info.get('env'):
            if (
                pr_info['env'] in THISENV and
                THISENV[pr_info['env']] != pr_info['ne']
            ):
                return True
            return False
        # "pr": { "any": ["ghprbPullId", "CHANGE_ID"] }
        elif pr_info.get('any'):
            for ev in pr_info['any']:
                if THISENV.get(ev):
                    return True
            return False
        # "pr": { "DRONE_BUILD_EVENT": "pull_request" }
        else:
            for ev, val in pr_info.items():
                if THISENV.get(ev) != val:
                    return False
            return True

    elif isinstance(ENVINFO['pr'], str):
        return bool(THISENV.get(ENVINFO['pr']))


def info():
    """
    A dictionary of all other methods in key/value pairs.
    """
    return {
        'name': name(),
        'is_ci': is_ci(),
        'is_pr': is_pr(),
    }

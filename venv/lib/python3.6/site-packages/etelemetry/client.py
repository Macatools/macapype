from requests import request, ConnectionError, ReadTimeout
import os

try:
    import ci_info
except ImportError:
    import warnings
    warnings.warn(
        "Deprecated version of ci-info found, upgrade to remove this warning", DeprecationWarning
    )
    import ci as ci_info

from .config import ET_PROJECTS

_available_version_checked = None


class BadVersionError(RuntimeError):
    """Local version is known to contain a critical bug etc."""
    pass


def _etrequest(endpoint, method="get", **kwargs):
    if kwargs.get('timeout') is None:
        kwargs['timeout'] = 5

    params = {}
    if ci_info.is_ci():
        # send along CI information
        params = ci_info.info()

    try:
        res = request(method, endpoint, params=params, **kwargs)
    except ConnectionError:
        raise RuntimeError("Connection to server could not be made")
    except ReadTimeout:
        raise RuntimeError(
            "No response from server in {timeout} seconds".format(
                timeout=kwargs.get('timeout')
            )
        )
    res.raise_for_status()
    return res


def get_project(repo, **rargs):
    """
    Fetch latest version from server.

    Parameters
    ==========
    repo : str
        GitHub repository as <owner>/<project>
    **rargs
        Request keyword arguments

    Returns
    =======
    response
        Dictionary with `version` field
    """
    if "NO_ET" in os.environ:
        return None
    if "/" not in repo:
        raise ValueError("Invalid repository")
    res = _etrequest(ET_PROJECTS.format(repo=repo), **rargs)
    return res.json(encoding="utf-8")


def check_available_version(project, version, lgr=None, raise_exception=False):
    """A helper to check (and report) if newer version of project is available
    Should be ok to execute multiple times, it will be checked only one time

    Parameters
    ----------
    project: str
      as on GitHub (e.g., sensein/etelemetry-client. Releases will be checked
    version: str
      local version of project
    lgr: python logger object
      external logger to be used
    raise_exception: bool
      raise a BadVersionError exception if a bad local version is detected
    """
    global _available_version_checked
    if _available_version_checked is not None:
        return _available_version_checked

    if lgr is None:
        import logging
        lgr = logging.getLogger('et-client')

    from pkg_resources import parse_version

    latest = {"version": "Unknown", "bad_versions": []}
    ret = None
    try:
        ret = get_project(project)
    except Exception as e:
        lgr.debug("Could not check %s for version updates: %s", project, e)
        return None
    finally:
        if ret:
            latest.update(**ret)
            local_version = parse_version(version)
            remote_version = parse_version(latest["version"])
            if local_version < remote_version:
                lgr.warning("A newer version (%s) of %s is available. You are "
                            "using %s", latest["version"], project, version)
            elif remote_version < local_version:
                lgr.debug(
                    "Running a newer version (%s) of %s than available (%s)",
                    version, project, latest["version"])
            else:  # ==
                lgr.debug("No newer (than %s) version of %s found available",
                          version, project)
            if latest["bad_versions"] and any(
                    [
                        local_version == parse_version(ver)
                        for ver in latest["bad_versions"]
                    ]
            ):
                message = ("You are using a version of {0} with a critical bug. "
                          "Please use a different version.").format(project)
                if raise_exception:
                    raise BadVersionError(message)
                else:
                    lgr.critical(message)
            _available_version_checked = latest
    return latest

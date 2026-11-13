"""Keeps Supabase projects awake: restores a paused project, and gives awake ones a little database activity.

Runs on GitHub (.github/workflows/keep-alive.yml), using only Python's standard library.
  SUPABASE_ACCESS_TOKEN   personal access token, stored as a GitHub secret (never in the code)
  SUPABASE_PROJECT_REFS   the projects to watch, separated by spaces

Never fails the run, so GitHub never sends an email: problems it can't fix itself (for example an expired
token) are only written as a WARNING in the run's log.
"""

import json
import os
import sys
import urllib.error
import urllib.request

API = os.environ.get("SUPABASE_API_URL", "https://api.supabase.com")
ALL_GOOD = {"ACTIVE_HEALTHY"}
ON_ITS_WAY = {"RESTORING", "COMING_UP", "RESTARTING", "UPGRADING", "RESIZING"}  # wait for the next run


class ApiError(Exception):
    pass


def call(token, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "ear-training-watchdog",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        raise ApiError(f"{method} {path}: HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise ApiError(f"{method} {path}: {error.reason}") from error


def watch(token, ref):
    """Handle one project. Returns True if it's fine (or being fixed), False if a person should look."""
    status = call(token, "GET", f"/v1/projects/{ref}")["status"]

    if status == "INACTIVE":
        call(token, "POST", f"/v1/projects/{ref}/restore")
        print(f"{ref}: was paused, restore started (takes a few minutes)")
        return True
    if status in ON_ITS_WAY:
        print(f"{ref}: {status}, nothing to do yet")
        return True
    if status not in ALL_GOOD:
        print(f"{ref}: unexpected status {status}, please check the Supabase dashboard")
        return False

    # Free projects pause after about a week without activity, so touch the database. This endpoint is
    # in beta, and a failure here isn't urgent: the project is awake, and a pause would be restored above.
    try:
        call(token, "POST", f"/v1/projects/{ref}/database/query/read-only", {"query": "select 1"})
        print(f"{ref}: awake, database reached")
    except ApiError as error:
        print(f"{ref}: awake, but the activity query failed ({error})")
    return True


def main():
    token = os.environ.get("SUPABASE_ACCESS_TOKEN")
    refs = os.environ.get("SUPABASE_PROJECT_REFS", "").split()
    if not token:
        print("SUPABASE_ACCESS_TOKEN is not set yet: skipping (see README, Online section)")
        return 0

    healthy = True
    for ref in refs:
        try:
            healthy = watch(token, ref) and healthy
        except ApiError as error:  # e.g. 401: the token expired or was deleted
            print(f"{ref}: could not check: {error}")
            healthy = False
    if not healthy:
        print("WARNING: something above needs a person (see the lines before this one)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

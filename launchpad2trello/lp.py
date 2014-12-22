import os

import requests


CACHE_DIR = os.path.expanduser('~/.launchpadlib/cache/')

ALL_STATUSES = (
    'New', 'Incomplete', 'Opinion', 'Invalid', 'Won\'t Fix', 'Confirmed',
    'Triaged', 'In Progress', 'Fix Committed', 'Fix Released')


def get_project(project_name):
    r = requests.get(
        'https://api.launchpad.net/devel/%(project_name)s' % {
            'project_name': project_name},
        headers={
            'Accept': 'application/json'})
    project = r.json()
    return project


def _yield_collection(url):
    """Generate a list of entries starting with the provided URL."""
    while True:
        r = requests.get(
            url,
            headers={
                'Accept': 'application/json'})

        collection = r.json()

        for bug in collection['entries']:
            yield bug

        if 'next_collection_link' not in collection:
            # the collection ends when we don't have another link to follow
            break

        # prepare the next URL to follow
        url = collection['next_collection_link']


def list_bugs(project):
    # by default, launchpad only returns open issues, so we need to explicitly
    # ask for all of them.
    request = requests.Request(
        'GET',
        project['self_link'],
        params={
            'ws.op': 'searchTasks',
            'status': ALL_STATUSES})
    url = request.prepare().url

    for bug in _yield_collection(url):
        # backwards compat
        bug['url'] = bug['web_link']

        # we don't need anything but the name, so just parse and pray
        bug['owner'] = {
            'name': bug['owner_link'].rsplit('/')[-1].replace('~', '', 1)}

        if bug.get('assignee_link'):
            # we don't need anything but the name, so just parse and pray
            assignee = bug['assignee_link'].rsplit('/')[-1].replace('~', '', 1)
            bug['assignee'] = {
                'name': assignee}

        if bug.get('milestone_link'):
            # we don't need anything but the name, so just parse and pray
            bug['milestone'] = {
                'name': bug['milestone_link'].rsplit('/')[-1]}

        # smash the overall bug and project-specific task together. we only
        # care about one project, so there's no reason to differentiate between
        # the two.
        bug.update(requests.get(bug['bug_link']).json())

        yield bug


def list_specifications(project):
    url = project['valid_specifications_collection_link']

    for spec in _yield_collection(url):
        yield spec

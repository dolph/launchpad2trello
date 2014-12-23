import logging

import requests

from launchpad2trello import cache


LOG = logging.getLogger(__name__)

ALL_STATUSES = (
    'New', 'Incomplete', 'Opinion', 'Invalid', 'Won\'t Fix', 'Confirmed',
    'Triaged', 'In Progress', 'Fix Committed', 'Fix Released')


@cache.cache_on_arguments(expiration_time=60)
def _get_json(url):
    LOG.info('GET %s' % url)
    return requests.get(
        url,
        headers={
            'Accept': 'application/json'}).json()


@cache.cache_on_arguments(expiration_time=60 * 60)
def get_bug(bug_link):
    """Inflate a task object."""
    return _get_json(bug_link)


@cache.cache_on_arguments(expiration_time=60 * 60 * 24 * 7)
def get_project(project_name):
    project = _get_json('https://api.launchpad.net/devel/%(project_name)s' % {
        'project_name': project_name})
    return project


def _yield_collection(url):
    """Generate a list of entries starting with the provided URL."""
    while True:
        collection = _get_json(url)

        for item in collection['entries']:
            yield item

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

    for task in _yield_collection(url):
        # backwards compat
        task['url'] = task['web_link']

        # we don't need anything but the name, so just parse and pray
        task['owner'] = {
            'name': task['owner_link'].rsplit('/')[-1].replace('~', '', 1)}

        if task.get('assignee_link'):
            # we don't need anything but the name, so just parse and pray
            assignee = task['assignee_link']
            assignee = assignee.rsplit('/')[-1].replace('~', '', 1)
            task['assignee'] = {
                'name': assignee}

        if task.get('milestone_link'):
            # we don't need anything but the name, so just parse and pray
            task['milestone'] = {
                'name': task['milestone_link'].rsplit('/')[-1]}

        # smash the project-specific task into the overall bug. we only
        # care about one project, so there's no reason to differentiate between
        # the two.
        task.update(get_bug(task['bug_link']))

        # this is really a bug + project-specific task
        yield task


def list_specifications(project):
    url = project['valid_specifications_collection_link']

    for spec in _yield_collection(url):
        if spec.get('milestone_link'):
            # we don't need anything but the name, so just parse and pray
            spec['milestone'] = {
                'name': spec['milestone_link'].rsplit('/')[-1]}

        yield spec

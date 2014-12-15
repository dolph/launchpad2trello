import os

from launchpadlib import launchpad


CLIENT_NAME = 'launchpad2trello'
LP_INSTANCE = 'production'
CACHE_DIR = os.path.expanduser('~/.launchpadlib/cache/')


def get_client():
    return launchpad.Launchpad.login_with(
        CLIENT_NAME, LP_INSTANCE, CACHE_DIR)


def list_tasks(project_name):
    client = get_client()

    project = client.projects[project_name]

    for task in project.searchTasks():
        yield {
            'id': task.bug.id,
            'title': task.bug.title,
            'url': task.web_link,
            'status': task.status,
            'owner': task.owner.name if task.owner else None,
            'assignee': task.assignee.name if task.assignee else None,
            'importance': task.importance,
            'milestone': task.milestone.name if task.milestone else None,
        }

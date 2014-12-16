import argparse

from launchpad2trello import lp
from launchpad2trello import trello


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'launchpad_project',
        help='Your Launchpad project name.')
    parser.add_argument(
        'trello_key',
        help='Your Trello API key.')
    parser.add_argument(
        'trello_secret',
        help='Your Trello API secret.')
    parser.add_argument(
        'trello_board_id',
        help='Your Trello board ID.')
    parser.add_argument(
        '--trello-token', metavar='trello_token',
        help='Your Trello API token.')

    args = parser.parse_args()

    lists_by_name = trello.create_lists_as_necessary(
        args.trello_key,
        args.trello_secret,
        args.trello_board_id,
        token=args.trello_token)

    for task in lp.list_tasks(args.launchpad_project):
        if task['status'] in ('Triaged', 'Confirmed'):
            list_id = lists_by_name['Approved']['id']
        elif task['status'] in ('In Progress',):
            list_id = lists_by_name['Doing']['id']
        elif task['status'] in ('Fix Committed',):
            list_id = lists_by_name['Done']['id']
        else:
            list_id = lists_by_name['Backlog']['id']

        trello.create_card(
            args.trello_key,
            args.trello_token,
            list_id=list_id,
            name='Bug %s: %s' % (task['id'], task['title']),
            description='Bug #%s' % task['id'],
            url=task['url'])


if __name__ == '__main__':
    main()

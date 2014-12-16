import argparse
import logging

from launchpad2trello import lp
from launchpad2trello import trello


LOG = logging.getLogger(__name__)


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
    parser.add_argument(
        '--debug',
        help='Enable debugging output.')

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level)

    lists_by_name = trello.create_lists_as_necessary(
        args.trello_key,
        args.trello_secret,
        args.trello_board_id,
        token=args.trello_token)

    cards_by_task_id = trello.index_cards(
        args.trello_key,
        args.trello_secret,
        args.trello_board_id,
        token=args.trello_token)

    for task in lp.list_tasks(args.launchpad_project):
        if task['status'] in ('In Progress',):
            list_id = lists_by_name['Doing']['id']
        elif task['status'] in ('Fix Committed',):
            list_id = lists_by_name['Done']['id']
        elif task['milestone'] is not None and task['milestone'] != 'next':
            list_id = lists_by_name['Approved']['id']
        else:
            # by default, we put everything else in the backlog
            list_id = lists_by_name['Backlog']['id']

        # task IDs are integers, but they're unicode as dict keys
        task_id = unicode(task['id'])
        card_name = 'Bug %s: %s' % (task_id, task['title'])
        card_description = 'Bug #%s' % task['id']

        if task_id in cards_by_task_id.keys():
            LOG.info('Card already exists for Bug %s' % task['id'])
            card = cards_by_task_id[unicode(task['id'])]

            if card_name != card['name']:
                LOG.info('Updating card name...')
                trello.update_card_name(
                    args.trello_key,
                    args.trello_token,
                    card['id'],
                    card_name)

            if list_id != card['idList']:
                LOG.info('Updating card list...')
                trello.update_card_list(
                    args.trello_key,
                    args.trello_token,
                    card['id'],
                    list_id)
        else:
            LOG.info('Creating card for Bug %s' % task['id'])
            trello.create_card(
                args.trello_key,
                args.trello_token,
                list_id=list_id,
                name=card_name,
                description=card_description,
                url=task['url'])


if __name__ == '__main__':
    main()

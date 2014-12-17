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

    trello_token = args.trello_token or trello.authorize(
        args.trello_key, args.trello_secret)

    lists_by_name = trello.create_lists_as_necessary(
        args.trello_key,
        trello_token,
        args.trello_board_id)

    cards_by_task_id = trello.index_cards(
        args.trello_key,
        trello_token,
        args.trello_board_id)

    for task in lp.list_tasks(args.launchpad_project):
        if task['status'] in ('Triaged',):
            list_id = lists_by_name['Approved']['id']
        elif task['status'] in ('In Progress',):
            list_id = lists_by_name['Doing']['id']
        elif task['status'] in ('Fix Committed',):
            list_id = lists_by_name['Dev Done']['id']
        elif task['status'] in ('Fix Released',):
            list_id = lists_by_name['Released']['id']
        elif task['milestone'] is not None and task['milestone'] != 'next':
            list_id = lists_by_name['Approved']['id']
        else:
            # by default, we put everything else in the backlog:
            # New, Incomplete, Opinion, Invalid, Won't Fix, Confirmed
            list_id = lists_by_name['Backlog']['id']

        # task IDs are integers, but they're unicode as dict keys
        task_id = unicode(task['id'])
        card_name = 'Bug %s: %s' % (task_id, task['title'])
        card_description = 'Bug #%s' % task['id']

        if task_id not in cards_by_task_id.keys():
            LOG.info('Creating card for Bug %s' % task['id'])
            card = trello.create_card(
                args.trello_key,
                trello_token,
                list_id=list_id,
                name=card_name,
                description=card_description,
                url=task['url'])
            cards_by_task_id[unicode(task['id'])] = card

        card = cards_by_task_id[unicode(task['id'])]

        if card_name != card['name']:
            LOG.info('Updating card name...')
            trello.update_card_name(
                args.trello_key,
                trello_token,
                card['id'],
                card_name)

        if list_id != card['idList']:
            LOG.info('Updating card list...')
            trello.update_card_list(
                args.trello_key,
                trello_token,
                card['id'],
                list_id)

        def ensure_label(card, color):
            labels = [x['color'] for x in card['labels']]

            if color not in labels:
                LOG.info('Adding %s label to card...' % color)

                # sorting returns them to a list
                new_colors = sorted(set(labels + [color]))

                trello.update_card_label(
                    args.trello_key,
                    trello_token,
                    card['id'],
                    new_colors)

        if task['importance'] == 'Critical':
            ensure_label(card, 'red')

        if task['importance'] == 'High':
            ensure_label(card, 'orange')

        if task['importance'] == 'Medium':
            ensure_label(card, 'yellow')

        if task['importance'] in ('Low',):
            ensure_label(card, 'green')

        if task['importance'] in ('Wishlist',):
            ensure_label(card, 'blue')


if __name__ == '__main__':
    main()

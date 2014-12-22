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
        '--debug', action='store_true',
        help='Enable debugging output.')

    args = parser.parse_args()

    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG

        import httplib2
        httplib2.debuglevel = 1

    logging.basicConfig(level=log_level)

    lp_project = lp.get_project(args.launchpad_project)

    trello_token = args.trello_token or trello.authorize(
        args.trello_key, args.trello_secret)

    lists_by_name = trello.create_lists_as_necessary(
        args.trello_key,
        trello_token,
        args.trello_board_id,
        ['Backlog', 'Approved', 'Doing', 'Dev Done', 'Released'])

    cards_by_bug_id, cards_by_blueprint_id = trello.index_cards(
        args.trello_key,
        trello_token,
        args.trello_board_id)

    def update_card_name(card, name):
        if name != card['name']:
            LOG.info('Updating card name...')
            trello.update_card_name(
                args.trello_key,
                trello_token,
                card['id'],
                name)

    def update_card_list(card, list_id):
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

    for bug in lp.list_bugs(lp_project):
        if bug['status'] in ('Triaged',):
            list_id = lists_by_name['Approved']['id']
        elif bug['status'] in ('In Progress',):
            list_id = lists_by_name['Doing']['id']
        elif bug['status'] in ('Fix Committed',):
            list_id = lists_by_name['Dev Done']['id']
        elif bug['status'] in ('Fix Released',):
            list_id = lists_by_name['Released']['id']
        elif bug.get('milestone') and bug['milestone'] != 'next':
            list_id = lists_by_name['Approved']['id']
        else:
            # by default, we put everything else in the backlog:
            # New, Incomplete, Opinion, Invalid, Won't Fix, Confirmed
            list_id = lists_by_name['Backlog']['id']

        # bug IDs are integers, but they're unicode as dict keys
        bug_id = unicode(bug['id'])
        card_name = 'Bug %s: %s' % (bug_id, bug['title'])
        card_description = 'Bug #%s' % bug['id']

        if bug_id not in cards_by_bug_id.keys():
            LOG.info('Creating card for Bug %s' % bug['id'])
            card = trello.create_card(
                args.trello_key,
                trello_token,
                list_id=list_id,
                name=card_name,
                description=card_description,
                url=bug['url'])
            cards_by_bug_id[unicode(bug['id'])] = card

        card = cards_by_bug_id[unicode(bug['id'])]

        update_card_name(card, card_name)
        update_card_list(card, list_id)

        if bug['importance'] == 'Critical':
            ensure_label(card, 'red')

        if bug['importance'] == 'High':
            ensure_label(card, 'orange')

        if bug['importance'] == 'Medium':
            ensure_label(card, 'yellow')

        if bug['importance'] in ('Low',):
            ensure_label(card, 'green')

        if bug['importance'] in ('Wishlist',):
            ensure_label(card, 'blue')

    for blueprint in lp.list_specifications(lp_project):
        if blueprint['lifecycle_status'] in ('Unknown',):
            list_id = lists_by_name['Backlog']['id']
        elif blueprint['lifecycle_status'] in ('Not started',):
            list_id = lists_by_name['Approved']['id']
        elif blueprint['lifecycle_status'] in (
                'Started', 'Slow progress', 'Good progress'):
            list_id = lists_by_name['Doing']['id']
        elif blueprint['lifecycle_status'] in ('Blocked',):
            # "Equivalent status but with Trello label = blocked" -gist (??)
            pass
        elif blueprint['lifecycle_status'] in (
                'Beta available', 'Needs code review', 'Implemented'):
            list_id = lists_by_name['Doing']['id']
        else:
            # by default, we put everything else in the backlog:
            # New, Incomplete, Opinion, Invalid, Won't Fix, Confirmed
            list_id = lists_by_name['Dev Done']['id']

        blueprint_id = blueprint['name']
        card_name = 'BP %s: %s' % (blueprint_id, blueprint['title'])
        card_description = 'BP %s' % blueprint['name']

        if blueprint_id not in cards_by_blueprint_id.keys():
            LOG.info('Creating card for Bug %s' % bug['id'])
            card = trello.create_card(
                args.trello_key,
                trello_token,
                list_id=list_id,
                name=card_name,
                description=card_description,
                url=bug['url'])
            cards_by_blueprint_id[blueprint_id] = card

        card = cards_by_blueprint_id[blueprint_id]

        update_card_name(card, card_name)
        update_card_list(card, list_id)

        # TODO(dolph): Bernardo has a bunch of trello labels to map to based on
        # the blueprint['priority']... but for now, they're all just wishlisty.
        ensure_label(card, 'blue')

if __name__ == '__main__':
    main()

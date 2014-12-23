import argparse
import logging

from launchpad2trello import lp
from launchpad2trello import trello


LOG = logging.getLogger(__name__)

EXPECTED_LABELS = {
    # bug priorities
    'Undecided': 'blue',
    'Critical': 'red',
    'High': 'green',
    'Medium': 'green',
    'Low': 'green',
    'Wishlist': 'blue',

    # blueprint priorities
    'Not': 'blue',
    'Undefined': 'blue',
    'Low': 'green',
    'Medium': 'green',
    'High': 'green',
    'Essential': 'red',

    # blueprint status
    'Blocked': 'red',

    # unused?
    'impacts:doc': 'orange',
    'impacts:qe': 'orange',
    'impacts:backport potential': 'orange',
    'impacts:approved': 'orange',
    'impacts:pending approval': 'orange',
    'impacts:review': 'orange',
    'impacts:drafting': 'orange',
    'impacts:discussion': 'orange',
    'impacts:new': 'orange',
    'impacts:superseded': 'orange',
    'impacts:obsolete': 'orange',
    'impacts:approved': 'orange',
    'impacts:needs approval': 'orange',
    'type:bug': 'black',
    'type:blueprint': 'black',
    'type:task': 'black',
    'type:spike': 'black',
}


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

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    lp_project = lp.get_project(args.launchpad_project)

    trello_token = args.trello_token or trello.authorize(
        args.trello_key, args.trello_secret)

    trello_board_id = trello.normalize_board_id(
        args.trello_key, trello_token, args.trello_board_id)

    lists_by_name = trello.create_lists_as_necessary(
        args.trello_key,
        trello_token,
        trello_board_id,
        ['Backlog', 'Approved', 'Doing', 'Dev Done', 'Released'])

    cards_by_bug_id, cards_by_blueprint_id = trello.index_cards(
        args.trello_key,
        trello_token,
        trello_board_id)

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

    def ensure_label(card, label_id, condition=True):
        """Ensures a card is labeled appropriately if the condition is true.

        If the condition is not true, ensures the card is not
        labeled as such.
        """
        if label_id not in card['idLabels'] and condition:
            LOG.info('Adding label %s to card...' % label_id)
            trello.label_card(
                args.trello_key,
                trello_token,
                card['id'],
                label_id)

        if label_id in card['idLabels'] and not condition:
            LOG.info('Removing label %s from card...' % label_id)
            trello.unlabel_card(
                args.trello_key,
                trello_token,
                card['id'],
                label_id)

    labels = trello.list_labels(
        args.trello_key, trello_token, trello_board_id)
    labels_by_name = dict((x['name'], x) for x in labels)

    def ensure_label_exists(board_id, name, color):
        if name not in labels_by_name.keys():
            label = trello.create_label(
                args.trello_key, trello_token, trello_board_id, name, color)
            labels_by_name[name] = label

    for label_name, label_color in EXPECTED_LABELS.iteritems():
        ensure_label_exists(trello_board_id, label_name, label_color)

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

        ensure_label(
            card, labels_by_name['Critical']['id'],
            condition=bug['importance'] == 'Critical')

        ensure_label(
            card, labels_by_name['High']['id'],
            condition=bug['importance'] == 'High')

        ensure_label(
            card, labels_by_name['Medium']['id'],
            condition=bug['importance'] == 'Medium')

        ensure_label(
            card, labels_by_name['Low']['id'],
            condition=bug['importance'] == 'Low')

        ensure_label(
            card, labels_by_name['Wishlist']['id'],
            condition=bug['importance'] == 'Wishlist')

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
            LOG.info('Creating card for BP %s' % blueprint_id)
            card = trello.create_card(
                args.trello_key,
                trello_token,
                list_id=list_id,
                name=card_name,
                description=card_description,
                url=blueprint['web_link'])
            cards_by_blueprint_id[blueprint_id] = card

        card = cards_by_blueprint_id[blueprint_id]

        update_card_name(card, card_name)
        update_card_list(card, list_id)

        ensure_label(
            card, labels_by_name['Not']['id'],
            condition=blueprint['priority'] == 'Not')

        ensure_label(
            card, labels_by_name['Undefined']['id'],
            condition=blueprint['priority'] == 'Undefined')

        ensure_label(
            card, labels_by_name['Low']['id'],
            condition=blueprint['priority'] == 'Low')

        ensure_label(
            card, labels_by_name['Medium']['id'],
            condition=blueprint['priority'] == 'Medium')

        ensure_label(
            card, labels_by_name['High']['id'],
            condition=blueprint['priority'] == 'High')

        ensure_label(
            card, labels_by_name['Essential']['id'],
            condition=blueprint['priority'] == 'Essential')

        ensure_label(
            card, labels_by_name['Blocked']['id'],
            condition=blueprint['implementation_status'] == 'Blocked')

        if blueprint.get('milestone'):
            # milestone labels are created on-demand; probably should set them
            # up first instead.
            ensure_label_exists(
                trello_board_id, blueprint['milestone']['name'], color=None)
            ensure_label(
                card, labels_by_name[blueprint['milestone']['name']]['id'])
            # FIXME(dolph): labels for other milestones are not removed, so if
            # a blueprint is retargeted to another milestone, you'll get two
            # labels in trello


if __name__ == '__main__':
    main()

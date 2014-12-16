import webbrowser

import requests
from requests import auth
from requests_oauthlib import OAuth1


CLIENT_NAME = 'launchpad2trello'
ENDPOINT = 'https://api.trello.com'
API_VERSION = '1'


class TrelloAuth(auth.AuthBase):
    """Attach Trello API authentication to each request."""
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def __call__(self, r):
        params = {'key': self.key}
        r.prepare_url(r.url, params)
        return r


def get_client(key, secret):
    session = requests.Session()
    session.auth = TrelloAuth(key, secret)
    return session


def authorize(key, secret):
    url = 'https://api.trello.com/1/authorize'
    auth = OAuth1(key, secret)
    r = requests.Request(
        'GET', url, auth=auth, params={
            'key': key,
            'name': CLIENT_NAME,
            'expiration': '1hour',  # change to 'never'
            'scope': 'read,write',
            'response_type': 'token'})
    prepared = r.prepare()
    webbrowser.open(prepared.url)
    return raw_input('Enter your token: ')


def create_list(key, token, board_id, name, position=None):
    assert board_id
    assert 1 <= len(name) <= 16384
    assert position in (None, 'top', 'bottom') or isinstance(position, int)

    payload = {
        'name': name,
        'idBoard': board_id,
        'pos': position,
    }
    r = requests.post(
        'https://api.trello.com/1/lists',
        params={'key': key, 'token': token},
        data=payload)
    print('%s %s' % (r.request.method, r.request.url))
    print(r.request.body)
    print('%s: %s' % (r.status_code, r.text))
    return r.body()['id']


def create_card(key, token, list_id, name, description, url):
    assert list_id
    assert 1 <= len(name) <= 16384
    assert 1 <= len(description) <= 16384
    assert url

    payload = {
        'idList': list_id,
        'name': name,
        'description': description,
        'urlSource': url,
    }
    r = requests.post(
        'https://api.trello.com/1/cards',
        params={'key': key, 'token': token},
        data=payload)
    print('%s %s' % (r.request.method, r.request.url))
    print(r.request.body)
    print('%s: %s' % (r.status_code, r.text))


def create_lists_as_necessary(key, secret, board_id, token=None):
    if token is None:
        token = authorize(key, secret)

    # for some reason, the board ID from the website doesn't work consistently
    # as an API reference, so we need to retrieve the board ID from the API
    r = requests.get(
        'https://api.trello.com/1/boards/%s' % board_id,
        params={'key': key, 'token': token})
    board_id = r.json()['id']

    r = requests.get(
        'https://api.trello.com/1/boards/%s/lists' % board_id,
        params={'key': key, 'token': token})
    lists = r.json()

    lists_by_name = dict([(x['name'], x) for x in lists])

    def create_list(list_name):
        if list_name not in lists_by_name.keys():
            list_id = create_list(key, token, board_id, name=list_name)
            lists_by_name[list_name] = list_id

    create_list('Backlog')
    create_list('Approved')
    create_list('Doing')
    create_list('Done')

    return lists_by_name
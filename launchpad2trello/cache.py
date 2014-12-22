import os

import dogpile.cache


CACHE_DIR = os.path.expanduser('/tmp/launchpad2trello')
if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR, 0o0700)

CACHE = dogpile.cache.make_region().configure(
    'dogpile.cache.dbm',
    expiration_time=15,
    arguments={'filename': '%s/cache.dbm' % CACHE_DIR})


cache_on_arguments = CACHE.cache_on_arguments

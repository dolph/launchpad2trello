import os
import shutil

import dogpile.cache


CACHE_DIR = '/tmp/launchpad2trello'
CACHE = None
cache_on_arguments = None


def configure():
    global CACHE, cache_on_arguments

    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR, 0o0700)

    CACHE = dogpile.cache.make_region().configure(
        'dogpile.cache.dbm',
        expiration_time=15,
        arguments={'filename': '%s/cache.dbm' % CACHE_DIR})
    cache_on_arguments = CACHE.cache_on_arguments


def purge():
    shutil.rmtree(CACHE_DIR)
    configure()


# TODO(dolph): this module probably shouldn't configure itself on import
configure()

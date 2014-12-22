import setuptools


setuptools.setup(
    name='launchpad2trello',
    version='1.0.0',
    description='Sync Launchpad activity to Trello',
    author='Dolph Mathews',
    author_email='dolph.mathews@gmail.com',
    url='http://github.com/dolph/launchpad2trello',
    packages=['launchpad2trello'],
    entry_points={
        'console_scripts': ['launchpad2trello = launchpad2trello.cli:main']},
    install_requires=[
        'argparse',
        'requests',
        'requests_oauthlib',
        'dogpile.cache'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
    ],
)

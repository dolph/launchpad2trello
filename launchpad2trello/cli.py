import argparse
import json

from launchpad2trello import lp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('project', help='Launchpad project name')

    args = parser.parse_args()

    for task in lp.list_tasks(args.project):
        print(json.dumps(task, indent=2))


if __name__ == '__main__':
    main()

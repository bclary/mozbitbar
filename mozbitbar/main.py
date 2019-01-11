# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function

from mozbitbar import log, recipe_handler
from mozbitbar.cli import cli
from mozbitbar.generate_and_run_recipe import run


def initialize_logging(args={}):
    log.setup_logger(**vars(args))


def main():
    # example of how to call and use Bitbar with this harness.
    # in a taskcluster/treeherder environment, the script will
    # call these methods instead of instead of main().
    args = cli()
    initialize_logging(args)
    run(args)
    recipe_handler.run_recipe(args.recipe)


if __name__ == '__main__':
    main()

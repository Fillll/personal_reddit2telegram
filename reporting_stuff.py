#enconding:utf-8
import logging
import sys
import os

import yaml
from raven import Client
from raven.handlers.logging import SentryHandler
from raven.conf import setup_logging

import utils


with open(os.path.join('configs', 'prod.yml')) as config_file:
    config = yaml.load(config_file.read())


if 'sentry' in config:
    client = Client(config['sentry'], auto_log_stacks=True)
    handler = SentryHandler(client)
    setup_logging(handler)
else:
    client = None
    logging.info('Sentry.io not loaded')


def report_error(fn):
    def wrapper(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except Exception as e:
            if client:  # has sentry instance
                client.captureException()
            else:
                logging.exception('Exception Ignored.')
    return wrapper

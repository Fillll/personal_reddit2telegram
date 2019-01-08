#encoding:utf-8

import datetime
import csv
import logging
from multiprocessing import Process
from datetime import datetime

import yaml
from croniter import croniter
import pymongo

from supplier import supply
from receiver import receive_check_reply


logger = logging.getLogger(__name__)


def read_own_cron(config):
    now = datetime.now()
    mins = now.minute
    users = pymongo.MongoClient(host=config['db']['host'])[config['db']['name']]['users']
    cur_users = users.find({'minute': mins})
    # cur_users = users.find({})
    for item in cur_users:
        supplying_process = Process(target=supply, args=(item['user'], config))
        supplying_process.start()
    receive_check_reply()


def main(config_filename):
    with open(config_filename) as config_file:
        config = yaml.load(config_file.read())
        read_own_cron(config)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/prod.yml')
    args = parser.parse_args()
    main(args.config)

#encoding:utf-8

import importlib
import logging
import random
import time

import yaml
import praw
import pymongo

import utils
from reporting_stuff import report_error
from utils import weighted_random_subreddit


def send_post(submission, r2t):
    return r2t.send_simple(submission,
        text='{title}\n\n{self_text}\n\n{upvotes} upvotes\n/r/{subreddit_name}\n{short_link}',
        other='{title}\n{link}\n\n{upvotes} upvotes\n/r/{subreddit_name}\n{short_link}',
        album='{title}\n{link}\n\n{upvotes} upvotes\n/r/{subreddit_name}\n{short_link}',
        gif='{title}\n\n{upvotes} upvotes\n/r/{subreddit_name}\n{short_link}',
        img='{title}\n\n{upvotes} upvotes\n/r/{subreddit_name}\n{short_link}'
    )


def get_subreddit(user_id, config):
    users = pymongo.MongoClient(host=config['db']['host'])[config['db']['name']]['users']
    user_doc = users.find_one({'user': user_id})
    return weighted_random_subreddit(user_doc['setting'])


@report_error
def supply(user_id, config, is_test=False):
    time.sleep(random.randrange(0, 40))
    reddit = praw.Reddit(
        user_agent=config['reddit']['user_agent'],
        client_id=config['reddit']['client_id'],
        client_secret=config['reddit']['client_secret'],
        username=config['reddit']['username'],
        password=config['reddit']['password']
    )
    subreddit = get_subreddit(user_id, config)
    submissions = reddit.subreddit(subreddit).hot(limit=100)
    channel_to_post = str(user_id)
    r2t = utils.Reddit2TelegramSender(channel_to_post, config)
    success = False
    for submission in submissions:
        link = submission.shortlink
        if r2t.was_before(link):
            continue
        if r2t.too_much_errors(link):
            continue
        success = send_post(submission, r2t)
        if success == utils.SupplyResult.SUCCESSFULLY:
            # Every thing is ok, post was sent
            r2t.mark_as_was_before(link, sent=True)
            break
        elif success == utils.SupplyResult.DO_NOT_WANT_THIS_SUBMISSION:
            # Do not want to send this post
            r2t.mark_as_was_before(link, sent=False)
            continue
        elif success == utils.SupplyResult.SKIP_FOR_NOW:
            # Do not want to send now
            continue
        elif success == utils.SupplyResult.STOP_THIS_SUPPLY:
            # If None — do not want to send anything this time
            break
        else:
            logging.error('Unknown SupplyResult. {}'.format(success))
    if success is False:
        pass


def main(config_filename, sub, is_test=False):
    with open(config_filename) as config_file:
        config = yaml.load(config_file.read())
        supply(sub, config, is_test)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/prod.yml')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--sub')
    args = parser.parse_args()
    main(args.config, args.sub, args.test)

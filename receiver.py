# -*- coding: utf-8 -*-

# from pprint import pprint
from datetime import datetime
import time

import yaml

import utils
import pymongo
from pymongo.collection import ReturnDocument


def reply(bot):
    text = '''Right format:
```
subreddit_1 weight_1
sub_2+sub_3 weight_2
...
subreddit_n weight_n
```'''
    bot.send_text(text, parse_mode='Markdown')


def receive_check_reply(config_filename=None):
    if config_filename is None:
        config_filename = 'configs/prod.yml'
    with open(config_filename) as config_file:
        config = yaml.load(config_file.read())
    r2t = utils.Reddit2TelegramSender('@r_channles_test', config)

    settings = pymongo.MongoClient(host=config['db']['host'])[config['db']['name']]['settings']
    users = pymongo.MongoClient(host=config['db']['host'])[config['db']['name']]['users']
    users.ensure_index([('user', pymongo.ASCENDING)])
    users.ensure_index([('minute', pymongo.ASCENDING)])

    last_update_doc = settings.find_one({
        'settings': 1,
    })

    if last_update_doc is None:
        last_update_doc = {
            'last_update': 0
        }
        settings.insert_one({
            'settings': 1,
            'last_update': 0
        })

    updates = r2t.telepot_bot.getUpdates(offset=last_update_doc['last_update'])

    last_update = 0
    for update in updates:
        # pprint(update)
        time.sleep(2)
        last_update = update['update_id']

        settings.find_one_and_update(
            {
                'settings': 1
            },
            {
                "$set": 
                {
                    'last_update': last_update
                }
            }
        )
        if 'message' not in update:
            continue
        if 'chat' not in update['message']:
            continue
        if 'text' not in update['message']:
            continue

        user_id = update['message']['chat']['id']
        talk_with_user = utils.Reddit2TelegramSender(user_id, config)

        new_setting = dict()
        query = update['message']['text'].split('\n')
        for line in query:
            clean_line = line.strip()
            items = clean_line.split()
            if len(items) != 2:
                reply(talk_with_user)
                return
            subreddit = items[0].strip()
            probalitily = items[1].strip()
            try:
                probalitily = float(probalitily)
            except:
                reply(talk_with_user)
                return
            if probalitily < 0:
                reply(talk_with_user)
                return
            new_setting[subreddit] = probalitily

        users.find_one_and_update(
            {
                'user': user_id
            },
            {
                "$set":
                    {
                        'setting': new_setting,
                        'setting_update_ts': datetime.now(),
                        'minute': sum(int(digit) for digit in str(user_id)) % 40
                    }
            },
            upsert=True
        )
        talk_with_user.send_text('Settings are successfully updated.')

        user_doc = users.find_one({'user': user_id})
        last_date = user_doc.get('last_date', datetime.now())
        if last_date < datetime.now():
            talk_with_user.send_text('Not payed.')
            return


if __name__ == '__main__':
    receive_check_reply()

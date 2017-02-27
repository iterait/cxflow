from .abstract_hook import AbstractHook
from ..nets.abstract_net import AbstractNet

import rethinkdb as r

from datetime import datetime
import json
import logging
from os import path
import pytz


class RethinkDBHook(AbstractHook):
    def __init__(self, net: AbstractNet, config: dict, credentials_file: str, **kwargs):
        super().__init__(net=net, config=config, **kwargs)
        with open(credentials_file, 'r') as f:
            self.credentials = json.load(f)

        logging.debug('Creating setup in the db')
        with r.connect(**self.credentials) as conn:
            response = r.table('setups')\
                        .insert({**config,
                                 **{'timestamp': r.expr(datetime.now(pytz.utc))},
                                 })\
                        .run(conn)
            if response['errors'] > 0:
                logging.error('Error: %s', response['errors'])
                return
            if response['inserted'] != 1:
                logging.error('Inserted unexpected number of documents: %s', response['inserted'])
                return
            self.rethink_id = response['generated_keys'][0]
            logging.debug('Created setup: %s', self.rethink_id)

        with open(path.join(net.log_dir, 'rethink_key.json'), 'w') as f:
            json.dump({'rethink_id': self.rethink_id}, f)

    def before_first_epoch(self, valid_results: dict, test_results: dict = None, **kwargs) -> None:
        logging.debug('Rethink: before first epoch')

        with r.connect(**self.credentials) as conn:
            response = r.table('training')\
                        .insert({**{'valid_{}'.format(key): value for key, value in valid_results.items()},
                                 **{'test_{}'.format(key): value for key, value in test_results.items()},
                                 **{'timestamp': r.expr(datetime.now(pytz.utc))},
                                 **{'setup_id': self.rethink_id},
                                 **{'epoch_id': 0}
                                 })\
                        .run(conn)
            if response['errors'] > 0:
                logging.error('Error: %s', response['errors'])
                return
            if response['inserted'] != 1:
                logging.error('Inserted unexpected number of documents: %s', response['inserted'])
                return
            progress_rethink_id = response['generated_keys'][0]
            logging.debug('Created train. progress: %s', progress_rethink_id)

    def after_epoch(self, epoch_id: int, train_results: dict, valid_results: dict, test_results: dict=None,
                    **kwargs) -> None:
        logging.info('Rethink: after epoch %d', epoch_id)

        with r.connect(**self.credentials) as conn:
            response = r.table('training')\
                        .insert({**{'train_{}'.format(key): value for key, value in train_results.items()},
                                 **{'valid_{}'.format(key): value for key, value in valid_results.items()},
                                 **{'test_{}'.format(key): value for key, value in test_results.items()},
                                 **{'timestamp': r.expr(datetime.now(pytz.utc))},
                                 **{'setup_id': self.rethink_id},
                                 **{'epoch_id': epoch_id}
                                 })\
                        .run(conn)
            if response['errors'] > 0:
                logging.error('Error: %s', response['errors'])
                return
            if response['inserted'] != 1:
                logging.error('Inserted unexpected number of documents: %s', response['inserted'])
                return
            progress_rethink_id = response['generated_keys'][0]
            logging.debug('Created train. progress: %s', progress_rethink_id)
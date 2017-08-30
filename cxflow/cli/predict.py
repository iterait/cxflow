import logging
import os.path as path

from typing import Optional, Iterable

from .util import fallback, validate_config, find_config
from .common import run
from ..utils.config import load_config


def predict(config_path: str, restore_from: Optional[str], cl_arguments: Iterable[str], output_root: str) -> None:
    """
    Run prediction from the specified config path.

    If the config contains a ``predict`` section:
        - override hooks with ``predict.hooks`` if present
        - update dataset, model and main loop sections if the respective sections are present

    :param config_path: path to the config file or the directory in which it is stored
    :param restore_from: backend-specific path to the already trained model to be restored from.
                         If ``None`` is passed, it is inferred from the configuration file location as the directory
                         it is located in.
    :param cl_arguments: additional command line arguments which will update the configuration
    :param output_root: output root in which the training directory will be created
    """
    config = None

    try:
        config_path = find_config(config_path)
        restore_from = restore_from or path.dirname(config_path)
        config = load_config(config_file=config_path, additional_args=cl_arguments)

        if 'predict' in config:
            for section in ['dataset', 'model', 'main_loop']:
                if section in config['predict']:
                    for key in config['predict'][section]:
                        config[section][key] = config['predict'][section][key]
            if 'hooks' in config['predict']:
                config['hooks'] = config['predict']['hooks']

        validate_config(config)

        logging.debug('\tLoaded config: %s', config)
    except Exception as ex:  # pylint: disable=broad-except
        fallback('Loading config failed', ex)

    run(config=config, output_root=output_root, restore_from=restore_from, predict=True)

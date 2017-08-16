"""
Module with hooks saving the trained model under certain criteria.
"""
import logging

import numpy as np

from .abstract_hook import AbstractHook
from ..models.abstract_model import AbstractModel


class SaveEvery(AbstractHook):
    """
    Save the model every `n` epochs.

    -------------------------------------------------------
    Example usage in config
    -------------------------------------------------------
    # save every 10th epoch
    hooks:
      - SaveEvery:
          n_epochs: 10
    -------------------------------------------------------
    # save every epoch and only warn on failure
    hooks:
      - SaveEvery:
          on_failure: warn
    -------------------------------------------------------
    """

    SAVE_FAILURE_ACTIONS = {'error', 'warn', 'ignore'}

    def __init__(self, model: AbstractModel, n_epochs: int=1, on_failure: str='error', **kwargs):
        """
        :param model: trained model
        :param n_epochs: how often is the model saved
        :param on_failure: action to be taken when model fails to save itself;
               one of SaverHook.SAVE_FAILURE_ACTIONS
        """
        assert on_failure in SaveEvery.SAVE_FAILURE_ACTIONS

        super().__init__(model=model, **kwargs)
        self._model = model
        self._n_epochs = n_epochs
        self._on_save_failure = on_failure

    def after_epoch(self, epoch_id: int, **_) -> None:
        """Save the model if epoch_id is divisible by self._save_every_n_epochs."""
        if epoch_id % self._n_epochs == 0:
            SaveEvery.save_model(model=self._model, name_suffix=str(epoch_id), on_failure=self._on_save_failure)

    @staticmethod
    def save_model(model: AbstractModel, name_suffix: str, on_failure: str) -> None:
        """
        Save the given model with the given name_suffix. On failure, take the specified action.
        :param model: the model to be saved
        :param name_suffix: name to be used for saving
        :param on_failure: action to be taken on failure; one of SaverHook.SAVE_FAILURE_ACTIONS

        Raises:
            IOError: on save failure and on_failure='error'
        """
        try:
            logging.debug('Saving the model')
            save_path = model.save(name_suffix)
            logging.info('Model saved to: %s', save_path)
        except Exception as ex:  # pylint: disable=broad-except
            if on_failure == 'error':
                raise IOError('Failed to save the model.') from ex
            elif on_failure == 'warn':
                logging.warning('Failed to save the model.')


class SaveBest(AbstractHook):
    """
    Save the model when it outperforms itself.

    -------------------------------------------------------
    Example usage in config
    -------------------------------------------------------
    # save model with minimal valid loss
    hooks:
      - class: BestSaverHook
    -------------------------------------------------------
    # save model with maximal train accuracy
    hooks:
      - class: SaveBest
        variable: accuracy
        condition: max
        stream: train
    -------------------------------------------------------
    """

    CONDITIONS = {'min', 'max'}

    def __init__(self,  # pylint: disable=too-many-arguments
                 model: AbstractModel, variable: str='loss', condition: str='min', stream: str='valid',
                 aggregation: str='mean', output_name: str='best', on_save_failure: str='error', **kwargs):
        """
        Example: metric=loss, condition=min -> saved the model when the loss is best so far (on `stream`).
        :param model: trained model
        :param variable: variable to be monitored
        :param condition: {min, max}
        :param stream: stream to be monitored
        :param aggregation: which aggregation to used (mean by default)
        :param output_name: suffix of the saved model
        :param on_save_failure: action to be taken when model fails to save itself, one of {'error', 'warn', 'ignore'}
        """

        assert on_save_failure in SaveEvery.SAVE_FAILURE_ACTIONS
        assert condition in SaveBest.CONDITIONS

        super().__init__(**kwargs)
        self._model = model
        self._variable = variable
        self._condition = condition
        self._stream_name = stream
        self._aggregation = aggregation
        self._output_name = output_name
        self._on_save_failure = on_save_failure

        self._best_value = None

    def _get_value(self, epoch_data: AbstractHook.EpochData) -> float:
        """
        Retrieve the value of the monitored variable from the given epoch data.

        Raises:
            KeyError: if any of the specified stream, variable or aggregation is not present in the epoch data.
            TypeError: if the variable value is not a dict when aggregation is specified
            ValueError: if the variable value is not a scalar
        """
        if self._stream_name not in epoch_data:
            raise KeyError('Stream `{}` was not found in the epoch data.\nAvailable streams are `{}`.'
                           .format(self._stream_name, epoch_data.keys()))

        stream_data = epoch_data[self._stream_name]
        if self._variable not in stream_data:
            raise KeyError('Variable `{}` for stream `{}` was not found in the epoch data. '
                           'Available variables for stream `{}` are `{}`.'
                           .format(self._variable, self._stream_name, self._stream_name, stream_data.keys()))

        value = stream_data[self._variable]
        if self._aggregation:
            if not isinstance(value, dict):
                raise TypeError('Variable `{}` is expected to be a dict when aggregation is specified. '
                                'Got `{}` instead.'.format(self._variable, type(value).__name__))
            if self._aggregation not in value:
                raise KeyError('Specified aggregation `{}` was not found in the variable `{}`. '
                               'Available aggregations: `{}`.'.format(self._aggregation, self._variable, value.keys()))
            value = value[self._aggregation]
        if not np.isscalar(value):
            raise ValueError('Variable `{}` value is not a scalar.'.format(value))

        return value

    def _is_value_better(self, new_value: float) -> bool:
        """Test if the new value is better than the best so far."""
        if self._best_value is None:
            return True
        if self._condition == 'min':
            return new_value < self._best_value
        if self._condition == 'max':
            return new_value > self._best_value

    def after_epoch(self, epoch_data: AbstractHook.EpochData, **_) -> None:
        """Save the model if the new value of the monitored variable is better than the best value so far."""
        new_value = self._get_value(epoch_data)

        if self._is_value_better(new_value):
            self._best_value = new_value
            SaveEvery.save_model(model=self._model, name_suffix='best', on_failure=self._on_save_failure)
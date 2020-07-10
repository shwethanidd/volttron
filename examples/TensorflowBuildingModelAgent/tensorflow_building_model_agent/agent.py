"""
"""

__docformat__ = 'reStructuredText'

from datetime import datetime
import gevent
import logging
import sys
import tensorflow as tf
import numpy as np
import pandas as pd
import numpy as np
from .dataset import generate_train_samples
from .dataset import generate_test_samples

from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core, RPC

_log = logging.getLogger(__name__)
utils.setup_logging()
__version__ = "0.1"


def tensorflow_agent(config_path, **kwargs):
    """Parses the Agent configuration and returns an instance of
    the agent created using that configuration.

    :param config_path: Path to a configuration file.

    :type config_path: str
    :returns: TensorflowBuildingModelAgent
    :rtype: TensorflowBuildingModelAgent
    """
    try:
        config = utils.load_config(config_path)
    except Exception:
        config = {}

    if not config.get("building_data_path"):
        raise ValueError("Configuration must have a path to building data csv.")
    building_data_path = config.get("building_data_path")

    return TensorflowBuildingModelAgent(config, building_data_path, **kwargs)


class TensorflowBuildingModelAgent(Agent):
    """
    Agent that shows how to load the trained building model for predicting power consumption
    """
    def __init__(self, config, hostport, **kwargs):
        super(TensorflowBuildingModelAgent, self).__init__(enable_store=True, **kwargs)
        default_config = {
            "main_model_path": "model/seq2seq_building1/1/",
            "encoder_model_path": "model/s2s_encoder_building1/1/",
            "decoder_model_path": "model/s2s_decoder_building1/1/",
            "building_data_path": "data/LSTM_3860_New_5min.csv"
        }
        if config:
            default_config.update(config)
        self.default_config = default_config
        
        self.vip.config.set_default("config", self.default_config)
        self.vip.config.subscribe(self.configure_main,
                                  actions=["NEW", "UPDATE"],
                                  pattern="config")
        self.config_update = False
        self.y_mean = None
        self.y_std = None

    def configure_main(self, config_name, action, contents, **kwargs):
        config = self.default_config.copy()
        config.update(contents)
        _log.debug("Update agent %s configuration -- config --  %s -- action -- %s", self.core.identity, config, action)
        if action == "NEW" or "UPDATE":
            self.main_model_path = config.get("main_model_path")
            self.encoder_model_path = config.get("encoder_model_path")
            self.decoder_model_path = config.get("decoder_model_path")
            self.config_update = True
            prediction = self.prediction_request()

    def prediction_request(self):
        self.core.spawn_later(5, self.predict_building_power)

    def predict_building_power(self):
        loaded_encoder = tf.saved_model.load(self.encoder_model_path)
        loaded_decoder = tf.saved_model.load(self.decoder_model_path)
        input_dim = 6
        output_dim = 1
        input_seq_len = 60 * input_dim
        output_seq_len = 60 * output_dim
        Train_size = 0.9
        df = pd.read_csv(self.main_model_path)
        Data_raw = pd.DataFrame(df)
        Data_raw = Data_raw.set_index(Data_raw.columns[0])
        Data_raw.index = pd.to_datetime(Data_raw.index)

        Data = Data_raw
        Data['hr_sin'] = np.round(np.sin(Data.index.hour * (2. * np.pi / 24)), decimals=2)
        Data['hr_cos'] = np.round(np.cos(Data.index.hour * (2. * np.pi / 24)), decimals=2)
        Data['wk_sin'] = np.round(np.sin((Data.index.weekday - 1) * (2. * np.pi / 12)), decimals=2)
        Data['wk_cos'] = np.round(np.cos((Data.index.weekday - 1) * (2. * np.pi / 12)), decimals=2)
        Data = Data.reset_index()

        df = Data
        df = df.drop('Time', 1)
        df.Power = df.Power.shift(-output_seq_len)
        df = df.replace('', np.nan, regex=True)
        df = df.dropna()
        df.to_csv('/tmp/BldgRawData.csv', sep=',', float_format='%.2f')
        _log.debug(df.head())

        Train_index = int(len(df) * (Train_size))
        df_test = df.iloc[Train_index:, :].copy()
        X_test = df_test.loc[:, df.columns[0:]].values.copy()
        y_test = df_test['Power'].values.copy().reshape(-1, 1)
        y_train = df_train['Power'].values.copy().reshape(-1, 1)

        ## z-score transform y
        self.y_main_model_path = y_train.mean()
        self.y_std = y_train.std()
        test_x, test_y = generate_test_samples(X_test, y_test, input_seq_len, output_seq_len)
        _log.debug("Loading encoder model")
        loaded_encoder = tf.saved_model.load(self.encoder_model_path)
        _log.debug("Loading decoder model")
        loaded_decoder = tf.saved_model.load(self.decoder_model_path)
        _log.debug("Loading model to get power prediction: ")
        predicted_values = self.decode_sequence(loaded_encoder, loaded_decoder, output_dim,
                                                test_x[0:2])  # - np.squeeze(test_y[0:1])
        _log.debug("Predicted values using decode sequence: {}".format(predicted_values))

    def decode_sequence(self, encoder_model, decoder_model, output_dim, input_seq, output_seq_len):

        # Encode the input as state vectors.
        states_value = encoder_model(tf.constant(input_seq, dtype=tf.float32))

        # Generate empty target sequence of length 1.
        target_seq = np.zeros((1, 1, output_dim))

        stop_condition = False
        predicted_values = np.zeros((input_seq.shape[0], output_seq_len))
        _log.debug("Running decoder sequence model: ")
        for i in range(output_seq_len):
            _log.debug("Running for iteration: {}".format(i))
            output_tokens, h, c = decoder_model(
                [tf.constant(target_seq, dtype=tf.float32)] + states_value)

            # print(output_tokens)
            predicted_values[:, i] = output_tokens[0, -1, 0].numpy()

            # Update the target sequence (of length 1).
            target_seq = np.zeros((1, 1, output_dim))
            # target_seq[0, 0, sampled_token_index] = 1.

            # Update states
            states_value = [h, c]
            # reverse transform the values
            predicted_values = predicted_values * self.y_mean + self.y_std
        return predicted_values


def main():
    """Main method called to start the agent."""
    utils.vip_main(tensorflow_agent, version=__version__)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass

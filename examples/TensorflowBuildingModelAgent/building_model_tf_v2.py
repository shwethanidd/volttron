import tensorflow as tf
from tensorflow import keras

# tf 2.2.0
tf.__version__

# from keras.layers import Input, LSTM

def seq2seq_model_builder(input_dim, output_dim, num_stacked_layers, hidden_dim, learning_rate, clipvalue):
    encoder_inputs = keras.layers.Input(shape=(None, input_dim), dtype='float32',)
    # encoder_inputs = embed_layer(encoder_inputs)
    #encoder_model = keras.Sequential()
    #for i in range(num_stacked_layers):
    #    if i < num_stacked_layers-1:
    #        encoder_model.add(keras.layers.LSTM(hidden_dim, return_state=True, return_sequences=True))
    #    else:
    #        encoder_model.add(keras.layers.LSTM(hidden_dim, return_state=True))
    encoder_model = keras.layers.LSTM(hidden_dim, return_state=True)
    encoder_outputs, state_h, state_c = encoder_model(encoder_inputs)
    
    decoder_inputs = keras.layers.Input(shape=(None, output_dim), dtype='float32',)
    # decoder_inputs = embed_layer(decoder_inputs)
    #decoder_model = keras.Sequential()
    #for i in range(num_stacked_layers):
    #    if i < num_stacked_layers-1:
    #        decoder_model.add(keras.layers.LSTM(hidden_dim, return_state=True, return_sequences=True))
    #    else:
    #        decoder_model.add(keras.layers.LSTM(hidden_dim, return_state=True, return_sequences=True))
    decoder_model = keras.layers.LSTM(hidden_dim, return_state=True, return_sequences=True)
    decoder_outputs, _, _ = decoder_model(decoder_inputs, initial_state=[state_h, state_c])
    
    decoder_dense = keras.layers.Dense(output_dim)
    decoder_outputs = decoder_dense(decoder_outputs)
    
    # dense_layer = Dense(VOCAB_SIZE, activation='softmax')
    # outputs = TimeDistributed(Dense(VOCAB_SIZE, activation='softmax'))(decoder_outputs)
    model = keras.Model([encoder_inputs, decoder_inputs], decoder_outputs)
    
    opt = keras.optimizers.Adam(learning_rate=learning_rate, clipvalue=clipvalue)
    model.compile(optimizer=opt, loss='mse', metrics=['mse'])
    
    return model

    # pip install gast==0.2.2
# tensorflow ==1.14

import tensorflow as tf
import platform
import numpy as np
import random
import math
import os
import copy
import pandas as pd
import numpy as np

# from build_model_with_outliers import build_graph
from dataset import generate_train_samples
from dataset import generate_test_samples


# print(f"PLATFORM:\n---------\n{platform.platform()}")
# print("\nTENSORFLOW:\n----------")
# for a in tf.version.__all__:
#     print(f"{a}: {getattr(tf.version, a)}")

# print(f"\nNUMPY:\n-----\n{np.version.version}")

# print(f"\nPYTHON:\n-------\n{sys.version}\n")


# Dic = '../data/3860_Data/'
Dic = './data/'
File = 'LSTM_Building1_New_5min'

# Data Format Parameters
input_dim = 6
output_dim = 1

input_seq_len = 60 * input_dim
output_seq_len = 60 * output_dim
Train_size = 0.9

# Training Paramters
total_iteractions = 5
batch_size = 64
KEEP_RATE = 0.5

## LSTM Network Parameters
# size of LSTM Cell
hidden_dim = 64 *2
# num of stacked lstm layers
num_stacked_layers = 3 * 2 


df = pd.read_csv(Dic + File + '.csv')
Data_raw = pd.DataFrame(df)
Data_raw = Data_raw.set_index(Data_raw.columns[0])
Data_raw.index = pd.to_datetime(Data_raw.index)

Data = Data_raw
Data['hr_sin'] = np.round(np.sin(Data.index.hour*(2.*np.pi/24)),decimals=2)
Data['hr_cos'] = np.round(np.cos(Data.index.hour*(2.*np.pi/24)),decimals=2)
Data['wk_sin'] = np.round(np.sin((Data.index.weekday-1)*(2.*np.pi/12)),decimals=2)
Data['wk_cos'] = np.round(np.cos((Data.index.weekday-1)*(2.*np.pi/12)),decimals=2)
Data = Data.reset_index()

df = Data
df = df.drop('Time', 1)
df.Power = df.Power .shift(-output_seq_len)
df = df.replace('',np.nan, regex=True)
df = df.dropna()
df.to_csv(Dic+ '{}_BldgRawData.csv'.format(File), sep=',', float_format='%.2f')
print(df.head())

Train_index = int(len(df)*(Train_size))
df_train = df.iloc[:Train_index, :].copy()
df_test = df.iloc[Train_index:, :].copy()
X_train = df_train.loc[:, df.columns[0:]].values.copy()
X_test = df_test.loc[:, df.columns[0:]].values.copy()
y_train = df_train['Power'].values.copy().reshape(-1, 1)
y_test = df_test['Power'].values.copy().reshape(-1, 1)
print (len(X_train), len(X_test), X_train.shape[1])

for i in range(X_train.shape[1] - 4):
    temp_mean = X_train[:, i].mean()
    temp_std = X_train[:, i].std()
    X_train[:, i] = (X_train[:, i] - temp_mean) / temp_std
    X_test[:, i] = (X_test[:, i] - temp_mean) / temp_std

## z-score transform y
y_mean = y_train.mean()
y_std = y_train.std()
y_train = (y_train - y_mean) / y_std
y_test = (y_test - y_mean) / y_std

x, y = generate_train_samples(X_train, y_train, input_seq_len, output_seq_len, batch_size = batch_size)
print(x.shape, y.shape)
test_x, test_y = generate_test_samples(X_test, y_test, input_seq_len, output_seq_len)
print("test_x: {}, shape: {}, test_y shape: {}".format(test_x, test_x.shape, test_y.shape))
print("test_x: {}".format(test_x))

test_x2 = test_x.reshape(test_x.shape[0],test_x.shape[1]*test_x.shape[2])

train_x, train_y = generate_test_samples(X_train, y_train, input_seq_len, output_seq_len)
train_x.shape, train_y.shape

train_input_y = np.zeros(train_y.shape)
train_input_y[:,1::,:] = train_y[:,:-1,:]
train_input_y.shape

test_input_y = np.zeros(test_y.shape)
test_input_y[:,1::,:] = test_y[:,:-1,:]
test_input_y.shape

## Parameters
learning_rate = 0.01
lambda_l2_reg = 0.003  

# gradient clipping - to avoid gradient exploding
clipvalue = 2.5

epochs = 2

# encoder model
encoder_inputs = keras.layers.Input(shape=(None, input_dim), dtype='float32',)
encoder_model = keras.layers.LSTM(hidden_dim, return_state=True)
encoder_outputs, state_h, state_c = encoder_model(encoder_inputs)
encoder_states = [state_h, state_c]

# decoder model GRU, LSTM
decoder_inputs = keras.layers.Input(shape=(None, output_dim), dtype='float32',)
decoder_model = keras.layers.LSTM(hidden_dim, return_state=True, return_sequences=True)
decoder_outputs, _, _ = decoder_model(decoder_inputs, initial_state=encoder_states)

decoder_dense = keras.layers.Dense(output_dim)
decoder_outputs = decoder_dense(decoder_outputs)

# seq2seq model for training
model = keras.Model([encoder_inputs, decoder_inputs], decoder_outputs)

# model training
opt = keras.optimizers.Adam(learning_rate=learning_rate, clipvalue=clipvalue)
model.compile(optimizer=opt, loss='mse', metrics=['mse'])
model.summary()

# model = seq2seq_model_builder(input_dim, output_dim, num_stacked_layers, hidden_dim, learning_rate, clipvalue)

callback = keras.callbacks.EarlyStopping(monitor='loss', patience=2)
model.fit([np.array(train_x),np.array(train_input_y)], np.array(train_y),
          batch_size=batch_size,
          epochs=epochs, callbacks=[callback],
          validation_split=0.2)

# Save model
# model.save('seq2seq_3860.h5')
# seq2seq
tf.saved_model.save(model, "data/seq2seq_Building1/1/")


test_loss, test_acc = model.evaluate([test_x, test_input_y], test_y)
print('\nTest accuracy: {}'.format(test_acc))

import numpy as np
np.sqrt(0.0161)

encoder_model = keras.Model(encoder_inputs, encoder_states)

decoder_state_input_h = keras.layers.Input(shape=(hidden_dim,))
decoder_state_input_c = keras.layers.Input(shape=(hidden_dim,))
decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]

decoder_outputs, state_h, state_c = decoder_model(
  decoder_inputs, initial_state=decoder_states_inputs)
decoder_states = [state_h, state_c]
decoder_outputs = decoder_dense(decoder_outputs)

decoder_model = keras.Model(
  [decoder_inputs] + decoder_states_inputs,
  [decoder_outputs] + decoder_states)


tf.saved_model.save(encoder_model, "data/s2s_encoder_Building1/1/")
tf.saved_model.save(decoder_model, "data/s2s_decoder_Building1/1/")

def decode_sequence(encoder_model, decoder_model, output_dim, input_seq):
    # Encode the input as state vectors.
    states_value = encoder_model(tf.constant(input_seq, dtype=tf.float32))

    # Generate empty target sequence of length 1.
    target_seq = np.zeros((1, 1, output_dim))
    # Populate the first character of target sequence with the start character.
    # target_seq[0, 0, target_token_index['\t']] = 1.

    # Sampling loop for a batch of sequences
    # (to simplify, here we assume a batch of size 1).
    stop_condition = False
    predicted_values = np.zeros((input_seq.shape[0],output_seq_len))
    for i in range(output_seq_len):
        output_tokens, h, c = decoder_model(
            [tf.constant(target_seq, dtype=tf.float32)] + states_value)

        #print(output_tokens)
        predicted_values[:,i] = output_tokens[0, -1, 0].numpy()
        
        # Update the target sequence (of length 1).
        target_seq = np.zeros((1, 1, output_dim))
        # target_seq[0, 0, sampled_token_index] = 1.

        # Update states
        states_value = [h, c]

    return predicted_values

loaded_encoder = tf.saved_model.load("data/s2s_encoder_Building1/1/")
loaded_decoder = tf.saved_model.load("data/s2s_decoder_Building1/1/")

#loaded_encoder(tf.constant(test_x[0:3], dtype=tf.float32))
predicted_values = decode_sequence(loaded_encoder, loaded_decoder, output_dim, test_x[0:2])# - np.squeeze(test_y[0:1])
predicted_values = predicted_values * y_std + y_mean

print("Predicted values using decode sequence: {}".format(predicted_values))
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            




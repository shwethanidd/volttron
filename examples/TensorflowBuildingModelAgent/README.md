# Tensorflow Building Model Agent

This is an example agent demonstrating how a VOLTTRON agent can run a trained building power prediction model to get 
building power predictions. The model used here is seq2seq LSTM (encoder decoder) machine learning model.
For more information about seq2seq LSTM model, please refer to tutorial in 
https://towardsdatascience.com/how-to-implement-seq2seq-lstm-model-in-keras-shortcutnlp-6f355f3e5639

# Installing pre-requisite packages
1. Go to VOLTTRON source directory. Activate the environment and Install Tensorflow within the activated environment.

    a. Install Tensorflow python package

    ```
    pip install --upgrade pip
    pip install tensorflow==2.1.0
    ```
   b. Install numpy and pandas
   ```
   pip install numpy
   pip install pandas
   ```

3. On another terminal, from the root of the VOLTTRON source, run the below script to create building power prediction 
   models (encoder and decoder models). This will create the models - "s2s_decoder_Building1", "s2s_encoder_Building1", "seq2seq_Building1" in 
   examples/TensorflowBuildingModelAgent/data folder.
    
   ```
   python examples/TensorflowBuildingModelAgent/building_model_tf_v2.py
   ```

## Tensorflow Agent Configuration

You can specify the configuration in  yaml format.  The yaml format is specified
below. 

```` yml
#LSTM encoder model path
encoder_model_path: ~/git/volttron/examples/TensorflowBuildingModelAgent/data/s2s_encoder_Building1/1/
#LSTM decoder model path
decoder_model_path: ~/git/volttron/examples/TensorflowBuildingModelAgent/data/s2s_decoder_Building1/1
#Raw building power and outdoor air temperature dataset
building_data_path: ~/git/volttron/examples/TensorflowBuildingModelAgent/data/LSTM_Building1_New_5min.csv
````

## Run the agent

1. Start the VOLTTRON platform

```
source env/bin/activate
./start-volttron
```

2. Start the tensorflow building model agent. The agent runs previously trained LSTM encoder and decoder models to predict building power

```
python scripts/install-agent.py -s examples/TensorflowBuildingModelAgent/ -c examples/TensorflowBuildingModelAgent/config.yml -i tensorflowbuildingagent --start
```

Check for prediction values in volttron.log

```
2020-07-11 15:59:25,261 (tensorflow_building_model_agentagent-0.1 3996) __main__ DEBUG: Predicted values using decode sequence: [[32.51015471 32.74936554 32.91824079 33.01002395 33.02244648 32.99464505
  32.95286922 32.89792642 32.82234242 32.72315551 32.60246549 32.46401053
  32.31115181 32.14663208 31.97291855 31.79237162 31.60718826 31.41932089
  31.23042177 31.04178754 30.85423738 30.66790159 30.48193215 30.29410002
  30.10028145 29.89372315 29.66391866 29.39465334 29.06042475 28.61958521
  28.00071507 27.07587115 25.6214896  23.37310841 20.61145304 18.49535939
  17.23050604 16.54152194 16.24035547 16.08734562 15.96527941 15.76005403
  15.50316798 15.32836397 15.27373678 15.27543659 15.27649823 15.27794224
  15.30409566 15.36330427 15.44649707 15.54339621 15.64999701 15.76462316
  15.88310605 15.99858718 16.10381286 16.19272617 16.26082952 16.30527282]
 [32.51015471 32.74936554 32.91824079 33.01002395 33.02244648 32.99464505
  32.95286922 32.89792642 32.82234242 32.72315551 32.60246549 32.46401053
  32.31115181 32.14663208 31.97291855 31.79237162 31.60718826 31.41932089
  31.23042177 31.04178754 30.85423738 30.66790159 30.48193215 30.29410002
  30.10028145 29.89372315 29.66391866 29.39465334 29.06042475 28.61958521
  28.00071507 27.07587115 25.6214896  23.37310841 20.61145304 18.49535939
  17.23050604 16.54152194 16.24035547 16.08734562 15.96527941 15.76005403
  15.50316798 15.32836397 15.27373678 15.27543659 15.27649823 15.27794224
  15.30409566 15.36330427 15.44649707 15.54339621 15.64999701 15.76462316
  15.88310605 15.99858718 16.10381286 16.19272617 16.26082952 16.30527282]]

```


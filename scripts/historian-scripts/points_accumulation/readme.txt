Instructions to run the script

1. Activate VOLTTRON environment
. env/bin/activate

2. Run the script by passing building name and masterdriver config path for that vuilding as input parameters
python accumulate_points.py SIGMA2 /home/volttron/MasterPointsList/SIGMA2

3. Output file containing all the device points and related meta data for that building gets generated in current folder.
For example: SIGMA2_points.csv
import pandas as pd
from datetime import datetime
import pytz
import os

#df2 = pd.read_csv('historian_anon-5903a6c2c56e526f26bea9de.csv', index_col=None)
#df2 = pd.read_csv('his.csv', index_col=None)
rootdir = 'import'
if not os.path.exists('new_import'):
    os.makedirs('new_import')

for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        print file
        fl = os.path.join(subdir, file)
        df2 = pd.read_csv(fl, index_col=None)
        try:
            def string_to_date(x):
                try:
                    # x = x[:-1]
                    temp = datetime.strptime(
                        x,
                        '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=pytz.utc)
                except TypeError:
                    raise
                except ValueError:
                    x += '.000'
                return x

            try:
                df2['ts'] = df2['ts'].map(lambda x: string_to_date(x))
                df2.to_csv('new_import/'+file, mode='w', header=True, index=False)
            except TypeError:
                df2.to_csv('new_import/' + file, mode='w', header=True, index=False)
                pass
            #df2['ts'] = pd.to_datetime(df2['ts'])

            # dg = pd.read_csv('dsf.csv', index_col=None)
            # dg['ts'] = dg['ts'].map(lambda x: string_to_date(x))
            # #dg['ts'] = pd.to_datetime(dg['ts'], format='%Y-%m-%d %H:%M:%S.%f', exact=True)
            # dg.to_csv('xms.csv', mode='w', header=False, index=False)
        except ValueError:
            pass
        except TypeError as exc:
            print("TypeError in {}".format(exc))
            pass
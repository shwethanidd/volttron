# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:

import pstats, cProfile

import time
start_time = time.time()
from dicttest2 import subscribe, publishtest, my_devices_callback, my_records_callback

def main():
    # pubsub = PubSub()
    # pubsub.subscribe('pubsub', 'devices', pubsub.my_devices_callback, '')
    # pubsub.subscribe('pubsub', 'records', pubsub.my_records_callback, '')
    # cProfile.runctx("pubsub.publishtest()", globals(), locals(), "Profile.prof")

    subscribe('pubsub', 'devices', my_devices_callback, 'bus1')
    subscribe('xpub', 'records', my_records_callback, 'bus2')
    cProfile.runctx("publishtest()", globals(), locals(), "Profile.prof")
    s = pstats.Stats("Profile.prof")
    s.strip_dirs().sort_stats("time").print_stats()
    #pubsub.publishtest()

    print("Time: {}".format(time.time() - start_time))

if __name__ == "__main__":
    main()
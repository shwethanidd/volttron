# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:

import pstats, cProfile

import time
from dicttest3 import subscribe, publishtest, my_devices_callback, my_records_callback

def main():
    start_time = time.time()
    subscribe("pubsub", "devices", my_devices_callback, "bus1")
    subscribe("pubsub", "records", my_records_callback, "bus1")
    cProfile.runctx("publishtest()", globals(), locals(), "Profile.prof")
    s = pstats.Stats("Profile.prof")
    s.strip_dirs().sort_stats("time").print_stats()
    #pubsub.publishtest()

    print("Time: {}".format(time.time() - start_time))

if __name__ == "__main__":
    main()
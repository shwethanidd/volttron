Platform Historian
==================

A platform historian is a
:doc:`"friendly named" <../messagebus/VIP/VIP-Known-Identities>`
historian on a VOLTTRON instance. It always has the identity
of platform.historian. A platform
historian is made available to a VOLTTRON central agent for monitoring
of the VOLTTRON instances health and plotting topics from the platform
historian. In order for one of the :doc:`historians <./>` to be turned
into a platform historian the identity keyword must be added to it's
configuration file with the value of platform.historian. The following
configuration file shows a sqlite based platform historian
configuration.

::

    {
        "agentid": "sqlhistorian-sqlite",
        "identity": "platform.historian",
        "connection": {
            "type": "sqlite",
            "params": {
                "database": "~/.volttron/data/platform.historian.sqlite"
            }
        }
    }

The platform historian will publish data about the current environment
to the following topics. These topics can be pasted into the volttron
central environment and will be able to be graphed appropriately.

+---------+-----------------------------------------------------------------+
| Index   | Topic                                                           |
+=========+=================================================================+
| 1       | datalogger/log/platform/status/cpu/times_percent/guest_nice     |
+---------+-----------------------------------------------------------------+
| 2       | datalogger/log/platform/status/cpu/times_percent/system         |
+---------+-----------------------------------------------------------------+
| 3       | datalogger/log/platform/status/cpu/percent                      |
+---------+-----------------------------------------------------------------+
| 4       | datalogger/log/platform/status/cpu/times_percent/irq            |
+---------+-----------------------------------------------------------------+
| 5       | datalogger/log/platform/status/cpu/times_percent/steal          |
+---------+-----------------------------------------------------------------+
| 6       | datalogger/log/platform/status/cpu/times_percent/user           |
+---------+-----------------------------------------------------------------+
| 7       | datalogger/log/platform/status/cpu/times_percent/nice           |
+---------+-----------------------------------------------------------------+
| 8       | datalogger/log/platform/status/cpu/times_percent/iowait         |
+---------+-----------------------------------------------------------------+
| 9       | datalogger/log/platform/status/cpu/times_percent/idle           |
+---------+-----------------------------------------------------------------+
| 10      | datalogger/log/platform/status/cpu/times_percent/guest          |
+---------+-----------------------------------------------------------------+
| 11      | datalogger/log/platform/status/cpu/times_percent/softirq        |
+---------+-----------------------------------------------------------------+


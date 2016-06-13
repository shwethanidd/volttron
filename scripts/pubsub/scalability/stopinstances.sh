#!/usr/bin/env bash

VOLTTRON_HOME=~/testing/pubsub/v1 volttron-ctl shutdown --platform
VOLTTRON_HOME=~/testing/pubsub/v2 volttron-ctl shutdown --platform
VOLTTRON_HOME=~/testing/pubsub/v3 volttron-ctl shutdown --platform
VOLTTRON_HOME=~/testing/pubsub/v4 volttron-ctl shutdown --platform
VOLTTRON_HOME=~/testing/pubsub/v5 volttron-ctl shutdown --platform
VOLTTRON_HOME=~/testing/pubsub/v6 volttron-ctl shutdown --platform

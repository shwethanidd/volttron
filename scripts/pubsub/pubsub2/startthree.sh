#!/usr/bin/env bash

vhome3=/tmp/v3
vip3=tcp://127.0.0.3:22916
volttronpub3=tcp://127.0.0.3:5000
volttronsub3=tcp://127.0.0.3:5001
v3log="$vhome3/volttron.log"
mkdir -p $vhome3

echo "Creating instances with $vhome1 and $vhome2"
echo "V3"
echo "home: $vhome3"
echo "vip: $vip3"
echo "pub: $volttronpub3"
echo "sub: $volttronsub3"
echo "--------------------------------------"

prefix="VOLTTRON_HOME=$vhome3 VOLTTRON_VIP_ADDR=$vip3 "
prefix="$prefix VOLTTRON_PUB_ADDR=$volttronpub3 "
prefix="$prefix VOLTTRON_SUB_ADDR=$volttronsub3"

sh -c "$prefix volttron -vv -l $vhome3/volttron.log&"

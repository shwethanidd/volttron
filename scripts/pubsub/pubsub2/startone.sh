#!/usr/bin/env bash

vhome1=/tmp/v1
vip1=tcp://127.0.0.1:22916
volttronpub1=tcp://127.0.0.1:5000
volttronsub1=tcp://127.0.0.1:5001
v1log="$vhome1/volttron.log"
mkdir -p $vhome1

echo "Creating instances with $vhome1 and $vhome2"
echo "V1"
echo "home: $vhome1"
echo "vip: $vip1"
echo "pub: $volttronpub1"
echo "sub: $volttronsub1"
echo "--------------------------------------"

prefix="VOLTTRON_HOME=$vhome1 VOLTTRON_VIP_ADDR=$vip1 "
prefix="$prefix VOLTTRON_PUB_ADDR=$volttronpub1 "
prefix="$prefix VOLTTRON_SUB_ADDR=$volttronsub1"

sh -c "$prefix volttron -vv -l $vhome1/volttron.log&"

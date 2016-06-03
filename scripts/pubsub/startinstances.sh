#!/usr/bin/env bash

vhome1=/tmp/v1
vip1=tcp://127.0.0.1:22916
volttronpub1=tcp://127.0.0.1:5000
volttronsub1=tcp://127.0.0.1:5001
v1log="$vhome1/volttron.log"
mkdir -p $vhome1

vhome2=/tmp/v2
vip2=tcp://127.0.0.2:22916
volttronpub2=tcp://127.0.0.2:5000
volttronsub2=tcp://127.0.0.2:5001
v2log="$vhome2/volttron.log"
mkdir -p $vhome2

echo "Creating instances with $vhome1 and $vhome2"
echo "V1"
echo "home: $vhome1"
echo "vip: $vip1"
echo "pub: $volttronpub1"
echo "sub: $volttronsub1"
echo "--------------------------------------"
echo "V2"
echo "home: $vhome2"
echo "vip: $vip2"
echo "pub: $volttronpub2"
echo "sub: $volttronsub2"

prefix="VOLTTRON_HOME=$vhome1 VOLTTRON_VIP_ADDR=$vip1 "
prefix="$prefix VOLTTRON_PUB_ADDR=$volttronpub1 "
prefix="$prefix VOLTTRON_SUB_ADDR=$volttronsub1"

sh -c "$prefix volttron -vv -l $vhome1/volttron.log&"

prefix="VOLTTRON_HOME=$vhome2 VOLTTRON_VIP_ADDR=$vip2 "
prefix="$prefix VOLTTRON_PUB_ADDR=$volttronpub2 "
prefix="$prefix VOLTTRON_SUB_ADDR=$volttronsub2"

sh -c "$prefix volttron -vv -l $vhome2/volttron.log&"


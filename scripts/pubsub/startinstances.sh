#!/usr/bin/env bash

vhome1=/tmp/v1
vip1=tcp://127.0.0.1:22916
volttronpub1=tcp://127.0.0.1:5000
volttronsub1=tcp://127.0.0.1:5001
volttronweb1=http://127.0.0.1:8080
v1log="$vhome1/volttron.log"
mkdir -p $vhome1
cat >$vhome1/config <<EOL
[volttron]
vip-address = $vip1
bind-web-address = $volttronweb1
publish-address = $volttronpub1
subscribe-address = $volttronsub1
EOL


vhome2=/tmp/v2
vip2=tcp://127.0.0.2:22916
volttronpub2=tcp://127.0.0.2:5000
volttronsub2=tcp://127.0.0.2:5001
volttronweb2=http://127.0.0.2:8080
v2log="$vhome2/volttron.log"
mkdir -p $vhome2
cat >$vhome2/config <<EOL
[volttron]
vip-address = $vip2
bind-web-address = $volttronweb2
publish-address = $volttronpub2
subscribe-address = $volttronsub2
EOL

vhome3=/tmp/v3
vip3=tcp://127.0.0.3:22916
volttronpub3=tcp://127.0.0.3:5000
volttronsub3=tcp://127.0.0.3:5001
volttronweb3=http://127.0.0.3:8080
v2log="$vhome3/volttron.log"
mkdir -p $vhome3
cat >$vhome3/config <<EOL
[volttron]
vip-address = $vip3
bind-web-address = $volttronweb3
publish-address = $volttronpub3
subscribe-address = $volttronsub3
EOL

echo "Creating instances with $vhome1 and $vhome2"
echo "V1"
echo "home: $vhome1"
echo "vip: $vip1"
echo "pub: $volttronpub1"
echo "sub: $volttronsub1"
echo "web: $volttronweb1"
echo "--------------------------------------"
echo "V2"
echo "home: $vhome2"
echo "vip: $vip2"
echo "pub: $volttronpub2"
echo "sub: $volttronsub2"
echo "web: $volttronweb2"
echo "--------------------------------------"
echo "V3"
echo "home: $vhome3"
echo "vip: $vip3"
echo "pub: $volttronpub3"
echo "sub: $volttronsub3"
echo "web: $volttronweb3"

prefix="VOLTTRON_HOME=$vhome1 "
#prefix="$prefix VOLTTRON_PUB_ADDR=$volttronpub1 "
#prefix="$prefix VOLTTRON_SUB_ADDR=$volttronsub1"

sh -c "$prefix volttron -vv -l $vhome1/volttron.log&"

sleep 1
prefix="VOLTTRON_HOME=$vhome2 "
#prefix="$prefix VOLTTRON_PUB_ADDR=$volttronpub2 "
#prefix="$prefix VOLTTRON_SUB_ADDR=$volttronsub2"

sh -c "$prefix volttron -vv -l $vhome2/volttron.log&"

prefix="VOLTTRON_HOME=$vhome3 "
#prefix="$prefix VOLTTRON_PUB_ADDR=$volttronpub3 "
#prefix="$prefix VOLTTRON_SUB_ADDR=$volttronsub3"

sh -c "$prefix volttron -vv -l $vhome3/volttron.log&"

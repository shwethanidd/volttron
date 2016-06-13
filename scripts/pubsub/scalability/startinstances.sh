\#!/usr/bin/env bash

echo "Creating instances with v1 through v4"
max=6
for (( i=1; i <= $max; ++i ))
do
    vhome=~/testing/pubsub/v$i
    vip=tcp://127.0.0.$i:22916
    volttronpub=tcp://127.0.0.$i:5000
    volttronsub=tcp://127.0.0.$i:5001
    volttronweb=http://127.0.0.$i:8080
    mkdir -p $vhome
    cat >$vhome/config <<EOL
[volttron]
vip-address = $vip
bind-web-address = $volttronweb
publish-address = $volttronpub
subscribe-address = $volttronsub
EOL
echo "--------------------------------------"
    echo "V$i"
    echo "home: $vhome"
    echo "vip: $vip"
    echo "pub: $volttronpub"
    echo "sub: $volttronsub"
    echo "web: $volttronweb"
done

echo "Starting instances v1 through v4"
for (( i=1; i <= $max; ++i ))
do
    vhome=~/testing/pubsub/v$i
    prefix="VOLTTRON_HOME=$vhome "
    sh -c "$prefix volttron -vv -l $vhome/volttron.log&"
done

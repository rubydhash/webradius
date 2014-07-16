#!/bin/bash

INTERFACE=lo
RESULT_FILE=resultrelease

if [ $# -eq 0 ]
then
  echo "No arguments supplied"
  exit 1
fi

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

COUNT=0

# Libera os IPs
while read line
do
  MAC=$( echo $line | cut -d ' ' -f1 )
  NAME="hostname"${COUNT}
  COUNT=$( expr $COUNT + 1 )
  ./simulate_dhcp_release.sh $MAC $INTERFACE $NAME > /dev/null 2>&1 &
done <$1

sleep 15

echo ""
echo "Testing DNS.."

./test_dns_entrys.sh $1

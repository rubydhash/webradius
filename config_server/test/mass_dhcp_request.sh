#!/bin/bash

INTERFACE=lo
RESULT_FILE=result

if [ $# -eq 0 ]
then
  echo "No arguments supplied"
  exit 1
fi

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

rm -f $RESULT_FILE 1> /dev/null 2>&1
date1=$(date +"%s")
date > $RESULT_FILE
COUNT=0

while read line
do
  MAC=$( echo $line | cut -d ' ' -f1 )
  NAME="hostname"${COUNT}
  COUNT=$( expr $COUNT + 1 )
  ./simulate_dhcp_request.sh $MAC $INTERFACE $NAME >> $RESULT_FILE 2>&1 &
done <$1

echo -n "Waiting dhtest..."

while : ; do
  sleep 1
  pid=$( pidof dhtest )
  if [[ $pid == "" ]]
  then
    break
  fi
  echo -n "."
done

date2=$(date +"%s")
date >> $RESULT_FILE
diff=$(($date2-$date1))

echo ""
echo "Finished, the result is in file '$RESULT_FILE'"
echo "$(($diff / 60)) minutes and $(($diff % 60)) seconds elapsed."

# Faz um sumário rápido dos resultados
OKCOUNT=$(cat $RESULT_FILE | grep -i ok | wc -l)
echo ""
echo "Summary:"
echo "Number of tested MACs: $COUNT"
echo "Number of sucessfull assigned IPs: $OKCOUNT"

echo ""
echo "Testing DNS.."

./test_dns_entrys.sh $1

#!/bin/bash

SERVER=192.168.56.2
NAS_SECRET=teste
RESULT_FILE=resultradius

if [ $# -eq 0 ]
then
  echo "No arguments supplied"
  exit 1
fi

rm -f $RESULT_FILE 1> /dev/null 2>&1
date1=$(date +"%s")
date > $RESULT_FILE
COUNT=0

while read line
do
  MAC=$( echo $line | cut -d ' ' -f1 )
  COUNT=$( expr $COUNT + 1 )
  radtest -x $MAC $MAC $SERVER 10 $NAS_SECRET >> $RESULT_FILE 2>&1 &
done <$1

echo -n "Waiting radtest..."

while : ; do
  sleep 1
  pid=$( pidof radtest )
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
OKCOUNT=$(cat $RESULT_FILE | grep rad_recv| grep -i accept | wc -l)
ERRORCOUNT=$(cat $RESULT_FILE | grep rad_recv| grep -i reject | wc -l)
echo ""
echo "Summary:"
echo "Number of tested MACs: $COUNT"
echo "Number of sucessfull authenticated MACs: $OKCOUNT"
echo "Number of reject authenticated MACs: $ERRORCOUNT"

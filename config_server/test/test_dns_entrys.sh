#!/bin/bash

SERVER=192.168.1.1
DOMAIN=jimmy.org.br
RESULT_FILE=resultdns

if [ $# -eq 0 ]
then
  echo "No arguments supplied"
  exit 1
fi

rm -f $RESULT_FILE 1> /dev/null 2>&1
date > $RESULT_FILE
COUNT=0

while read line
do
  MAC=$(echo $line | cut -d ' ' -f1)
  NAME="hostname"${COUNT}
  COUNT=$( expr $COUNT + 1 )
  dig @$SERVER $NAME.$DOMAIN >> $RESULT_FILE
  dig @$SERVER $NAME.$DOMAIN TXT >> $RESULT_FILE
done <$1

date >> $RESULT_FILE

# Faz um sumário rápido dos resultados
ACOUNT=$(cat $RESULT_FILE | grep -i -A1 ";; answer section" | grep A | awk '{ print $5 }' | sort | sed '/^$/d' | wc -l)
TXTCOUNT=$(cat $RESULT_FILE | grep -i -A1 ";; answer section" | grep TXT | awk '{ print $5 }' | sort | sed '/^$/d' | wc -l)
ERRORS=$(cat $RESULT_FILE | grep -i "nxdomain" | wc -l)
echo ""
echo "Summary DNS test:"
echo "Number of A: $ACOUNT"
echo "Number of TXT: $TXTCOUNT"
echo "Number of errors: $ERRORS"

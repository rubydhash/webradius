#!/bin/bash

mac="$1"
interface="$2"
hostname="$3"
tmpfile=$(mktemp)

if [[ $3 != "" ]]
then
  dhtest -V -p -r -i $interface -m $mac -h $hostname -T 5 > $tmpfile 2>&1
elif [[ $2 != "" ]]
then
  dhtest -V -p -r -i $interface -m $mac -T 5 > $tmpfile 2>&1
elif [[ $1 != "" ]]
then
  dhtest -V -p -r -i $interface -T 5 > $tmpfile 2>&1
else
  echo "Usage $0 MAC INTERFACE HOSTNAME"
  exit 0
fi

result=$(cat $tmpfile | grep -i sent)

if [[ $result != "" ]]
then
  echo "$1 release OK!"
else
  echo "$1 release Error!"
fi

rm $tmpfile

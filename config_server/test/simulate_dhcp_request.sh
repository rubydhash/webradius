#!/bin/bash

mac="$1"
interface="$2"
hostname="$3"
tmpfile=$(mktemp)
timeout=5

if [[ $3 != "" ]]
then
  dhtest -V -p -i $interface -m $mac -h $hostname -d $hostname -T $timeout > $tmpfile 2>&1
elif [[ $2 != "" ]]
then
  dhtest -V -p -i $interface -m $mac -T $timeout > $tmpfile 2>&1
elif [[ $1 != "" ]]
then
  dhtest -V -p -i $interface -T 5 > $tmpfile 2>&1
else
  echo "Usage $0 MAC INTERFACE HOSTNAME"
  exit 0
fi

result=$(cat $tmpfile | grep -i ack)
assignedip=$(cat $tmpfile | grep "offered IP" | tail -n1 | awk '{ print $7 }')
assignedfqdn=$(cat $tmpfile | grep "Client name" | awk '{ print $5 }')

if [[ $result != "" ]]
then
  if [[ $assignedfqdn != "" ]]
  then
    echo "$1 $assignedip $assignedfqdn request OK!"
  else
    echo "$1 $assignedip request OK!"
  fi
else
  echo "$1 request Error!"
fi

rm $tmpfile

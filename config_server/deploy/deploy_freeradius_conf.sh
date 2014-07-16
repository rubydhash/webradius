#!/bin/bash

if [ ! -f deploy.conf ]
then
  echo "O arquivo de configuração deploy.conf é necessário."
  echo "Este arquivo deve estar na mesma pasta do script de deploy."
  echo "Consulte o exemplo de configuração no SVN."
  exit
fi

# Carrega arquivo de configuração
. deploy.conf

BASEDIR=/usr/local/radius/

/etc/init.d/radiusd stop

cd /root/repositorio/
rm -rf config_server
svn export http://your.svn.server/webradius/trunk/config_server

# Ajusta o IP do servidor na configuração
sed "s/IPSERVIDOR/$serverip/" config_server/freeradius/raddb/sites-available/dhcp > config_server/freeradius/raddb/sites-available/dhcp2
mv config_server/freeradius/raddb/sites-available/dhcp2 config_server/freeradius/raddb/sites-available/dhcp
sed "s/IPSERVIDOR/$serverip/" config_server/freeradius/raddb/policy.conf > config_server/freeradius/raddb/policy.conf2
mv config_server/freeradius/raddb/policy.conf2 config_server/freeradius/raddb/policy.conf

rm -rf $BASEDIR/etc/temp_raddb
cp -rf $BASEDIR/etc/raddb $BASEDIR/etc/temp_raddb
rm -rf $BASEDIR/etc/raddb
cp -rf /root/repositorio/config_server/freeradius/raddb $BASEDIR/etc/raddb

mkdir -p $BASEDIR/etc/raddb/sites-enabled/
ln -sfv $BASEDIR/etc/raddb/sites-available/dhcp $BASEDIR/etc/raddb/sites-enabled/
ln -sfv $BASEDIR/etc/raddb/sites-available/control-socket $BASEDIR/etc/raddb/sites-enabled/
ln -sfv $BASEDIR/etc/raddb/sites-available/default $BASEDIR/etc/raddb/sites-enabled/
ln -sfv $BASEDIR/etc/raddb/sites-available/inner-tunnel $BASEDIR/etc/raddb/sites-enabled/

cp /root/repositorio/config_server/freeradius/dictionary $BASEDIR$BASEDIR/share/freeradius/dictionary

chmod +x /usr/local/radius/etc/raddb/python/rotateddns.py
chmod +x /usr/local/radius/etc/raddb/scripts/*

/etc/init.d/radiusd start

#!/bin/bash

/etc/init.d/apache2 stop

if [ ! -f deploy.conf ]
then
  echo "O arquivo de configuração deploy.conf é necessário."
  echo "Este arquivo deve estar na mesma pasta do script de deploy."
  echo "Consulte o exemplo de configuração no SVN."
  exit
fi

# Carrega arquivo de configuração
. deploy.conf

BASEDIR=/usr/local/lib

rm -rf $BASEDIR/webradius-project

mkdir -p /root/repositorio/
cd /root/repositorio/
rm -rf webradius-project
svn export http://your.svn.server/webradius/trunk/webradius-project

# Ajusta o IP do servidor na configuração
sed "s/IPSERVIDOR/$serverip/" webradius-project/webradius-project/settings.py > webradius-project/webradius-project/settings.py2
sed "s/NOMESERVIDOR/$servername/" webradius-project/webradius-project/settings.py2 > webradius-project/webradius-project/settings.py
sed "s/NOMESERVIDOR.teste.example.com/$servername.teste.example.com/" webradius-project/webradius-project/settings.py > webradius-project/webradius-project/settings.py2
mv webradius-project/webradius-project/settings.py2 webradius-project/webradius-project/settings.py

cp -rf webradius-project $BASEDIR/webradius-project

/etc/init.d/apache2 start

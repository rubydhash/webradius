# -*- coding: utf-8 -*- 

import os  
from subprocess import PIPE, Popen
from lib.utils import shell

class Snmp(shell.Shell):
    def snmpget(self,host,oid,version="1", community="public"):    
        out_, error_ = self.run("snmpget -c %s -v %s %s %s" %(community,version,host,oid), "read")
        try:
            return out_.strip().split('=')[1]
        except IndexErrror:
            pass
        return None
        
    def snmpwalk(self,host,oid,version="1", community="public"):
        out = self.run("snmpwalk -c %s -v %s %s %s" %(community,version,host,oid),"readlines")
        value = []
        for o in out:         
            value.append(o.split('=')[1].strip())   
        return value
        
    def snmpset(self,host,oid, valor, version="1", community="public"):
        out_, error_ = self.run("snmpset -c %s -v %s %s %s %s" %(community,version,host,oid,valor),"read")
        if error_ is None:
            try:
                return out_.split('=')[1].strip()
            except:
                pass 
        return None

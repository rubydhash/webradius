#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Script para rotacionar os nomes antigos da tabelas ddns

import syslog
import sys
import traceback
import psycopg2
import datetime
from exceptions import Exception
import dns.rcode

from config import *
import dnslease
import dnsrecord

syslog.openlog(facility=syslog.LOG_DAEMON)

def log(str):
    syslog.syslog(str)

log("Starting DDNS rotate")

conn = None

try:
    conn = psycopg2.connect(database=db,
                            user=db_user_name,
                            password=db_passwd,
                            host=db_hostname)

    now = datetime.datetime.now()
    delta = datetime.timedelta(seconds=rotateseconds)
    rotate_date = now - delta 
    
    leases = dnslease.DdnsLease.load_all_expired(conn, rotate_date.strftime('%Y-%m-%d %H:%M:%S'))
    
    for lease in leases:     
        drec = dnsrecord.DnsRecord(dns_server_ip, lease.domain(),
                                        lease.rev_domain, dns_ttl,
                                        dns_key_name, dns_key, lease.hostname,
                                        lease.txt, lease.ip)
      
        try:
            lease.delete()

            drec.search_a()
            
            conn.commit()
            
            rcode = drec.delete_a()
            if rcode != dns.rcode.NXRRSET:
                drec.delete_txt()
                log("Deleted A entry: %s -> %s" % (lease.fwd_name, lease.ip))                                
            else:
                log("Name changed by external: %s" % (lease.fwd_name))
            
            drec.delete_rev()
            log("Deleted PTR entry: %s -> %s" % (lease.rev_name, lease.fwd_name))            
        except Exception, e:
            str = traceback.format_exc()
            log('Error deleting DNS entry, exception %s: %s - %s' % (e.__class__.__name__, e, str))

except Exception, e:    
    log('Error while processing Freeradius DDNS rotate script, exception %s: %s' % (e.__class__.__name__, e))
finally:
    log("Finished DDNS rotate")
    syslog.closelog()
    if conn is not None:
        conn.close()

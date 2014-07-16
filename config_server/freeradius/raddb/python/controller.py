# -*- coding: utf-8 -*-

import radiusd
import psycopg2
import sys, traceback
import dns.rcode
import datetime
from exceptions import Exception

from freeradiusfqdn import FreeradiusFqdn
from dnslease import DdnsLease
from dnsrecord import DnsRecord
from poolinfo import Poolinfo
from radippool import Radippool
from txthash import TxtHash

# Classe controller que vai processar tudo que é necessário para o funcionando do DDNS
class DdnsController:
    __db_conn = None
    __manual_connection = False
    __db_hostname = None
    __db = None
    __db_user_name = None
    __db_passwd = None
    __dns_server_ip = None
    __dns_key_name = None
    __dns_key = None
    __dns_ttl = None
    __mode = None

    def initialize(self, dns_server_ip, dns_key_name, dns_key, dns_ttl, mode):
        self.__mode = mode
        self.__validate_mode()
        self.__dns_server_ip = dns_server_ip
        self.__dns_key_name = dns_key_name
        self.__dns_key = dns_key
        self.__dns_ttl = dns_ttl

    def __validate_mode(self):
        if self.__mode != "deny":
            raise Exception("The only implemented mode is 'deny'")
        
    def set_conn(self, conn):
        self.__db_conn = conn

    def connect(self, db, db_user_name, db_passwd, db_hostname):
        self.__db = db
        self.__db_user_name = db_user_name
        self.__db_passwd = db_passwd
        self.__db_hostname = db_hostname
        self.__db_conn = psycopg2.connect(database=self.__db,
                                          user=self.__db_user_name,
                                          password=self.__db_passwd,
                                          host=self.__db_hostname)
        self.__manual_connection = True

    def finish(self):        
        if self.__manual_connection and self.__db_conn is not None:
            self.__db_conn.close()
            
    def __get_tuple_item(self, name, tp):
        for item in tp:
            if item[0] == name:
                fitem = item[1]
                if fitem[0] == '"':
                    fitem = fitem[1:]
                if fitem[-1] == '"':
                    fitem = fitem[:-1]
                return fitem
        return None
    
    def __compare_fqdn_hostname(self, fqdn, hostname):
        if fqdn[-1] != '.':
            fqdn = fqdn + '.'
        if hostname[-1] != '+':
            hostname = hostname + '.'
        if fqdn == hostname:
            return True
        else:
            return False

    def __process_request(self, req_tuple):
        reply_list = []

        # Pega todas as variaveis usadas da tupla de requisicao  
        hostname = self.__get_tuple_item("DHCP-Hostname", req_tuple)
        raw_fqdn = self.__get_tuple_item("DHCP-Client-FQDN", req_tuple)
        mac = self.__get_tuple_item("Calling-Station-Id", req_tuple)
        # O identificador do Client é sempre o MAC, mas se for usado o Client-Identifier o TXT tem um prefixo diferente
        client_identifier = self.__get_tuple_item('DHCP-Client-Identifier', req_tuple) 
        # HW Type, vai ser sempre Ethernet, mas melhor preparar o código para expansão
        hw_type = self.__get_tuple_item('DHCP-Hardware-Type', req_tuple)
        client_ip = self.__get_tuple_item('DHCP-Client-IP-Address', req_tuple)
        gateway = self.__get_tuple_item('DHCP-Gateway-IP-Address', req_tuple)        

        # Hostname e fqdn não podem ser os dois nulos
        if hostname is None and raw_fqdn is None:
            reply_list.append(('DHCP-Client-FQDN', raw_fqdn))
            return None
        elif raw_fqdn is not None:            
            try:
                fqdn = FreeradiusFqdn(raw_fqdn)
            except Exception, e:
                # Em caso de exceção o FQDN enviado pelo cliente é mal formado
                radiusd.radlog(radiusd.L_INFO, "Bad FQDN %s" % (raw_fqdn))
                return None

        # O hostname e o fqdn não podem ser diferentes, isso indica que o cliente já
        # tem um fqdn real, ou seja não precisa de um nome completo novo.
        if hostname is not None and raw_fqdn is not None:
            if not self.__compare_fqdn_hostname(fqdn.fqdn, hostname):
                return None
            
        # A principio o FQDN de resposta é o mesmo que o cliente enviou
        if self.__mode == "deny" and raw_fqdn is not None:
            reply_list.append(('DHCP-Client-FQDN', raw_fqdn))
                    
        poolinfo = Poolinfo(self.__db_conn)
        
        if not poolinfo.load_by_mac(mac):
            # Tenta pelo gateway
            if gateway is None or not poolinfo.load_by_gw(gateway):
                return tuple(reply_list)
        
        # O dominio e o dominio reverso tem que estar setados
        if poolinfo.domain_name is None or poolinfo.domain_name == '':
            return tuple(reply_list)
        
        if poolinfo.rev_domain_name is None or poolinfo.rev_domain_name == '':
            return tuple(reply_list)
        
        ippool = Radippool(self.__db_conn, mac)
        
        if not ippool.load():
            return tuple(reply_list)
        
        if ippool.is_expired():
            return tuple(reply_list)         
        
        if client_identifier is None:                
            txt = TxtHash(False, mac, hw_type)
        else:
            txt = TxtHash(True, client_identifier, hw_type)
                    
        dnsrecord = DnsRecord(self.__dns_server_ip, poolinfo.domain_name,
                              poolinfo.rev_domain_name, self.__dns_ttl, self.__dns_key_name,
                              self.__dns_key, hostname, txt.txt(), ippool.ip)           
        
        ddns_lease = DdnsLease(self.__db_conn)
        
        # Controla se vamos precisar inserir entradas novas no banco e no DNS
        insert = None
        
        if ddns_lease.load_by_fwd(hostname, poolinfo.domain_name):
            if ddns_lease.mac != mac:
                # Sendo diferente temos que checar se essa entrada anterior já não expirou, se expirou temos que remove-la
                if ddns_lease.is_expired():                        
                    dnsrremove = DnsRecord(self.__dns_server_ip, ddns_lease.domain(),
                                           ddns_lease.rev_domain, self.__dns_ttl,
                                           self.__dns_key_name,
                                           self.__dns_key, ddns_lease.hostname,
                                           ddns_lease.txt, ddns_lease.ip)
                    
                    # Remove o registro DNS do lease que está vencido
                    # Em caso de erro prossegue pois pode ter sido removida por fora as entradas
                    try:
                        dnsrremove.delete_rev()
                        if dnsrremove.delete_a() != dns.rcode.NXRRSET:
                            # Só tenta remover o TXT se conseguiu remover a entrada A
                            dnsrremove.delete_txt()
                    except:
                        radiusd.radlog(radiusd.L_INFO, "Error deleting expired lease: %s -> %s" % (ddns_lease.fwd_name, ddns_lease.ip))
                    
                    # Remove o lease DNS expirado
                    ddns_lease.delete()
                    
                    # Agora temos que sinalizar a criação de um novo lease e DNS
                    insert = True
                else:
                    # Já tinha um cliente com o mesmo hostname e sem estar expirado, então não vamos fazer nada
                    return tuple(reply_list)
            else:
                # Trocando o IP tem que remover o reverso antigo e atualizar as entradas A e PTR
                if ddns_lease.ip != ippool.ip:
                    radiusd.radlog(radiusd.L_INFO, "Updating IP from %s: %s" % (ddns_lease.fwd_name, ippool.ip))
                    
                    dnsrev = DnsRecord(self.__dns_server_ip, ddns_lease.domain(),
                                       ddns_lease.rev_domain, self.__dns_ttl,
                                       self.__dns_key_name,
                                       self.__dns_key, ddns_lease.hostname,
                                       ddns_lease.txt, ddns_lease.ip)
                    dnsrev.delete_rev()
                    
                    # Esse codigo indica que o TXT não existe ou não tem o valor esperado
                    # Nesse caso o lease não vale mais então temos que deleta-lo
                    if dnsrecord.update_a() == dns.rcode.NXRRSET:
                        # Tenta deletar o reverso também
                        ddns_lease.delete()
                        
                        # Já retorna daqui mesmo
                        return tuple(reply_list)
                    
                    dnsrecord.update_rev()
                    
                    ddns_lease.ip = ippool.ip
                    ddns_lease.rev_name = dnsrecord.get_rev_name()

                # Sendo o mesmo MAC atualiza o expiry do DNS Lease
                ddns_lease.expiry = datetime.datetime.now() + datetime.timedelta(seconds=poolinfo.lease_time)
                
                radiusd.radlog(radiusd.L_INFO, "Updated DNS Lease expiry from %s: %s " % (ddns_lease.fwd_name, ddns_lease.expiry))

                # Não precisa criar um novo lease nem DNS
                insert = False
        # Se não achou pelo hostname tenta pelo IP, pode ser que um lease vencido esteja impedindo o cadastro
        elif ddns_lease.load_by_ip(ippool.ip):
            if (ddns_lease.mac != mac and ddns_lease.is_expired()) or \
                (ddns_lease.mac == mac and ddns_lease.hostname != hostname):                        
                    dnsrremove = DnsRecord(self.__dns_server_ip, ddns_lease.domain(),
                                           ddns_lease.rev_domain, self.__dns_ttl,
                                           self.__dns_key_name,
                                           self.__dns_key, ddns_lease.hostname,
                                           ddns_lease.txt, ddns_lease.ip)
                    
                    # Em caso de erro prossegue pois pode ter sido removida por fora as entradas
                    try:
                        dnsrremove.delete_rev()
                        if dnsrremove.delete_a() != dns.rcode.NXRRSET:
                            # Só tenta remover o TXT se conseguiu remover a entrada A
                            dnsrremove.delete_txt()
                    except:
                        radiusd.radlog(radiusd.L_INFO, "Error deleting lease: %s -> %s" % (ddns_lease.fwd_name, ddns_lease.ip))
                    
                    # Remove o lease expirado do banco
                    ddns_lease.delete()
                    
                    # Agora temos que sinalizar a criação de um novo lease e DNS
                    insert = True            
        else:
            # Não achamos um lease, então temos que criar um e a entrada DNS também
            insert = True
            
        # Commita tudo até aqui, pois podem ocorrer erros a seguir mas o que foi feito já tem que ser commitado
        self.__db_conn.commit()

        if insert is not None and insert:
            ddns_lease = DdnsLease(self.__db_conn)
            
            ddns_lease.expiry = datetime.datetime.now() + datetime.timedelta(seconds=poolinfo.lease_time)
            ddns_lease.ip = ippool.ip
            ddns_lease.hostname = hostname
            ddns_lease.mac = mac
            ddns_lease.rev_domain = poolinfo.rev_domain_name
            ddns_lease.fwd_name = ddns_lease.create_fwd_name(hostname, poolinfo.domain_name)
            ddns_lease.rev_name = dnsrecord.get_rev_name()
            ddns_lease.hw_type = txt.hw_type_to_int()
            ddns_lease.txt = txt.txt()

            ddns_lease.save(insert=True)

            # Testa se existe a entrada A, se existir tenta um update senão adiciona
            if dnsrecord.search_a():
                rcode = dnsrecord.update_a() 
                if rcode != dns.rcode.NOERROR:
                    radiusd.radlog(radiusd.L_INFO, "The name is managed by external %s - %d - %s - %s" % (ddns_lease.fwd_name, rcode, mac, txt.txt()))                    
                    self.__db_conn.rollback()
                    return tuple(reply_list)
                
                dnsrecord.update_rev()
                
                radiusd.radlog(radiusd.L_INFO, "Updated forward map from %s to %s" % (ddns_lease.fwd_name, ddns_lease.ip))
                radiusd.radlog(radiusd.L_INFO, "Updated reverse map from %s to %s" % (dnsrecord.get_rev_name(), ddns_lease.fwd_name))
            else:
                # Tem que testar a entrada TXT também, se tiver tem que cancelar
                if dnsrecord.search_txt():
                    radiusd.radlog(radiusd.L_INFO, "The name is managed by external %s - %s - %s" % (ddns_lease.fwd_name, mac, txt.txt()))  
                    self.__db_conn.rollback()
                    return tuple(reply_list)
                
                rcode = dnsrecord.add_a_and_txt()
                if rcode != dns.rcode.NOERROR:
                    radiusd.radlog(radiusd.L_INFO, "Error adding forward map from %s to %s: %s" % (ddns_lease.fwd_name, ddns_lease.ip, rcode))
                    self.__db_conn.rollback()
                    return tuple(reply_list)
                
                dnsrecord.update_rev()
                
                radiusd.radlog(radiusd.L_INFO, "Added new forward map from %s to %s" % (ddns_lease.fwd_name, ddns_lease.ip))
                radiusd.radlog(radiusd.L_INFO, "Added reverse map from %s to %s" % (dnsrecord.get_rev_name(), ddns_lease.fwd_name))
        else:
            ddns_lease.save()

        # Por enquanto só implementa o modo 'deny'
        # Se não tiver um raw_fqdn é pq o cliente não enviu o FQDN, então não precisamos responder com um FQDN
        if self.__mode == "deny" and raw_fqdn is not None:
            # Ajusta o fqdn para apontar para a entrada que adicionamos no DNS
            fqdn.fqdn = ddns_lease.fwd_name
            answer = fqdn.get_deny_answer()
            
            # Pega o valor atual, remove e adiciona o novo
            for item in reply_list:
                if item[0] == 'DHCP-Client-FQDN':
                    reply_list.remove(('DHCP-Client-FQDN', item[1]))
                    
            reply_list.append(('DHCP-Client-FQDN', answer))

        return tuple(reply_list)
    
    def __process_release(self, req_tuple):
        hostname = self.__get_tuple_item("DHCP-Hostname", req_tuple)
        mac = self.__get_tuple_item("Calling-Station-Id", req_tuple)
        client_identifier = self.__get_tuple_item('DHCP-Client-Identifier', req_tuple)
        hw_type = self.__get_tuple_item('DHCP-Hardware-Type', req_tuple)
        client_ip = self.__get_tuple_item('DHCP-Client-IP-Address', req_tuple)    
        gateway = self.__get_tuple_item('DHCP-Gateway-IP-Address', req_tuple)       

        ippool = Radippool(self.__db_conn, mac)
        
        if not ippool.load_by_ip(client_ip):
            return None
        
        # Se for dinamico dentro de um Pool nao faz o Release
        if ippool.is_static_overlapped():
            return None
        
        # Libera o IP do pool
        ippool.release()
        # Independete se tem DDNS quero comitar a liberação do IP
        self.__db_conn.commit()
        
        ddns_lease = DdnsLease(self.__db_conn)
        
        # Se não enviou o IP do cliente tenta pelo hostname
        if client_ip is None:
            # Se não enviou o hostname não da para remover
            if hostname is None:
                return None
            
            poolinfo = Poolinfo(self.__db_conn)
        
            if not poolinfo.load_by_mac(mac):
                # Tenta pelo gateway
                if gateway is None or not poolinfo.load_by_gw(gateway):
                    return None
            
            if poolinfo.domain_name is None or poolinfo.domain_name == '':
                return None
            
            if not ddns_lease.load_by_fwd(hostname, poolinfo.domain_name):
                return None
        else:
            if not ddns_lease.load_by_ip(client_ip):
                return None
        
        # Se tiver um lease então tem que remover as entradas do DNS e do Banco
        dnsrecord = DnsRecord(self.__dns_server_ip, ddns_lease.domain(),
                              ddns_lease.rev_domain, self.__dns_ttl,
                              self.__dns_key_name,
                              self.__dns_key, ddns_lease.hostname,
                              ddns_lease.txt, ddns_lease.ip)
        
        ddns_lease.delete()
        
        # Testa se o DNS está up antes efetuando uma busca
        # Se não estiver up vai lançar uma exceção
        dnsrecord.search_a()
        
        # Com a 'garantia' que o DNS está up já remove do banco
        # Essa garantia é meio falha, mas da alguma segurança de remover do banco sem deixar as entradas no DNS
        self.__db_conn.commit()
        
        # Tem que deletar a entrada tipo A antes, pois se não tiver o TXT vai dar erro
        # Se der erro é pq a entrada TXT não existe ou foi alterado, isso indica que a entrada DNS
        # foi alterado por outro programa. Nesse caso tem que dar erro mesmo.
        # Mas só deleta o TXT se conseguir deletar a entrada tipo A.
        # Como já foi deletado do banco essa entrada vai ficar no DNS.
        rcode = dnsrecord.delete_a()
        if rcode != dns.rcode.NXRRSET:
            dnsrecord.delete_txt()
        else:
            # Dando erro vamos logar que um externo modificou o registro que estava sendo gerenciado
            radiusd.radlog(radiusd.L_INFO, "Name changed by external: %s" % (ddns_lease.fwd_name))
        dnsrecord.delete_rev()

        return None

    def process(self, req_tuple):        
        if self.__db_conn is None:
            radiusd.radlog(radiusd.L_INFO, "Error, there is no database connection.")
            return None
        
        message_type = self.__get_tuple_item("DHCP-Message-Type", req_tuple)
        
        if message_type is None:
            radiusd.radlog(radiusd.L_INFO, "Invalid DHCP Message Type")
            return None
        
        try:
            if message_type == 'DHCP-Request':
                return self.__process_request(req_tuple)
            elif message_type == 'DHCP-Release':
                return self.__process_release(req_tuple)
            else:
                return None
        except Exception, e:
            # TODO Remover stack abaixo depois de estabilizado
            str = traceback.format_exc()
            radiusd.radlog(radiusd.L_INFO, 'Error while processing Freeradius DDNS module, exception %s: %s - %s' % (e.__class__.__name__, e, str))            
            self.__db_conn.rollback()
        finally:
            # Tem que executar o commit obrigatoriamente para encerrar a transação iniciada implicitamente,
            # se ocorrer erro o rollback da exceção será executado antes
            self.__db_conn.commit()
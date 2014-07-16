# -*- coding: utf-8 -*-

import dns.query
import dns.tsigkeyring
import dns.update
import dns.reversename
import dns.resolver
import dns.name
from exceptions import Exception

class DnsRecord:
    __keyring = None
    __server_ip = None
    __domain = None
    __rev_domain = None
    __ttl = None
    __hostname = None
    __txt_value = None
    __ip = None
    __resolver = None

    def __init__(self, server_ip, domain, rev_domain, ttl, dns_key_name, dns_key, hostname, txt_value, ip):
        self.__keyring = dns.tsigkeyring.from_text({dns_key_name : dns_key})
        self.__server_ip = server_ip
        self.__domain = domain
        self.__rev_domain = rev_domain
        self.__ttl = ttl
        self.__hostname = hostname
        self.__txt_value = txt_value
        self.__ip = ip
        self.__prepare_resolver()
        
    def __prepare_resolver(self):
        # Ajusta o resolver padrão para apontar para o servidor e dominio correto
        self.__resolver = dns.resolver.get_default_resolver()
        self.__resolver.nameservers = [self.__server_ip]
        self.__resolver.search = [dns.name.from_text(self.__domain)]
        # Espera quase nada pelo servidor, eu não posso travar a concessão de um IP pq o DNS está fora
        self.__resolver.timeout = 1
        # O total de segundos que vai tentar, com timeout=0.4 da tempo de tentar duas vezes
        # Esses valores podem ser 'tunados' caso o comportamento não esteja sendo adequado, como por exemplo
        # o servidor DHCP não estar conseguindo atendar todos os clientes em tempo habil quando o DNS estiver fora.
        # Mas acredito que com esses valores o servidor consegue responder em tempo hábil
        self.__resolver.lifetime = 2.1
        # Tenta de novo em casa de falha no servidor
        self.__resolver.retry_servfail = True
        
        dns.resolver.override_system_resolver(self.__resolver)
        
    def get_fqdn(self):
        if self.__hostname[-1] == '.':
            return self.__hostname + self.__domain + '.'
        else:
            return self.__hostname + '.' + self.__domain + '.'

    def get_domain_fqdn(self):
        if self.__domain[-1] != '.':
            return self.__domain + '.'
        
    def get_rev_domain_fqdn(self):
        if self.__rev_domain[-1] != '.':
            return self.__rev_domain + '.'
        
    def get_rev_name(self):
        return dns.reversename.from_address(self.__ip).to_text()
        
    def validate_rev_name(self):
        rev_name = dns.reversename.from_address(self.__ip).to_text()
        # Se o ip não está no dominio de reversos não atualiza
        if not rev_name.endswith(self.get_rev_domain_fqdn()):
            return None
        # Pega a parte do nome que interessa
        return rev_name.partition(self.get_rev_domain_fqdn())[0][:-1]

    # Resolve o nome, se não resolve ele lança uma exceção do tipo NXDOMAIN
    def search_a(self):
        try:
            dns.resolver.query(self.__hostname, 'A')
            return True
        # Essa exceção indica que o nome não existe, as outras são consideradas erros        
        except dns.resolver.NXDOMAIN:
            return False
        except dns.resolver.NoAnswer:
            return False
        
    def search_txt(self):
        try:
            dns.resolver.query(self.__hostname, 'TXT')
            return True
        # Essa exceção indica que o nome não existe, as outras são consideradas erros        
        except dns.resolver.NXDOMAIN:
            return False
        except dns.resolver.NoAnswer:
            return False

    def update_a(self):
        try:
            update = dns.update.Update(self.get_domain_fqdn(), keyring=self.__keyring)
            # Só realiza o update se tiver uma entrada TXT e o valor dela bater com o calculado pelo servidor
            update.present(self.__hostname, 'TXT', self.__txt_value)
            update.replace(self.__hostname, self.__ttl, 'A', self.__ip)
            return dns.query.tcp(update, self.__server_ip).rcode()
        except Exception, error:
            raise Exception("Error updating DNS A Entry: %s" % (error))

    def update_rev(self):
        try:
            name = self.validate_rev_name()
            if not name:
                return None
            
            update = dns.update.Update(self.get_rev_domain_fqdn(), keyring=self.__keyring)
            update.replace(name, self.__ttl, 'PTR', self.get_fqdn())
            return dns.query.tcp(update, self.__server_ip).rcode()
        except Exception, error:
            raise Exception("Error updating DNS PTR Entry: %s" % (error))
        
    def add_a(self):
        try:
            update = dns.update.Update(self.get_domain_fqdn(), keyring=self.__keyring)
            update.add(self.__hostname, self.__ttl, 'A', self.__ip)
            return dns.query.tcp(update, self.__server_ip).rcode()
        except Exception, error:
            raise Exception("Error inserting DNS A Entry: %s" % (error))
        
    def add_txt(self):
        try:
            update = dns.update.Update(self.get_domain_fqdn(), keyring=self.__keyring)
            update.add(self.__hostname, self.__ttl, 'TXT', self.__txt_value)
            return dns.query.tcp(update, self.__server_ip).rcode()
        except Exception, error:
            raise Exception("Error inserting DNS TXT Entry: %s" % (error))
        
    def delete_a(self):
        try:
            update = dns.update.Update(self.get_domain_fqdn(), keyring=self.__keyring)
            update.present(self.__hostname, 'TXT', self.__txt_value)
            update.delete(self.__hostname, 'A')
            return dns.query.tcp(update, self.__server_ip).rcode()
        except Exception, error:
            raise Exception("Error deleting DNS A Entry: %s" % (error))
        
    def add_a_and_txt(self):
        try:            
            update = dns.update.Update(self.get_domain_fqdn(), keyring=self.__keyring)
            update.add(self.__hostname, self.__ttl, 'A', self.__ip)
            update.add(self.__hostname, self.__ttl, 'TXT', self.__txt_value)
            return dns.query.tcp(update, self.__server_ip).rcode()
        except Exception, error:
            raise Exception("Error inserting DNS A Entry: %s" % (error))

    def delete_rev(self):
        try:            
            name = self.validate_rev_name()
            if not name:
                return None
            
            update = dns.update.Update(self.get_rev_domain_fqdn(), keyring=self.__keyring)
            update.present(name, 'PTR', self.get_fqdn())
            update.delete(name, 'PTR')
            return dns.query.tcp(update, self.__server_ip).rcode()
        except Exception, error:
            raise Exception("Error deleting DNS PTR Entry: %s" % (error))
        
    def delete_txt(self):
        try:
            update = dns.update.Update(self.get_domain_fqdn(), keyring=self.__keyring)
            update.delete(self.__hostname, 'TXT')
            return dns.query.tcp(update, self.__server_ip).rcode()
        except Exception, error:
            raise Exception("Error deleting DNS TXT Entry: %s" % (error))
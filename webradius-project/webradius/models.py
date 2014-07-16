# -*- coding: utf-8 -*-

import re
import iptools
import datetime

from django.db import models
from django.utils.translation import ugettext as _
from django.core import exceptions
from django.core import urlresolvers
from lib.djangoutils.pgfields import ArrayField
from lib.djangoutils import modelfields
from lib.backend import ldapbackend

from webradius import util


class Log(models.Model):
    created = models.DateTimeField(_(u'Date'), auto_now_add=True, db_index=True)
    user = models.ForeignKey('auth.User')
    msg = models.TextField()

    class Meta:
        verbose_name = _(u'Log')
        verbose_name_plural = (_(u'Logs'))
        db_table = 'weblog'
    
    def __unicode__(self):
        return self.msg
    
    def msg_exp(self):
        MAC_RE = r'.*([0-9a-fA-F]{2}(\-?|\:?)[0-9a-fA-F]{2}(\-?|\:?)[0-9a-fA-F]{2}(\-?|\:?)[0-9a-fA-F]{2}(\-?|\:?)[0-9a-fA-F]{2}(\-?|\:?)[0-9a-fA-F]{2}(\-?|\:?)).*'
        mac_re = re.compile(MAC_RE)
        
        matchs = mac_re.match(self.msg)
        if matchs is not None:
            mac = matchs.group(1)
            url = "<a href=\"%s\">%s</a>" % (urlresolvers.reverse('webradius:mac_detail_by_mac', args=(mac,)), mac)            
            return self.msg.replace(mac, url)
        return self.msg        

class Nas(models.Model):
    id = models.AutoField(primary_key=True)
    nasname = models.CharField(max_length=128)
    shortname = models.CharField(max_length=32)
    type = models.CharField(max_length=30)
    ports = models.IntegerField(null=True, blank=True)
    secret = models.CharField(max_length=60)
    server = models.CharField(max_length=64, blank=True)
    community = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=200, blank=True)
    
    def __unicode__(self):
        return self.nasname
    
    class Meta:
        db_table = 'nas'
        
class Poolinfo(models.Model):
    id = util.BigAutoField(primary_key=True)
    pool_name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=64)
    mask = models.GenericIPAddressField()
    router_address = models.GenericIPAddressField()
    domain_name = models.CharField(max_length=254, blank=True)
    rev_domain_name = models.CharField(max_length=254, blank=True)
    dns_server = models.GenericIPAddressField()
    dns_server2 = models.GenericIPAddressField(null=True, blank=True)
    netbios = models.CharField(max_length=254, blank=True)
    netbios_name_server = models.GenericIPAddressField(null=True, blank=True)
    netbios_name_server2 = models.GenericIPAddressField(null=True, blank=True)
    netbios_node_type = models.SmallIntegerField(null=True, blank=True, default=1)
    mtu = models.BigIntegerField(null=True, blank=True)
    ntp_server = models.CharField(max_length=128, blank=True)
    lease_time = models.BigIntegerField()
    next_server = models.GenericIPAddressField(null=True, blank=True)
    root_path = models.CharField(max_length=128, blank=True)
    boot_filename = models.CharField(max_length=128, blank=True)
    init_address = models.GenericIPAddressField(null=True, blank=True)
    end_address = models.GenericIPAddressField(null=True, blank=True)
    bind_gateways = ArrayField(dbtype="inet", null=True, blank=True)
    vlan_id = models.SmallIntegerField(null=True, blank=True)

    def __unicode__(self):
        return "%s" % (self.description)
    
    class Meta:
        db_table = 'poolinfo'
        
    def __get_bind_list_from_dict(self, bdict):
        blist = ()
        for key, value in bdict:
            if value != '{' and value != '}':
                blist.append(value)
        return blist
        
    def get_bind_gateways_list(self):
        # Se já for uma lista só retorna, senão transforma a string em uma lista        
        if isinstance(self.bind_gateways, list):
            return self.bind_gateways
        else:
            if isinstance(self.bind_gateways, dict):
                return self.__get_bind_list_from_dict(self.bind_gateways)
            elif self.bind_gateways is None:
                return []
            else:
                return self.bind_gateways.replace('{','').replace('}','').split(',')
        
    def is_in_subnet_range(self, ip):
        if ip in self.subnet_range():
            return True
        return False
    
    def is_in_range(self, ip):
        if ip in self.range():
            return True
        return False
        
    def is_range_avaiable(self):
        for pool in Poolinfo.objects.all():
            # Exclui o próprio pool da checagem
            if pool.pool_name == self.pool_name:
                continue
            iprange = pool.range()
            if self.init_address in iprange:
                return False, 'init_address', pool
            if self.end_address in iprange:
                return False, 'end_address', pool
        return True, 'none', None
    
    # Valida se todas as maquinas com IP estático associadas a esse Pool continuam
    # dentro do range do mesmo
    def validate_static_macs(self):        
        pool = Poolinfo.objects.get(pool_name=self.pool_name)
        macs = Macinfo.objects.filter(pool=pool.id, static=True)
        
        # Se não tem máquinas associadas pode prosseguir
        if len(macs) < 1:
            return True, None, None
        
        for mac in macs:
            if not mac.static_ip in self.range():
                if mac.static_ip < self.init_address:
                    return False, mac, 'init_address'
                else:
                    return False, mac, 'end_address'
            
        return True, None, None
        
    
    def validate_bind_gateways(self):
        for pool in Poolinfo.objects.all():
            # Exclui o próprio pool da checagem
            if pool.pool_name == self.pool_name:
                continue
            
            for a in self.get_bind_gateways_list():
                if pool.bind_gateways is None:
                    continue
                for b in pool.get_bind_gateways_list():
                    if a == b:
                        return False, a, pool
        return True, None, None

    def validate(self):
        # Valida a máscara de rede
        if not iptools.ipv4.validate_netmask(self.mask):
            return False, 'mask'
        # Valida a subrede
        if not self.validate_subnet():
            return False, 'router_address'
        # Valida se o range especificado esta na subrede
        if not self.init_address in self.subnet_range():
            return False, 'init_address'
        if not self.end_address in self.subnet_range():
            return False, 'end_address'
        
        return True, 'none'
    
    def validate_subnet(self):
        return iptools.ipv4.validate_subnet("%s/%s" % (self.subnet_addr(), self.cidr_prefix()))
    
    def cidr_prefix(self):
        return iptools.ipv4.netmask2prefix(self.mask)
    
    def broadcast(self):
        return iptools.ipv4.subnet2block("%s/%s" % (self.router_address, self.mask))[1]
    
    def subnet_addr(self):
        return iptools.ipv4.subnet2block("%s/%s" % (self.router_address, self.mask))[0]
    
    def range(self):
        return iptools.IpRange(self.init_address, self.end_address)
    
    def subnet_range(self):
        return iptools.IpRange(self.subnet_addr(), self.broadcast())
    
    def __insert_ips_range(self, pool_range):
        for ip in pool_range:
            # Checa se o IP já existe
            ippoolentry_found = Radippool.objects.filter(framedipaddress=ip)
            
            if len(ippoolentry_found) >= 1:
                ippoolentry = ippoolentry_found[0]
            else:
                ippoolentry = Radippool()
                # Insere ip com timestamp zerado para assegurar que já esta vencido
                ippoolentry.expiry_time = datetime.datetime.fromtimestamp(0)            
            
            ippoolentry.pool_name = self.pool_name
            ippoolentry.framedipaddress = ip            
            ippoolentry.save()
            
    def __delete_ips_range(self, pool_range):
        for ip in pool_range:
            ippool = Radippool.objects.filter(framedipaddress=ip)
            ippool.delete()
    
    def insert_all_ips(self):
        self.__insert_ips_range(self.range())
        
    def delete_all_ips(self):
        self.__delete_ips_range(self.range())
        
    def update_ips(self, old_range):
        self.delete_difference_ips(old_range)
        self.insert_difference_ips(old_range)
        
    def insert_difference_ips(self, old_range):
        set_old_range = set(old_range)
        set_range = set(self.range())
        
        to_insert_ips = set_range.difference(set_old_range)
        
        self.__insert_ips_range(to_insert_ips)
            
    def delete_difference_ips(self, old_range):
        set_old_range = set(old_range)
        set_range = set(self.range())
        
        to_delete_ips = set_old_range.difference(set_range)
        
        self.__delete_ips_range(to_delete_ips)

    def count_machines_on_pool(self):
        return Macinfo.objects.filter(pool=self.id).count()
    
    # Retorna se o Pool já está cheio, ou seja, se já tem máquinas o suficiente para consumir todos os ips
    def is_full(self):
        return (self.count_machines_on_pool() >= len(self.range()))
    
    def update_group_attributes(self):
        self.delete_all_group_attributes()
        self.insert_all_group_attributes()
        
    def insert_all_group_attributes(self):
        self.__insert_group_check()
        self.__insert_group_reply()

    def delete_all_group_attributes(self):
        self.__delete_group_check()
        self.__delete_group_reply()
    
    def __delete_group_check(self):
        objects = Radgroupcheck.objects.filter(groupname=self.pool_name)
        for obj in objects:
            obj.delete()
    
    def __delete_group_reply(self):
        objects = Radgroupreply.objects.filter(groupname=self.pool_name)
        for obj in objects:
            obj.delete()        
        
    # Insere os atribustos de checagem do Radius para o grupo do Pool
    def __insert_group_check(self):
        # Por enquanto não tem nenhum atributo de checagem no Pool
        return
        
    # Insere os atributos de resposta do Radius para o grupo do Pool
    def __insert_group_reply(self):
        # Atualmente todos os atributos são relacionados ao ID da VLAN
        if not self.vlan_id or self.vlan_id == 0 or self.vlan_id == 1:
            return
        
        tunnel_medium = Radgroupreply()
        tunnel_id = Radgroupreply()
        tunnel_type = Radgroupreply()
        tunnel_type.groupname = tunnel_medium.groupname = tunnel_id.groupname = self.pool_name
        tunnel_type.op = tunnel_medium.op = tunnel_id.op = "="
        tunnel_type.attribute = "Tunnel-Type"
        tunnel_id.attribute = "Tunnel-Private-Group-ID"
        tunnel_medium.attribute = "Tunnel-Medium-Type"
        # Valor 13 = VLAN
        tunnel_type.value = 13
        tunnel_id.value = self.vlan_id
        # Valor 6 = 802
        tunnel_medium.value = 6
        
        tunnel_type.save()
        tunnel_medium.save()
        tunnel_id.save()
    
    def save(self, *args, **kwargs):
        old_range = kwargs.pop('old_range', None)
        if old_range is not None:
            self.update_ips(old_range)
        else:
            self.insert_all_ips()
        self.update_group_attributes()
        super(Poolinfo, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        self.delete_all_ips()
        self.delete_all_group_attributes()
        super(Poolinfo, self).delete(*args, **kwargs)
        
    def assigned_ips(self):
        return Radippool.objects.filter(pool_name=self.pool_name).filter(expiry_time__gt=datetime.datetime.now()).order_by('framedipaddress')
    
    def assigned_ips_count(self):
        return len(self.assigned_ips())
    
    def assigned_ips_utilization(self):
        return self.assigned_ips_count()/float(len(self.range()))*100
    
    def lease_time_delta(self):
        return datetime.timedelta(seconds=self.lease_time)
    
    @staticmethod
    def get_static_prefix():
        return 'static'

    @staticmethod
    def get_static_pool_name(mac):
        return Poolinfo.get_static_prefix() + '-' + mac

    @staticmethod
    def edit_static_pool(pool, mac, static_ip, router_address, mask, dns_server,
                         domain, rev_domain, next_server, root_path, boot_filename,
                         netbios_name_server, netbios_name_server2, netbios_node_type,
                         change_name=False):
        if change_name:
            pool.pool_name = Poolinfo.get_static_pool_name(mac)
        pool.description = Poolinfo.get_static_pool_name(mac)
        # Tempo de concessão de 3 dias        
        pool.lease_time = 259200
        pool.init_address = static_ip
        pool.end_address = static_ip
        pool.router_address = router_address
        pool.mask = mask
        pool.dns_server = dns_server
        pool.domain_name = domain
        pool.rev_domain_name = rev_domain
        pool.next_server = next_server
        pool.root_path = root_path
        pool.boot_filename = boot_filename
        pool.netbios_name_server = netbios_name_server
        pool.netbios_name_server2 = netbios_name_server2
        pool.netbios_node_type = netbios_node_type

    @staticmethod
    def create_static_pool(mac, static_ip, router_address, mask, dns_server,
                           domain, rev_domain, next_server, root_path, boot_filename,
                           netbios_name_server, netbios_name_server2, netbios_node_type):
        pool = Poolinfo()
        Poolinfo.edit_static_pool(pool, mac, static_ip, router_address, mask,
                                  dns_server, domain, rev_domain, next_server,
                                  root_path, boot_filename, netbios_name_server,
                                  netbios_name_server2, netbios_node_type, True)
        return pool
    
    @staticmethod
    def delete_pool(pool_id):
        old_pool = Poolinfo.objects.get(pk=pool_id)
        old_pool.delete()

class Macinfo(models.Model):
    id = util.BigAutoField(primary_key=True)
    mac = modelfields.MACAddressField(unique=True)
    description = models.TextField()
    pool = models.ForeignKey(Poolinfo, db_column='pool')
    insert_date = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField(null=True, blank=True)
    static = models.BooleanField()
    static_standalone = models.BooleanField(default=False)
    static_ip = models.GenericIPAddressField(null=True, blank=True)
    vlan_id = models.SmallIntegerField(null=True, blank=True)
    full_access = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.mac
    
    class Meta:
        db_table = 'macinfo'
    
    def update_attributes(self):
        self.delete_all_attributes()
        self.insert_all_attributes()
        
    def insert_all_attributes(self):
        self.__insert_group()
        self.__insert_check()
        self.__insert_reply()

    def delete_all_attributes(self):
        self.__delete_group()
        self.__delete_check()
        self.__delete_reply()
    
    def __delete_check(self):
        objects = Radcheck.objects.filter(username=self.mac)
        for obj in objects:
            obj.delete()
    
    def __delete_reply(self):
        objects = Radreply.objects.filter(username=self.mac)
        for obj in objects:
            obj.delete() 
            
    def __delete_group(self):
        objects = Radusergroup.objects.filter(username=self.mac)
        for obj in objects:
            obj.delete()  
            
    # Vincula ao grupo do Pool
    def __insert_group(self):
        if self.pool is None:
            return
        
        user_group = Radusergroup()
        user_group.groupname = self.pool.pool_name
        user_group.username = self.mac
        user_group.priority = 1
        user_group.save()     
        
    # Insere os atribustos de checagem do Radius para essa máquina
    def __insert_check(self):
        # Atributo para fazer o MAC Authentication
        mac_auth_attribute = Radcheck()
        mac_auth_attribute.username = mac_auth_attribute.value = self.mac
        mac_auth_attribute.op = ":="
        mac_auth_attribute.attribute = "Cleartext-Password"
        
        # Atributo para designar o nome do Pool dessa máquina
        pool_attribute = Radcheck()
        pool_attribute.username = self.mac
        pool_attribute.value = self.pool.pool_name
        pool_attribute.op = ":="
        pool_attribute.attribute = "Pool-Name"
        
        if self.expiry_time:
            expiry_attribute = Radcheck()
            expiry_attribute.username = self.mac
            # Gera a string de data e hora no formato reconhecido pelo rlm_expiration do Freeradius
            expiry_attribute.value = self.expiry_time.strftime('%B %d %Y %H:%M:%S')
            expiry_attribute.op = ":="
            expiry_attribute.attribute = "Expiration"
            expiry_attribute.save()     
        
        mac_auth_attribute.save()
        pool_attribute.save()
        
    # Insere os atributos de resposta do Radius para essa máquina
    def __insert_reply(self):
        # Atualmente todos os atributos são relacionados ao ID da VLAN
        if not self.vlan_id or self.vlan_id == 0 or self.vlan_id == 1:
            return
        
        tunnel_medium = Radreply()
        tunnel_id = Radreply()
        tunnel_type = Radreply()
        tunnel_type.username = tunnel_medium.username = tunnel_id.username = self.mac
        tunnel_type.op = tunnel_medium.op = tunnel_id.op = "="
        tunnel_type.attribute = "Tunnel-Type"
        tunnel_id.attribute = "Tunnel-Private-Group-ID"
        tunnel_medium.attribute = "Tunnel-Medium-Type"
        # Valor 13 = VLAN
        tunnel_type.value = 13
        tunnel_id.value = self.vlan_id
        # Valor 6 = 802
        tunnel_medium.value = 6
        
        tunnel_type.save()
        tunnel_medium.save()
        tunnel_id.save()

    def release_all_associated_ips(self):
        Radippool.objects.filter(pool_key=self.mac)\
                 .exclude(pool_name__startswith=Poolinfo.get_static_prefix())\
                 .update(expiry_time=datetime.datetime.fromtimestamp(0),
                         pool_key="",
                         calledstationid="",
                         callingstationid="",
                         nasipaddress="",
                         username="")

    def release_overlapped_static_ip(self, ip=None):
        if ip is None:
            static_ip = self.static_ip
        else:
            static_ip = ip
        
        ip = Radippool.objects.get(framedipaddress=static_ip)        
        ip.expiry_time = datetime.datetime.fromtimestamp(0)
        ip.pool_key = ""
        ip.calledstationid = ""
        ip.callingstationid = ""
        ip.username = ""
        ip.save()
    
    def reserve_overlapped_static_ip(self, ip=None):
        if ip is None:
            static_ip = self.static_ip
        else:
            static_ip = ip
        
        ip = Radippool.objects.get(framedipaddress=static_ip)
        ip.expiry_time = Macinfo.get_static_overlapped_expiry()
        ip.pool_key = self.mac
        ip.calledstationid = 'dynamic-static'
        ip.callingstationid = self.mac
        ip.username = "DHCP-%s" % (self.mac)
        ip.save()
        
        # Libera qualquer outro IP do mesmo Pool do estático atribuido a essa máquina
        Radippool.objects.filter(pool_key=self.mac, pool_name=ip.pool_name)\
                  .exclude(framedipaddress=static_ip)\
                  .update(expiry_time=datetime.datetime.fromtimestamp(0),
                          pool_key="",
                          calledstationid="",
                          callingstationid="",
                          nasipaddress="",
                          username="")

    def create_static_pool(self, router_address, mask, dns_server,
                           domain, rev_domain, next_server, root_path,
                           boot_filename, netbios_name_server,
                           netbios_name_server2, netbios_node_type):
        self.pool = Poolinfo.create_static_pool(self.mac, self.static_ip,
                                                router_address,
                                                mask, dns_server,
                                                domain, rev_domain,
                                                next_server, root_path,
                                                boot_filename, netbios_name_server,
                                                netbios_name_server2,
                                                netbios_node_type)
        self.pool.save()
        # Pequeno hack pois estava dando erro de consistência ao salvar.
        self.pool = Poolinfo.objects.get(pk=self.pool.id)
        
    def edit_static_pool(self, old_ip, router_address, mask, dns_server,
                         domain, rev_domain, next_server, root_path, boot_filename,
                         netbios_name_server, netbios_name_server2, netbios_node_type):
        # O formulário altera o pool com base no combobox, temos que forçar o pool certo
        self.pool = Poolinfo.objects.get(pool_name=Poolinfo.get_static_pool_name(self.mac))
        Poolinfo.edit_static_pool(self.pool, self.mac, self.static_ip,
                                  router_address, mask, dns_server, domain,
                                  rev_domain, next_server, root_path,
                                  boot_filename, netbios_name_server,
                                  netbios_name_server2, netbios_node_type)
        self.pool.save(old_range=iptools.IpRange(old_ip, old_ip))

    def adjust_static(self, cleaned_data, was_static, was_standalone, old_pool_id, old_ip):
        if was_static != self.static:
            # Deixando de ser estática tem que deletar o pool estático ou liberar o
            # IP estático reservado no Pool
            if was_static:
                if was_standalone:
                    Poolinfo.delete_pool(old_pool_id)
                else:
                    # Seta o IP antigo
                    self.static_ip = old_ip
                    self.release_overlapped_static_ip()
            # Passando a ser estática tem que criar o pool ou reservar o IP
            else:
                if self.static_standalone:
                    # Libera todos os IPs associados a essa máquina antes de associar o IP estático
                    self.release_all_associated_ips()
                    # Criar o Pool estático
                    self.create_static_pool(cleaned_data.get('router_address'),
                                           cleaned_data.get('mask'),
                                           cleaned_data.get('dns_server'),
                                           cleaned_data.get('domain_name'),
                                           cleaned_data.get('rev_domain_name'),
                                           cleaned_data.get('next_server'),
                                           cleaned_data.get('root_path'),
                                           cleaned_data.get('boot_filename'),
                                           cleaned_data.get('netbios_name_server'),
                                           cleaned_data.get('netbios_name_server2'),
                                           cleaned_data.get('netbios_node_type'))
                else:
                    self.reserve_overlapped_static_ip()
        # Se não mudou e já era estática
        elif self.static:
            # Se deixou ou passou a ser standalone tem que ajustar
            if was_standalone != self.static_standalone:
                if was_standalone:
                    # Deleta o pool estatico
                    Poolinfo.delete_pool(old_pool_id)
                    # Reserva o novo IP
                    self.reserve_overlapped_static_ip()
                else:
                    # Libera o IP antigo
                    self.release_overlapped_static_ip(old_ip)
                    # Cria o novo Pool                  
                    self.create_static_pool(cleaned_data.get('router_address'),
                                           cleaned_data.get('mask'),
                                           cleaned_data.get('dns_server'),
                                           cleaned_data.get('domain_name'),
                                           cleaned_data.get('rev_domain_name'),
                                           cleaned_data.get('next_server'),
                                           cleaned_data.get('root_path'),
                                           cleaned_data.get('boot_filename'),
                                           cleaned_data.get('netbios_name_server'),
                                           cleaned_data.get('netbios_name_server2'),
                                           cleaned_data.get('netbios_node_type'))
            # Se já era standalone edita o Pool estático  
            elif self.static_standalone:
                self.edit_static_pool(old_ip,
                                     cleaned_data.get('router_address'),
                                     cleaned_data.get('mask'),
                                     cleaned_data.get('dns_server'),
                                     cleaned_data.get('domain_name'),
                                     cleaned_data.get('rev_domain_name'),
                                     cleaned_data.get('next_server'),
                                     cleaned_data.get('root_path'),
                                     cleaned_data.get('boot_filename'),
                                     cleaned_data.get('netbios_name_server'),
                                     cleaned_data.get('netbios_name_server2'),
                                     cleaned_data.get('netbios_node_type'))
            # A ultima hipotese é ser estatico nao standalone, altera o IP
            elif self.static_ip != old_ip:
                self.release_overlapped_static_ip(old_ip)
                self.reserve_overlapped_static_ip()
        
    def save(self, *args, **kwargs):
        self.mac = self.mac.lower()
        
        # TODO Tentar rodar o prepare_save aqui
        # por enquanto esta sendo chamado no form        
        
        self.update_attributes()
        super(Macinfo, self).save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        self.delete_all_attributes()
        super(Macinfo, self).delete(*args, **kwargs)
        if self.static:
            if self.static_standalone:
                self.pool.delete()
            else:
                self.release_overlapped_static_ip()
    
    @staticmethod
    def get_static_overlapped_expiry():
        return datetime.datetime(9999, 12, 31, 23, 59, 59)

class Ddns(models.Model):
    id = util.BigAutoField(primary_key=True)
    expiry = models.DateTimeField()
    mac = models.CharField(max_length=20)
    ip = models.GenericIPAddressField()
    hostname = models.CharField(max_length=254)
    fwd_name = models.CharField(max_length=254)
    txt = models.CharField(max_length=254)
    rev_name = models.CharField(max_length=254, blank=True)
    rev_domain = models.CharField(max_length=254, blank=True)
    hw_type = models.IntegerField()
    
    def __unicode__(self):
        return "%s %s %s %s %s %s %s %s %s" % (self.ip, self.mac, self.expiry,
                                               self.hostname, self.fwd_name,
                                               self.txt, self.rev_domain,
                                               self.rev_domain, self.hw_type)
    
    class Meta:
        db_table = 'ddns'

class Portdetailed():
    mask_unit=4278190080
    mask_subslot=15728640
    mask_port=1044480
    mask_vlan=255

    def get_unit(self):
        return ((int(self.nasportid) & self.mask_unit) >> 24)

    def get_subslot(self):
        return ((int(self.nasportid) & self.mask_subslot) >> 20)

    def get_port(self):
        return ((int(self.nasportid) & self.mask_port) >> 12)

    def get_vlan(self):
        return (int(self.nasportid) & self.mask_vlan)

    def portdetailed(self):
        return "%s/%s/%s - %s" % (self.get_unit(), self.get_subslot(), self.get_port(), self.get_vlan())

class Getnas():
    def nas(self):
        nas = None
        try:
            nas = Nas.objects.get(nasname=self.nasipaddress)
        except:
            return None
        return nas

class Radacct(models.Model, Portdetailed, Getnas):
    radacctid = util.BigAutoField(primary_key=True)
    acctsessionid = models.CharField(max_length=64)
    acctuniqueid = models.CharField(max_length=32, unique=True)
    username = models.CharField(max_length=253, blank=True)
    groupname = models.CharField(max_length=253, blank=True)
    realm = models.CharField(max_length=64, blank=True)
    nasipaddress = models.GenericIPAddressField()
    nasportid = models.CharField(max_length=15, blank=True)
    nasporttype = models.CharField(max_length=32, blank=True)
    acctstarttime = models.DateTimeField(null=True, blank=True)
    acctstoptime = models.DateTimeField(null=True, blank=True)
    acctsessiontime = models.BigIntegerField(null=True, blank=True)
    acctauthentic = models.CharField(max_length=32, blank=True)
    connectinfo_start = models.CharField(max_length=50, blank=True)
    connectinfo_stop = models.CharField(max_length=50, blank=True)
    acctinputoctets = models.BigIntegerField(null=True, blank=True)
    acctoutputoctets = models.BigIntegerField(null=True, blank=True)
    calledstationid = models.CharField(max_length=50, blank=True)
    callingstationid = models.CharField(max_length=50, blank=True)
    acctterminatecause = models.CharField(max_length=32, blank=True)
    servicetype = models.CharField(max_length=32, blank=True)
    xascendsessionsvrkey = models.CharField(max_length=10, blank=True)
    framedprotocol = models.CharField(max_length=32, blank=True)
    framedipaddress = models.GenericIPAddressField(null=True, blank=True)
    acctstartdelay = models.IntegerField(null=True, blank=True)
    acctstopdelay = models.IntegerField(null=True, blank=True)
    
    def __unicode__(self):
        return "%s %s %s %s %s %s %s" % (self.acctsessionid, self.acctuniqueid,
                                         self.username, self.groupname, 
                                         self.acctstarttime.__str__(),
                                         self.acctstoptime.__str__(),
                                         self.calledstationid)

    def is_mac(self):
        if modelfields.mac_re.match(self.username) is not None:
            return True
        
        return False
    
    def sessiontime(self):
        if self.acctstoptime is None:
            result = datetime.datetime.now().replace(microsecond=0) - self.acctstarttime.replace(microsecond=0)
        else:
            result = self.acctstoptime.replace(microsecond=0) - self.acctstarttime.replace(microsecond=0)
        return result
    
    def download(self):
        if self.acctstoptime is None:
            return None
        return self.acctoutputoctets/1024/1024
    
    def upload(self):
        if self.acctstoptime is None:
            return None
        return self.acctinputoctets/1024/1024
        
    class Meta:
        db_table = 'radacct'
        
class Radcheck(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=64)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2)
    value = models.CharField(max_length=253)
    
    def __unicode__(self):
        return "%s[%s] %s %s" % (self.username, self.attribute, self.op, self.value)
    
    class Meta:
        db_table = 'radcheck'
        
class Radgroupcheck(models.Model):
    id = models.AutoField(primary_key=True)
    groupname = models.CharField(max_length=64)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2)
    value = models.CharField(max_length=253)
    
    def __unicode__(self):
        return "%s[%s] %s %s" % (self.username, self.attribute, self.op, self.value)
    
    class Meta:
        db_table = 'radgroupcheck'

class Radgroupreply(models.Model):
    id = models.AutoField(primary_key=True)
    groupname = models.CharField(max_length=64)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2)
    value = models.CharField(max_length=253)
    
    def __unicode__(self):
        return "%s[%s] %s %s" % (self.username, self.attribute, self.op, self.value)
    
    class Meta:
        db_table = 'radgroupreply'
        
class Radippool(models.Model):
    id = util.BigAutoField(primary_key=True)
    pool_name = models.CharField(max_length=64)
    framedipaddress = models.GenericIPAddressField()
    nasipaddress = models.CharField(max_length=16)
    pool_key = models.CharField(max_length=64)
    calledstationid = models.CharField(max_length=64, blank=True)
    callingstationid = models.TextField()
    expiry_time = models.DateTimeField()
    username = models.TextField(blank=True)
    
    def is_static(self):
        if self.pool_name.startswith(Poolinfo.get_static_prefix()) \
            or self.expiry_time == Macinfo.get_static_overlapped_expiry():
            return True
        else:
            return False
    
    def __unicode__(self):
        return "%s -> %s " % (self.pool_name, self.framedipaddress.__str__())
    
    class Meta:
        db_table = 'radippool'

class Radpostauth(models.Model, Portdetailed, Getnas):
    id = util.BigAutoField(primary_key=True)
    username = models.CharField(max_length=253)
    pass_field = models.CharField(max_length=128, db_column='pass', blank=True)
    reply = models.CharField(max_length=32, blank=True)
    calledstationid = models.CharField(max_length=50, blank=True)
    callingstationid = models.CharField(max_length=50, blank=True)
    authdate = models.DateTimeField()
    nasportid = models.CharField(max_length=15, blank=True)
    nasipaddress = models.GenericIPAddressField()
    
    def __unicode__(self):
        return "%s %s %s" % (self.username, self.reply, self.authdate.__str__())
    
    class Meta:
        db_table = 'radpostauth'
        
    def is_mac(self):
        if modelfields.mac_re.match(self.username) is not None:
            return True
        
        return False
    
    def reason(self):
        if self.reply != "Access-Reject":
            return ""
        
        machine = None
        ldap_user = None
        local_user = None
        
        try:
            try:
                machine = Macinfo.objects.get(mac=self.username)            
            except exceptions.ObjectDoesNotExist:
                pass
            
            try:
                local_user = Radcheck.objects.get(username=self.username, attribute="Cleartext-Password")
            except exceptions.ObjectDoesNotExist:
                pass
            
            ldap_user = ldapbackend.LdapBackend().get_user_by_name(self.username)    
        except:
            return _(u"Erro ao determinar causa")
                    
        if machine is None and ldap_user is None and local_user is None:            
            return _(u"Usuário não cadastrado")
        
        if machine is not None and machine.expiry_time <= datetime.datetime.now():
            return _(u"Cadastro expirado")
        
        return _(u"Erro não identificado, talvez senha errada")

class Radreply(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=64)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2)
    value = models.CharField(max_length=253)
    
    def __unicode__(self):
        return "%s[%s] %s %s" % (self.username, self.attribute, self.op, self.value)
    
    class Meta:
        db_table = 'radreply'
        
class Radusergroup(models.Model):
    username = models.CharField(primary_key=True, max_length=64)
    groupname = models.CharField(max_length=64)
    priority = models.IntegerField()
    
    def __unicode__(self):
        return "%s %s %s" % (self.username, self.groupname, self.priority)
    
    class Meta:
        db_table = 'radusergroup'

class Macvendor(models.Model):
    mac_prefix = models.CharField(max_length=64, primary_key=True)
    vendor_name = models.CharField(max_length=200)
    class Meta:
        db_table = 'macvendor'

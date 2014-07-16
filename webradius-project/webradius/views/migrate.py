# -*- coding: utf-8 -*-

from webradius import models
from django import shortcuts
from lib.djangoutils  import customviews
from django.contrib.messages import api
from django.core import urlresolvers
from django.utils.translation import ugettext as _
from pyparsing import *
import datetime, time, re
from webradius.models import Poolinfo

class BasePyParser(object):
    filename = None
    file_content = None
    parser_def = None
    
    def __init__(self, base_path, filename, parser_def):
        # Considero que o arquivo esta em /tmp
        self.filename = base_path + filename
        
        self.parser_def = parser_def
        # Se der uma exceção deixa rolar para parar a requisição mesmo
        file_to_parse = open(self.filename, "r")
        self.file_content = file_to_parse.read()
        file_to_parse.close()
        
    def parse(self):
        return self.parser_def.parseString(self.file_content)
    
    def normalize_mac(self, tokens):
        mac = tokens["mac"]
        if ':' in mac:
            tokens["mac"] = mac.replace(':', '-')
        else:
            tokens["mac"] = mac 
        tokens["mac"] = tokens["mac"].lower()
    
class ParserStaticIps(BasePyParser):
    def __init__(self, base_path, filename):
        quoted_str = QuotedString('"', escChar='\\')
        ip_address = Combine(Word(nums) + ('.' + Word(nums)) * 3)
        hexint = Word(hexnums, exact=2)
        mac_address = Combine(hexint + (':' + hexint) * 5) | Combine(hexint + ('-' + hexint) * 5)
        
        mac_address.setParseAction(self.normalize_mac)
        
        parser_stmt = quoted_str("name") + mac_address("mac") + ip_address("ip") + \
                     ip_address("router") + ip_address("dns") + quoted_str("domain") + \
                     quoted_str("rev_domain") + ip_address("mask") + quoted_str("full_access")

        parser_def = Dict(ZeroOrMore(Group(parser_stmt)))
        
        super(ParserStaticIps, self).__init__(base_path, filename, parser_def)
        
class ParserStaticOverlappedIps(BasePyParser):
    def __init__(self, base_path, filename):
        quoted_str = QuotedString('"', escChar='\\')
        ip_address = Combine(Word(nums) + ('.' + Word(nums)) * 3)
        hexint = Word(hexnums, exact=2)
        mac_address = Combine(hexint + (':' + hexint) * 5) | Combine(hexint + ('-' + hexint) * 5)
        
        mac_address.setParseAction(self.normalize_mac)
        
        parser_stmt = quoted_str("name") + mac_address("mac") + ip_address("ip") + \
                     quoted_str("pool_name") + quoted_str("full_access")

        parser_def = Dict(ZeroOrMore(Group(parser_stmt)))
        
        super(ParserStaticOverlappedIps, self).__init__(base_path, filename, parser_def)

class ParserDHCPDLease(BasePyParser):
    starts_str = "starts"
    ends_str = "ends"
    tstp_str = "tstp"
    tsfp_str = "tsfp"
    cltt_str = "cltt"
    atsfp_str = "atsfp"
    hdw_str = "hardware"
    uid_str = "uid"
    binding_str = "binding"
    next_binding_str = "next binding"
    hostname_str = "client-hostname"
    fwd_name_str = "set ddns-fwd-name"
    fqdn_str = "set ddns-client-fqdn"
    txt_str = "set ddns-txt"
    rev_name_str = "set ddns-rev-name"
    
    def __init__(self, base_path, filename):
        LBRACE, RBRACE, SEMI, EQUAL = map(Suppress,'{};=')
        ip_address = Combine(Word(nums) + ('.' + Word(nums)) * 3)
        hexint = Word(hexnums,exact=2)
        mac_address = Combine(hexint + (':' + hexint) * 5)
        hdw_type = Word(alphanums)
        quoted_str = QuotedString('"', escChar='\\')
        
        mac_address.setParseAction(self.normalize_mac)
        
        yyyymmdd = Combine((Word(nums,exact=4) | Word(nums,exact=2))+
                            ('/' + Word(nums, exact=2)) * 2)
        hhmmss = Combine(Word(nums,exact=2) + (':' + Word(nums, exact=2)) * 2)
        date_ref = oneOf(list("0123456"))("weekday") + yyyymmdd("date") + \
                   hhmmss("time")
        date_ref.setParseAction(self.utc_to_local_time)

        starts_stmt = self.starts_str + date_ref + SEMI
        ends_stmt = self.ends_str + (date_ref | "never") + SEMI
        tstp_stmt = self.tstp_str + date_ref + SEMI
        tsfp_stmt = self.tsfp_str + date_ref + SEMI
        cltt_stmt = self.cltt_str + date_ref + SEMI
        atsfp_stmt = self.atsfp_str + date_ref + SEMI
        hdw_stmt = self.hdw_str + hdw_type("type") + mac_address("mac") + SEMI
        uid_stmt = self.uid_str + quoted_str + SEMI
        binding_stmt = self.binding_str + Word(alphanums) + Word(alphanums) + SEMI
        nextBinding_stmt = self.next_binding_str + Word(alphanums) + Word(alphanums) + SEMI
        hostname_stmt = self.hostname_str + quoted_str + SEMI
        fwdName_stmt = self.fwd_name_str + EQUAL + quoted_str + SEMI
        fqdn_stmt = self.fqdn_str + EQUAL + quoted_str + SEMI
        txt_stmt = self.txt_str + EQUAL + quoted_str + SEMI
        revName_stmt = self.rev_name_str + EQUAL + quoted_str + SEMI
        
        lease_statement = starts_stmt | ends_stmt | tstp_stmt | tsfp_stmt | hdw_stmt | \
                         uid_stmt | binding_stmt | nextBinding_stmt | cltt_stmt | \
                         hostname_stmt | fwdName_stmt | txt_stmt | \
                         revName_stmt | fqdn_stmt | atsfp_stmt

        lease_def = "lease" + ip_address("ipaddress") + LBRACE + \
                    Dict(ZeroOrMore(Group(lease_statement)))("attr") + RBRACE
        
        server_duid = "server-duid" + quoted_str("serverid") + SEMI
        
        leaseDictDef = Dict(ZeroOrMore(Group(lease_def | server_duid)))
        
        super(ParserDHCPDLease, self).__init__(base_path, filename, leaseDictDef)
        
    def utc_to_local_time(self, tokens):
        utctime = datetime.datetime.strptime("%(date)s %(time)s" % tokens,
                                             "%Y/%m/%d %H:%M:%S")
        localtime = utctime-datetime.timedelta(0, time.timezone, 0)
        tokens["utcdate"], tokens["utctime"] = tokens["date"], tokens["time"]
        tokens["localdate"], tokens["localtime"] = str(localtime).split()
        tokens["localdatetime"] = localtime
        del tokens["date"]
        del tokens["time"]
        
class ParserPools(BasePyParser):
    def __init__(self, base_path, filename):
        quoted_str = QuotedString('"', escChar='\\')
        ip_address = Combine(Word(nums) + ('.' + Word(nums)) * 3)
        netbios_node_type = Word(nums)
        
        pool_stmt = quoted_str("name") + quoted_str("desc") + ip_address("start") + ip_address("end") + \
                    ip_address("mask") + ip_address("router") + ip_address("broadcast") + \
                    quoted_str("domain") + quoted_str("rev_domain") + ip_address("dns") + \
                    ip_address("dns2") + ip_address("wins") + ip_address("wins2") + \
                    netbios_node_type("node_type") + quoted_str("ntp") + quoted_str("root_path") + \
                    quoted_str("filename") + ip_address("next_server")

        parser_def = Dict(ZeroOrMore(Group(pool_stmt)))
        
        super(ParserPools, self).__init__(base_path, filename, parser_def)

class MigrateCreatePools(customviews.SuperuserResctrictedView):    
    def get(self, request, *args, **kwargs):
        filename = self.kwargs.get('filename')
        
        parser = ParserPools("/tmp/", filename)
        
        pools = parser.parse()
        
        if len(pools) == 0:
            api.error(request, _(u"Erro ao carregar o arquivo %s" % (filename)))
            return shortcuts.redirect(urlresolvers.reverse('webradius:pool_list'))
        
        for pool in pools:
            result = models.Poolinfo.objects.filter(pool_name=pool.name)
            
            if len(result) >= 1:
                api.error(request, _(u"Um pool com o mesmo nome já está cadastrado: %s" % (pool.name)))
                return shortcuts.redirect(urlresolvers.reverse('webradius:pool_list'))

            new_pool = Poolinfo()
            new_pool.pool_name = pool.name
            new_pool.description = pool.desc
            new_pool.mask = pool.mask
            new_pool.router_address = pool.router
            new_pool.domain_name = pool.domain
            new_pool.rev_domain_name = pool.rev_domain
            new_pool.dns_server = pool.dns
            new_pool.dns_server2 = pool.dns2
            new_pool.ntp_server = pool.ntp
            new_pool.root_path = pool.root_path
            new_pool.boot_filename = pool.filename
            new_pool.next_server = pool.next_server
            new_pool.init_address = pool.start
            new_pool.end_address = pool.end
            new_pool.netbios_name_server = pool.wins
            new_pool.netbios_name_server2 = pool.wins2
            new_pool.netbios_node_type = pool.node_type
            new_pool.lease_time = 60 * 60 * 24 * 3
        
            result, name = new_pool.validate()
            
            if not result:
                api.error(request, _(u"Erro ao validar pool: %s" % (name)))
                return shortcuts.redirect(urlresolvers.reverse('webradius:pool_list'))
            
            result, name, pool_collide = new_pool.is_range_avaiable()
            
            if not result:
                api.error(request, _(u"Erro ao validar pool, IP já usado em outro Pool: %s - %s" % (name, pool_collide.pool_name)))
                return shortcuts.redirect(urlresolvers.reverse('webradius:pool_list'))
                            
            new_pool.save()
            
        api.success(request, _(u"Sucesso ao importar POOLs"))
        
        # Da um redirect para o mac_list, vai mostrar as mensagens de erro lá usando a api de mensagens do django
        return shortcuts.redirect(urlresolvers.reverse('webradius:pool_list'))
    
class MigrateInsertStaticMacs(customviews.SuperuserResctrictedView):    
    def get(self, request, *args, **kwargs):
        filename = self.kwargs.get('filename')
        
        parser = ParserStaticIps("/tmp/", filename)
        
        static_macs = parser.parse()
        
        if len(static_macs) == 0:
            api.error(request, _(u"Erro ao carregar o arquivo %s" % (filename)))
            return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
        
        for smac in static_macs:
            result = models.Macinfo.objects.filter(mac=smac.mac)
            
            if len(result) >= 1:
                api.error(request, _(u"O seguinte MAC já está cadastrado: %s" % (smac.mac)))
                return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
            
            machine = models.Macinfo()
            machine.mac = smac.mac
            machine.description = smac.name
            machine.static = True
            machine.static_standalone = True
            machine.static_ip = smac.ip
            machine.vland_id = 0
            if smac.full_access == 'true':
                machine.full_access = True
            else:
                machine.full_access = False

            pool = models.Poolinfo.create_static_pool(smac,
                                                      smac.ip,
                                                      smac.router, 
                                                      smac.mask, 
                                                      smac.dns,
                                                      smac.domain,
                                                      smac.rev_domain,
                                                      None, None, None,
                                                      None, None, 1)
        
            result, name = pool.validate()
            
            if not result:
                api.error(request, _(u"Erro ao validar pool para MAC estático: %s" % (name)))
                return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
            
            result, name, pool_collide = pool.is_range_avaiable()
            
            if not result:
                api.error(request, _(u"Erro ao validar pool, IP já usado em outro Pool: %s - %s" % (name, pool_collide.pool_name)))
                return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
            
            machine.create_static_pool(smac.router, 
                                       smac.mask, 
                                       smac.dns,
                                       smac.domain,
                                       smac.rev_domain,
                                       None, None, None,
                                       None, None, 1)
                            
            machine.save()
            
        api.success(request, _(u"Sucesso ao importar MACs"))
        
        # Da um redirect para o mac_list, vai mostrar as mensagens de erro lá usando a api de mensagens do django
        return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
    
class MigrateInsertStaticOverlappedMacs(customviews.SuperuserResctrictedView):    
    def get(self, request, *args, **kwargs):
        filename = self.kwargs.get('filename')
        
        parser = ParserStaticOverlappedIps("/tmp/", filename)
        
        static_macs = parser.parse()
        
        if len(static_macs) == 0:
            api.error(request, _(u"Erro ao carregar o arquivo %s" % (filename)))
            return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
        
        for smac in static_macs:
            result = models.Macinfo.objects.filter(mac=smac.mac)
            
            if len(result) >= 1:
                api.error(request, _(u"O seguinte MAC já está cadastrado: %s" % (smac.mac)))
                return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
            
            machine = models.Macinfo()
            
            # Checa se o Pool associado a máquina existe
            try:
                machine.pool = models.Poolinfo.objects.get(pool_name=smac.pool_name)
            except:
                api.error(request, _(u"O Pool associado a máquina não existe: %s -> %s" % (smac.pool_name, smac.mac)))
                return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
            
            if not machine.pool.is_in_range(smac.ip):
                api.error(request, _(u"O IP não está contido no Pool: %s -> %s" % (smac.ip, smac.pool_name)))
                return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
            
            machine.mac = smac.mac
            machine.description = smac.name
            machine.static = True
            machine.static_standalone = False            
            machine.static_ip = smac.ip
            machine.vland_id = 0
            if smac.full_access == 'true':
                machine.full_access = True
            else:
                machine.full_access = False
                
            machine.reserve_overlapped_static_ip()
                            
            machine.save()
            
        api.success(request, _(u"Sucesso ao importar MACs"))
        
        # Da um redirect para o mac_list, vai mostrar as mensagens de erro lá usando a api de mensagens do django
        return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))

class MigrateDHCPDLease(customviews.SuperuserResctrictedView):
    pools = None
    
    def __init__(self):
        self.pools = models.Poolinfo.objects.all().exclude(pool_name__startswith='static')
    
    def __is_in_pools(self, ip):
        for pool in self.pools:
            if pool.is_in_subnet_range(ip):
                return True, pool
        return False, None
    
    def __write_server_duid(self, out_file, duid):
        rewrite = "server-duid \"" + duid + "\";\n"
        out_file.write(rewrite)
    
    def __write_to_file(self, out_file, parser, attr, ip, next_binding, hostname,
                        fqdn, txt, fwd_name, rev_name):
        
        rewrite = "lease " + ip + " {\n"
        if attr.starts:
            rewrite += "  starts " + attr.starts[0] + " " + attr.starts[1] + " " + attr.starts[2] + ";\n"
        if attr.ends:
            rewrite += "  ends " + attr.ends[0] + " " + attr.ends[1] + " " + attr.ends[2] + ";\n"
        if attr.tstp:
            rewrite += "  tstp " + attr.tstp[0] + " " + attr.tstp[1] + " " + attr.tstp[2] + ";\n"
        if attr.cltt:
            rewrite += "  cltt " + attr.cltt[0] + " " + attr.cltt[1] + " " + attr.cltt[2] + ";\n"
        if attr.atsfp:
            rewrite += "  atsfp " + attr.atsfp[0] + " " + attr.atsfp[1] + " " + attr.atsfp[2] + ";\n"
        if attr.binding:
            rewrite += "  binding state " + attr.binding[1] + ";\n"
        if next_binding:
            rewrite += "  next binding state " + next_binding[1] + ";\n"
        if attr.get(parser.hdw_str) is not None:
            rewrite += "  hardware ethernet " + attr.hardware.mac.replace('-', ':') + ";\n"
        if attr.uid:
            uid_escape = attr.uid.replace("\"", "\\\"")
            rewrite += "  uid \"" + uid_escape + "\";\n"
        if fqdn:
            rewrite += "  set ddns-client-fqdn = \"" + fqdn + "\";\n"
        if rev_name:
            rewrite += "  set ddns-rev-name = \"" + rev_name + "\";\n"
        if txt:
            rewrite += "  set ddns-txt = \"" + txt + "\";\n"
        if fwd_name:
            rewrite += "  set ddns-fwd-name = \"" + fwd_name + "\";\n"
        if hostname:
            rewrite += "  client-hostname \"" + hostname + "\";\n"        
        rewrite += "}\n"
        
        out_file.write(rewrite)
        
    # Retorna o valor para o hw_type passado, só da suporte a Ethernet a principio
    def __hw_type_to_int(self, hw_type):
        return {
            'ethernet': 1,
        }[hw_type]
        
    def __extract_hostname(self, fwd_name, domain):
        if not fwd_name.endswith(domain):
            return None
        hostname = fwd_name.split(domain)[0].split('.')[0]
        return hostname
    
    def __migrate_leases(self, request, out_file, parser, leases):
        count = 0
        
        for lease in leases:
            # Se for o id do servidor pula e escreve no arquivo de saida
            if lease[0] == "server-duid":
                self.__write_server_duid(out_file, lease[1])
                continue
            
            attr = lease.attr
            
            ip = lease.ipaddress
            uid = attr.uid                        
            next_binding = attr.get(parser.next_binding_str)
            hostname = attr.get(parser.hostname_str)
            fqdn = attr.get(parser.fqdn_str)
            txt = attr.get(parser.txt_str)
            fwd_name = attr.get(parser.fwd_name_str)
            rev_name = attr.get(parser.rev_name_str)
            
            # Sem MAC só escreve no arquivo de saida
            if attr.get(parser.hdw_str) is None:
                self.__write_to_file(out_file, parser, attr, lease.ipaddress,
                                     next_binding, hostname, fqdn, txt,
                                     fwd_name, rev_name)
                continue
            
            mac = attr.hardware.mac
            hwtype = attr.hardware.type
            end_date = attr.ends.utcdate
            end_time = attr.ends.utctime
            binding_state = attr.binding[1]
            
            in_pool, pool = self.__is_in_pools(ip)
            
            # Se esse ip não estiver em nenhum pool apenas escreve ele no arquivo de saida
            if not in_pool:
                self.__write_to_file(out_file, parser, attr, lease.ipaddress,
                                     next_binding, hostname, fqdn, txt,
                                     fwd_name, rev_name)
                continue
            
            # Tendo fwd_name eu insiro uma entrada na tabela DDNS
            if fwd_name:
                name = None
                # Se o hostname for nulo usa o fqdn 
                if hostname is None:
                    # Se o fqdn for nulo também tenta extrair do fwd_name o hostname
                    if fqdn is None:
                        name = self.__extract_hostname(fwd_name, pool.domain_name)
                    else:
                        name = fqdn
                else:
                    name = hostname
                
                # Se apesar de tudo name for nulo ou tiver um ponto no name não inclui
                if name is not None and name.find('.') == -1:
                    # Procura uma entrada para esse IP, se não tiver cria
                    ddns = models.Ddns.objects.filter(fwd_name=fwd_name)
                    if len(ddns) < 1:
                        ddns = models.Ddns()
                    else:
                        ddns = ddns[0]
                    
                    # Não pode faltar o cadastro de domínio e domínio reverso
                    if pool.domain_name is None or pool.rev_domain_name is None:
                        raise Exception("Pool de destino não tem dominio e dominio reverso: %s" % (pool.pool_name))
                    
                    dt = datetime.datetime.strptime(end_date + ' ' + end_time, '%Y/%m/%d %H:%M:%S')
                    ddns.expiry = dt
                    ddns.mac = mac
                    ddns.ip = ip
                    ddns.hostname = name
                    ddns.fwd_name = fwd_name
                    ddns.txt = txt
                    ddns.rev_name = rev_name
                    if pool.rev_domain_name != "vazio":
                        ddns.rev_domain = pool.rev_domain_name
                    ddns.hw_type = self.__hw_type_to_int(hwtype)
                    
                    # Insere ou faz update no banco
                    ddns.save()
            
            # Tem reverso mas não tem fwd_name
            # Não vou fazer nada a princípio, o tempo irá resolver
            #if rev_name and not fwd_name:
            #    continue
            
            macinfo = models.Macinfo.objects.filter(mac=mac)
            if len(macinfo) >= 1:
                macinfo = macinfo[0]
                # Se já existe uma máquina com IP estático com esse MAC não altera ela
                if macinfo.static:
                    continue
                
                # Se ja venceu essa concessao prevalece o que ja esta cadastrado
                if datetime.datetime.now() > attr.ends.localdatetime:
                    continue
            else:
                macinfo = models.Macinfo()
            
            macinfo.mac = mac
            macinfo.description = "Máquina migrada."
            macinfo.pool = pool
            macinfo.static = False
            macinfo.static_ip = ''
            
            macinfo.save()
            
            ippool = models.Radippool.objects.filter(framedipaddress=ip)
            # Senão achar é algum IP que saiu do range na migração, então não migra o lease do IP
            if len(ippool) >= 1:
                ippool = ippool[0]
                
                # Se o lease que achou não está vencido eu não mecho nele
                if ippool.expiry_time >= datetime.datetime.now():
                    continue
                
                unset_expiry = "1969-12-31 21:00:00"
                str_expiry = "%s" % (ippool.expiry_time)
                
                # Só define o lease se este IP não tinha um lease já definido
                if str_expiry == unset_expiry:
                    ippool.pool_key = mac
                    ippool.calledstationid = "Freeradius-DHCP"
                    ippool.callingstationid = mac
                    dt = datetime.datetime.strptime(end_date + ' ' + end_time, '%Y/%m/%d %H:%M:%S')
                    ippool.expiry_time = dt
                    ippool.username = "DHCP-" + mac
                    
                    ippool.save()                
            
            # Contador
            count += 1
        
        api.success(request, _(u"Sucesso ao importar Leases: %s" % (count)))            
    
    def get(self, request, *args, **kwargs):
        filename = self.kwargs.get('filename')
        
        parser = ParserDHCPDLease("/tmp/", filename)
        
        leases = parser.parse()
        
        if len(leases) == 0:
            api.error(request, _(u"Erro ao carregar o arquivo %s" % (filename)))
            return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
        
        try:
            out_file_name = "/tmp/out_leases"
            out_file = open(out_file_name, "w")
        except:
            api.error(request, _(u"Erro ao abrir o arquivo %s" % (out_file_name)))
            return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
        
        try:
            self.__migrate_leases(request, out_file, parser, leases)
        finally:
            out_file.close()
        
        # Da um redirect para o mac_list, vai mostrar as mensagens de erro lá usando a api de mensagens do django
        return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))

class MigrateGenerateLeasesFile(customviews.SuperuserResctrictedView):
    pools = None
    machines = None
    all_ddns = None
    all_radippool = None
    regex_str = "([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})"
    
    def __init__(self):
        self.machines = models.Macinfo.objects.all()
        self.all_ddns = models.Ddns.objects.all()
        self.all_radippool = models.Radippool.objects.all()
    
    def __write_server_duid(self, out_file, duid):
        rewrite = "server-duid \"" + duid + "\";\n"
        out_file.write(rewrite)
        
    def __get_octal_str(self, integer):
        oct_number = oct(integer)
        str_oct = str(oct_number)[1:]
        
        if len(str_oct) == 0:
            str_oct = "000"
        elif len(str_oct) == 1:
            str_oct = "00" + str_oct
        elif len(str_oct) == 2:
            str_oct = "0" + str_oct
            
        str_oct = "\\" + str_oct
        return str_oct
        
    def __get_uid_buffer(self, mac, hw_type):
        mac_itens = []
        
        for item in re.finditer(self.regex_str, mac):
            for item2 in item.groups():
                mac_itens.append(item2)
    
        numbers = self.__get_octal_str(hw_type)
        
        for item in mac_itens:
            a = int(item, 16)
            numbers += self.__get_octal_str(a)
        
        return numbers
    
    def __write_to_file(self, out_file, ippool, machine, pool, ddns):
        diff = datetime.timedelta(seconds=pool.lease_time)
        try:
            starts = ippool.expiry_time - diff
        except:
            # Se der erro ao calcular a diferenca nao gera o lease
            return
        str_starts = starts.strftime("%w %Y/%m/%d %H:%M:%S")
        str_ends = ippool.expiry_time.strftime("%w %Y/%m/%d %H:%M:%S")
        
        rewrite = "lease " + ippool.framedipaddress + " {\n"
        rewrite += "  starts " + str_starts + ";\n"
        rewrite += "  ends " + str_ends + ";\n"
        
        # Se não está vencido o lease o binding state é active
        if ippool.expiry_time > datetime.datetime.now():
            rewrite += "  binding state active;\n"
            rewrite += "  next binding state free;\n"
        else:
            rewrite += "  binding state free;\n"
            
        rewrite += "  hardware ethernet " + machine.mac.replace('-', ':') + ";\n"
                
        if ddns is not None:
            # Se o prefixo for 31 tem que escrever o uid do cliente
            if ddns.txt[:2] == "31":
                rewrite += "  uid \"" + self.__get_uid_buffer(ddns.mac, ddns.hw_type) + "\";\n"
            
            rewrite += "  set ddns-fwd-name = \"" + ddns.fwd_name + "\";\n"
            rewrite += "  set ddns-txt = \"" + ddns.txt + "\";\n"
            rewrite += "  set ddns-rev-name = \"" + ddns.rev_name + "\";\n"
            
            rewrite += "  client-hostname \"" + ddns.hostname + "\";\n"
        
        rewrite += "}\n\n"        
        
        out_file.write(rewrite)
    
    def __generate_leases_file(self, request, out_file):
        count = 0
        
        for ippool in self.all_radippool:            
            machine = self.machines.filter(mac=ippool.pool_key)
            
            if len(machine) == 0:
                continue
            else:
                machine = machine[0]
            
            pool = machine.pool
            ddns = self.all_ddns.filter(mac=machine.mac)
            
            if len(ddns) == 0:
                ddns = None
            else:
                ddns = ddns[0]
                
            count = count + 1
            
            self.__write_to_file(out_file, ippool, machine, pool, ddns)
        
        api.success(request, _(u"Sucesso ao gerar leases: %s" % (count)))            
    
    def get(self, request, *args, **kwargs):
        try:
            out_file_name = "/tmp/out_leases"
            out_file = open(out_file_name, "w")
        except:
            api.error(request, _(u"Erro ao abrir o arquivo %s" % (out_file_name)))
            return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
        
        try:
            self.__generate_leases_file(request, out_file)
        finally:
            out_file.close()
        
        return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
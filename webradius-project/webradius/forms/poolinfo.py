# -*- coding: utf-8 -*-

from django import forms
from webradius import models
from django.utils.translation import ugettext as _
from django.forms import util
from django.core import urlresolvers
from lib.djangoutils.pgfields import ArrayFormField
import iptools

class PoolSearchForm(forms.Form):
    pool_name = forms.CharField(label=_(u'Nome'), min_length=3, max_length=64, required=False)
    init_address = forms.GenericIPAddressField(label=_(u'Endereço inicial:'), protocol='ipv4', required=False)
    end_address = forms.GenericIPAddressField(label=_(u'Endereço final:'), protocol='ipv4', required=False)
    mask = forms.GenericIPAddressField(label=_(u'Máscara:'), protocol='ipv4', required=False)
    router_address = forms.GenericIPAddressField(label=_(u'Roteador:'), protocol='ipv4', required=False)
    domain_name = forms.CharField(label=_(u'Domínio:'), min_length=3, max_length=254, required=False)
    dns_server = forms.GenericIPAddressField(label=_(u'DNS 1:'), protocol='ipv4', required=False)
    dns_server2 = forms.GenericIPAddressField(label=_(u'DNS 2:'), protocol='ipv4', required=False)
    mtu = forms.IntegerField(label=_(u'MTU:'), min_value=100, max_value=10000, required=False)
    ntp_server = forms.CharField(label=_(u'NTP:'), min_length=3, max_length=128, required=False)
    lease_time = forms.IntegerField(label=_(u'Concessão(seg):'), min_value=3600, required=False)

class PoolAddForm(forms.ModelForm):
    NETBIOS_NODE_TYPE = (
        (1, _(u"Broadcast")),
        (2, _(u"Peer")),
        (4, _(u"Mixed")), 
        (8, _(u"Hybrid")),  
    )    
    
    pool_name = forms.CharField(label=_(u'Nome'), min_length=3, max_length=64, required=True)
    description = forms.CharField(label=_(u'Descrição'), min_length=5, max_length=64, required=True)
    init_address = forms.GenericIPAddressField(label=_(u'Endereço inicial:'), protocol='ipv4', required=True)
    end_address = forms.GenericIPAddressField(label=_(u'Endereço final:'), protocol='ipv4', required=True)
    mask = forms.GenericIPAddressField(label=_(u'Máscara:'), protocol='ipv4', required=True)
    router_address = forms.GenericIPAddressField(label=_(u'Roteador:'), protocol='ipv4', required=True)
    lease_time = forms.IntegerField(label=_(u'Concessão(seg):'), min_value=3600, required=True)
    domain_name = forms.CharField(label=_(u'Domínio:'), min_length=3, max_length=254, required=False)
    rev_domain_name = forms.CharField(label=_(u'Domínio para IP reverso:'), min_length=3, max_length=254, required=False)
    dns_server = forms.GenericIPAddressField(label=_(u'DNS 1:'), protocol='ipv4', required=True)
    dns_server2 = forms.GenericIPAddressField(label=_(u'DNS 2:'), protocol='ipv4', required=False)
    netbios = forms.CharField(label=_(u'NetBIOS'), min_length=3, max_length=254, required=False)
    netbios_name_server = forms.GenericIPAddressField(label=_(u'NBNS/WINS:'), protocol='ipv4', required=False)
    netbios_name_server2 = forms.GenericIPAddressField(label=_(u'NBNS/WINS 2:'), protocol='ipv4', required=False)
    netbios_node_type = forms.ChoiceField(label=_(u'Tipo de nó NetBIOS:'), choices=NETBIOS_NODE_TYPE, initial=1)
    mtu = forms.IntegerField(label=_(u'MTU:'), min_value=100, max_value=10000, required=False)
    ntp_server = forms.CharField(label=_(u'NTP:'), min_length=3, max_length=128, required=False)
    next_server = forms.GenericIPAddressField(label=_(u'Próximo servidor:'), protocol='ipv4', required=False)
    root_path = forms.CharField(label=_(u'Caminho para o arquivo de boot'), min_length=3, max_length=128, required=False)
    boot_filename = forms.CharField(label=_(u'Arquivo de boot'), min_length=3, max_length=128, required=False)
    bind_gateways = ArrayFormField(label=_(u'Gateways associados'), required=False)
    vlan_id = forms.IntegerField(label=_(u"VLAN ID:"), min_value=2, max_value=4093, required=False)

    class Meta:
        model = models.Poolinfo
        fields = ['pool_name', 'description', 'init_address', 'end_address', \
                  'mask', 'router_address', 'vlan_id', 'lease_time', \
                  'domain_name', 'rev_domain_name', 'dns_server', \
                  'dns_server2', 'netbios', 'netbios_name_server', \
                  'netbios_name_server2', 'netbios_node_type', 'mtu', \
                  'ntp_server', 'next_server', 'root_path', \
                  'boot_filename', 'bind_gateways']

    def validate_pool(self, pool, cleaned_data):        
        result, name = pool.validate()
    
        if not result:
            if name == 'mask':
                message = _(u"A máscara de rede %s é inválida") % (pool.mask)
            elif name == 'router_address':
                message = _(u"A subrede %s/%s é inválida") % (pool.subnet_addr(), pool.mask)
            elif name == 'init_address':
                message = _(u"O endereço inicial do pool está fora da subrede %s/%s") % (pool.subnet_addr(), pool.mask)
            elif name == 'end_address':
                message = _(u"O endereço final do pool está fora da subrede %s/%s") % (pool.subnet_addr(), pool.mask)
            
            self._errors[name] = util.ErrorList([message])
            del cleaned_data[name]
            return False
        
        result, name, pool_collide = pool.is_range_avaiable()
        
        if not result:
            if pool_collide.pool_name.startswith('static'):
                machine = models.Macinfo.objects.get(pool=pool_collide.id)
                message = _(u"O endereço IP fornecido já está em uso pela máquina <a href=\"%s\">%s</a>") % \
                        (urlresolvers.reverse('webradius:mac_detail', args=(machine.id,)), machine.mac)
                
            else:
                message = _(u"A faixa de endereços IPs fornecida já está em uso no Pool <a href=\"%s\">%s</a> cuja faixa de endereços é %s - %s") % \
                    (urlresolvers.reverse('webradius:pool_detail', args=(pool_collide.id,)), \
                     pool_collide.pool_name, pool_collide.init_address, \
                     pool_collide.end_address)
            
            self._errors[name] = util.ErrorList([message])
            del cleaned_data[name]
            
            return False
        
        # Só checa os MACs associados se for edição
        if self.instance.id is not None:
            result, mac, name = pool.validate_static_macs()
            
            if not result:
                message = _(u"A nova faixa de endereços do Pool não abrange o IP estático da máquina <a href=\"%s\">%s</a>: %s") % \
                            (urlresolvers.reverse('webradius:mac_detail', args=(mac.id,)), mac.mac, mac.static_ip)
                
                self._errors[name] = util.ErrorList([message])
                del cleaned_data[name]
                
                return False
        
        result, gateway, pool_collide = pool.validate_bind_gateways()
        
        if not result:
            message = _(u"O gateway '%s' já está associado ao pool <a href=\"%s\">%s</a>") % \
                        (gateway, urlresolvers.reverse('webradius:pool_detail', args=(pool_collide.id,)), \
                         pool_collide.pool_name)
            self._errors['bind_gateways'] = util.ErrorList([message])
            del cleaned_data['bind_gateways']
            return False
        
        return True
    
    # Valida o nome do pool, por enquanto é feito apenas durante a inserção pois depois não é alterado mais.
    # Checa se contem caracteres não ASCII, não permite se tiver
    def validate_name(self, cleaned_data):        
        if not self.instance.id is None:
            return True
        
        pool_name = cleaned_data['pool_name']
        try:
            pool_name.decode('ascii')
        except:
            msg = _(u"O nome do Pool não pode conter caracteres especiais.")
            self._errors['pool_name'] = util.ErrorList([msg])
            del cleaned_data['pool_name']
            return False
        
        # Não pode começar com 'static'
        if pool_name.startswith('static'):
            msg = _(u"O nome do Pool não pode começar com a palavra 'static'")
            self._errors['pool_name'] = util.ErrorList([msg])
            del cleaned_data['pool_name']
            return False
        
        # O nome do pool não pode conter espaços
        for char in pool_name:
            if char.isspace():
                msg = _(u"O nome do Pool não pode conter espaços.")
                self._errors['pool_name'] = util.ErrorList([msg])
                del cleaned_data['pool_name']
                return False
        
        return True
    
    def clean_bind_gateways(self):
        for gip in self.cleaned_data['bind_gateways']:
            # Se não for nem um ipv4 nem um ipv6 válido gera um erro
            # O suporte a ipv6 não está habilitado, por isso vou comentar o código ipv6
            #if not iptools.ipv4.validate_ip(gip) and not iptools.ipv6.validate_ip(gip):
            if not iptools.ipv4.validate_ip(gip):
                raise forms.ValidationError(u'IP inválido: %s' % gip )
        return self.cleaned_data['bind_gateways']
    
    def clean(self):
        cleaned_data = self.cleaned_data  
        
        if not self.validate_name(cleaned_data):
            return cleaned_data
        
        pool = self.__get_instance_from_data(cleaned_data)
        
        if pool is None:
            raise forms.ValidationError(_(u"Erro inesperado ao validar Pool"))
        
        if not self.validate_pool(pool, cleaned_data):
            return cleaned_data
        
        return cleaned_data
    
    def reset_errors(self):
        del self._errors
    
    def __get_instance_from_data(self, dict_data):
        new_pool = models.Poolinfo()
        
        # Se for edição o nome do Pool já está preenchido na instancia
        if self.instance.id is not None:
            new_pool.pool_name = self.instance.pool_name
        else:
            new_pool.pool_name = dict_data.get('pool_name')    
        new_pool.description = dict_data.get('description')
        new_pool.mask = dict_data.get('mask')
        new_pool.router_address = dict_data.get('router_address')
        new_pool.init_address = dict_data.get('init_address')
        new_pool.end_address = dict_data.get('end_address')
        new_pool.lease_time = dict_data.get('lease_time')
        new_pool.dns_server = dict_data.get('dns_server')
       
        fields = [new_pool.pool_name, new_pool.description, new_pool.mask,
                    new_pool.router_address, new_pool.init_address,
                    new_pool.end_address, new_pool.lease_time,
                    new_pool.dns_server]
        
        if None in fields:
            return None
        
        new_pool.rev_domain_name = dict_data.get('rev_domain_name')        
        new_pool.dns_server2 = dict_data.get('dns_server2')
        new_pool.netbios = dict_data.get('netbios')
        new_pool.netbios_name_server = dict_data.get('netbios_name_server')
        new_pool.netbios_name_server2 = dict_data.get('netbios_name_server2')
        new_pool.netbios_node_type = dict_data.get('netbios_node_type')
        new_pool.mtu = dict_data.get('mtu')
        new_pool.ntp_server = dict_data.get('ntp_server')        
        new_pool.next_server = dict_data.get('next_server')
        new_pool.root_path = dict_data.get('root_path')
        new_pool.boot_filename = dict_data.get('boot_filename')        
        new_pool.bind_gateways = dict_data.get('bind_gateways')
        new_pool.vlan_id = dict_data.get('vlan_id')
                
        return new_pool
    
    def save(self, commit=True):
        instance = super(PoolAddForm, self).save(commit=False)
        
        if commit:
            if self.instance.id:
                old_range = self.__get_instance_from_data(self.initial).range()
            else:
                old_range = None
            instance.save(old_range=old_range)
        return instance

class PoolEditForm(PoolAddForm):
    def __init__(self, *args, **kwargs):
        super(PoolAddForm, self).__init__(*args, **kwargs)
        # Retira o campo que não pode ser editado
        self.fields.pop('pool_name')
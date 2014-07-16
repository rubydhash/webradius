# -*- coding: utf-8 -*-

from django import forms
from webradius import models
from django.utils.translation import ugettext as _
from django.forms import util
from django.core import urlresolvers 
from lib.djangoutils import modelfields
import datetime

class MacSearchForm(forms.Form):
    datetime_formats = ['%d-%m-%Y %H:%M:%S',
                        '%d-%m-%Y %H:%M',
                        '%d-%m-%Y',
                        '%d/%m/%Y %H:%M:%S',
                        '%d/%m/%Y %H:%M',
                        '%d/%m/%Y',
                        '%d/%m/%Y %H:%M:%S',
                        '%d/%m/%Y %H:%M',
                        '%d/%m/%Y']
    
    mac = forms.CharField(label=_(u"MAC"), min_length=2, max_length=18, required=False)
    description = forms.CharField(label=_(u'Descrição'), min_length=3, max_length=100, required=False)
    start_expiry = forms.DateTimeField(label=_(u'Data mínima de expiração'), input_formats=datetime_formats, required=False)
    end_expiry = forms.DateTimeField(label=_(u'Data máxima de expiração'), input_formats=datetime_formats, required=False)
    static = forms.BooleanField(label=_(u'IP estático?'), required=False)
    pool = forms.ModelChoiceField(queryset=models.Poolinfo.objects.all().exclude(pool_name__startswith='static').order_by('pool_name'), required=False)
    static_ip = forms.CharField(label=_(u"IP"), min_length=2, max_length=15, required=False)
    full_access = forms.BooleanField(label=_(u'Acesso irrestrito'), required=False)
    
    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        self.fields['start_expiry'].widget.attrs['class'] = 'date_time_input'
        self.fields['end_expiry'].widget.attrs['class'] = 'date_time_input'
    
    class Media:
        js = ('webradius/form.js',)

class MacAddForm(forms.ModelForm):
    datetime_formats = ['%d-%m-%Y %H:%M:%S',
                        '%d-%m-%Y %H:%M',
                        '%d-%m-%Y',
                        '%d/%m/%Y %H:%M:%S',
                        '%d/%m/%Y %H:%M',
                        '%d/%m/%Y',
                        '%d/%m/%Y %H:%M:%S',
                        '%d/%m/%Y %H:%M',
                        '%d/%m/%Y']
    
    NETBIOS_NODE_TYPE = (
        (1, _(u"Broadcast")),
        (2, _(u"Peer")),
        (4, _(u"Mixed")), 
        (8, _(u"Hybrid")),  
    )    

    mac = modelfields.MACAddressFormField(label=_(u'MAC'))
    description = forms.CharField(label=_(u'Descrição'), min_length=3, max_length=100)
    static = forms.BooleanField(label=_(u'IP estático?'), required=False)
    expiry_time = forms.DateTimeField(label=_(u'Data de expiração:'), input_formats=datetime_formats, required=False)
    pool = forms.ModelChoiceField(queryset=models.Poolinfo.objects.all().exclude(pool_name__startswith='static').order_by('pool_name'), empty_label=None, required=False)
    static_standalone = forms.BooleanField(label=_(u'IP estático fora de um Pool?'), required=False)
    static_ip = forms.GenericIPAddressField(label=_(u'IP:'), protocol='ipv4', required=False)    
    vlan_id = forms.IntegerField(label=_(u"VLAN ID:"), min_value=2, max_value=4093, required=False)
    
    # Informações do IP estático
    full_access = forms.BooleanField(label=_(u'Acesso irrestrito'), required=False)
    mask = forms.GenericIPAddressField(label=_(u'Máscara:'), protocol='ipv4', required=False)
    router_address = forms.GenericIPAddressField(label=_(u'Roteador:'), protocol='ipv4', required=False)    
    dns_server = forms.GenericIPAddressField(label=_(u'DNS:'), protocol='ipv4', required=False)    
    domain_name = forms.CharField(label=_(u'Domínio (opcional):'), min_length=3, max_length=254, required=False)
    rev_domain_name = forms.CharField(label=_(u'Domínio para IP reverso (opcional):'), min_length=3, max_length=254, required=False)
    next_server = forms.GenericIPAddressField(label=_(u'Próximo servidor:'), protocol='ipv4', required=False)
    root_path = forms.CharField(label=_(u'Caminho para o arquivo de boot'), min_length=3, max_length=128, required=False)
    boot_filename = forms.CharField(label=_(u'Arquivo de boot'), min_length=3, max_length=128, required=False)    
    netbios_name_server = forms.GenericIPAddressField(label=_(u'NBNS/WINS:'), protocol='ipv4', required=False)
    netbios_name_server2 = forms.GenericIPAddressField(label=_(u'NBNS/WINS 2:'), protocol='ipv4', required=False)
    netbios_node_type = forms.ChoiceField(label=_(u'Tipo de nó NetBIOS:'), choices=NETBIOS_NODE_TYPE, initial=1)
    
    # Atributos da classe, fora do form mostrado ao usuário
    dynamic_ip_in_use = False
    dynamic_pool_full = False
    force = False
    
    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.fields['expiry_time'].widget.attrs['class'] = 'date_time_input'

    class Media:
        js = ('webradius/form.js',)

    class Meta:
        model = models.Macinfo
        fields = ['mac', 'description', 'expiry_time', 'vlan_id', \
                  'static', 'static_standalone', 'pool', 'full_access', 'static_ip', 'mask', 'router_address', \
                  'dns_server', 'domain_name', 'rev_domain_name', 'next_server', \
                  'root_path', 'boot_filename', 'netbios_name_server', 'netbios_name_server2', \
                  'netbios_node_type']
        
    def clean_mac(self):
        new_mac = self.cleaned_data.get('mac').lower()

        # Se for edição não valida esse campo
        if self.instance.id is not None:
            return new_mac
        
        macl = models.Macinfo.objects.filter(mac=new_mac)
         
        if len(macl) >= 1:
            smac = macl[0]
            message = u"O mac fornecedido já está cadastrado: <a href=\"%s\">%s</a>" \
                      % (urlresolvers.reverse('webradius:mac_detail', args=(smac.id,)), new_mac)
            raise forms.ValidationError(message)
        return new_mac
        
    def validate_pool(self, pool, cleaned_data):
        result, name = pool.validate()

        if not result:
            if name == 'mask':
                message = _(u"A máscara de rede %s é inválida") % (pool.mask)
                self._errors[name] = util.ErrorList([message])
                del cleaned_data[name]
            elif name == 'router_address':
                message = _(u"A subrede %s/%s é inválida") % (pool.subnet_addr(), pool.mask)
                self._errors[name] = util.ErrorList([message])
                del cleaned_data[name]
            elif name == 'init_address' or name == 'end_address':
                message = _(u"O endereço IP fornecido está fora da subrede %s/%s") % (pool.subnet_addr(), pool.mask)
                self._errors['static_ip'] = util.ErrorList([message])
                del cleaned_data['static_ip']
            else:
                message = _(u"Erro de validação na subrede especificada")
                self._errors['pool'] = util.ErrorList([message])
                del cleaned_data['pool']
            return False
        
        result, name, pool_collide = pool.is_range_avaiable()
        
        if not result:            
            if pool_collide.pool_name.startswith('static'):
                machine = models.Macinfo.objects.get(pool=pool_collide.id)
                message = _(u"O endereço IP fornecido já está em uso pela máquina <a href=\"%s\">%s</a>") % \
                        (urlresolvers.reverse('webradius:mac_detail', args=(machine.id,)), machine.mac)
                
            else:
                message = _(u"O endereço IP fornecido já está em uso em <a href=\"%s\">%s</a> cuja faixa de endereços é %s - %s") % \
                    (urlresolvers.reverse('webradius:pool_detail', args=(pool_collide.id,)), \
                     pool_collide.pool_name, pool_collide.init_address, \
                     pool_collide.end_address)
            self._errors['static_ip'] = util.ErrorList([message])
            del cleaned_data['static_ip']
            
            return False
        
        return True
    
    def validate_static_overlapped(self, cleaned_data, mac):
        pool = cleaned_data.get('pool')
        static_ip = cleaned_data.get('static_ip')
        
        if not pool.is_in_range(static_ip):
            self._errors["pool"] = util.ErrorList(
                [u"O IP não está contido na intervalo do Pool selecionado."])
            del cleaned_data['pool']
            return False
        
        # Busca uma máquina que já tenha o mesmo IP, excluindo a propria máquina se for uma edição
        if self.instance.id is None:
            result = models.Macinfo.objects.filter(static_ip=static_ip)
        else:
            result = models.Macinfo.objects.filter(static_ip=static_ip).exclude(pk=self.instance.id)
        
        if len(result) > 0:
            self._errors["static_ip"] = util.ErrorList(
                [u"O endereço IP fornecido já está em uso pela máquina <a href=\"%s\">%s</a>" \
                 % (urlresolvers.reverse('webradius:mac_detail', args=(result[0].id,)), result[0].mac)])
            del cleaned_data['static_ip']
            return False
        
        # Checa se o IP está atualmente atribuido a cliente dinâmico
        radippool = models.Radippool.objects.get(framedipaddress=static_ip)
        
        if radippool.expiry_time > datetime.datetime.now() and radippool.pool_key != mac:
            self.dynamic_ip_in_use = True
            if not self.force:
                self._errors["static_ip"] = util.ErrorList(
                    [u"O endereço IP fornecido está atualmente em uso por um cliente dinâmico. Esse cadastro pode gerar conflito de IP. Para confirmar clique novamente em cadastrar/salvar."])
                del cleaned_data['static_ip']                
                return False
            else:
                return True
                
        return True

    def validate_optional_fields(self, cleaned_data):
        result = True
        if cleaned_data.get('static'):
            if not cleaned_data.get('static_ip'):
                if self._errors.get('static_ip') is None:
                    self._errors["static_ip"] = util.ErrorList(
                        [u"O campo 'IP' é obrigatório quando o IP for estático."])
                result = False

            if cleaned_data.get('static_standalone'):
                if not cleaned_data.get('mask'):
                    if self._errors.get('mask') is None:
                        self._errors["mask"] = util.ErrorList([u"O campo 'Máscara' é obrigatório quando o IP for estático."])
                    result = False
                if not cleaned_data.get('router_address'):
                    if self._errors.get('router_address') is None:
                        self._errors["router_address"] = util.ErrorList(
                            [u"O campo 'Roteador' é obrigatório quando o IP for estático."])
                    result = False
                if not cleaned_data.get('dns_server'):
                    if self._errors.get('dns_server') is None:
                        self._errors["dns_server"] = util.ErrorList(
                            [u"O campo 'DNS' é obrigatório quando o IP for estático."])
                    result = False
        else:
            if not cleaned_data.get('pool'):
                if self._errors.get('pool') is None:
                    self._errors["pool"] = util.ErrorList(
                        [u"É necessário selecionar o Pool quando o ip for dinâmico."])
                result = False
        
        return result
    
    # Se for dinâmico tem que checar se já não há mais hosts do que o suportado em um determinado Pool de endereços
    # Só serve como warning 
    def is_dynamic_pool_full(self, cleaned_data):
        pool = cleaned_data.get('pool')
        if pool.is_full():
            self.dynamic_pool_full = True            
            return True
        return False
    
    def clean(self):
        cleaned_data = self.cleaned_data

        # Se já tem algum erro retorna de cara
        if len(self._errors) > 0:
            return cleaned_data
        
        if not self.validate_optional_fields(cleaned_data):
            return cleaned_data

        # Se for edição o mac já está no objeto
        if self.instance.id is not None:
            mac = self.instance.mac
        else:
            mac = cleaned_data.get('mac')

        if cleaned_data.get('static'):
            if cleaned_data.get('static_standalone'):
                # Tanto para edição quanto para criação ele "cria" um pool provisorio para validação
                pool = models.Poolinfo.create_static_pool(mac,
                                                          cleaned_data.get('static_ip'),
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
                if not self.validate_pool(pool, cleaned_data):
                    return cleaned_data
            else:
                result = self.validate_static_overlapped(cleaned_data, mac)
                if not result:
                    return cleaned_data
        
        if self.is_dynamic_pool_full(cleaned_data):
            self.dynamic_pool_full = True
            return cleaned_data
        
        return cleaned_data
    
    def reset_errors(self):
        del self._errors
        
    def __get_element_from_list(self, l, name):
        for item in l:
            if item == name:
                return item
        return False
    
    def save(self, commit=True):
        instance = super(MacAddForm, self).save(commit=False)
        
        if self.instance.id is None:
            was_static = False
            old_pool_id = None
            old_ip = None
            was_standalone = None
        else:
            if self.__get_element_from_list(self.changed_data, 'static') :
                was_static = self.initial['static']
            else:
                was_static = instance.static
            
            if self.__get_element_from_list(self.changed_data, 'static_standalone'):
                was_standalone = self.initial['static_standalone']
            else:
                was_standalone = instance.static_standalone
            
            if self.__get_element_from_list(self.changed_data, 'static_ip'):
                old_ip = self.initial['static_ip']
            else:
                old_ip = instance.static_ip
            
            if self.__get_element_from_list(self.changed_data, 'pool'):
                old_pool_id = self.initial['pool']
            else:
                old_pool_id = instance.pool.id
        
        instance.adjust_static(self.cleaned_data, was_static, was_standalone,
                               old_pool_id, old_ip)
        
        if commit:
            instance.save()
        return instance
        
class MacEditForm(MacAddForm):
    def __init__(self, *args, **kwargs):
        super(MacAddForm, self).__init__(*args, **kwargs)
        # Retira o campo que não pode ser editado
        self.fields.pop('mac')
        self.fields['expiry_time'].widget.attrs['class'] = 'date_time_input'
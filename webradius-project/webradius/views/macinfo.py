# -*- coding: utf-8 -*-

from django import shortcuts
from django.views import generic
from django.core import exceptions
from datetime import datetime
from django import http
from django.contrib.messages import api
from django.core import urlresolvers
from django.utils.translation import ugettext as _
from lib.djangoutils  import customviews
from webradius.forms import macinfo 
from webradius import models

class MachinesView(generic.View):
    template_name = 'webradius/mac_list.html'
    model = models.Macinfo
    
    def get(self, request, *args, **kwargs):
        form = macinfo.MacSearchForm()
        return shortcuts.render(request, self.template_name, {'form': form, 'object_list': []})
    
    def post(self, request, *args, **kwargs):
        object_list = []
        form = macinfo.MacSearchForm(request.POST)
        if form.is_valid():
            fdata = form.cleaned_data
            
            if fdata.get('mac'):
                # Substitui todos os caracteres ':' por '-'
                mac_search = fdata.get('mac').replace(':', '-')
                object_list = self.model.objects.filter(mac__icontains=mac_search)
            else:
                object_list = self.model.objects.all()
            if fdata.get('description'):
                object_list = object_list.filter(description__icontains=fdata.get('description'))            
            if fdata.get('insert_date'):
                object_list = object_list.filter(insert_date=fdata.get('insert_date'))
            if fdata.get('start_expiry') or fdata.get('end_expiry'):
                if fdata.get('start_expiry'):
                    start_expiry = fdata.get('start_expiry')
                else:
                    start_expiry = datetime(1969, 12, 31, 23, 59, 59)
                if fdata.get('end_expiry'):
                    end_expiry = fdata.get('end_expiry')
                else:
                    end_expiry = datetime(9999, 12, 31, 23, 59, 59)

                object_list = object_list.filter(expiry_time__range=[start_expiry, end_expiry])                
            if fdata.get('static') and fdata.get('static_ip'):
                    object_list = object_list.filter(static=fdata.get('static'))
                    object_list = object_list.filter(static_ip__contains=fdata.get('static_ip'))                
            else:
                if fdata.get('pool'):
                    object_list = object_list.filter(pool=fdata.get('pool'))
            
            if fdata.get('full_access'):
                object_list = object_list.filter(full_access=True)
                    
            printpdf = request.POST.get('printpdf')
            if printpdf:
                attach = request.GET.get('attachpdf') or ''
                if attach:
                    attach = 'attachment;'
                response = http.HttpResponse(mimetype='application/pdf')
                response['Content-Disposition'] = '%s filename=USER_REPORT_%s.pdf' % (
                attach, datetime.now().strftime('%Y%m%d%H%M%S'))
                from webradius.report import MacReport
                from geraldo.generators import PDFGenerator
                report = MacReport(queryset=object_list)
                report.generate_by(PDFGenerator, filename=response)
                return response
            
        return shortcuts.render(request, self.template_name, {'form': form, 'object_list': object_list})

class MachineAddView(customviews.RestrictedView):
    perm_name = 'add'
    template_name = 'webradius/mac_add.html'
    template_force_name = 'webradius/mac_add_force.html'
    model = models.Macinfo
    
    def get(self, request, *args, **kwargs):
        mac = self.kwargs.get('mac')
        if mac is not None:
            form_initial = {'mac': mac}                    
            form = macinfo.MacAddForm(initial=form_initial)
        else:
            form = macinfo.MacAddForm()
                
        if models.Poolinfo.objects.all().exclude(pool_name__startswith='static').count() == 0:
            api.info(request, _(u'Não há nenhum Pool de endereços cadastrado ainda'))
            return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
        return shortcuts.render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        force = request.GET.get('force')
        
        form = macinfo.MacAddForm(request.POST)
        if force:
            form.force = True
        
        if form.is_valid():
            machine = form.save()
                           
            models.Log(user=request.user, msg=_(u"Máquina '%s' cadastrado" % machine.mac)).save()                
            api.success(request, _(u'Máquina cadastrada com sucesso'))
            
            if form.dynamic_pool_full:
                api.warning(request, _(u'O pool associado a máquina tem mais máquinas do que IPs disponíveis.'))
            
            return shortcuts.redirect(urlresolvers.reverse('webradius:mac_detail', args=(machine.id,)))
        
        if form.dynamic_ip_in_use:
            return shortcuts.render(request, self.template_force_name, {'form': form})
        else:
            return shortcuts.render(request, self.template_name, {'form': form})
            

class MachineDeleteView(customviews.RestrictedView):
    perm_name = 'delete'
    model = models.Macinfo

    def get(self, request, *args, **kwargs):
        machine = shortcuts.get_object_or_404(self.model, pk=self.kwargs.get('pk'))
        
        machine.delete()
        
        api.success(self.request, _(u"Máquina removida com sucesso"))
        models.Log(user=self.request.user, msg=_(u"Máquina '%s' removida" % machine.mac)).save()
        
        return shortcuts.redirect(urlresolvers.reverse('webradius:mac_list'))
    
class MachineDetailBaseView():
    def return_response(self, request, machine):
        ips = models.Radippool.objects.filter(pool_key=machine.mac).filter(expiry_time__gt=datetime.now())
        
        if request.user.is_superuser:
            logs = models.Log.objects.filter(msg__contains=machine.mac).order_by('-created')[:20]
        else:
            logs = models.Log.objects.filter(msg__contains=machine.mac).filter(user=request.user).order_by('-created')[:20]
        
        try:
            vendor = models.Macvendor.objects.get(mac_prefix=machine.mac[:8].upper())
        except:
            vendor = None
            
        sessions = models.Radacct.objects.filter(username=machine.mac).order_by('-acctstarttime')[:20]

        auths = models.Radpostauth.objects.filter(username=machine.mac).order_by('-id')[:20]
        
        dns_entrys = models.Ddns.objects.filter(mac=machine.mac).order_by('-expiry')
        
        return shortcuts.render(request, self.template_name, {'object': machine, 'lastchanges': logs,
                                                              'ips': ips, 'vendor': vendor,
                                                              'sessions': sessions,
                                                              'auths': auths,
                                                              'dns_entrys': dns_entrys})

class MachineDetailView(generic.View, MachineDetailBaseView):
    model = models.Macinfo
    template_name = 'webradius/mac_detail.html'
    
    def get(self, request, *args, **kwargs):
        machine = shortcuts.get_object_or_404(self.model, pk=self.kwargs.get('pk'))
        
        return super(MachineDetailView, self).return_response(request, machine)

class MachineDetailByMacView(generic.View, MachineDetailBaseView):
    model = models.Macinfo
    template_name = 'webradius/mac_detail.html'
    
    def get(self, request, *args, **kwargs):
        mac = self.kwargs.get('mac')
        try:            
            machine = self.model.objects.get(mac=mac)
        except exceptions.ObjectDoesNotExist:
            return shortcuts.redirect(urlresolvers.reverse('webradius:mac_may_add', args=(mac,)))
        
        return super(MachineDetailByMacView, self).return_response(request, machine)
    
class MachineMayAddView(generic.View):
    model = models.Macinfo
    template_name = 'webradius/mac_may_add.html'
    
    def get(self, request, *args, **kwargs):
        return shortcuts.render(request, self.template_name, {'mac': self.kwargs.get('mac')})

class MachineEditView(customviews.RestrictedView):
    perm_name = 'change'
    model = models.Macinfo
    template_name = 'webradius/mac_edit.html'
    template_force_name = 'webradius/mac_edit_force.html'
    
    def __get_form(self, machine, post=None):
        form_initial = {'mask': machine.pool.mask,
                        'router_address': machine.pool.router_address,
                        'dns_server': machine.pool.dns_server,
                        'domain_name': machine.pool.domain_name,
                        'rev_domain_name': machine.pool.rev_domain_name,
                        'next_server': machine.pool.next_server,
                        'root_path': machine.pool.root_path,
                        'boot_filename': machine.pool.boot_filename,
                        'netbios_name_server': machine.pool.netbios_name_server,
                        'netbios_name_server2': machine.pool.netbios_name_server2,
                        'netbios_node_type': machine.pool.netbios_node_type}
        if post is not None:
            return macinfo.MacEditForm(post, instance=machine, initial=form_initial)
        else:
            return macinfo.MacEditForm(instance=machine, initial=form_initial)
 
    def get(self, request, *args, **kwargs):
        machine = shortcuts.get_object_or_404(models.Macinfo, pk=self.kwargs.get('pk'))         
        return shortcuts.render(request, self.template_name, {'form': self.__get_form(machine),
                                                              'object': machine})
 
    def post(self, request, *args, **kwargs):
        machine = shortcuts.get_object_or_404(self.model, pk=self.kwargs.get('pk'))
        force = request.GET.get('force')        
        
        form = self.__get_form(machine, request.POST)
        if force:
            form.force = True
 
        if form.is_valid():
            if not form.has_changed():
                form.reset_errors()
                api.info(request, _(u'Nenhuma alteração efetuada'))
                return shortcuts.render(request, self.template_name, {'form': form,
                                                                      'object': machine})
            
            machine = form.save()
            
            api.success(request, _(u'Máquina alterada com sucesso'))
            
            if form.dynamic_pool_full:
                api.warning(request, _(u'O pool associado a máquina tem mais máquinas do que IPs disponíveis.'))
            
            models.Log(user=request.user, msg=_(u"Máquina '%s' alterada" % machine.mac)).save()
            return shortcuts.redirect(urlresolvers.reverse('webradius:mac_detail', args=(machine.id,)))
        
        if form.dynamic_ip_in_use:
            return shortcuts.render(request, self.template_force_name, {'form': form,
                                                                        'object': machine})
        else:
            return shortcuts.render(request, self.template_name, {'form': form,
                                                                  'object': machine})
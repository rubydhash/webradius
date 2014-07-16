# -*- coding: utf-8 -*-

from webradius.forms import poolinfo 
from webradius import models
from django import shortcuts
from django.views import generic
from datetime import datetime
from django import http
from lib.djangoutils import customviews
from django.contrib.messages import api
from django.core import urlresolvers
from django.utils.translation import ugettext as _

class PoolsView(generic.View):
    model = models.Poolinfo
    template_name = 'webradius/pool_list.html'
    
    def get(self, request, *args, **kwargs):
        form = poolinfo.PoolSearchForm()
        
        object_list = self.model.objects.all()
        object_list = object_list.exclude(pool_name__startswith=self.model.get_static_prefix())
        
        return shortcuts.render(request, self.template_name, {'form': form, 'object_list': object_list})
    
    def post(self, request, *args, **kwargs):
        object_list = []
        form = poolinfo.PoolSearchForm(request.POST)
        if form.is_valid():
            fdata = form.cleaned_data
            
            object_list = self.model.objects.all()
            object_list = object_list.exclude(pool_name__startswith=self.model.get_static_prefix())

            if fdata.get('pool_name'):
                object_list = object_list.filter(pool_name=fdata.get('pool_name'))                
            if fdata.get('init_address'):
                object_list = object_list.filter(init_address=fdata.get('init_address'))            
            if fdata.get('end_address'):
                object_list = object_list.filter(end_address=fdata.get('end_address'))
            if fdata.get('mask'):
                object_list = object_list.filter(mask=fdata.get('mask'))
            if fdata.get('domain_name'):
                object_list = object_list.filter(domain_name=fdata.get('domain_name'))
            if fdata.get('router_address'):
                object_list = object_list.filter(router_address=fdata.get('router_address'))
            if fdata.get('dns_server'):
                object_list = object_list.filter(dns_server=fdata.get('dns_server'))
            if fdata.get('dns_server2'):
                object_list = object_list.filter(dns_server2=fdata.get('dns_server2'))
            if fdata.get('mtu'):
                object_list = object_list.filter(mtu=fdata.get('mtu'))
            if fdata.get('ntp_server'):
                object_list = object_list.filter(ntp_server=fdata.get('ntp_server'))
            if fdata.get('lease_time'):
                object_list = object_list.filter(lease_time=fdata.get('lease_time'))

            printpdf = request.POST.get('printpdf')
            if printpdf:
                attach = request.GET.get('attachpdf') or ''
                if attach:
                    attach = 'attachment;'
                response = http.HttpResponse(mimetype='application/pdf')
                response['Content-Disposition'] = '%s filename=USER_REPORT_%s.pdf' % (
                attach, datetime.now().strftime('%Y%m%d%H%M%S'))
                from webradius.report import PoolReport
                from geraldo.generators import PDFGenerator
                report = PoolReport(queryset=object_list)
                report.generate_by(PDFGenerator, filename=response)
                return response
            
        return shortcuts.render(request, self.template_name, {'form': form, 'object_list': object_list})

class PoolDetailBaseView():
    model = models.Poolinfo
    template_name = 'webradius/pool_detail.html'
    
    def return_response(self, request, pool):     
        if pool.pool_name.startswith(models.Poolinfo.get_static_prefix()):
            return shortcuts.redirect(urlresolvers.reverse('handler403'))
        
        return shortcuts.render(request, self.template_name, {'object': pool})

class PoolDetailView(generic.View, PoolDetailBaseView):
    model = models.Poolinfo
    template_name = 'webradius/pool_detail.html'
    
    def get(self, request, *args, **kwargs):
        pool = shortcuts.get_object_or_404(self.model, pk=self.kwargs.get('pk'))
        
        return super(PoolDetailView, self).return_response(request, pool)
    
class PoolDetailByNameView(generic.View, PoolDetailBaseView):
    model = models.Poolinfo
    template_name = 'webradius/pool_detail.html'
    
    def get(self, request, *args, **kwargs):
        pool = shortcuts.get_object_or_404(self.model, pool_name=self.kwargs.get('name'))
        
        return super(PoolDetailByNameView, self).return_response(request, pool)
    
class PoolAddView(customviews.RestrictedView):
    model = models.Poolinfo
    template_name = 'webradius/pool_add.html'
    perm_name = 'add'
    
    def get(self, request, *args, **kwargs):
        form = poolinfo.PoolAddForm()
        return shortcuts.render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = poolinfo.PoolAddForm(request.POST)
        
        if form.is_valid():
            pool = form.save()

            models.Log(user=request.user, msg=_(u"Pool '%s' cadastrado" % pool.pool_name)).save()
            api.success(request, _(u'Pool cadastrado com sucesso'))
            return shortcuts.redirect(urlresolvers.reverse('webradius:pool_detail', args=(pool.id,)))            
 
        return shortcuts.render(request, self.template_name, {'form': form})
    
class PoolDeleteView(customviews.RestrictedView):
    model = models.Poolinfo
    perm_name = 'delete'

    def get(self, request, *args, **kwargs):
        pool = shortcuts.get_object_or_404(self.model, pk=self.kwargs.get('pk'))
        
        if pool.pool_name.startswith(models.Poolinfo.get_static_prefix()):
            return shortcuts.redirect(urlresolvers.reverse('handler403'))
        
        if pool.count_machines_on_pool() >= 1:
            api.error(self.request, _(u"O Pool %s não pode ser deletado pois ele contem máquinas associadas" % pool.pool_name))
            return shortcuts.redirect(urlresolvers.reverse('webradius:pool_detail', args=(pool.id,)))
        name = pool.pool_name
        pool.delete()
        
        api.success(self.request, _(u"Pool '%s' removido com sucesso" % name))
        models.Log(user=self.request.user, msg=_(u"Pool '%s' removido" % pool.pool_name)).save()
        
        return shortcuts.redirect(urlresolvers.reverse('webradius:pool_list'))
    
class PoolEditView(customviews.RestrictedView):
    model = models.Poolinfo
    template_name = 'webradius/pool_edit.html'
    perm_name = 'change'

    def get(self, request, *args, **kwargs):
        pool = shortcuts.get_object_or_404(self.model, pk=self.kwargs.get('pk')) 
        
        if pool.pool_name.startswith(models.Poolinfo.get_static_prefix()):
            return shortcuts.redirect(urlresolvers.reverse('handler403'))
        
        form = poolinfo.PoolEditForm(instance=pool)
        return shortcuts.render(request, self.template_name, {'form': form,
                                                              'object': pool})

    def post(self, request, *args, **kwargs):
        pool_edit = shortcuts.get_object_or_404(self.model, pk=self.kwargs.get('pk'))
        
        if pool_edit.pool_name.startswith(models.Poolinfo.get_static_prefix()):
            return shortcuts.redirect(urlresolvers.reverse('handler403'))
        
        form = poolinfo.PoolEditForm(request.POST, instance=pool_edit)

        if form.is_valid():
            if not form.has_changed():
                api.info(request, _(u'Nenhuma alteração efetuada'))
                form.reset_errors()
                return shortcuts.render(request, self.template_name, {'form': form,
                                                                      'object': pool_edit})
            
            pool = form.save()
            
            api.success(request, _(u'Pool alterado com sucesso'))
            models.Log(user=request.user, msg=_(u"Pool '%s' alterado" % pool_edit.pool_name)).save()
            return shortcuts.redirect(urlresolvers.reverse('webradius:pool_detail', args=(pool.id,))) 
        return shortcuts.render(request, self.template_name, {'form': form,
                                                              'object': pool_edit})

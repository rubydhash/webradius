# -*- coding: utf-8 -*-

from webradius.forms import nas 
from webradius import models
from django import shortcuts
from django.views import generic
from lib.djangoutils  import customviews
from django.contrib.messages import api
from django.core import urlresolvers
from django.utils.translation import ugettext as _

class NASView(generic.View):
    model = models.Nas
    template_name = 'webradius/nas_list.html'
    
    def get(self, request, *args, **kwargs):
        form = nas.NASSearchForm()
        return shortcuts.render(request, self.template_name, {'form': form, 'object_list': []})
    
    def post(self, request, *args, **kwargs):
        object_list = []
        form = nas.NASSearchForm(request.POST)
                
        if form.is_valid():
            fdata = form.cleaned_data
            
            object_list = self.model.objects.all()
            
            if fdata.get('shortname'):
                object_list = object_list.filter(shortname__icontains=fdata.get('shortname'))
                
            if fdata.get('nasname'):
                object_list = object_list.filter(nasname__icontains=fdata.get('nasname'))
                
            if fdata.get('description'):
                object_list = object_list.filter(description__icontains=fdata.get('description'))
                
            if fdata.get('type'):
                object_list = object_list.filter(type__icontains=fdata.get('type'))            
            
        return shortcuts.render(request, self.template_name, {'form': form, 'object_list': object_list})
    
class NASDetailView(generic.View):
    model = models.Nas
    template_name = 'webradius/nas_detail.html'
    
    def get(self, request, *args, **kwargs):
        nas = shortcuts.get_object_or_404(self.model, pk=self.kwargs.get('pk'))
        return shortcuts.render(request, self.template_name, {'object': nas})
    
class NASAddView(customviews.RestrictedView):
    model = models.Nas
    template_name = 'webradius/nas_add.html'
    perm_name = 'add'
    
    def get(self, request, *args, **kwargs):
        form = nas.NASAddForm()
        return shortcuts.render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = nas.NASAddForm(request.POST)
        
        if form.is_valid():
            if not form._errors:
                form.save()                
                models.Log(user=request.user, msg=_(u"NAS '%s' cadastrado" % form.cleaned_data['nasname'])).save()
                api.success(request, _(u'NAS cadastrado com sucesso'))
                return shortcuts.redirect(urlresolvers.reverse('webradius:nas_list'))
 
        return shortcuts.render(request, self.template_name, {'form': form})
    
class NASDeleteView(customviews.RestrictedView):
    model = models.Nas
    perm_name = 'delete'

    def get(self, request, *args, **kwargs):
        nas = shortcuts.get_object_or_404(self.model, pk=self.kwargs.get('pk'))
        
        name = nas.nasname
        nas.delete()
        
        api.success(self.request, _(u"NAS '%s' removido com sucesso" % name))
        models.Log(user=self.request.user, msg=_(u"NAS '%s' removido" % name)).save()
        
        return shortcuts.redirect(urlresolvers.reverse('webradius:nas_list'))
    
class NASEditView(customviews.RestrictedView):
    model = models.Nas
    template_name = 'webradius/nas_edit.html'
    perm_name = 'change'

    def get(self, request, *args, **kwargs):
        nasobj = shortcuts.get_object_or_404(self.model, pk=self.kwargs.get('pk'))
        form = nas.NASEditForm(instance=nasobj)
        return shortcuts.render(request, self.template_name, {'form': form,
                                                              'object': nasobj})

    def post(self, request, *args, **kwargs):
        nas_edit = shortcuts.get_object_or_404(self.model, pk=self.kwargs.get('pk'))
        form = nas.NASEditForm(request.POST, instance=nas_edit)

        if form.is_valid():            
            if not form.has_changed():
                api.info(request, _(u'Nenhuma alteração efetuada'))
                return shortcuts.render(request, self.template_name, {'form': form,
                                                            'object': nas_edit})
            
            if not form._errors:
                form.save()
                api.success(request, _(u'NAS alterado com sucesso'))
                models.Log(user=request.user, msg=_(u"NAS '%s' alterado" % nas_edit.nasname)).save()
                return shortcuts.redirect(urlresolvers.reverse('webradius:nas_list')) 
        return shortcuts.render(request, self.template_name, {'form': form,
                                                    'object': nas_edit})

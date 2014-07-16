# -*- coding: utf-8 -*-

from django.views import generic
from django.conf import settings
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.shortcuts import redirect, render, get_object_or_404, render_to_response
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect, HttpResponse
import json

#
#  Restricted View 
#

class SimpleView(generic.View):
    template_name = None
    context_view = {}
    context_view_l = []
    
    def get_render(self,request,*args,**kwargs):
        for cl in self.context_view_l:
            self.context_view.update({cl: getattr(self, cl)})
        return render(request,self.template_name,self.context_view)
        
    
class RestrictedView(SimpleView):
    perm_name = None
    model = None
    restricted_post_only = None
    
    def dispatch(self, request, *args, **kwargs):
        # Format perm_name
        if self.model:
            self.perm_name = '%s.%s_%s' % (self.model._meta.app_label, self.perm_name, self.model._meta.module_name)
            
        # Restricted POST only
        if self.restricted_post_only:
            if request.method == 'POST':
                @permission_required(self.perm_name,login_url=settings.URL403)
                def wrapper(request, *args, **kwargs):
                    return super(RestrictedView, self).dispatch(request, *args, **kwargs)
                return wrapper(request, *args, **kwargs)
            else:
                def wrapper(request, *args, **kwargs):
                    return super(RestrictedView, self).dispatch(request, *args, **kwargs)
                return wrapper(request, *args, **kwargs)
        else:
            # Restricted ALL 
            @permission_required(self.perm_name,login_url=settings.URL403)
            def wrapper(request, *args, **kwargs):
                return super(RestrictedView, self).dispatch(request, *args, **kwargs)
            return wrapper(request, *args, **kwargs)

class SuperuserResctrictedView(SimpleView):
    def superuser_check(self, user):
        return user.is_superuser
    
    def dispatch(self, request, *args, **kwargs): 
        @user_passes_test(self.superuser_check, login_url=settings.URL403)
        def wrapper(request, *args, **kwargs):
            return super(SuperuserResctrictedView, self).dispatch(request, *args, **kwargs)
        return wrapper(request, *args, **kwargs)
            

#
#  Restricted Generic 
#        

class RestrictedDetailView(generic.DetailView):
    def dispatch(self, request, *args, **kwargs):
        @permission_required('%s.list_%s' % (self.model._meta.app_label, self.model._meta.module_name),login_url=settings.URL403)
        def wrapper(request, *args, **kwargs):
            return super(RestrictedDetailView, self).dispatch(request, *args, **kwargs)
        return wrapper(request, *args, **kwargs)

        
class RestrictedListView(generic.ListView):
    def dispatch(self, request, *args, **kwargs):
        @permission_required('%s.list_%s' % (self.model._meta.app_label, self.model._meta.module_name),login_url=settings.URL403)
        def wrapper(request, *args, **kwargs):
            return super(RestrictedListView, self).dispatch(request, *args, **kwargs)
        return wrapper(request, *args, **kwargs)

class RestrictedListReportView(generic.ListView):
    def dispatch(self, request, *args, **kwargs):
        @permission_required('%s.report_%s' % (self.model._meta.app_label, self.model._meta.module_name),login_url=settings.URL403)
        def wrapper(request, *args, **kwargs):
            return super(RestrictedListReportView, self).dispatch(request, *args, **kwargs)
        return wrapper(request, *args, **kwargs)


class RestrictedCreateView(generic.CreateView):   
    msg_form_success = _(u'Cadastro realizado com sucesso')
    urldo = None
    title_name = None
    title_name_plural = None
    url_name = None
         
    def get_success_url(self):
        return self.success_url or reverse(self.url_name)
    
    def form_save_action(self,*args,**kwargs):
        pass
        
    def form_valid(self, form):
        self.object = form.save()
        self.form_save_action()
        messages.success(self.request,self.msg_form_success)
        return super(RestrictedCreateView, self).form_valid(form)
        
    def get_context_data(self, **kwargs):
        context = super(RestrictedCreateView, self).get_context_data(**kwargs)
        if self.urldo: context['urldo'] = reverse(self.urldo)
        if self.url_name: context['urlget'] = self.get_success_url()
        if self.title_name: context['title_name'] = self.title_name
        if self.title_name_plural: context['title_name_plural'] = self.title_name_plural
        
        return context        
        
    def dispatch(self, request, *args, **kwargs):
        @permission_required('%s.add_%s' % (self.model._meta.app_label, self.model._meta.module_name),login_url=settings.URL403)
        def wrapper(request, *args, **kwargs):
            return super(RestrictedCreateView, self).dispatch(request, *args, **kwargs)
        return wrapper(request, *args, **kwargs)


class RestrictedUpdateView(generic.UpdateView):
    
    msg_form_success = _(u'Cadastro alterado com sucesso')
    msg_form_unchanged = _(u'Cadastro não alterado')
    urldo = None
    title_name = None
    title_name_plural = None
    url_name = None
        
    def get_success_url(self):
        return self.success_url or reverse(self.url_name)
    
    def form_save_action(self,*args,**kwargs):
        pass
                    
    def form_valid(self, form):
        if form.has_changed():
            self.object = form.save()
            self.form_save_action(formchange=form.changed_data)
            messages.success(self.request,self.msg_form_success)
        else:
            messages.info(self.request,self.msg_form_unchanged)
        return super(RestrictedUpdateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(RestrictedUpdateView, self).get_context_data(**kwargs)
        if self.urldo: context['urldo'] = reverse(self.urldo, kwargs={'pk': self.object.id})
        if self.url_name: context['urlget'] = self.get_success_url()        
        if self.title_name: context['title_name'] = self.title_name
        if self.title_name_plural: context['title_name_plural'] = self.title_name_plural
        return context
            
    def dispatch(self, request, *args, **kwargs):
        @permission_required('%s.change_%s' % (self.model._meta.app_label, self.model._meta.module_name),login_url=settings.URL403)
        def wrapper(request, *args, **kwargs):
            return super(RestrictedUpdateView, self).dispatch(request, *args, **kwargs)
        return wrapper(request, *args, **kwargs)


class RestrictedDeleteView(generic.DeleteView):
    url_name = None
    msg_success = _(u'Cadastro removido com sucesso')
    
    def get_success_url(self):
        return self.success_url or reverse(self.url_name)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        if self.msg_success:
            messages.success(self.request,self.msg_success)
        return HttpResponseRedirect(self.get_success_url())
                    
    def dispatch(self, request, *args, **kwargs):
        @permission_required('%s.delete_%s' % (self.model._meta.app_label, self.model._meta.module_name),login_url=settings.URL403)
        def wrapper(request, *args, **kwargs):
            return super(RestrictedDeleteView, self).dispatch(request, *args, **kwargs)
        return wrapper(request, *args, **kwargs)
        
    


class RestrictedPostUpdateView(generic.UpdateView):
    msg_form_success = _(u'Cadastro alterado com sucesso')
    msg_form_unchanged = _(u'Cadastro não alterado')
    urldo = None
    title_name = None
    title_name_plural = None
    url_name = None

    def get_success_url(self):
        return self.success_url or reverse(self.url_name)

    def form_save_action(self,*args,**kwargs):
        pass

    def form_valid(self, form):
        if form.has_changed():
            self.object = form.save()
            self.form_save_action(formchange=form.changed_data)
            messages.success(self.request,self.msg_form_success)
        else:
            messages.info(self.request,self.msg_form_unchanged)
        return super(RestrictedPostUpdateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(RestrictedPostUpdateView, self).get_context_data(**kwargs)
        if self.urldo: context['urldo'] = reverse(self.urldo, kwargs={'pk': self.object.id})
        if self.url_name: context['urlget'] = self.get_success_url()        
        if self.title_name: context['title_name'] = self.title_name
        if self.title_name_plural: context['title_name_plural'] = self.title_name_plural
        return context

    def dispatch(self, request, *args, **kwargs):        
        if request.method == 'POST':
            @permission_required('%s.change_%s' % (self.model._meta.app_label, self.model._meta.module_name),login_url=settings.URL403)
            def wrapper(request, *args, **kwargs):
                return super(RestrictedPostUpdateView, self).dispatch(request, *args, **kwargs)
            return wrapper(request, *args, **kwargs)
        else:
            def wrapper(request, *args, **kwargs):
                return super(RestrictedPostUpdateView, self).dispatch(request, *args, **kwargs)
            return wrapper(request, *args, **kwargs)


class RestrictedFormView(generic.FormView):

    def dispatch(self, request, *args, **kwargs):
        @permission_required('%s.list_%s' % (self.model._meta.app_label, self.model._meta.module_name),login_url=settings.URL403)
        def wrapper(request, *args, **kwargs):
            return super(RestrictedFormView, self).dispatch(request, *args, **kwargs)
        return wrapper(request, *args, **kwargs)


#
#  Restricted Generic custom method 
#

class ListFormView(generic.ListView):
    urldo = None
    title_name = None
    title_name_plural = None
    url_name = None
    success_url = None
    
    def get_success_url(self):
        return self.success_url or reverse(self.url_name)
        
    def get_context_data(self, **kwargs):
        context = super(ListFormView, self).get_context_data(**kwargs)
        context['form'] = self.form_class()
        if self.urldo: context['urldo'] = reverse(self.urldo)
        if self.url_name: context['urlget'] = self.get_success_url()        
        if self.title_name: context['title_name'] = self.title_name
        if self.title_name_plural: context['title_name_plural'] = self.title_name_plural
                
        return context
                

class RestrictedListCreateView(RestrictedCreateView):
    
    querysetdef = None
    
    def get_context_data(self, **kwargs):
        context = super(RestrictedListCreateView, self).get_context_data(**kwargs)
        context['object_list'] = self.querysetdef or self.model.objects.all()
        return context        


class RestrictedListUpdateView(RestrictedPostUpdateView):
    
    querysetdef = None
    
    def get_context_data(self, **kwargs):
        context = super(RestrictedListUpdateView, self).get_context_data(**kwargs)
        context['object_list'] = self.querysetdef or self.model.objects.all()
        return context
                


class AutoCompleteView(generic.View):
    model = None
    args = None

    def get(self,request,*args,**kwargs):
        object_list = self.model.objects.filter(self.args)
        result = [ dict(id=l.id,label=l.__unicode__(),value=l.pk) for l in object_list ]
        return HttpResponse(json.dumps(result), mimetype="application/x-javascript")

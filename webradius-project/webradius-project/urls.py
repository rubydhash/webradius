from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse_lazy
from django.views import generic

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    # Sobrescrevendo telas de erro
    url(r'^403/$', generic.TemplateView.as_view(template_name="403.html"), name='handler403'),
    url(r'^404/$', generic.TemplateView.as_view(template_name="404.html"), name='handler404'),
    url(r'^500/$', generic.TemplateView.as_view(template_name="500.html"), name='handler500'),
    # Links para login e logout
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name="sys_login"),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login', name="sys_logout"),
    # Interface admin    
    url(r'^admin/', include(admin.site.urls)),
    # Da um redirect do / para o webradius
    url(r'^$', generic.RedirectView.as_view(url=reverse_lazy('webradius:index'))),
    # Inclui os links do webradius
    url(r'^webradius/', include('webradius.urls', namespace="webradius")),
)

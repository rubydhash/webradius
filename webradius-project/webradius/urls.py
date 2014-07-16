# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

from webradius.views import index
from webradius.views import macinfo
from webradius.views import poolinfo
from webradius.views import nas
from webradius.views import reports
from webradius.views import migrate

urlpatterns = patterns(
    '',
    # Index
    url(r'^$', index.IndexView.as_view(), name='index'),
    
    # Telas de pool
    url(r'^pool/$', poolinfo.PoolsView.as_view(), name='pool_list'),
    url(r'^pool/add$', poolinfo.PoolAddView.as_view(), name='pool_add'),
    url(r'^pool/(?P<pk>\d+)/$', poolinfo.PoolDetailView.as_view(), name='pool_detail'),
    url(r'^pool/byname/(?P<name>\w{1,55})/$', poolinfo.PoolDetailByNameView.as_view(), name='pool_detail_by_name'),
    url(r'^pool/delete/(?P<pk>\d+)/$', poolinfo.PoolDeleteView.as_view(), name='pool_delete'),
    url(r'^pool/edit/(?P<pk>\d+)/$', poolinfo.PoolEditView.as_view(), name='pool_edit'),

    # Telas de MAC
    url(r'^machine/$', macinfo.MachinesView.as_view(), name='mac_list'),
    url(r'^machine/add$', macinfo.MachineAddView.as_view(), name='mac_add'),
    url(r'^machine/add/(?P<mac>.{1,61})/$', macinfo.MachineAddView.as_view(), name='mac_add2'),
    url(r'^machine/addforce$', macinfo.MachineAddView.as_view(), name='mac_add_force'),
    url(r'^machine/(?P<pk>\d+)/$', macinfo.MachineDetailView.as_view(), name='mac_detail'),
    url(r'^machine/bymac/(?P<mac>.{1,61})/$', macinfo.MachineDetailByMacView.as_view(), name='mac_detail_by_mac'),
    url(r'^machine/mayadd/(?P<mac>.{1,61})/$', macinfo.MachineMayAddView.as_view(), name='mac_may_add'),
    url(r'^machine/delete/(?P<pk>\d+)/$', macinfo.MachineDeleteView.as_view(), name='mac_delete'),
    url(r'^machine/edit/(?P<pk>\d+)/$', macinfo.MachineEditView.as_view(), name='mac_edit'),
    
    # Telas de NAS
    url(r'^nas/$', nas.NASView.as_view(), name='nas_list'),
    url(r'^nas/add$', nas.NASAddView.as_view(), name='nas_add'),
    url(r'^nas/(?P<pk>\d+)/$', nas.NASDetailView.as_view(), name='nas_detail'),
    url(r'^nas/delete/(?P<pk>\d+)/$', nas.NASDeleteView.as_view(), name='nas_delete'),
    url(r'^nas/edit/(?P<pk>\d+)/$', nas.NASEditView.as_view(), name='nas_edit'),
    
    # Telas de relatórios
    url(r'^reports/$', reports.ReportsView.as_view(), name='reports'),
    url(r'^reports/movedmacs$', reports.ReportsMovedMacsView.as_view(), name='report_movedmacs'),
    url(r'^reports/opensessions$', reports.ReportsOpenSessionsView.as_view(), name='report_opensessions'),
    url(r'^reports/postauth$', reports.ReportsPostAuthView.as_view(), name='report_postauth'),
    url(r'^reports/postauth/sessions/(?P<pk>\d+)/$', reports.ReportsPostAuthSessionsView.as_view(), name='report_postauth_sessions'),
    url(r'^reports/qtdsessions$', reports.ReportsQtdSessionsView.as_view(), name='report_qtdsessions'),
    
    # Migração, depois de migrar desativar essas urls
    #url(r'^migrate/createpools/(?P<filename>\w{1,50})$', migrate.MigrateCreatePools.as_view(), name='mg_pools'),
    #url(r'^migrate/insertstatic/(?P<filename>\w{1,50})$', migrate.MigrateInsertStaticMacs.as_view(), name='mg_insert'),
    #url(r'^migrate/insertstaticover/(?P<filename>\w{1,50})$', migrate.MigrateInsertStaticOverlappedMacs.as_view(), name='mg_insert_over'),
    #url(r'^migrate/dhcpd/(?P<filename>\w{1,50})$', migrate.MigrateDHCPDLease.as_view(), name='mg_dhcpd'),
    url(r'^migrate/generate/$', migrate.MigrateGenerateLeasesFile.as_view(), name='mg_generate'),
)

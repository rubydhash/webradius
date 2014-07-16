# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _
from geraldo import Report, ReportBand, Label, ObjectValue, SystemField, \
    BAND_WIDTH, landscape
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_RIGHT, TA_LEFT

class MacReport(Report):
    title = _(u'Relatório de Máquinas')
    print_if_empty = True
    page_size = landscape(A4)

    class band_begin(ReportBand):
        height = 1 * cm
        elements = []
        borders = {'bottom': True}

    class band_detail(ReportBand):
        height = 0.5 * cm
        default_style = {'fontSize': 8}
        elements = [
            ObjectValue(attribute_name='mac', top=0.1 * cm, left=0.5 * cm, width=10 * cm,
                        get_value=lambda instance: instance.mac[:17],
                        style={'fontName': 'Helvetica-Bold'}),
            ObjectValue(attribute_name='description', top=0.1 * cm, left=4.0 * cm, width=10 * cm,
                        get_value=lambda instance: instance.description[:50],
                        style={'fontName': 'Helvetica-Bold'}),
            ObjectValue(attribute_name='insert_date', top=0.1 * cm, left=15 * cm, width=15 * cm,
                        get_value=lambda instance: instance.insert_date.strftime('%d/%m/%Y %H:%M:%S')),
            ObjectValue(attribute_name='expiry_time', top=0.1 * cm, left=18.5 * cm, width=5 * cm,
                        get_value=lambda instance: (_(u'Não expira') if not instance.expiry_time else instance.expiry_time.strftime('%d/%m/%Y %H:%M:%S'))),
            ObjectValue(attribute_name='static', top=0.1 * cm, left=22 * cm,
                        get_value=lambda instance: (_(u'Sim') if instance.static else _(u'Não'))),
            ObjectValue(attribute_name='ip_or_pool', top=0.1 * cm, left=23.8 * cm,
                        get_value=lambda instance: (instance.static_ip if instance.static else instance.pool.description)),

        ]

        borders = {'left': True, 'right': True, 'top': True}

    class band_page_header(ReportBand):
        height = 2 * cm
        elements = [
            SystemField(expression='%(report_title)s', top=0, left=0, width=BAND_WIDTH,
                        style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_LEFT}),

            Label(text=_(u"Endereço MAC"), top=1.4 * cm, left=0.5 * cm, width=10 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}),
            Label(text=_(u"Descrição"), top=1.4 * cm, left=4.0 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"Data de cadastro"), top=1.4 * cm, left=15 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"Data de expiração"), top=1.4 * cm, left=18.5 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"Estático?"), top=1.4 * cm, left=22 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"IP ou Pool"), top=1.4 * cm, left=23.8 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),

        ]
        borders = {'bottom': True}

    class band_page_footer(ReportBand):
        height = 0.5 * cm
        elements = [
            SystemField(expression='Página %(page_number)d de %(page_count)d', top=0.1 * cm,
                        width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
        ]
        borders = {'top': True}

class PoolReport(Report):
    title = _(u'Relatório de Pools')
    print_if_empty = True
    page_size = landscape(A4)

    class band_begin(ReportBand):
        height = 1 * cm
        elements = []
        borders = {'bottom': True}

    class band_detail(ReportBand):
        height = 0.5 * cm
        default_style = {'fontSize': 8}
        elements = [
            ObjectValue(attribute_name='pool_name', top=0.1 * cm, left=0.1 * cm, width=10 * cm,
                        get_value=lambda instance: instance.pool_name,
                        style={'fontName': 'Helvetica-Bold'}),
            ObjectValue(attribute_name='init_address', top=0.1 * cm, left=6 * cm, width=10 * cm,
                        get_value=lambda instance: instance.init_address,
                        style={'fontName': 'Helvetica-Bold'}),
            ObjectValue(attribute_name='end_address', top=0.1 * cm, left=9 * cm, width=15 * cm,
                        get_value=lambda instance: instance.end_address),
            ObjectValue(attribute_name='mask', top=0.1 * cm, left=12 * cm, width=5 * cm,
                        get_value=lambda instance: instance.mask),
            ObjectValue(attribute_name='router_address', top=0.1 * cm, left=14.5 * cm,
                        get_value=lambda instance: instance.router_address),
            ObjectValue(attribute_name='n_ips', top=0.1 * cm, left=16.3 * cm,
                        get_value=lambda instance: len(instance.range())),
            ObjectValue(attribute_name='n_macs', top=0.1 * cm, left=17.8 * cm,
                        get_value=lambda instance: instance.count_machines_on_pool()),
            ObjectValue(attribute_name='leased_ips', top=0.1 * cm, left=20.2 * cm,
                        get_value=lambda instance: instance.assigned_ips_count()),
            ObjectValue(attribute_name='percent_leased', top=0.1 * cm, left=23 * cm,
                        get_value=lambda instance: instance.assigned_ips_utilization()),
            ObjectValue(attribute_name='VLAN ID', top=0.1 * cm, left=26.2 * cm,
                        get_value=lambda instance: ("" if instance.vlan_id is None else instance.vlan_id)),
        ]

        borders = {'left': True, 'right': True, 'top': True}

    class band_page_header(ReportBand):
        height = 2 * cm
        elements = [
            SystemField(expression='%(report_title)s', top=0, left=0.1, width=BAND_WIDTH,
                        style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_LEFT}),

            Label(text=_(u"Nome"), top=1.4 * cm, left=0 * cm, width=10 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}),
            Label(text=_(u"Endereço Inicial"), top=1.4 * cm, left=6 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"Endereço Final"), top=1.4 * cm, left=9 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"Máscara"), top=1.4 * cm, left=12 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"Roteador"), top=1.4 * cm, left=14.5 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"Nº IPs"), top=1.4 * cm, left=16.3 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"Nº Máquinas"), top=1.4 * cm, left=17.8 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"IPs concedidos"), top=1.4 * cm, left=20.2 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"% concedidos"), top=1.4 * cm, left=23 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),
            Label(text=_(u"VLAN ID"), top=1.4 * cm, left=26.2 * cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 10}, width=5 * cm),

        ]
        borders = {'bottom': True}

    class band_page_footer(ReportBand):
        height = 0.5 * cm
        elements = [
            SystemField(expression='Página %(page_number)d de %(page_count)d', top=0.1 * cm,
                        width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
        ]
        borders = {'top': True}

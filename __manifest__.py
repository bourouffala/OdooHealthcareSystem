# -*- coding: utf-8 -*-
{
   'name': "Prestation patient",
    'version': '10.0.1.0.0',
    'summary': """Gestion des Prestation des patients.""",
    'description': """Gestion des Prestation des patients.""",
    'author': "BOUROUFFALA Mohamed El Amine",
    'maintainer': 'SIBIC',
    'company': "SIBIC",
    'website': "https://www.sibic.dz",
    'category': 'Healthcare',
    'depends': ['sale','base', 'mail', 'account','report','web','web_tour'],
    'data': [
        'security/lab_users.xml',
        'security/ir.model.access.csv',
        'views/prestataion_sequence.xml',
        'views/prestataion_sale.xml',
        'report/reports.xml',
         ],
    'images': [
    'static/description/banner.jpg',
    'static/description/icon.png',

    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    
}

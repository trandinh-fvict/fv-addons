# odoo_gemini_connector/__manifest__.py
# -*- coding: utf-8 -*-
{
    'name': 'Odoo 18 Gemini Direct Connector',
    'version': '18.0.1.0.0',
    'summary': 'Đưa Gemini AI vào thay thế cho olg api mặc định của Odoo',
    'description': """
    """,
    'author': 'FV2573',
    'category': 'Extra Tools',
    'license': 'LGPL-3',
    'depends': ['html_editor'], 
    'data': [],
    'assets': {
        'web.assets_backend': [
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}

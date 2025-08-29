# -*- coding: utf-8 -*-
{
    'name': 'TPM Score Summary',
    'version': '18.0.1.0.0',
    'category': 'Operations',
    'summary': '',
    'description': """    """,
    'author': 'FV2573',
    'website': 'https://trandinh-fvict.github.io/',
    'depends': ['base', 'web', 'mail'],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/sequences.xml',
        # 'data/eval_questions.xml',

        # Views (load views with actions first, then menus)
        'views/teamconf_views.xml',
        'views/evaluation_views.xml',
        'views/templates.xml',
        'views/menus.xml',

        # Reports
        # 'report/report_templates.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_frontend': [
            '/tpm_score_summary/static/src/css/evaluation_matrix.css',
            '/tpm_score_summary/static/src/js/evaluation_matrix.js',
        ],
    },
}

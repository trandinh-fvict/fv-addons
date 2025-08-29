{
    'name': 'Survey User Input PDF',
    'summary': 'Print survey.user_input results to PDF with customizable template.',
    'version': '18.0.1.0.0',
    'category': 'Survey',
    'author': 'FV2573',
    'website': 'https://trandinh-fvict.github.io',
    'depends': ['survey'],
    'data': [
        'report/survey_user_input_report_template.xml',
        'report/survey_user_input_report.xml',
        'views/survey_user_input_view.xml'
    ],
    'assets': {
        'web.report_assets_common': [
            '/survey_user_input_pdf/static/css/report.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3'
}

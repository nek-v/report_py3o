# -*- coding: utf-8 -*-
{
    'name': 'Py3o Report Engine',
    'version': '11.0.1.0.2',
    'category': 'Reporting',
    "sequence": 1,
    'summary': 'Reporting engine based on Libreoffice',
    'description': 'Reporting engine based on Libreoffice',
    'author': 'Vu Luan (doanvuluan23@gmail.com), Odoo Community Association (OCA)',
    'depends': ['report_pdf_preview'],
    'external_dependencies': {
        'python': [
            'py3o.template',
            'py3o.formats',
            'PyPDF2',
            'openpyxl'
        ]
    },
    'data': [
        'security/ir.model.access.csv',
        'views/ir_actions_report_view.xml',
        'views/py3o_template_view.xml',
        'views/template.xml',
        'demo/report_py3o.xml',
    ],
}

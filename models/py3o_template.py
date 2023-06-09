# -*- coding: utf-8 -*-
from odoo import fields, models

class Py3oTemplate(models.Model):
    _name = 'py3o.template'

    name = fields.Char(required=True)
    py3o_template_data = fields.Binary("LibreOffice Template", required=True)
    filetype = fields.Selection(
        selection=[
            ('odt', "ODF Text Document (odt)"),
            ('ods', "ODF Spreadsheet (ods)"),
        ],
        string="LibreOffice Template File Type",
        required=True,
        default='odt')

# -*- coding: utf-8 -*-

from odoo import api, fields, models

class Users(models.Model):
    _inherit = 'res.users'

    @api.multi
    def _py3o_get_images(self):
        results = []
        results.append({
            'content': self.env.user.company_id.logo,
            'column': 'B1',
            'width': None,
            'height': None,
            'filetype': None  # PNG, JPEG
        })
        results.append({
            'content': self.image,
            'column': 'B5',
            'width': None,
            'height': None,
            'filetype': None
        })
        return results

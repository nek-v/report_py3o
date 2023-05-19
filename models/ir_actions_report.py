# -*- coding: utf-8 -*-

import mimetypes
from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    py3o_filetype = fields.Selection(selection=[('odt', 'docx'), ('ods', 'xlsx')], string='Output Format')
    is_doc = fields.Boolean(string='Download Doc (odt -> doc)')
    report_type = fields.Selection(selection_add=[('py3o', 'Py3o')])
    py3o_template_fallback = fields.Char(string='Fallback', size=128)
    module = fields.Char(string='Module')
    py3o_pdf = fields.Boolean(string='Py3o PDF', default=False, help=_('if set to true, the action will convert .docx or .xlsx to pdf'))
    py3o_multi_in_one = fields.Boolean(string='Multiple Records in a Single Report', default=False)
    py3o_template_id = fields.Many2one('py3o.template', "Template")

    @api.model
    def get_from_report_name(self, report_name, report_type):
        return self.search([('report_name', '=', report_name), ('report_type', '=', report_type)])

    @api.multi
    def get_report_download_filename(self, res_ids):
        self.ensure_one()
        if self.print_report_name and not len(res_ids) > 1:
            obj = self.env[self.model].browse(res_ids)
            name = safe_eval(self.print_report_name, {'object': obj})
            if '.ods' in name:
                return name.split('.ods')[0]
            if '.odt' in name:
                return name.split('.odt')[0]
        return '%s' % (self.name)

    @api.noguess
    def report_action(self, docids, data=None, config=True):
        result = super(IrActionsReport, self).report_action(docids, data, config)
        if self.report_type == 'py3o' and self.py3o_pdf and self.py3o_filetype == 'odt':
            result['py3_preview'] = True
            result['minetype'] = self.get_minetype()
        return result
    
    def get_minetype(self):
        if self.py3o_pdf and self.py3o_filetype == 'odt':
            minetype = mimetypes.guess_type('x.pdf')[0]
        elif self.py3o_filetype == 'odt' and self.is_doc:
            minetype = mimetypes.guess_type('x.doc')[0]
        elif self.py3o_filetype == 'odt':
            minetype = mimetypes.guess_type('x.docx')[0]
        elif self.py3o_filetype == 'ods':
            minetype = mimetypes.guess_type('x.xlsx')[0]
        return minetype
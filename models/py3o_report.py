# -*- coding: utf-8 -*-

import os
import html
import pytz
import tempfile
import logging
import openpyxl
import base64
import pkg_resources
import subprocess
from decimal import Decimal
from genshi.core import Markup
from io import BytesIO
from contextlib import closing
from base64 import b64decode
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime
from py3o import formats
from py3o.formats import Formats, UnkownFormatException
from py3o.template import Template
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import image_resize_image
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang, format_date, find_in_path
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.translate import translate
from .utils import get_digits

logger = logging.getLogger(__name__)

class Py3oReport(models.TransientModel):
    _name = 'py3o.report'
    _description = 'Report Py30'

    ir_actions_report_id = fields.Many2one('ir.actions.report', required=True, string='ir.actions.report')

    @api.multi
    def _get_template(self, report_xml):
        flbk_filename = pkg_resources.resource_filename(
            'odoo.addons.%s' % report_xml.module,
            report_xml.py3o_template_fallback,
        )
        if self._is_valid_template_filename(flbk_filename):
            with open(flbk_filename, 'rb') as tmpl:
                return tmpl.read()
        return None

    @api.multi
    def _create_single_report(self, model_instance):
        self.ensure_one()
        report_xml = self.ir_actions_report_id
        tmpl_data = None
        result_fd, result_path = tempfile.mkstemp(suffix='.' + report_xml.py3o_filetype, prefix='p3o-report-tmp-')
        if report_xml.py3o_template_id.py3o_template_data:
            tmpl_data = b64decode(report_xml.py3o_template_id.py3o_template_data)
        else:
            tmpl_data = self._get_template(report_xml)
        if tmpl_data is None:
            raise ValidationError(_('Template or Fallback did not found. ({})'.format(report_xml.name)))
        in_stream = BytesIO(tmpl_data)
        with closing(os.fdopen(result_fd, 'r+b')) as out_stream:
            template = Template(in_stream, out_stream, escape_false=True)
            data = self.get_report_data(model_instance)
            template.render(data)
        self._convert_single_report_cmd(result_path, self.get_format_type())
        self._cleanup_tempfiles([result_path])
        return result_path.split('.')[0] + '.' + self.get_format_type()

    @api.multi
    def create_report(self, res_ids):
        model_instances = self.env[self.ir_actions_report_id.model].browse(res_ids)
        reports_path = []
        if len(res_ids) > 1 and self.ir_actions_report_id.py3o_multi_in_one:
            reports_path.append(self._create_single_report(model_instances))
        else:
            for record in model_instances:
                reports_path.append(self._create_single_report(record))
        result_path, converter_type = self._merge_results(reports_path, model_instances)
        with open(result_path, 'r+b') as fd:
            res = fd.read()
        return res, converter_type

    def get_format_type(self):
        format_type = 'xlsx'
        if self.ir_actions_report_id.py3o_pdf:
            format_type = 'pdf'
        elif self.ir_actions_report_id.py3o_filetype == 'odt' and not self.ir_actions_report_id.is_doc:
            format_type = 'docx'
        elif self.ir_actions_report_id.py3o_filetype == 'odt' and self.ir_actions_report_id.is_doc:
            format_type = 'doc'
        return format_type

    @api.multi
    def _is_valid_template_filename(self, filename):
        if filename and os.path.isfile(filename):
            fname, ext = os.path.splitext(filename)
            ext = ext.replace('.', '')
            try:
                fformat = Formats().get_format(ext)
                if fformat and fformat.native:
                    return True
            except UnkownFormatException:
                logger.warning("Invalid py3o template %s", filename, exc_info=1)
        logger.warning('%s is not a valid Py3o template filename', filename)
        return False

    @api.model
    def _cleanup_tempfiles(self, temporary_files):
        for file in temporary_files:
            try:
                os.unlink(file)
            except (OSError, IOError):
                logger.error('Error when trying to remove file %s' % file)

    @api.multi
    def _zip_results(self, reports_path, model_instances):
        self.ensure_one()
        report_xml = self.ir_actions_report_id
        result_path = tempfile.mktemp(suffix='zip', prefix='py3o-zip-result-')
        with ZipFile(result_path, 'w', ZIP_DEFLATED) as zf:
            cpt = 0
            for report in reports_path:
                if report_xml.py3o_filetype == 'ods':
                    self.insert_images(report, model_instances.ids[cpt], model=report_xml.model)
                zfname_prefix = self.ir_actions_report_id.get_report_download_filename([model_instances.ids[cpt]])
                fname = "%s_%d.%s" % (zfname_prefix, cpt, report.split('.')[-1])
                zf.write(report, fname)
                cpt += 1
        self._cleanup_tempfiles(reports_path)
        return result_path

    @api.multi
    def _merge_results(self, reports_path, model_instances):
        self.ensure_one()
        report_xml = self.ir_actions_report_id
        if len(reports_path) == 1 and len(model_instances) == 1:
            if report_xml.py3o_filetype == 'ods':
                self.insert_images(reports_path[0], model_instances)
            return reports_path[0], '.' + self.get_format_type()
        return self._zip_results(reports_path, model_instances), '.zip'

    @api.multi
    def get_report_data(self, model_instance):
        self.ensure_one()
        return dict(
            objects=model_instance,
            company=self.env.user.company_id,
            user=self.env.user,
            b64decode=b64decode,
            env=self.env,
            o_formatLang=self._format_lang,
            o_format_date=self._format_date,
            format_ddmmyyy=self._format_ddmmyyy,
            contact_address=self._contact_address,
            today=fields.Date.context_today(self),
            barcode=self.ir_actions_report_id.barcode,
            gettext=self._translate_text,
            format_multiline_value=self._format_multiline_value,
            company_name=self._company_name,
        )

    @api.multi
    def insert_images(self, path, model_instance, model=None):
        if model:
            model_instance = self.env[model].browse(model_instance)
        if hasattr(model_instance, '_py3o_get_images'):
            results = model_instance._py3o_get_images()
            image_path = []
            for res in results:
                data = base64.decodestring(image_resize_image(base64_source=res['content'], size=(res['width'] or None, res['height'] or None), filetype=res['filetype']))
                mimetype = guess_mimetype(data).split('image/')[1]
                result_fd, result_path = tempfile.mkstemp(suffix='.' + mimetype, prefix='py3-logo-')
                tmpfile = os.fdopen(result_fd, 'w+b')
                tmpfile.write(data)
                tmpfile.close()
                workbook = openpyxl.load_workbook(path)
                worksheet = workbook.active
                worksheet.add_image(openpyxl.drawing.image.Image(result_path), res['column'])
                workbook.save(path)
                image_path.append(result_path)
            self._cleanup_tempfiles(image_path)

    def _format_ddmmyyy(self, date, date_time=False):
        if not date:
            return False
        timezone = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
        if date_time:
            date = timezone.localize(datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(timezone)
        else:
            date = timezone.localize(datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)).astimezone(timezone)
        if self.env.user.lang == 'vi_VN':
            return 'Ngày {} tháng {} năm {}'.format(date.strftime('%d'), date.strftime('%m'), date.strftime('%Y'))
        else:
            return 'Day {} month {} year {}'.format(date.strftime('%d'), date.strftime('%m'), date.strftime('%Y'))

    def _translate_text(self, source):
        if source:
            IrTranslation = self.env['ir.translation']
            lang = self._context.get('lang')
            name = 'ir.actions.report'
            domain = [
                ('res_id', '=', self.ir_actions_report_id.id),
                ('type', '=', 'report'),
                ('src', '=', source),
                ('lang', '=', lang)
            ]
            translation = IrTranslation.search(domain)
            if not translation:
                vals = {
                    'src': source,
                    'type': 'report',
                    'lang': lang,
                    'res_id': self.ir_actions_report_id.id,
                    'name': name
                }
                IrTranslation.create(vals)
            return translate(self.env.cr, name, 'report', lang, source) or source

    def _convert_single_report_cmd(self, result_path, format_type, library='soffice'):
        command = [
            find_in_path(library), '--headless', '--convert-to', format_type, result_path
        ]
        subprocess.check_output(command, cwd=os.path.dirname(result_path))

    def _contact_address(self, partner_id, upper=False, keep_country=False):
        address = partner_id.contact_address
        if not keep_country and partner_id.country_id:
            address = ','.join(address.split(',')[:-1])
        if upper:
            address = address.upper()
        return '{}'.format(address)

    def _format_multiline_value(self, value):
        if value:
            return Markup(html.escape(value).replace('\n', '<text:line-break/>').replace('\t', '<text:s/><text:s/><text:s/><text:s/>'))
        return ""

    def _format_date(self, value, lang_code=False, date_format=False):
        return format_date(self.env, value, lang_code=lang_code, date_format=date_format)

    def _format_lang(self, value, lang_code=False, digits=None, grouping=True, 
        monetary=False, dp=False, currency_obj=False, no_break_space=True):
        env = self.env
        if lang_code:
            context = dict(env.context, lang=lang_code)
            env = env(context=context)
        if digits is None:
            digits = get_digits(value)
        formatted_value = formatLang(env, value, digits=digits, grouping=grouping, monetary=monetary, dp=dp, currency_obj=currency_obj)
        if currency_obj and currency_obj.symbol and no_break_space:
            parts = []
            if currency_obj.position == 'after':
                parts = formatted_value.rsplit(" ", 1)
            elif currency_obj and currency_obj.position == 'before':
                parts = formatted_value.split(" ", 1)
            if parts:
                formatted_value = "\N{NO-BREAK SPACE}".join(parts)
        return formatted_value

    def _company_name(self, objects):
        return '{}'.format(objects.company_id.name.upper())

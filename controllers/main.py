# -*- coding: utf-8 -*-

import json
import mimetypes
from werkzeug import exceptions
from odoo.http import route, request, content_disposition, serialize_exception as _serialize_exception
from odoo.addons.web.controllers.main import ReportController
from odoo.tools import html_escape
import os
import tempfile
from contextlib import closing

class ReportController(ReportController):

    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter != 'py3o':
            return super(ReportController, self).report_routes(reportname=reportname, docids=docids, converter=converter, **data)
        ir_report = request.env['ir.actions.report']
        action_py3o_report = ir_report.get_from_report_name(reportname, converter)
        if not action_py3o_report or not docids:
            raise exceptions.HTTPException(description='Odoo Server Error')
        docids = [int(i) for i in docids.split(',')]
        py3o_report = request.env['py3o.report'].create({'ir_actions_report_id': action_py3o_report.id})
        res, converter_type = py3o_report.create_report(docids)
        content_type = mimetypes.guess_type('x' + converter_type)[0]
        file_name = action_py3o_report.get_report_download_filename(docids)
        http_headers = [
            ('Content-Type', content_type),
            ('Content-Length', len(res)),
            ('Content-Disposition', content_disposition(file_name + converter_type))
        ]
        http_headers[2]= ('Content-Disposition', http_headers[2][1].replace('attachment', 'inline'))
        if data.get('token', False):
            return request.make_response(res, headers=http_headers, cookies={'fileToken': data.get('token')})
        return request.make_response(res, headers=http_headers)

    @route()
    def report_download(self, data, token, **kw):
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        if type != 'py3o':
            return super(ReportController, self).report_download(data, token)
        try:
            reportname = url.split('/report/py3o/')[1].split('?')[0]
            docids = None
            if '/' in reportname:
                reportname, docids = reportname.split('/')
            if not docids:
                raise exceptions.HTTPException(description='Odoo Server Error')
            return self.report_routes(reportname=reportname, docids=docids, converter=type, **{'token': token})
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))

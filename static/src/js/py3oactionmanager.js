odoo.define('report_py3o.py3oactionmanager', function (require) {

var ActionManager = require('web.ActionManager');
var core = require('web.core');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');
var Session = require('web.Session');
var PreviewDialog = require('report_pdf_preview.PreviewDialog');
var _t = core._t;

Session.include({
    get_file: function(options) {
        var self = this;
        var token = new Date().getTime();
        options.session = this;
        var params = _.extend({}, options.data || {}, {token: token});
        var url = options.session.url(options.url, params);
        if (options.hasOwnProperty('action') && options.action && options.action.hasOwnProperty('py3_preview') && options.action['py3_preview'] == true){
            if (options.complete) { options.complete(); }
            var dialog=PreviewDialog.createPreviewDialog(self, url, options.action['minetype'], false);
                $.when(dialog,dialog._opened).then(function (dialog) {
                    dialog.$modal.find('.preview-download').hide();
                })
            return true;
        } else {
        return self._super(options);
        }
    }
});

var trigger_download = function (session, response, c, action, options) {
    return session.get_file({
        url: '/report/download',
        data: {data: JSON.stringify(response)},
        complete: framework.unblockUI,
        error: c.rpc_error.bind(c),
        success: function () {
            if (action && options && !action.dialog) {
                options.on_close();
            }
        },
        action: action
    });
};

ActionManager.include({
    ir_actions_report: function(action, options) {
        var self = this;
        framework.blockUI();
        action = _.clone(action);
        _t =  core._t;

        // Py3o reports
        if ('report_type' in action && action.report_type == 'py3o' ) {
            var report_url = '/report/py3o/' + action.report_name;
            // generic report: no query string
            // particular: query string of action.data.form and context
            if (!('data' in action) || !(action.data)) {
                if ('active_ids' in action.context) {
                    report_url += "/" + action.context.active_ids.join(',');
                }
            } else {
                report_url += "&options=" + encodeURIComponent(JSON.stringify(action.data));
                report_url += "&context=" + encodeURIComponent(JSON.stringify(action.context));
            }

            var response = new Array();
            response[0] = report_url;
            response[1] = action.report_type;
            var c = crash_manager;
            return trigger_download(self.getSession(), response, c, action, options);
        } else {
            return self._super(action, options);
        }
    }
});

});

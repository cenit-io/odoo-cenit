# -*- coding: utf-8 -*-

import logging
import inflect

from odoo import http
from odoo import SUPERUSER_ID
from odoo.http import request
from openerp.modules.registry import Registry


_logger = logging.getLogger(__name__)


class WebhookController(http.Controller):

    @http.route(['/cenit/<string:action>',
                 '/cenit/<string:action>/<string:root>'],
                type='json', auth='none', methods=['POST'])
    def cenit_post(self, action, root=None):
        status_code = 400
        environ = request.httprequest.headers.environ.copy()

        key = environ.get('HTTP_X_USER_ACCESS_KEY', False)
        token = environ.get('HTTP_X_USER_ACCESS_TOKEN', False)
        db_name = environ.get('HTTP_TENANT_DB', False)

        if not db_name:
            host = environ.get('HTTP_HOST', "")
            db_name = host.replace(".", "_").split(":")[0]

        # if db_name in http.db_list():
        registry = RegistryManager.get(db_name)
        with registry.cursor() as cr:
            connection_model = registry['cenit.connection']
            domain = [('key', '=', key), ('token', '=', token)]
            _logger.info(
                "Searching for a 'cenit.connection' with key '%s' and "
                "matching token", key)
            rc = connection_model.search(cr, SUPERUSER_ID, domain)
            _logger.info("Candidate connections: %s", rc)
            if rc:
                p = inflect.engine()
                flow_model = registry['cenit.flow']
                context = {'sender': 'client', 'action': action}

                if root is None:
                    for root, data in request.jsonrequest.items():
                        root = p.singular_noun(root) or root
                        rc = flow_model.receive(cr, SUPERUSER_ID, root,
                                                data, context)
                        if rc:
                            status_code = 200
                else:
                    root = p.singular_noun(root) or root
                    rc = flow_model.receive(cr, SUPERUSER_ID, root,
                                            request.jsonrequest, context)
                    if rc:
                        status_code = 200
            else:
                status_code = 404

        return {'status': status_code}

    @http.route('/cenit/<string:root>',
        type='json', auth='none', methods=['GET'])
    def cenit_get(self, root):
        return {'status': 403}

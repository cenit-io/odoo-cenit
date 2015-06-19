# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2014 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import requests
import simplejson
import logging

from openerp import models, fields, api, exceptions
from openerp.addons.web.http import request


_logger = logging.getLogger(__name__)

API_PATH = "/api/v1"


class CenitApi(models.AbstractModel):

    _name = "cenit.api"

    @api.one
    def _get_values(self):
        vals = self.read([])[0]
        vals.pop('create_uid')
        vals.pop('create_date')
        vals.pop('__last_update')
        vals.pop('write_uid')
        vals.pop('write_date')
        vals.pop('display_name')
        vals.pop('id')

        return vals

    @api.one
    def _calculate_update(self, values):
        update = {}
        for k,v in values.items():
            if k == "%s" % (self.cenit_models):
                update = {
                    'cenitID': v[0]['id']
                }

        return update

    @api.one
    def push_to_cenit(self):
        path = "/setup/push"
        values = {
            self.cenit_model: self._get_values()
        }

        rc = False
        #~ try:
        rc = self.post(path, values)

        if rc.get('success', False):
            update = self._calculate_update(rc['success'])[0]
            rc = self.with_context(local=True).write(update)
        else:
            _logger.error (rc.get('errors'))
            return False
        #~ except Warning as e:
            #~ _logger.exception(e)

        return rc

    @api.one
    def drop_from_cenit (self):
        path = "/setup/%s/%s" % (self.cenit_model, self.cenitID)

        rc = False

        #~ try:
        rc = self.delete (path)
        #~ except Warning as e:
            #~ _logger.exception (e)

        return rc

    @api.model
    def post (self, path, vals):
        config = self.instance()
        payload = simplejson.dumps(vals)

        _logger.info("\n\nPosting payload: %s\n", payload)

        r = requests.post(
            config.get('cenit_url') + API_PATH + path,
            data = payload,
            headers = self.headers(config)
        )
        if 200 <= r.status_code < 300:
            return simplejson.loads(r.content)

        error = simplejson.loads(r.content)
        if 400 <= error.get('code', 400) < 500:
            raise exceptions.AccessError("Error trying to connect to Cenit.")

        raise exceptions.ValidationError("Cenit returned with errors")


    @api.model
    def get(self, path, params=None):
        config = self.instance()

        r = requests.get(
            config.get('cenit_url') + API_PATH + path,
            params = params,
            headers = self.headers(config)
        )
        if 200 <= r.status_code < 300:
            return simplejson.loads(r.content)


        error = simplejson.loads(r.content)
        if 400 <= error.get('code', 400) < 500:
            raise exceptions.AccessError("Error trying to connect to Cenit.")

        raise exceptions.ValidationError("Cenit returned with errors")

    @api.model
    def put(self, path, vals):
        config = self.instance()
        payload = simplejson.dumps(vals)

        r = requests.put(
            config.get('cenit_url') + API_PATH + path,
            data = payload,
            headers = self.headers(config)
        )
        if 200 <= r.status_code < 300:
            return simplejson.loads(r.content)


        error = simplejson.loads(r.content)
        if 400 <= error.get('code', 400) < 500:
            raise exceptions.AccessError("Error trying to connect to Cenit.")

        raise exceptions.ValidationError("Cenit returned with errors")

    @api.model
    def delete(self, path):
        config = self.instance()

        r = requests.delete (
            config.get('cenit_url') + API_PATH + path,
            headers = self.headers(config)
        )
        if 200 <= r.status_code < 300:
            return True

        error = simplejson.loads(r.content)
        if 400 <= error.get('code', 400) < 500:
            raise exceptions.AccessError("Error trying to connect to Cenit.")

        raise exceptions.ValidationError("Cenit returned with errors")

    @api.model
    def instance(self):
        icp = self.env['ir.config_parameter']

        config = {
            'cenit_url': icp.get_param(
                "odoo_cenit.cenit_url", default=None
            ),
            'cenit_user_key': icp.get_param(
                "odoo_cenit.cenit_user_key", default=None
            ),
            'cenit_user_token': icp.get_param(
                "odoo_cenit.cenit_user_token", default=None
            ),
        }

        return config

    @api.model
    def headers(self, config):
        return {
            'Content-Type': 'application/json',
            'X-User-Access-Key': config.get('cenit_user_key'),
            'X-User-Access-Token': config.get('cenit_user_token')
        }

    @api.model
    def create(self, vals):
        obj = super(CenitApi, self).create(vals)

        local = self.env.context.get('local', False)
        if local:
            return obj

        rc = False
        try:
            rc = obj.push_to_cenit()
        except requests.ConnectionError as e:
            _logger.exception(e)
#             warning = {
#                 'title': _('Error!'),
#                 'message' :
#                     _('Cenit refused the connection. It is probably down.')
#             }
            return False # {'warning': warning}
        except Exception as e:
            _logger.exception(e)
#             warning = {
#                 'title': _('Error!'),
#                 'message' :
#                     _('Something wicked happened.')
#             }
            return False # {'warning': warning}

        if not rc:
#             warning = {
#                 'title': _('Error!'),
#                 'message' :
#                     _('Something wicked happened.')
#             }
            return False # {'warning': warning}

        return obj

    @api.one
    def write(self, vals):
        res = super(CenitApi, self).write(vals)

        local = self.env.context.get('local', False)
        if local:
            return res

        cp = vals.copy ()
        if cp.pop ('cenitID', False):
            if len (cp.keys ()) == 0:
                return res

        try:
            self.push_to_cenit()
        except requests.ConnectionError as e:
            _logger.exception(e)
#             warning = {
#                 'title': _('Error!'),
#                 'message' :
#                     _('Cenit refused the connection. It is probably down.')
#             }
            return False # {'warning': warning}
        except Exception as e:
            _logger.exception(e)
#             warning = {
#                 'title': _('Error!'),
#                 'message' :
#                     _('Something wicked happened.')
#             }
            return False # {'warning': warning}

        #~ if not rc:
            #~ warning = {
                #~ 'title': _('Error!'),
                #~ 'message' :
                    #~ _('Something wicked happened.')
            #~ }
            #~ return {'warning': warning}
            #~
        return res

    @api.one
    def unlink(self):
        rc = True
        try:
            rc = self.drop_from_cenit()
            pass
        except requests.ConnectionError as e:
            _logger.exception(e)
#                 warning = {
#                     'title': _('Error!'),
#                     'message' :
#                         _('Cenit refused the connection. It is probably down.')
#                 }
            return False # {'warning': warning}
        except Exception as e:
            _logger.exception(e)
#                 warning = {
#                     'title': _('Error!'),
#                     'message' :
#                         _('Something wicked happened.')
#                 }
            return False # {'warning': warning}

        if rc:
            rc = super(CenitApi, self).unlink ()

        if not rc:
#             warning = {
#                 'title': _('Error!'),
#                 'message' :
#                     _('Something wicked happened.')
#             }
            return False # {'warning': warning}
        return rc

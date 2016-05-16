#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#  Copyright 2015 D.H. Bahr <dhbahr@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import logging
import requests
import simplejson

from openerp import models, fields, exceptions


_logger = logging.getLogger(__name__)


COLLECTION_NAME = "basic"
COLLECTION_VERSION = "1.0.0"


class CenitSettings (models.TransientModel):

    _name = 'cenit.hub.settings'
    _inherit = 'res.config.settings'

    cenit_url = fields.Char ('Cenit URL')
    cenit_user_key = fields.Char ('Cenit User key')
    cenit_user_token = fields.Char ('Cenit User token')
    #~ odoo_endpoint = fields.Many2one ('cenit.connection', string='Odoo endpoint')

    module_cenit_extra = fields.Boolean('Use extra Toolkit',
        help="Allow you to import your existant Cenit data and provides a"
             "dynamic mapper for your DataTypes and Schemas"
    )

    module_cenit_desk = fields.Boolean('Desk API',
        help=""
    )

    module_cenit_mailchimp = fields.Boolean('Mailchimp API',
        help=""
    )

    module_cenit_mandrill = fields.Boolean('Mandrill API',
        help=""
    )

    module_cenit_shipstation = fields.Boolean('Shipstation API',
        help=""
    )

    module_cenit_shipwire = fields.Boolean('Shipwire API',
        help=""
    )

    module_cenit_slack = fields.Boolean('Slack API',
        help=""
    )

    module_cenit_twilio = fields.Boolean('Twilio API',
        help=""
    )

    module_cenit_twitter = fields.Boolean('Twitter API',
        help=""
    )

    module_cenit_asana = fields.Boolean('Asana API',
        help=""
    )

    module_cenit_messagebird = fields.Boolean('MessageBird API',
        help=""
    )

    ############################################################################
    # Default values getters
    ############################################################################

    def get_default_cenit_url (self, cr, uid, ids, context=None):
        cenit_url = self.pool.get ("ir.config_parameter").get_param (
            cr, uid, "odoo_cenit.cenit_url", default=None, context=context
        )

        return {'cenit_url': cenit_url or 'https://cenit.io'}

    def get_default_cenit_user_key (self, cr, uid, ids, context=None):
        cenit_user_key = self.pool.get ("ir.config_parameter").get_param (
            cr, uid, "odoo_cenit.cenit_user_key", default=None, context=context
        )
        return {'cenit_user_key': cenit_user_key or False}

    def get_default_cenit_user_token (self, cr, uid, ids, context=None):
        cenit_user_token = self.pool.get ("ir.config_parameter").get_param (
            cr, uid, "odoo_cenit.cenit_user_token", default=None, context=context
        )

        return {'cenit_user_token': cenit_user_token or False}

    #~ def get_default_odoo_endpoint (self, cr, uid, ids, context=None):
        #~ odoo_endpoint = self.pool.get ("ir.config_parameter").get_param (
            #~ cr, uid, "odoo_cenit.odoo_endpoint", default=None, context=context
        #~ )
#~
        #~ if (type(odoo_endpoint) in (unicode, str)) and odoo_endpoint.isdigit ():
            #~ odoo_endpoint = int(odoo_endpoint)
#~
        #~ return {'odoo_endpoint': odoo_endpoint or False}

    ############################################################################
    # Values setters
    ############################################################################

    def set_cenit_url (self, cr, uid, ids, context=None):
        config_parameters = self.pool.get ("ir.config_parameter")
        for record in self.browse (cr, uid, ids, context=context):
            config_parameters.set_param (
                cr, uid, "odoo_cenit.cenit_url",
                record.cenit_url or '', context=context
            )

    def set_cenit_user_key (self, cr, uid, ids, context=None):
        config_parameters = self.pool.get ("ir.config_parameter")
        for record in self.browse (cr, uid, ids, context=context):
            config_parameters.set_param (
                cr, uid, "odoo_cenit.cenit_user_key",
                record.cenit_user_key or '', context=context
            )

    def set_cenit_user_token (self, cr, uid, ids, context=None):
        config_parameters = self.pool.get ("ir.config_parameter")
        for record in self.browse (cr, uid, ids, context=context):
            config_parameters.set_param (
                cr, uid, "odoo_cenit.cenit_user_token",
                record.cenit_user_token or '', context=context
            )

    #~ def set_odoo_endpoint (self, cr, uid, ids, context=None):
        #~ config_parameters = self.pool.get ("ir.config_parameter")
        #~ for record in self.browse (cr, uid, ids, context=context):
            #~ config_parameters.set_param (
                #~ cr, uid, "odoo_cenit.odoo_endpoint",
                #~ record.odoo_endpoint.id or '', context=context
            #~ )

    ############################################################################
    # Actions
    ############################################################################

    def execute(self, cr, uid, ids, context=None):
        prev = {}
        prev.update(
            self.get_default_cenit_user_key(cr, uid, ids, context=context)
        )
        prev.update(
            self.get_default_cenit_user_token(cr, uid, ids, context=context)
        )

        rc = super(CenitSettings, self).execute(cr, uid, ids, context=context)

        objs = self.browse(cr, uid, ids)
        if not objs:
            return rc
        obj = objs[0]

        same = (prev.get('cenit_user_key', False) == obj.cenit_user_key) and \
               (prev.get('cenit_user_token', False) == obj.cenit_user_token)
        empty = not (obj.cenit_user_key and obj.cenit_user_token)
        install = context.get('install', False)

        if (same or empty) and not install:
            return rc

        installer = self.pool.get('cenit.collection.installer')
        data = installer.get_collection_data(
            cr, uid,
            COLLECTION_NAME,
            version=COLLECTION_VERSION,
            context=context
        )

        ctx = context.copy()
        ctx.update({
            "coll_name": COLLECTION_NAME,
            "coll_ver": COLLECTION_VERSION,
        })

        installer.install_collection(cr, uid, data.get('id'), context=ctx)

        self.post_install(cr, uid, ids, context=None)
        return rc

    def post_install(self, cr, uid, ids, context=None):
        icp = self.pool.get("ir.config_parameter")
        conn_pool = self.pool.get("cenit.connection")
        hook_pool = self.pool.get("cenit.webhook")
        role_pool = self.pool.get("cenit.connection.role")

        conn_data = {
            "name": "My Odoo host",
            "url": icp.get_param(cr, uid, 'web.base.url', default=None)
        }
        conn = conn_pool.create(cr, uid, conn_data, context=context)

        hook_data = {
            "name": "Cenit webhook",
            "path": "cenit/push",
            "method": "post",
        }
        hook = hook_pool.create(cr, uid, hook_data, context=context)

        role_data = {
            "name": "My Odoo role",
            "connections": [(6, False, [conn])],
            "webhooks": [(6, False, [hook])],
        }
        role = role_pool.create(cr, uid, role_data, context=context)

        icp.set_param(cr, uid, 'cenit.odoo_feedback.hook', hook)
        icp.set_param(cr, uid, 'cenit.odoo_feedback.conn', conn)
        icp.set_param(cr, uid, 'cenit.odoo_feedback.role', role)

        return True


class CenitAccountSettings(models.TransientModel):
    _name = "cenit.account.settings"
    _inherit = "res.config.settings"

    cenit_email = fields.Char ('Cenit user email')
    cenit_captcha = fields.Char ('Enter the text in the image')

    ############################################################################
    # Default values getters
    ############################################################################

    def get_default_cenit_email (self, cr, uid, ids, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)

        return {'cenit_email': user.login or False}

    ############################################################################
    # Actions
    ############################################################################

    def fields_view_get(self, cr, uid, view_id=None, view_type='tree',
                        context=None, toolbar=False, submenu=False):

        rc = super(CenitAccountSettings, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu
        )

        arch = rc['arch']
        if not arch.startswith('<form string="Cenit Hub account settings">'):
            return rc

        icp = self.pool.get("ir.config_parameter")
        hub_host = icp.get_param(cr, uid, "odoo_cenit.cenit_url",
                                 default='https://cenit.io')
        if hub_host.endswith("/"):
            hub_host = hub_host[:-1]
        hub_hook = "captcha"
        hub_url = "{}/{}".format(hub_host, hub_hook)

        try:
            r = requests.get(hub_url)
        except Exception as e:
            _logger.error("\n\Error: %s\n", e)
            raise exceptions.AccessError("Error trying to connect to Cenit.")

        captcha_data = simplejson.loads(r.content)
        token = captcha_data.get('token', False)
        if not token:
            raise exceptions.AccessError("Error trying to connect to Cenit.")

        icp.set_param(cr, uid, 'cenit.captcha.token', token, context=context)

        arch = arch.replace(
            'img_data_here', '{}/{}'.format(hub_url, token)
        )

        rc['arch'] = arch
        return rc

    def execute(self, cr, uid, ids, context=None):
        rc = super(CenitAccountSettings, self).execute(
            cr, uid, ids, context=context
        )

        if not context.get('install', False):
            return rc

        objs = self.browse(cr, uid, ids)
        if not objs:
            return rc
        obj = objs[0]

        icp = self.pool.get("ir.config_parameter")
        token = icp.get_param(cr, uid, 'cenit.captcha.token', default=None)

        cenit_api = self.pool.get('cenit.api')
        path = "/setup/account"
        vals = {
            'email': obj.cenit_email,
            'token': token,
            'code': obj.cenit_captcha,
        }

        res = cenit_api.post(cr, uid, path, vals, context=context)
        _logger.info("\n\nRES: %s\n", res)

        icp.set_param(cr, uid, 'odoo_cenit.cenit_user_key', res.get('number'))
        icp.set_param(cr, uid, 'odoo_cenit.cenit_user_token', res.get('token'))

        return rc

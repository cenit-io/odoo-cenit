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

    def sync_with_cenit(self, cr, uid, context=None):
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

        installer.install_common_data(cr, uid, data.get('data'))

        self.post_install(cr, uid, context=context)

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

        self.sync_with_cenit(cr, uid, context=context)
        return rc

    def post_install(self, cr, uid, context=None):
        icp = self.pool.get("ir.config_parameter")
        conn_pool = self.pool.get("cenit.connection")
        hook_pool = self.pool.get("cenit.webhook")
        role_pool = self.pool.get("cenit.connection.role")
        names_pool = self.pool.get("cenit.namespace")


        domain = [('name', '=', 'MyOdoo')]
        namesp = names_pool.search(cr, uid, domain, context=context)


        conn_data = {
            "name": "My Odoo host",
            "namespace": namesp[0],
            "url": icp.get_param(cr, uid, 'web.base.url', default=None,context=context)
        }
        conn = conn_pool.create(cr, uid, conn_data, context=context)

        hook_data = {
            "name": "Cenit webhook",
            "path": "cenit/push",
            "namespace": namesp[0],
            "method": "post"
        }
        hook = hook_pool.create(cr, uid, hook_data, context=context)

        role_data = {
            "namespace": namesp[0],
            "name": "My Odoo role",
            "connections": [(6, False, [conn])],
            "webhooks": [(6, False, [hook])],
        }
        role = role_pool.create(cr, uid, role_data, context=context)

        icp.set_param(cr, uid, 'cenit.odoo_feedback.hook', hook)
        icp.set_param(cr, uid, 'cenit.odoo_feedback.conn', conn)
        icp.set_param(cr, uid, 'cenit.odoo_feedback.role', role)

        return True

    def update_collection(self, cr, uid, ids, context):
        installer = self.pool.get('cenit.collection.installer')
        objs = self.browse(cr, uid, ids, context)
        if objs:
            obj = objs[0]
            if obj.module_cenit_asana:
                installer.install_collection(cr, uid, {'name': 'asana'}, context)
            if obj.module_cenit_desk:
                installer.install_collection(cr, uid, {'name': 'desk'}, context)
            if obj.module_cenit_mailchimp:
                installer.install_collection(cr, uid, {'name': 'mailchimp'}, context)
            if obj.module_cenit_mandrill:
                installer.install_collection(cr, uid, {'name': 'mandrill'}, context)
            if obj.module_cenit_messagebird:
                installer.install_collection(cr, uid, {'name': 'messagebird'}, context)
            if obj.module_cenit_shipstation:
                installer.install_collection(cr, uid, {'name': 'shipstation'}, context)
            if obj.module_cenit_shipwire:
                installer.install_collection(cr, uid, {'name': 'shipwire'}, context)
            if obj.module_cenit_slack:
                installer.install_collection(cr, uid, {'name': 'slack'}, context)
            if obj.module_cenit_twilio:
                installer.install_collection(cr, uid, {'name': 'twilio'}, context)
            if obj.module_cenit_twitter:
                installer.install_collection(cr, uid, {'name': 'twitter'}, context)


class CenitAccountSettings(models.TransientModel):
    _name = "cenit.account.settings"
    _inherit = "res.config.settings"

    cenit_email = fields.Char ('Cenit user email')
    cenit_captcha = fields.Char ('Text in the image')
    cenit_passwd = fields.Char ('Cenit password')
    confirm_passwd = fields.Char ('Confirm password')

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

        if context.get('sign_up'):
            arch = rc['arch']

            email = context.get('email')
            passwd = context.get('passwd')
            confirmation = context.get('confirmation')

            icp = self.pool.get("ir.config_parameter")
            hub_host = icp.get_param(cr, uid, "odoo_cenit.cenit_url", default='https://cenit.io',context=context)
            if hub_host.endswith("/"):
                hub_host = hub_host[:-1]
            path = "/setup/user"
            vals = {
                      "email": email,
                      "password": passwd,
                      "password_confirmation": confirmation
            }

            payload = simplejson.dumps(vals)
            url = hub_host + "/api/v2" + path

            try:
                _logger.info("[POST] %s", url)
                r = requests.post(url, data=payload)
            except Exception as e:
                _logger.error(e)
                raise exceptions.AccessError("Error trying to connect to Cenit.")

            if 200 <= r.status_code < 300:
                response = r.json()
            else:
                try:
                    error = r.json()
                    _logger.error(error)
                except Exception as e:
                    _logger.error(e)
                    raise exceptions.ValidationError("Cenit returned with errors")

                if r.status_code == 406:
                       key = str(error.keys()[0])
                       raise exceptions.ValidationError(key.capitalize()+ " "+ str(error[key][0]))
                else:
                    raise exceptions.AccessError("Error trying to connect to Cenit.")

            token = response.get('token', False)

            icp = self.pool.get('ir.config_parameter')


            hub_hook = "captcha"
            hub_url = "{}/{}/{}".format(hub_host, hub_hook, token)

            try:
                r = requests.get(hub_url)
            except Exception as e:
                _logger.error("\n\Error: %s\n", e)
                raise exceptions.AccessError("Error trying to connect to Cenit.")

            icp.set_param(cr, uid, 'cenit.captcha.token', token, context=context)

            arch = arch.replace(
                'img_data_here', '{}'.format(hub_url)
            )

            rc['arch'] = arch
        return rc

    def execute(self, cr, uid, ids, context=None):
        cenit_api = self.pool.get('cenit.api')
        path = "/setup/user"
        icp = self.pool.get('ir.config_parameter')

        vals = {
                  "token": icp.get_param(cr, uid,'cenit.captcha.token',context=context),
                  "code": context.get('code')
        }

        res = cenit_api.post(cr, uid, path, vals, context=context)
        icp.set_param(cr, uid, 'odoo_cenit.cenit_user_key', res.get('number'), context=context)
        icp.set_param(cr, uid, 'odoo_cenit.cenit_user_token', res.get('token'), context=context)

        hub = self.pool.get('cenit.hub.settings')
        hub.sync_with_cenit(cr, uid, context=context)

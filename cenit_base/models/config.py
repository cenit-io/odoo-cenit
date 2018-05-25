#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# config.py
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
import json

from odoo import models, fields, exceptions


_logger = logging.getLogger(__name__)

COLLECTION_NAME = "basic"
COLLECTION_VERSION = "1.0.0"


class CenitSettings(models.TransientModel):
    _name = 'cenit.hub.settings'
    _inherit = 'res.config.settings'

    cenit_url = fields.Char('Cenit URL')
    cenit_user_key = fields.Char('Cenit User key')
    cenit_user_token = fields.Char('Cenit User token')

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

    def get_values_cenit_url(self, context):
        cenit_url = self.env["ir.config_parameter"].get_param(
            "odoo_cenit.cenit_url", default=None)

        return {'cenit_url': cenit_url or 'https://cenit.io'}

    def get_values_cenit_user_key(self, context):
        cenit_user_key = self.env["ir.config_parameter"].get_param(
            "odoo_cenit.cenit_user_key", default=None)
        return {'cenit_user_key': cenit_user_key or False}

    def get_values_cenit_user_token(self, context):
        cenit_user_token = self.env["ir.config_parameter"].get_param(
            "odoo_cenit.cenit_user_token", default=None)

        return {'cenit_user_token': cenit_user_token or False}


    ############################################################################
    # Values setters
    ############################################################################

    def set_values(self):
        config_parameters = self.env["ir.config_parameter"]
        cenit_url = config_parameters.search([('key', '=', 'odoo_cenit.cenit_url')]).value

        config_parameters.set_param("odoo_cenit.cenit_url",
                                        cenit_url or '')

        for record in self.browse(self.ids):
            config_parameters.set_param("odoo_cenit.cenit_user_key",
                                        record.cenit_user_key or ''
            )
        for record in self.browse(self.ids):
            config_parameters.set_param("odoo_cenit.cenit_user_token",
                                         record.cenit_user_token or ''
            )

    # def set_values_cenit_user_key(self):
    #     config_parameters = self.env["ir.config_parameter"]
    #     for record in self.browse (self.ids):
    #         config_parameters.set_param (
    #             "odoo_cenit.cenit_user_key",
    #             record.cenit_user_key or ''
    #         )
    #
    # def set_values_cenit_user_token(self):
    #     config_parameters = self.env["ir.config_parameter"]
    #     for record in self.browse(self.ids):
    #         config_parameters.set_param (
    #             "odoo_cenit.cenit_user_token",
    #             record.cenit_user_token or ''
    #         )

    ############################################################################
    # Actions
    ############################################################################

    def sync_with_cenit(self):
        installer = self.env['cenit.collection.installer']

        data = installer.get_collection_data(
            COLLECTION_NAME,
            version=COLLECTION_VERSION
        )

        installer.install_common_data(data.get('data'))

        self.post_install()

    def execute(self):
        prev = {}
        prev.update(
            self.get_values_cenit_user_key(self.env.context)
        )
        prev.update(
            self.get_values_cenit_user_token(self.env.context)
        )

        rc = super(CenitSettings, self).execute()

        objs = self.browse(self.ids)
        if not objs:
            return rc
        obj = objs[0]

        same = (prev.get('cenit_user_key', False) == obj.cenit_user_key) and \
               (prev.get('cenit_user_token', False) == obj.cenit_user_token)
        empty = not (obj.cenit_user_key and obj.cenit_user_token)
        install = self.env.context.get('install', False)

        if (same or empty) and not install:
            return rc

        self.sync_with_cenit()
        return rc

    def post_install(self):
        icp = self.env["ir.config_parameter"]
        conn_pool = self.env["cenit.connection"]
        hook_pool = self.env["cenit.webhook"]
        role_pool = self.env["cenit.connection.role"]
        names_pool = self.env["cenit.namespace"]

        domain = [('name', '=', 'MyOdoo')]
        namesp = names_pool.search(domain)

        conn_data = {
            "name": "My Odoo host",
            "namespace": namesp[0]['id'],
            "url": icp.get_param('web.base.url', default=None)
        }
        conn = conn_pool.create(conn_data)

        hook_data = {
            "name": "Cenit webhook",
            "path": "cenit/push",
            "namespace": namesp[0]['id'],
            "method": "post"
        }
        hook = hook_pool.create(hook_data)

        role_data = {
            "namespace": namesp[0]['id'],
            "name": "My Odoo role",
            #"connections": [(6, False, [conn['id']])],
            "webhooks": [(6, False, [hook['id']])],
        }
        role = role_pool.create(role_data)
        role_pool.write({"connections": [conn['id']], "id": role['id']})

        icp.set_param('cenit.odoo_feedback.hook', hook)
        icp.set_param('cenit.odoo_feedback.conn', conn)
        icp.set_param('cenit.odoo_feedback.role', role)

        return True

    def update_collection(self):
        installer = self.env['cenit.collection.installer']
        objs = self.browse(self.ids)
        if objs:
            obj = objs[0]
            if obj.module_cenit_asana:
                installer.install_collection({'name': 'asana'})
            if obj.module_cenit_desk:
                installer.install_collection({'name': 'desk'})
            if obj.module_cenit_mailchimp:
                installer.install_collection({'name': 'mailchimp'})
            if obj.module_cenit_mandrill:
                installer.install_collection({'name': 'mandrill'})
            if obj.module_cenit_messagebird:
                installer.install_collection({'name': 'messagebird'})
            if obj.module_cenit_shipstation:
                installer.install_collection({'name': 'shipstation'})
            if obj.module_cenit_shipwire:
                installer.install_collection({'name': 'shipwire'})
            if obj.module_cenit_slack:
                installer.install_collection({'name': 'slack'})
            if obj.module_cenit_twilio:
                installer.install_collection({'name': 'twilio'})
            if obj.module_cenit_twitter:
                installer.install_collection({'name': 'twitter'})


class CenitAccountSettings(models.TransientModel):
    _name = "cenit.account.settings"
    _inherit = "res.config.settings"

    cenit_email = fields.Char('Cenit user email')
    cenit_captcha = fields.Char('Text in the image')
    cenit_passwd = fields.Char('Cenit password')
    confirm_passwd = fields.Char('Confirm password')

    ############################################################################
    # Default values getters
    ############################################################################

    def get_values_cenit_email(self, context):
        user = self.env['res.users'].browse(self.env.uid)

        return {'cenit_email': user.login or False}

    ############################################################################
    # Actions
    ############################################################################

    def fields_view_get(self, view_id=None, view_type='tree',
                        context=None, toolbar=False):

        rc = super(CenitAccountSettings, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar)

        if self.env.context.get('next_view'):
            arch = rc['arch']

            email = self.env.context.get('email')
            passwd = self.env.context.get('passwd')
            confirmation = self.env.context.get('confirmation')

            icp = self.env["ir.config_parameter"]
            hub_host = icp.get_param("odoo_cenit.cenit_url", default='https://cenit.io')
            if hub_host.endswith("/"):
                hub_host = hub_host[:-1]
            path = "/setup/user"
            vals = {
                "email": email,
                "password": passwd,
                "password_confirmation": confirmation
            }

            payload = json.dumps(vals)
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
                    key = str(list(error.keys())[0])
                    raise exceptions.ValidationError(key.capitalize() + " " + str(error[key][0]))
                else:
                    raise exceptions.AccessError("Error trying to connect to Cenit.")

            token = response.get('token', False)

            icp = self.env['ir.config_parameter']

            hub_hook = "captcha"
            hub_url = "{}/{}/{}".format(hub_host, hub_hook, token)

            try:
                r = requests.get(hub_url)
            except Exception as e:
                _logger.error("\n\Error: %s\n", e)
                raise exceptions.AccessError("Error trying to connect to Cenit.")

            icp.set_param('cenit.captcha.token', token)

            arch = arch.replace(
                'img_data_here', '{}'.format(hub_url)
            )

            rc['arch'] = arch
        return rc

    def execute(self):
        cenit_api = self.env['cenit.api']
        path = "/setup/user"
        icp = self.env['ir.config_parameter']

        vals = {
            "token": icp.get_param('cenit.captcha.token'),
            "code": self.env.context.get('code')
        }

        res = cenit_api.post(path, vals)
        icp.set_param('odoo_cenit.cenit_user_key', res.get('number'))
        icp.set_param('odoo_cenit.cenit_user_token', res.get('token'))

        hub = self.env['cenit.hub.settings']
        hub.sync_with_cenit()


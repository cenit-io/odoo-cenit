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

from openerp import models, fields


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

    ############################################################################
    # Default values getters
    ############################################################################

    def get_default_cenit_url (self, cr, uid, ids, context=None):
        cenit_url = self.pool.get ("ir.config_parameter").get_param (
            cr, uid, "odoo_cenit.cenit_url", default=None, context=context
        )

        return {'cenit_url': cenit_url or 'https://www.cenithub.com'}

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

        if same or empty:
            return rc

        installer = self.pool.get('cenit.collection.installer')
        data = installer.get_collection_data(
            cr, uid,
            COLLECTION_NAME,
            version=COLLECTION_VERSION,
            context=context
        )

        installer.install_collection(cr, uid, data.get('id'), context=context)

        return rc


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

    def fields_view_get(self,
        cr, uid,
        view_id=None, view_type='tree',
        context=None, toolbar=False, submenu=False
    ):

        rc = super(CenitAccountSettings, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu
        )

        arch = rc['arch']
        if not arch.startswith('<form string="Cenit Hub account settings">'):
            return rc

        img_data = "data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="

        arch = arch.replace(
            'img_data_here', img_data
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

        cenit_api = self.pool.get('cenit.api')
        path = "/setup/account"
        vals = {'email': obj.cenit_email}
        rc = cenit_api.put(cr, uid, path, vals, context=context)
        _logger.info("\n\nRC: %s\n", rc)


        return rc

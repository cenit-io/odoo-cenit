#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  connection.py
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

from odoo import models, fields, api, exceptions

from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class CenitConnection(models.Model):
    _name = 'cenit.connection'
    _inherit = 'cenit.api'

    cenit_model = 'connection'
    cenit_models = 'connections'

    cenitID = fields.Char('Cenit ID')

    namespace = fields.Many2one('cenit.namespace', string='Namespace',
                                ondelete='cascade')

    name = fields.Char('Name', required=True)
    url = fields.Char('URL', required=True)

    key = fields.Char('Key', readonly=True)
    token = fields.Char('Token', readonly=True)

    url_parameters = fields.One2many(
        'cenit.parameter',
        'conn_url_id',
        string='Parameters'
    )
    header_parameters = fields.One2many(
        'cenit.parameter',
        'conn_header_id',
        string='Header Parameters'
    )
    template_parameters = fields.One2many(
        'cenit.parameter',
        'conn_template_id',
        string='Template Parameters'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(namespace, name)',
         'The name must be unique for each namespace!'),
    ]

    @api.one
    def _get_values(self):
        vals = {
            'name': self.name,
            'url': self.url,
            'namespace': self.namespace.name,
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        _reset = []
        params = []
        for param in self.url_parameters:
            params.append({
                'key': param.key,
                'value': param.value
            })
        vals.update({'parameters': params})
        _reset.append('parameters')

        headers = []
        for header in self.header_parameters:
            headers.append({
                'key': header.key,
                'value': header.value
            })
        vals.update({'headers': headers})
        _reset.append('headers')

        template = []
        for tpl in self.template_parameters:
            template.append({
                'key': tpl.key,
                'value': tpl.value
            })
        vals.update({'template_parameters': template})
        _reset.append('template_parameters')

        vals.update(
            {
                "_primary": ["namespace", "name"],
                "_reset": _reset
            }
        )

        return vals

    def _calculate_update(self, values):
        update = {}
        for k, v in values.items():
            if k == "%s" % (self.cenit_models):
                update = {
                    'cenitID': v[0]['id'],
                }

        return update

    @api.one
    def _get_conn_data(self):
        path = "/setup/connection/%s" % self.cenitID
        rc = self.get(path)

        vals = {
            'key': rc['number'],
            'token': rc['token'],
        }

        self.with_context(local=True).write(vals)
        return

    @api.model
    def create(self, vals):
        if not isinstance(vals['namespace'], int):
            vals['namespace'] = vals['namespace']['id']
        obj = super(CenitConnection, self).create(vals)

        if obj and obj.cenitID and not self.env.context.get('local', False):
            obj._get_conn_data()

        return obj


class CenitWebhook(models.Model):

    @api.depends('method')
    def _compute_purpose(self):
        self.purpose = {
            'get': 'send'
        }.get(self.method, 'receive')

    _name = 'cenit.webhook'
    _inherit = 'cenit.api'

    cenit_model = 'webhook'
    cenit_models = 'webhooks'

    cenitID = fields.Char('Cenit ID')

    namespace = fields.Many2one('cenit.namespace', string='Namespace',
                                ondelete='cascade')
    name = fields.Char('Name', required=True)
    path = fields.Char('Path', required=True)
    purpose = fields.Char(compute='_compute_purpose', store=True)
    description = fields.Text('Description')
    method = fields.Selection(
        [
            ('get', 'GET'),
            ('post', 'POST'),
            ('put', 'PUT'),
            ('delete', 'DELETE'),
            ('patch', 'PATCH'),
            ('copy', 'COPY'),
            ('head', 'HEAD'),
            ('options', 'OPTIONS'),
            ('link', 'LINK'),
            ('unlink', 'UNLINK'),
            ('purge', 'PURGE'),
            ('lock', 'LOCK'),
            ('unlock', 'UNLOCK'),
            ('propfind', 'PROPFIND')
        ],
        'Method', default='post', required=True
    )

    url_parameters = fields.One2many(
        'cenit.parameter',
        'hook_url_id',
        string='Parameters'
    )
    header_parameters = fields.One2many(
        'cenit.parameter',
        'hook_header_id',
        string='Header Parameters'
    )
    template_parameters = fields.One2many(
        'cenit.parameter',
        'hook_template_id',
        string='Template Parameters'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(namespace, name)',
         'The name must be unique for each namespace!')
    ]

    @api.one
    def _get_values(self):
        vals = {
            'name': self.name,
            'path': self.path,
            'purpose': self.purpose,
            'method': self.method,
            'namespace': self.namespace.name,
            '_type': 'Setup::PlainWebhook',
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        _reset = []
        params = []
        for param in self.url_parameters:
            params.append({
                'key': param.key,
                'value': param.value
            })
        vals.update({'parameters': params})
        _reset.append('parameters')

        vals.update(
            {
                '_reset': _reset,
                '_primary': ['name', 'namespace']
            }
        )

        return vals

    @api.model
    def create(self, vals):
        if not isinstance(vals['namespace'], int):
            vals['namespace'] = vals['namespace']['id']
        return super(CenitWebhook, self).create(vals)


class CenitOperation(models.Model):
    _name = 'cenit.operation'
    _inherit = 'cenit.api'

    cenit_model = 'operation'
    cenit_models = 'operations'

    @api.depends('resource_id', 'method')
    def _compute_extra_fields(self):
        for record in self:
            record.namespace = record.resource_id.namespace.name
            record.path = record.resource_id.path + '/' + record.method

    namespace = fields.Char(compute='_compute_extra_fields')
    path = fields.Char(compute='_compute_extra_fields')

    cenitID = fields.Char('Cenit ID')

    resource_id = fields.Many2one('cenit.resource', string='Resource')

    def _compute_display_name(self):
        for record in self:
            record.display_name = record.method.upper()

    def name_get(self):
        result = []
        for record in self:
            resource = record.resource_id
            if not resource:
                resource_id = record.env.context['resource_id']
                resource = record.env['cenit.resource'].search([('id', '=', resource_id)])
            name = resource.namespace.name + ' | ' + resource.name + ' | ' + record['method'].upper()
            result.append((record.id, name))
        return result

    @api.depends('method')
    def _compute_purpose(self):
        for record in self:
            record.purpose = {
                'get': 'send'
            }.get(record.method, 'receive')

    purpose = fields.Char(compute='_compute_purpose', store=True)
    method = fields.Selection(
        [
            ('get', 'GET'),
            ('post', 'POST'),
            ('put', 'PUT'),
            ('delete', 'DELETE'),
            ('patch', 'PATCH'),
            ('copy', 'COPY'),
            ('head', 'HEAD'),
            ('options', 'OPTIONS'),
            ('link', 'LINK'),
            ('unlink', 'UNLINK'),
            ('purge', 'PURGE'),
            ('lock', 'LOCK'),
            ('unlock', 'UNLOCK'),
            ('propfind', 'PROPFIND')
        ],
        'Method', default='post', required=True
    )
    description = fields.Text('Description')
    url_parameters = fields.One2many(
        'cenit.parameter',
        'operation_url_id',
        string='Parameters'
    )

    _sql_constraints = [
        ('method_uniq', 'UNIQUE(method, resource_id)',
         'The method must be unique for each resource!')
    ]

    @api.one
    def _get_values(self):
        vals = {
            'method': self.method,
            '_type': 'Setup::Operation'
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        _reset = []

        resource_id = self.resource_id or self.env.context['resource_id']
        resource = self.env['cenit.resource'].search([('id', '=', resource_id)])
        vals.update({'resource': {
            'id': resource.cenitID,
            "_reference": True
        }})
        _reset.append('resource')

        params = []
        for param in self.url_parameters:
            params.append({
                'key': param.key,
                'value': param.value
            })
        vals.update({'parameters': params})
        _reset.append('parameters')

        vals.update({
            '_reset': _reset
        })

        return vals


class CenitConnectionRole(models.Model):
    _name = 'cenit.connection.role'
    _inherit = 'cenit.api'

    cenit_model = 'connection_role'
    cenit_models = 'connection_roles'

    cenitID = fields.Char('Cenit ID')

    namespace = fields.Many2one('cenit.namespace', string='Namespace',
                                ondelete='cascade')

    name = fields.Char('Name', required=True)

    connections = fields.Many2many(
        'cenit.connection',
        string='Connections'
    )

    webhooks = fields.Many2many(
        'cenit.webhook',
        string='Webhooks'
    )

    operations = fields.Many2many(
        'cenit.operation',
        string='Operations'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(namespace, name)',
         'The name must be unique for each namespace!'),
    ]

    @api.one
    def _get_values(self):
        vals = {
            'name': self.name,
            'namespace': self.namespace.name,
        }
        if self.cenitID:
            vals.update({'id': self.cenitID})

        _reset = []

        connections = []
        for conn in self.connections:
            vals_ = conn._get_values()
            if isinstance(vals_, list):
                vals_ = vals_[0]
            connections.append(vals_)

        vals.update({
            'connections': connections,
        })
        _reset.append('connections')

        webhooks = []
        for hook in self.webhooks:
            vals_ = hook._get_values()
            if isinstance(vals_, list):
                vals_ = vals_[0]
            webhooks.append(vals_)
        for hook in self.operations:
            vals_ = hook._get_values()
            if isinstance(vals_, list):
                vals_ = vals_[0]
            webhooks.append(vals_)

        vals.update({
            'webhooks': webhooks
        })
        _reset.append('webhooks')

        vals.update({
            '_reset': _reset,
            '_primary': ['name', 'namespace']
        })

        return vals


class CenitParameter(models.Model):
    _name = 'cenit.parameter'
    _description = 'Cenit parameter'

    key = fields.Char('Key', required=True)
    value = fields.Char('Value')

    conn_url_id = fields.Many2one(
        'cenit.connection'
    )

    conn_header_id = fields.Many2one(
        'cenit.connection',
        string='Connection'
    )

    conn_template_id = fields.Many2one(
        'cenit.connection'
    )

    hook_url_id = fields.Many2one(
        'cenit.webhook'
    )

    hook_header_id = fields.Many2one(
        'cenit.webhook'
    )

    hook_template_id = fields.Many2one(
        'cenit.webhook'
    )

    operation_url_id = fields.Many2one(
        'cenit.operation',
        string='Operation'
    )

    resource_url_id = fields.Many2one(
        'cenit.resource'
    )

    resource_header_id = fields.Many2one(
        'cenit.resource'
    )

    resource_template_id = fields.Many2one(
        'cenit.resource'
    )


class CenitResource(models.Model):
    _name = 'cenit.resource'
    _inherit = 'cenit.api'

    cenit_model = 'resource'
    cenit_models = 'resources'

    cenitID = fields.Char('Cenit ID')

    namespace = fields.Many2one('cenit.namespace', string='Namespace', ondelete='cascade')
    name = fields.Char('Name', required=True)
    path = fields.Char('Path', required=True)
    description = fields.Text('Description')

    operations = fields.One2many(
        'cenit.operation',
        'resource_id',
        string='Operations'
    )

    @api.one
    @api.depends('operations')
    def _get_operations_list(self):
        self.ensure_one()
        operations_list = ""
        for operation in self.operations:
            if operations_list != "":
                operations_list += " and "
            operation_name = operation.name_get()[0]
            if operation_name:
                operations_list += operation_name[1]
        self.operations_list = operations_list

    operations_list = fields.Text(compute="_get_operations_list", string="Operations List")
    url_parameters = fields.One2many(
        'cenit.parameter',
        'resource_url_id',
        string='Parameters'
    )
    header_parameters = fields.One2many(
        'cenit.parameter',
        'resource_header_id',
        string='Header Parameters'
    )
    template_parameters = fields.One2many(
        'cenit.parameter',
        'resource_template_id',
        string='Template Parameters'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(namespace, name)',
         'The name must be unique for each namespace!')
    ]

    @api.one
    def _get_values(self):
        vals = {
            'name': self.name,
            'path': self.path,
            'description': self.description or '',
            'namespace': self.namespace.name,
            '_type': 'Setup::Resource',
            '_primary': ['name', 'namespace']
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        _reset = []
        operations = []
        for operation in self.operations:
            operations.append(operation._get_values()[0])
        vals.update({'operations': operations})
        _reset.append('operations')

        params = []
        for param in self.url_parameters:
            params.append({
                'key': param.key,
                'value': param.value
            })
        vals.update({'parameters': params})
        _reset.append('parameters')

        headers = []
        for header in self.header_parameters:
            headers.append({
                'key': header.key,
                'value': header.value
            })
        vals.update({'headers': headers})
        _reset.append('headers')

        template = []
        for tpl in self.template_parameters:
            template.append({
                'key': tpl.key,
                'value': tpl.value
            })
        vals.update({'template_parameters': template})
        _reset.append('template_parameters')

        vals.update({
            '_reset': _reset
        })

        return vals

    @api.model
    def create(self, vals):
        if not isinstance(vals['namespace'], int):
            vals['namespace'] = vals['namespace']['id']
        return super(CenitResource, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(CenitResource, self).write(vals)
        if 'operations' in vals:
            for operation in vals['operations']:
                if operation[0] == 3:
                    operation_id = operation[1]
                    self.env['cenit.operation'].search([('id', '=', operation_id)]).unlink()
        return res


class CenitEvent(models.Model):
    _name = "cenit.event"
    _inherit = "cenit.api"

    cenit_model = 'event'
    cenit_models = 'events'

    cenitID = fields.Char('CenitID')
    namespace = fields.Many2one('cenit.namespace', string='Namespace',
                                ondelete='cascade')

    name = fields.Char('Name', required=True, unique=True)
    type_ = fields.Selection(
        [
            ('Setup::Observer', 'Observer'),
            ('Setup::Scheduler', 'Scheduler'),
        ],
        string="Type"
    )
    cenit_type = fields.Selection(
        [
            ('on_create', 'On Create'),
            ('on_write', 'On Update'),
            ('on_create_or_write', 'On Create or Update')
        ],
        string="Event"
    )
    schema = fields.Many2one('cenit.schema', string='Data type')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(namespace, name)',
         'The name must be unique for each namespace!')
    ]

    @api.one
    def _get_values(self):
        vals = {
            'namespace': self.namespace.name,
            'name': self.name,
            '_type': "Setup::Observer",
            'data_type': {
                "_reference": True,
                "id": self.schema.cenitID
            },
            'triggers': {
                'on_create':
                    '{"created_at":{"0":{"o":"_not_null","v":["","",""]}}}',
                'on_write':
                    '{"updated_at":{"0":'
                    '{"o":"_presence_change","v":["","",""]}}}',
                'on_create_or_write':
                    '{"updated_at":{"0":{"o":"_change","v":["","",""]}}}',
            }[self.cenit_type]
        }

        return vals

    @api.one
    def _calculate_update(self, values):
        update = {}
        for k, v in values.items():
            if k == self.cenit_models:
                update = {
                    'cenitID': v[0]['id'],
                    'type_': v[0]['_type']
                }

        return update


class CenitTranslator(models.Model):
    _name = "cenit.translator"
    _inherit = "cenit.api"

    cenit_model = 'translator'
    cenit_models = 'translators'

    cenitID = fields.Char('CenitID')
    namespace = fields.Many2one('cenit.namespace', string='Namespace',
                                ondelete='cascade')
    name = fields.Char('Name', required=True, unique=True)
    type_ = fields.Char("Type")
    mime_type = fields.Char('MIME Type')
    schema = fields.Many2one('cenit.schema', string='Data type')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(namespace, name)',
         'The name must be unique for each namespace!')
    ]


class CenitFlow(models.Model):
    _name = "cenit.flow"
    _inherit = 'cenit.api'

    cenit_model = 'flow'
    cenit_models = 'flows'

    cenitID = fields.Char('Cenit ID')

    namespace = fields.Many2one('cenit.namespace', string='Namespace',
                                ondelete='cascade')

    name = fields.Char('Name', size=64, required=True, unique=True)
    enabled = fields.Boolean('Enabled', default=True)
    event = fields.Many2one("cenit.event", string='Event')
    discard_events = fields.Boolean("Discard events", default=False)

    cron = fields.Many2one('ir.cron', string='Cron rules')
    base_action_rules = fields.Many2many(
        'base.automation', string='Action Rule'
    )

    format_ = fields.Selection(
        [
            ('application/json', 'JSON'),
            ('application/EDI-X12', 'EDI')
        ],
        'Format', default='application/json', required=True
    )
    local = fields.Boolean('Bypass Cenit', default=False)
    cenit_translator = fields.Many2one('cenit.translator', "Translator")

    schema = fields.Many2one(
        'cenit.schema', 'Data type', required=True
    )
    data_type = fields.Many2one(
        'cenit.data_type', string='Source data type'
    )
    webhook = fields.Reference(string='Webhook',
                               selection=[('cenit.webhook', 'Plain'), ('cenit.operation', 'Operation')], required=True)
    connection_role = fields.Many2one(
        'cenit.connection.role', string='Connection role'
    )

    @api.depends('webhook')
    def _compute_method(self):
        self.method = self.webhook.method

    method = fields.Char(compute="_compute_method")

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(namespace, name)',
         'The name must be unique for each namespace!')
    ]

    @api.one
    def _get_values(self):
        vals = {
            'namespace': self.namespace.name,
            'name': self.name,
            'active': self.enabled,
            'discard_events': False,
            'data_type_scope': 'All',
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        event = {
            "_reference": True,
            "id": self.event.cenitID,
        }
        vals.update({
            'event': event,
            'data_type_scope': 'Event',
        })

        if self.cenit_translator:
            vals.update({
                'translator': {
                    '_reference': True,
                    'id': self.cenit_translator.cenitID,
                }
            })

        if self.schema.cenitID:
            vals.update({
                'custom_data_type': {
                    '_reference': True,
                    'id': self.schema.cenitID
                }
            })

        if self.connection_role:
            vals.update({
                'connection_role': {
                    '_reference': True,
                    'id': self.connection_role.cenitID
                }
            })

        if self.webhook:
            vals.update({
                'webhook': {
                    '_reference': True,
                    'id': self.webhook.cenitID
                }
            })

        return vals

    @api.one
    def _calculate_update(self, values):
        update = {}
        for k, v in values.items():
            if k == "%s" % (self.cenit_models,):
                update = {
                    'cenitID': v[0]['id'],

                }
        return update

    @api.onchange('webhook')
    def on_webhook_changed(self):
        return {
            'value': {
                'connection_role': ""
            },
            "domain": {
                "connection_role": [
                    ('webhooks', 'in', self.webhook.id)
                ]
            }
        }

    @api.onchange('schema')
    def on_schema_changed(self):
        return {
            'value': {
                'data_type': "",
                'event': "",
            },
            "domain": {
                "data_type": [
                    ('schema', '=', self.schema.id),
                    ('enabled', '=', True)
                ],
                'event': [
                    ('schema', '=', self.schema.id)
                ],
            }
        }

    @api.onchange('schema', 'webhook')
    def _on_schema_or_hook_changed(self):
        return {
            'value': {
                'cenit_translator': "",
            },
            'domain': {
                'cenit_translator': [
                    ('schema', 'in', (self.schema.id, False)),
                    ('type_', '=', {'get': 'Import', }.get(self.webhook.method, 'Export'))
                ]
            }
        }

    @api.one
    def _get_direction(self):
        my_url = self.env['ir.config_parameter'].get_param(
            'web.base.url', default=''
        )

        conn = self.connection_role.connections and \
               self.connection_role.connections[0]
        my_conn = conn.url == my_url

        rc = {
            ('get', True): 'send',
            ('put', False): 'send',
            ('post', False): 'send',
            ('delete', False): 'send',
        }.get((self.webhook.method, my_conn), 'receive')

        return rc

    @api.one
    def _get_data_types(self, dt_id):
        dt_pool = self.env['cenit.data_type']

        if self.data_type:
            return self.data_type
        else:
            domain = [('schema', '=', self.schema.id), ('enabled', '=', True), ('id', '=', dt_id)]
            return dt_pool.search(domain)

    @api.model
    def create(self, vals):
        local = (vals.get('cenitID', False) is False) or \
                (self.env.context.get('local'), False)

        if not isinstance(vals['namespace'], int):
            vals['namespace'] = vals['namespace']['id']

        obj = super(CenitFlow, self).create(vals)
        return obj

    @api.model
    def find(self, model, purpose):
        rc = []
        domain = [("schema.slug", "=", model)]
        objs = self.search(domain)
        if objs:
            rc = [x for x in objs if
                  ((x._get_direction()[0] == purpose) and x.enabled)]

        return rc

    @api.one
    def set_receive_execution(self):
        return True

    @api.model
    def receive(self, model, data):
        res = False
        context = self.env.context.copy() or {}
        flows = self.find(model.lower(), 'receive')

        if not flows:
            return res

        data_types = set()
        for flow in flows:
            dts = flow._get_data_types()
            for dt in dts:
                data_types.add(dt)
        for dt in data_types:
            klass = self.env[dt.model.model]

            if flow.format_ == 'application/json':
                action = context.get('action', 'push')
                wh = self.env['cenit.handler']
                context.update({'receive_object': True})

                action = getattr(wh, action, False)
                if action:
                    root = dt.cenit_root
                    res = action(data, root)

            elif flow.format_ == 'application/EDI-X12':
                for edi_document in data:
                    klass.edi_import(edi_document)
                res = True
        return res

    @api.one
    def set_send_execution(self):
        return True

    @api.model
    def send(self, obj, flow_id, dt_id):
        flow = self.browse(flow_id)
        if not (flow and flow.enabled):
            return False

        ws = self.env['cenit.serializer']

        data_types = flow._get_data_types(dt_id)
        if isinstance(data_types, list) and len(data_types) == 1:
            data_types = data_types[0]

        data = None
        if flow.format_ == 'application/json':
            data = []
            for dt in data_types:
                match = dt.ensure_object(obj)
                if isinstance(match, list):
                    match = match[0]
                if match:
                    data.append(ws.serialize(obj, dt))
        elif flow.format_ == 'application/EDI-X12':
            dt = data_types[0]
            if dt.ensure_object(obj):
                data = dt.model.edi_export([obj])

        rc = False
        if data:
            _logger.info("\n\nPushing: %s\n", data)
            rc = flow._send(data)

        return rc

    @api.model
    def send_all(self, id_, dt, domain=list()):
        flow = self.browse(id_)
        dt_ = flow.data_type or dt
        mo = self.env[dt_.model.model]
        _logger.info("Performing search on %s with %s", mo, domain)
        data = []

        query = "SELECT id from %s" % dt.model.model.replace(".", "_")
        for entry in domain:
            query += " WHERE %s%s'%s'" % (entry[0], entry[1], entry[2])

        self.env.cr.execute(query)
        rc = self.env.cr.fetchall()
        objs = mo.browse([x[0] for x in rc])

        if flow.format_ == 'application/json':
            ws = self.env['cenit.serializer']
            for x in objs:
                if dt_.ensure_object(x):
                    data.append(ws.serialize(x, dt_))
        elif flow.format_ == 'application/EDI-X12' and \
                hasattr(mo, 'edi_export'):
            for x in objs:
                if dt_.ensure_object(x):
                    data.append(mo.edi_export(x))

        if data:
            return flow._send(data)
        return False

    @api.one
    def _send(self, data):
        method = "http_post"
        return getattr(self, method)(data)

    @api.one
    def http_post(self, data):
        path = "/%s/%s" % (self.schema.namespace.slug, self.schema.slug,)

        values = data[0]

        rc = False
        try:
            rc = self.post(path, values)
        except Warning as e:
            _logger.exception(e)

        return rc

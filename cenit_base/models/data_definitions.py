#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  data_definitions.py
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
import simplejson

from openerp import models, fields, api


_logger = logging.getLogger(__name__)


class CenitSchema(models.Model):

    @api.one
    def cenit_root(self):
        schema = simplejson.loads(self.schema)
        root = schema.get('title', False)

        if not root:
            root = schema.get('name', False)

        if not root:
            root = ".".join(self.uri.split(".")[:-1])

        return "_".join(root.lower().split())

    _name = 'cenit.schema'
    _inherit = 'cenit.api'

    cenit_model = 'schema'
    cenit_models = 'schemas'

    cenitID = fields.Char('Cenit ID')
    datatype_cenitID = fields.Char ('Cenit DT ID')

    library = fields.Many2one(
        'cenit.library',
        string = 'Library',
        required = True,
        ondelete = 'cascade'
    )
    uri = fields.Char('Uri', required=True)
    schema = fields.Text('Schema')

    name = fields.Char('Name', compute='_compute_name')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(library,uri)',
        'The uri must be unique for each library!'),
    ]

    @api.depends('library', 'uri')
    @api.one
    def _compute_name(self):
        self.name = "%s | %s" % (self.library.name, self.uri)

    @api.one
    def _get_values(self):
        vals = {
            'library': {
                'id': self.library.cenitID
            },
            'uri': self.uri,
            'schema': self.schema,
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        return vals

    @api.one
    def _calculate_update(self, values):
        update = {}

        for k,v in values.items():
            if k == "%s" % (self.cenit_models):
                update = {
                    'cenitID': v[0]['id'],
                }
                if v[0].get('data_types', False):
                    update.update({
                        'datatype_cenitID': v[0]['data_types'][0]['id'],
                    })

        return update


class CenitLibrary(models.Model):

    _name = 'cenit.library'
    _inherit = 'cenit.api'

    cenit_model = 'library'
    cenit_models = 'libraries'

    cenitID = fields.Char('Cenit ID')

    name = fields.Char('Name', required=True)
    slug = fields.Char('Slug')

    schemas = fields.One2many(
        'cenit.schema',
        'library',
        string = 'Schemas'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    @api.one
    def _get_values(self):
        vals = {
            'name': self.name
        }
        if self.cenitID:
            vals.update({'id': self.cenitID})

        return vals

    @api.one
    def _calculate_update(self, values):
        update = {}

        for k,v in values.items():
            if k == "%s" % (self.cenit_models):
                update = {
                    'cenitID': v[0]['id'],
                }
                path = "/setup/library/%s" % (update.get('cenitID'))
                rc = self.get(path)
                slug = rc.get('library', {}).get('slug', False)
                if slug:
                    update.update({'slug': slug})

        return update


class CenitDataType(models.Model):

    @api.onchange('library')
    def _on_library_changed(self):
        return {
            'value': {
                'schema': '',
            },
            'domain': {
                'schema': [
                    ('id', 'in', [x.id for x in self.library.schemas])
                ]
            }
        }

    @api.depends('schema')
    def _compute_root(self):
        self.cenit_root = self.schema.cenit_root()

    _name = 'cenit.data_type'

    cenit_root = fields.Char(compute='_compute_root', store=True)

    name = fields.Char('Name', size=128, required=True)
    active = fields.Boolean('Active', default=True)
    library = fields.Many2one(
        'cenit.library',
        string = 'Library',
        required = True,
        ondelete = 'cascade'
    )

    model = fields.Many2one('ir.model', 'Model', required=True)
    schema = fields.Many2one('cenit.schema', 'Schema')

    lines = fields.One2many('cenit.data_type.line', 'data_type', 'Mapping')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    @api.one
    def _get_flows(self):
        flow_pool = self.env['cenit.flow']

        domain = [
            ('schema', '=', self.schema.id),
            ('data_type', 'in', (self.id, False))
        ]
        return flow_pool.search(domain) or []

    @api.one
    def sync_rules(self, flows=None):
        if not flows:
            flows = self._get_flows()[0]

        for flow in flows:
            purpose = flow._get_direction()[0]
            if purpose != 'send':
                continue
            flow.set_send_execution()

    @api.model
    def create(self, vals):
        obj = super(CenitDataType, self).create(vals)
        obj.sync_rules()

        return obj

    @api.one
    def write(self, vals):
        res = super(CenitDataType, self).write(vals)

        if res:
            self.sync_rules()

        return res

    @api.one
    def unlink(self):
        flows = self._get_flows()

        res = super(CenitDataType, self).unlink()

        if res:
            self.sync_rules(flows)

        return res


class CenitDataTypeLine(models.Model):
    _name = 'cenit.data_type.line'

    data_type = fields.Many2one('cenit.data_type', 'Data Type')

    name = fields.Char('Name')
    value = fields.Char('Value')

    line_type = fields.Selection(
        [
            ('field', 'Field'),
            ('model', 'Model'),
            ('default', 'Default'),
            ('reference', 'Reference')
        ],
        'Type'
    )
    reference = fields.Many2one('cenit.data_type', 'Reference')
    line_cardinality = fields.Selection(
        [
            ('2many', '2many'),
            ('2one', '2one')
        ],
        'Cardinality'
    )
    primary = fields.Boolean('Primary')

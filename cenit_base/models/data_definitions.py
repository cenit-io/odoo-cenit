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

from datetime import datetime


_logger = logging.getLogger(__name__)


class CenitNameSpace(models.Model):
    _name = 'cenit.namespace'
    _inherit = 'cenit.api'

    cenit_model = 'namespace'
    cenit_models = 'namespaces'

    cenitID = fields.Char('Cenit ID')

    name = fields.Char('Name', required=True)
    slug = fields.Char('Slug')
    schemas = fields.One2many('cenit.schema', 'namespace', string='Schemas')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
        ('slug_uniq', 'UNIQUE(slug)', 'The slug must be unique!')
    ]

    @api.one
    def _get_values(self):
        vals = {
            'name': self.name
        }
        if self.cenitID:
            vals.update({'id': self.cenitID})

        vals.update({'_primary': ['name']})

        return vals

    @api.one
    def _calculate_update(self, values):
        update = {}

        for k, v in values.items():
            if k == "%s" % (self.cenit_models,):
                update = {
                    'cenitID': v[0]['id'],
                }
                path = "/setup/namespace/%s" % (update.get('cenitID'))
                rc = self.get(path)
                slug = rc.get('namespace', {}).get('slug', False)
                if slug:
                    update.update({'slug': slug})

        return update

    @api.model
    def create(self, vals):
        slug = vals.get("slug", False)
        if not slug:
            name = vals.get("name")
            vals.update({"slug": name.lower().replace(" ", "_")})

        return super(CenitNameSpace, self).create(vals)

    @api.one
    def write(self, vals):
        slug = vals.get("slug", None)
        if not slug and slug is False:
            name = vals.get("name", False)
            if not name:
                name = self.name
            vals.update({"slug": name.lower().replace(" ", "_")})

        return super(CenitNameSpace, self).write(vals)


class CenitLibrary(models.Model):

    _name = 'cenit.library'
    _inherit = 'cenit.api'

    cenit_model = 'library'
    cenit_models = 'libraries'

    cenitID = fields.Char('Cenit ID')

    name = fields.Char('Name', required=True)
    slug = fields.Char('Slug')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
        ('slug_uniq', 'UNIQUE(slug)', 'The slug must be unique!')
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

        for k, v in values.items():
            if k == "%s" % (self.cenit_models,):
                update = {
                    'cenitID': v[0]['id'],
                }
                path = "/setup/library/%s" % (update.get('cenitID'))
                rc = self.get(path)
                slug = rc.get('library', {}).get('slug', False)
                if slug:
                    update.update({'slug': slug})

        return update

    @api.model
    def create(self, vals):
        slug = vals.get("slug", False)
        if not slug:
            name = vals.get("name")
            vals.update({"slug": name.lower().replace(" ", "_")})

        return super(CenitLibrary, self).create(vals)

    @api.one
    def write(self, vals):
        slug = vals.get("slug", None)
        if not slug and slug is False:
            name = vals.get("name", False)
            if not name:
                name = self.name
            vals.update({"slug": name.lower().replace(" ", "_")})

        return super(CenitLibrary, self).write(vals)


class CenitSchema(models.Model):

    @api.one
    def cenit_root(self):
        # return "%s/%s" % (self.library.slug or "odoo", self.slug)
        return self.slug

    _name = 'cenit.schema'
    _inherit = 'cenit.api'

    cenit_model = 'data_type'
    cenit_models = 'data_types'

    cenitID = fields.Char('Cenit ID')

    #library = fields.Many2one('cenit.library', string='Library',
                             # ondelete='cascade')
    slug = fields.Char('Slug', required=True)
    schema = fields.Text('Schema')

    name = fields.Char('Name')
    namespace = fields.Many2one('cenit.namespace', string='Namespace', required=True,
                              ondelete='cascade')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(namespace,name)',
         'The name must be unique for each namespace!'),
        ('slug_uniq', 'UNIQUE(namespace,slug)',
         'The slug must be unique for each namespace!'),
    ]

    @api.one
    def _get_values(self):
        vals = {
            #'library': {
             #   '_reference': True,
               # 'id': self.library.cenitID
           # },
           'namespace': {
                 '_reference': True,
                 'id': self.namespace.cenitID
            },
            'name': self.name,
            'slug': self.slug,
            'schema': self.schema,
            '_type': 'Setup::JsonDataType',
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

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


class CenitDataTypeTrigger(models.Model):
    _name = "cenit.data_type.trigger"

    data_type = fields.Many2one("cenit.data_type", "Data Type")
    name = fields.Selection([
        ("on_create", "On creation"),
        ("on_write", "On update"),
        ("on_create_or_write", "On creation or update"),
        ("interval", "On interval"),
        ("only_manual", "Only manually"),
    ], required=True)

    cron = fields.Many2one('ir.cron', string='Cron rules')
    cron_lapse = fields.Integer("Interval number", default=10)
    cron_units = fields.Selection([
        ('minutes', 'Minutes'), ('hours', 'Hours'), ('work_days', 'Work Days'),
        ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')
    ], string="Interval units", default='minutes')
    cron_restrictions = fields.Selection([
        ("create", "Newly created"), ("update", "Newly updated"), ("all", "All")
    ], string="Restrictions", default="all")
    base_action_rules = fields.Many2many(
        'base.action.rule', string='Action Rules'
    )

    last_execution = fields.Datetime()
    
    @api.one
    def unlink(self):
        if self.cron:
            self.cron.unlink()
        if self.base_action_rules:
            for bar in self.base_action_rules:
                bar.server_action_ids.unlink()
            self.base_action_rules.unlink()
        
        return super(CenitDataTypeTrigger, self).unlink()

    @api.one
    def sync(self):
        if not self.data_type.enabled:
            if self.cron:
                self.cron.unlink()
            if self.base_action_rules:
                for bar in self.base_action_rules:
                    bar.server_action_ids.unlink()
                self.base_action_rules.unlink()

        if self.name == 'only_manual':

            if self.base_action_rules:
                for bar in self.base_action_rules:
                    bar.server_action_ids.unlink()
                self.base_action_rules.unlink()

            elif self.cron:
                self.cron.unlink()

        if self.name == 'interval':
            ic_obj = self.env['ir.cron']

            if self.cron:
                vals_ic = {
                    'name': 'send_%s_%s' % (
                        self.cron_restrictions, self.data_type.model.model),
                    'interval_number': self.cron_lapse,
                    'interval_type': self.cron_units,
                }
                _logger.info("\n\nWRITE IC: %s\n", vals_ic)
                self.cron.write(vals_ic)
            else:
                vals_ic = {
                    'name': 'send_%s_%s' % (
                        self.cron_restrictions, self.data_type.model.model),
                    'interval_number': self.cron_lapse,
                    'interval_type': self.cron_units,
                    'numbercall': -1,
                    'model': 'cenit.data_type',
                    'function': 'perform_scheduled_action',
                    'args': '(%s,)' % str(self.data_type.id)
                }
                _logger.info("\n\nCREATE IC: %s\n", vals_ic)
                ic = ic_obj.create(vals_ic)
                self.with_context(local=True).write({'cron': ic.id})

            if self.base_action_rules:
                for bar in self.base_action_rules:
                    bar.server_action_ids.unlink()
                self.base_action_rules.unlink()

        elif self.name in ('on_create', 'on_write', 'on_create_or_write'):
            ias_obj = self.env['ir.actions.server']
            bar_obj = self.env['base.action.rule']

            if self.base_action_rules:
                for bar in self.base_action_rules:
                    bar.server_action_ids.unlink()
                self.base_action_rules.unlink()

            rules = []
            action_name = 'send_one_%s_as_%s' % (
                self.data_type.model.model, self.data_type.cenit_root
            )
            cd = "self.pool.get('{}').browse(cr, uid, {}).trigger_flows(obj)".format(
                self.data_type._name,
                self.data_type.id
            )
            vals_ias = {
                'name': action_name,
                'model_id': self.data_type.model.id,
                'state': 'code',
                'code': cd
            }
            ias = ias_obj.create(vals_ias)
            vals_bar = {
                'name': action_name,
                'active': True,
                'kind': self.name,
                'model_id': self.data_type.model.id,
                'server_action_ids': [(6, False, [ias.id])]
            }
            bar = bar_obj.create(vals_bar)
            rules.append((4, bar.id, False))

            self.with_context(local=True).write(
                {'base_action_rules': rules}
            )

            if self.cron:
                self.cron.unlink()

        return True


class CenitDataType(models.Model):

    @api.onchange('namespace')
    def _on_namespace_changed(self):
        return {
            'value': {
                'schema': '',
            },
            'domain': {
                'schema': [
                    ('id', 'in', [x.id for x in self.namespace.schemas])
                ]
            }
        }

    @api.depends('schema')
    def _compute_root(self):
        self.cenit_root = self.schema.cenit_root()[0]

    _name = 'cenit.data_type'

    cenit_root = fields.Char(compute='_compute_root', store=True)

    name = fields.Char('Name', size=128, required=True)
    enabled = fields.Boolean('Enabled', default=True)
    #library = fields.Many2one('cenit.library', string='Library', required=True,
                              #ondelete='cascade')

    namespace = fields.Many2one('cenit.namespace', string='Namespace', required=True,
                              ondelete='cascade')

    model = fields.Many2one('ir.model', 'Model', required=True)
    schema = fields.Many2one('cenit.schema', 'Schema')

    lines = fields.One2many('cenit.data_type.line', 'data_type', 'Mapping')
    domain = fields.One2many('cenit.data_type.domain_line', 'data_type',
                             'Conditions')

    triggers = fields.One2many("cenit.data_type.trigger", "data_type",
                               "Trigger on")

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    @api.one
    def _get_flows(self):
        flow_pool = self.env['cenit.flow']
        if not self.search([('id', '=', self.id)]):
            return []

        domain = [
            ('schema', '=', self.schema.id),
            ('data_type', 'in', (self.id, False))
        ]
        return flow_pool.search(domain) or []

    @api.one
    def sync_rules(self):
        for trigger in self.triggers:
            trigger.sync()

    # @api.model
    # def perform_scheduled_action(self, dt_id):
    #     _logger.info("Performing scheduled trigger")
    #     dt = self.browse(dt_id)
    #
    #     flow_pool = self.env["cenit.flow"]
    #     flows = dt._get_flows()
    #     if isinstance(flows, list) and len(flows) == 1:
    #         flows = flows[0]
    #
    #     to_trigger = {
    #         "cenit": None,
    #         "other": []
    #     }
    #     for flow in flows:
    #         if flow.enabled and not flow.local and not to_trigger["cenit"]:
    #             to_trigger["cenit"] = flow.id
    #         if flow.enabled and flow.local:
    #             to_trigger["other"].append(flow.id)
    #
    #     for trigger in dt.triggers:
    #         if trigger.name != 'interval':
    #             continue
    #
    #         domain = []
    #
    #         if trigger.last_execution and (
    #            trigger.cron_restrictions == "create"):
    #             domain.append(("create_date", '>', trigger.last_execution))
    #         elif trigger.last_execution and (
    #            trigger.cron_restrictions == "update"):
    #             domain.append(("write_date", '>', trigger.last_execution))
    #
    #         trigger.last_execution = fields.Datetime.now()
    #
    #         if to_trigger["cenit"]:
    #             flow_pool.send_all(to_trigger["cenit"], dt, domain)
    #
    #         for id_ in to_trigger["other"]:
    #             flow_pool.send_all(id_, dt, domain)

    @api.one
    def trigger_flows(self, obj):
        flow_pool = self.env["cenit.flow"]
        flows = self._get_flows()
        if isinstance(flows, list) and len(flows) == 1:
            flows = flows[0]

        to_trigger = {
            "cenit": None,
            "other": []
        }
        for flow in flows:
            if flow.enabled and not flow.local and not to_trigger["cenit"]:
                to_trigger["cenit"] = flow.id
            if flow.enabled and flow.local:
                to_trigger["other"].append(flow.id)

        if to_trigger["cenit"]:
            flow_pool.send(obj, to_trigger["cenit"])

        for id_ in to_trigger["other"]:
            flow_pool.send(obj, id_)

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
        triggers = self.triggers
        res = super(CenitDataType, self).unlink()

        if res:
            for trigger in triggers:
                trigger.unlink()

        return res

    @api.one
    def get_search_domain(self):
        return [x.as_search_domain() for x in self.domain]

    @api.one
    def ensure_object(self, obj):
        rc = self.model.model == obj._name
        if not rc or not self.enabled:
            return False

        match = False
        domain = self.get_search_domain()[0]
        if domain:
            if isinstance(domain, list) and len(domain) > 1:
                domain = [item for subdomain in domain for item in subdomain]
            elif isinstance(domain[0], list):
                domain = domain[0]
            domain.append(("id", "=", obj.id))
            match = obj.search(domain) or False
        return match


class CenitDataTypeDomainLine(models.Model):
    _name = 'cenit.data_type.domain_line'

    data_type = fields.Many2one('cenit.data_type', 'Data Type')

    field = fields.Char('Field', required=True)
    value = fields.Char('Value', required=True)

    op = fields.Selection(
        [
            ('=', 'Equal'),
            ('!=', 'Different'),
            ('in', 'In'),
            ('not in', 'Not in'),
        ],
        'Condition', required=True
    )

    @api.one
    def as_search_domain(self):
        value = self.value
        if self.op in ("in", "not in"):
            value = value.split(",")
        return self.field, self.op, value


class CenitDataTypeLine(models.Model):
    _name = 'cenit.data_type.line'

    data_type = fields.Many2one('cenit.data_type', 'Data Type')

    name = fields.Char('Name', required=True)
    value = fields.Char('Value', required=True)

    line_type = fields.Selection(
        [
            ('field', 'Field'),
            ('model', 'Model'),
            ('reference', 'Reference'),
            ('default', 'Default'),
            ('code', 'Python code'),
        ],
        'Type', required=True
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
    inlined = fields.Boolean('Inlined')

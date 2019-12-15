#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# collection.py
#
# Copyright 2015 D.H. Bahr <dhbahr@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
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

import logging, os
import json
import base64

from odoo import models, api, exceptions

_logger = logging.getLogger(__name__)


class CollectionInstaller(models.TransientModel):
    """
       Class to install Cenit collections
    """
    _name = "cenit.collection.installer"
    _description = 'Collection installer'

    @api.model
    def _install_namespaces(self, values, data_types_list, snippets_list):
        namespace_pool = self.env['cenit.namespace']
        schema_pool = self.env['cenit.schema']

        for namespace in values:
            namespace_data = {
                'cenitID': namespace.get('id'),
                'name': namespace.get('name'),
                'slug': namespace.get('slug'),
            }

            domain = [('name', '=', namespace_data.get('name'))]
            candidates = namespace_pool.search(domain)
            if not candidates:
                nam = namespace_pool.with_context(local=True).create(
                    namespace_data)
            else:
                nam = candidates[0]
                nam.with_context(local=True).write(namespace_data)

            values = (x for x in data_types_list if
                      (x['namespace'] == nam.name) and 'snippet' in x)

            for schema in values:
                schema_code = self.get_snippetcode(schema['snippet']['name'], snippets_list)

                sch_data = {
                    'cenitID': schema.get('id'),
                    'name': schema.get('name'),
                    'slug': schema.get('slug'),
                    'schema': schema_code.encode('utf-8'),
                    'namespace': nam.id
                }

                domain = [('name', '=', sch_data.get('name')),
                          ('namespace', '=', sch_data.get('namespace'))]

                candidates = schema_pool.search(domain)

                if not candidates:
                    schema_pool.with_context(local=True).create(sch_data)
                else:
                    sch = candidates[0]
                    sch.with_context(local=True).write(sch_data)

        candidates = namespace_pool.search([('name', '=', 'Odoo')])
        if not candidates:
            names_data = {
                "name": "Odoo",
                "slug": "odoo",
            }
            namespace_pool.with_context(local=True).create(names_data)

    @api.model
    def _get_operations(self, ref_id, values):
        operations = values.get('operations', [])
        oper = []

        for operation in operations:
            if not operation.get('resource'):
                continue

            operation_data = {
                'method': operation.get('method'),
                'resource_id': ref_id,
                'cenitID': operation.get('id')
            }
            oper.append([0, False, operation_data])

        rc = {
            'operations': oper
        }

        return rc

    @api.model
    def _get_param_lines(self, ref_id, values, prefix):
        parameter_pool = self.env['cenit.parameter']

        url = []
        header = []
        template = []

        params = {
            'parameters': url,
            'headers': header,
            'template_parameters': template,
        }

        fields = {
            'parameters': '%s_url_id' % (prefix,),
            'headers': '%s_header_id' % (prefix,),
            'template_parameters': '%s_template_id' % (prefix,),
        }

        for key in ('parameters', 'headers', 'template_parameters'):
            vals = values.get(key, [])
            field = fields.get(key)
            if not hasattr(parameter_pool, field):
                continue
            param = params.get(key)

            strict_keys = []

            for entry in vals:
                if not entry.get('key'):
                    continue

                domain = [
                    ('key', '=', entry.get('key')),
                    (field, '=', ref_id),
                ]
                candidates = parameter_pool.search(domain)

                param_data = {
                    'key': entry.get('key'),
                    'value': entry.get('value')
                }

                if not candidates:
                    param.append([0, False, param_data])
                else:
                    p = candidates[0]
                    param.append([1, p.id, param_data])

                strict_keys.append(param_data.get('key'))

            domain = [
                ('key', 'not in', strict_keys),
                (field, '=', ref_id),
            ]

            left_overs = parameter_pool.search(domain)
            for entry in left_overs:
                param.append([2, entry.id, False])

        rc = {
            'url_parameters': params.get('parameters'),
            'header_parameters': params.get('headers'),
            'template_parameters': params.get('template_parameters'),
        }

        return rc

    @api.model
    def _install_connections(self, values):
        connection_pool = self.env['cenit.connection']
        names_pool = self.env['cenit.namespace']
        cenit_api = self.env['cenit.api']

        for connection in values:
            if connection.get('id'):
                path = "/setup/connection/%s.json" % (connection.get('id'),)
                rc = cenit_api.get(path)
                conn_data = {
                    'cenitID': rc.get('id'),
                    'name': rc.get('name'),
                    'url': rc.get('url'),
                    'key': rc.get('number'),
                    'token': rc.get('token'),
                }
            else:
                conn_data = {
                    'cenitID': connection.get('id'),
                    'name': connection.get('name'),
                    'url': connection.get('url'),
                    'key': connection.get('number'),
                    'token': connection.get('token'),
                }

            domain = [('name', '=', connection.get('namespace'))]
            rc = names_pool.search(domain)
            conn_data.update({
                'namespace': rc[0].id
            })

            domain = [('name', '=', conn_data.get('name')),
                      ('namespace', '=', conn_data.get('namespace'))]
            candidates = connection_pool.search(domain)

            if not candidates:
                conn = connection_pool.with_context(local=True).create(
                    conn_data
                )
            else:
                conn = candidates[0]
                conn.with_context(local=True).write(conn_data)

            conn_params = self._get_param_lines(conn.id, connection, "conn")
            conn.with_context(local=True).write(conn_params)

    @api.model
    def _install_resources(self, values):
        resource_pool = self.env['cenit.resource']
        names_pool = self.env['cenit.namespace']

        for resource in values:
            resource_data = {
                'cenitID': resource.get('id'),
                'name': resource.get('name'),
                'path': resource.get('path'),
                'description': resource.get('description'),
            }

            domain = [('name', '=', resource.get('namespace'))]
            candidates = names_pool.search(domain)
            if not candidates:
                raise exceptions.ValidationError(
                    "There's no namespace named %s" % (
                        resource.get('namespace'),))

            resource_data.update({
                'namespace': candidates[0].id
            })

            domain = [('name', '=', resource_data.get('name')),
                      ('namespace', '=', resource_data.get('namespace'))]
            candidates = resource_pool.search(domain)

            if not candidates:
                res = resource_pool.with_context(local=True).create(resource_data)
            else:
                res = candidates[0]
                res.with_context(local=True).write(resource_data)

            resource_params = self._get_param_lines(res.id, resource, "resource")
            res.with_context(local=True).write(resource_params)

            resource_operations = self._get_operations(res.id, resource)
            res.with_context(local=True).write(resource_operations)

    @api.model
    def _install_webhooks(self, values):
        webhook_pool = self.env['cenit.webhook']
        names_pool = self.env['cenit.namespace']

        for webhook in values:
            hook_data = {
                'cenitID': webhook.get('id'),
                'name': webhook.get('name'),
                'path': webhook.get('path'),
                'method': webhook.get('method'),
                'purpose': webhook.get('purpose'),
            }

            domain = [('name', '=', webhook.get('namespace'))]
            candidates = names_pool.search(domain)
            if not candidates:
                raise exceptions.ValidationError(
                    "There's no namespace named %s" % (
                        webhook.get('namespace'),))

            hook_data.update({
                'namespace': candidates[0].id
            })

            domain = [('name', '=', hook_data.get('name')),
                      ('namespace', '=', hook_data.get('namespace'))]
            candidates = webhook_pool.search(domain)

            if not candidates:
                hook = webhook_pool.with_context(local=True).create(
                    hook_data
                )
            else:
                hook = candidates[0]
                hook.with_context(local=True).write(hook_data)

            hook_params = self._get_param_lines(hook.id, webhook, "hook")
            hook.with_context(local=True).write(hook_params)

    @api.model
    def _install_connection_roles(self, values):
        role_pool = self.env['cenit.connection.role']
        conn_pool = self.env['cenit.connection']
        hook_pool = self.env['cenit.webhook']
        oper_pool = self.env['cenit.operation']
        resr_pool = self.env['cenit.resource']
        names_pool = self.env['cenit.namespace']

        for role in values:
            role_data = {
                'cenitID': role.get('id'),
                'name': role.get('name')
            }

            domain = [('name', '=', role.get('namespace'))]
            candidates = names_pool.search(domain)
            if not candidates:
                raise exceptions.ValidationError(
                    "There's no namespace named %s" % (role.get('namespace'),))

            role_data.update({
                'namespace': candidates[0].id
            })

            domain = [('name', '=', role_data.get('name')),
                      ('namespace', '=', role_data.get('namespace'))]
            candidates = role_pool.search(domain)

            if not candidates:
                crole = role_pool.with_context(local=True).create(role_data)
            else:
                crole = candidates[0]
                crole.with_context(local=True).write(role_data)

            connections = []
            webhooks = []

            for connection in role.get('connections', []):
                domain = [('name', '=', connection.get('name')),
                          ('namespace', '=', connection.get('namespace'))]
                candidates = conn_pool.search(domain)

                if candidates:
                    conn = candidates[0]
                    connections.append(conn.id)

            for webhook in role.get('webhooks', []):
                domain = [('name', '=', webhook.get('name')),
                          ('namespace', '=', webhook.get('namespace'))]
                candidates = hook_pool.search(domain)
                type = 'webhooks'
                if not candidates:
                    resource = resr_pool.search([
                        ('namespace', '=', webhook.get('resource', []).get('namespace')),
                        ('name', '=', webhook.get('resource', []).get('name'))
                    ])
                    domain = [('resource_id', '=', resource.id), ('method', '=', webhook.get('method'))]
                    candidates = oper_pool.search(domain)
                    type = 'operations'

                if candidates:
                    hook = candidates[0]
                    webhooks.append(hook.id)

            role_members = {
                'connections': [(6, False, connections)],
                type: [(6, False, webhooks)],
            }
            crole.with_context(local=True).write(role_members)

    @api.model
    def _install_flows(self, values):
        flow_pool = self.env['cenit.flow']
        names_pool = self.env['cenit.namespace']
        sch_pool = self.env['cenit.schema']
        hook_pool = self.env['cenit.webhook']
        oper_pool = self.env['cenit.operation']
        role_pool = self.env['cenit.connection.role']
        ev_pool = self.env['cenit.event']
        trans_pool = self.env['cenit.translator']

        for flow in values:
            flow_data = {
                'cenitID': flow.get('id'),
                'name': flow.get('name'),
                'enabled': flow.get('active', False),
                'format_': 'application/json',
            }

            # Updating namespace in flow
            domain = [('name', '=', flow.get('namespace'))]
            rc = names_pool.search(domain)
            if not rc:
                raise exceptions.ValidationError("There's no namespace named %s" % (flow.get('namespace'),))

            flow_data.update({
                'namespace': rc[0].id
            })

            # Updating translator
            trans = flow.get('translator')
            namesp = names_pool.search([('name', '=', trans.get('namespace'))])
            rc = trans_pool.search([('name', '=', trans.get('name')),
                                    ('namespace', '=', namesp[0].id)])
            if not rc:
                continue

            flow_data.update({
                'cenit_translator': rc[0].id
            })

            # Updating schema
            sch_updated = False
            dt = {}
            if rc[0].schema:
                flow_data.update({'schema': rc[0].schema.id})
                sch_updated = True
            elif 'custom_data_type' in flow:
                dt = flow.get('custom_data_type')
            else:
                dt = flow.get('target_data_type')

            if not sch_updated:
                if not dt:
                    continue

                rc = names_pool.search([('name', '=', dt.get('namespace'))])
                sch = sch_pool.search([('name', '=', dt.get('name')),
                                       ('namespace', '=', rc[0].id)])
                if not sch:
                    raise exceptions.ValidationError(
                        "There's no definition of a \'%s\' data type in this collection" % (dt.get('name')))

                flow_data.update({
                    'schema': sch[0].id
                })

            # Updating event in Flow
            if 'event' in flow:
                ev = flow.get('event', {})
                namesp = names_pool.search([('name', '=', ev.get('namespace'))])
                rc = ev_pool.search([('name', '=', ev.get('name')),
                                     ('namespace', '=', namesp[0].id)])
                if not rc:
                    raise exceptions.ValidationError(
                        "There's no definition of an \'%s\' event in this collection" % (ev.get('name')))

                flow_data.update({
                    'event': rc[0].id
                })

            # Updating webhook
            hook = flow.get('webhook', {})
            if hook:
                namesp = names_pool.search([('name', '=', hook.get('namespace'))])
                domain = [('name', '=', hook.get('name')), ('namespace', '=', namesp.id)]
                rc = hook_pool.search(domain)
                if not rc:
                    domain = ([('resource_id.namespace', '=', hook['resource']['namespace']),
                                    ('resource_id.name', '=', hook['resource']['name']),
                                    ('method', '=', hook.get('method'))]
)
                    rc = oper_pool.search(domain)
                    if not rc:
                        continue
                flow_data.update({
                    'webhook': rc._name + ',' + str(rc.id)
                })

            # Updating role
            if 'connection_role' in flow:
                role = flow.get('connection_role', {})
                namesp = names_pool.search(
                    [('name', '=', role.get('namespace'))])
                domain = [('name', '=', role.get('name')),
                          ('namespace', '=', namesp[0].id)]
                rc = role_pool.search(domain)
                if rc:
                    flow_data.update({
                        'connection_role': rc[0].id
                    })

            domain = [
                ('name', '=', flow_data.get('name')),
                ('namespace', '=', flow_data.get('namespace')),
                '|',
                ('enabled', '=', True),
                ('enabled', '=', False),
            ]
            candidates = flow_pool.search(domain)

            if not candidates:
                flow = flow_pool.with_context(local=True).create(flow_data)
            else:
                flow = candidates[0]
                flow.with_context(local=True).write(flow_data)

    @api.model
    def _install_translators(self, values):
        trans_pool = self.env['cenit.translator']
        sch_pool = self.env['cenit.schema']
        names_pool = self.env['cenit.namespace']
        translators_types = (
            # Template (Export)
            "Setup::LiquidTemplate",  # 'liquid'
            "Setup::XsltTemplate",  # 'xslt'
            "Setup::ErbTemplate",  # 'html.erb' and 'js.erb'
            "Setup::RubyTemplate",  # 'ruby'
            "Setup::ErbTemplate",  # 'js.erb'
            "Setup::PrawnTemplate",  # 'pdf.prawn'

            # Converter (Conversion)
            "Setup::LiquidConverter",  # 'liquid'
            "Setup::XsltConverter",  # 'xslt'
            "Setup::RubyConverter",  # 'ruby'
            "Setup::MappingConverter",  # 'mapping'

            # Parser (Import)
            "Setup::RubyParser",  # 'ruby'

            # Updater (Update)
            "Setup::RubyUpdater",  # 'ruby'
        )

        for translator in values:
            if translator.get('_type') not in translators_types:
                continue
            trans_data = {
                'cenitID': translator.get('id'),
                'name': translator.get('name'),
                'type_': translator.get('type'),
                'mime_type': translator.get('mime_type', False)
            }

            # Updating namespace for translator
            rc = names_pool.search([('name', '=', translator.get('namespace'))])
            if not rc:
                raise exceptions.ValidationError(
                    "There's no namespace named %s" % (
                        translator.get('namespace'),))

            trans_data.update({
                'namespace': rc[0].id
            })

            # Updating schema
            schema = translator.get({
                                        'Setup::RubyParser': 'target_data_type',
                                        'Setup::RubyTemplate': 'source_data_type',
                                    }.get(translator.get('_type')), {})

            if schema:
                namesp = names_pool.search(
                    [('name', '=', schema.get('namespace'))])
                domain = [
                    ('name', '=', schema.get('name')),
                    ('namespace', '=', namesp[0].id)
                ]
                candidates = sch_pool.search(domain)
                if candidates:
                    schema_id = candidates[0].id or False

                    trans_data.update({
                        'schema': schema_id
                    })

            domain = [('name', '=', trans_data.get('name')),
                      ('namespace', '=', trans_data.get('namespace'))]
            candidates = trans_pool.search(domain)
            if not candidates:
                trans_pool.with_context(local=True).create(trans_data)
            else:
                candidates[0].with_context(local=True).write(trans_data)

    @api.model
    def _install_events(self, values):
        ev_pool = self.env['cenit.event']
        sch_pool = self.env['cenit.schema']
        names_pool = self.env['cenit.namespace']

        for event in values:
            ev_data = {
                'cenitID': event.get('id'),
                'name': event.get('name'),
                'type_': event.get('_type'),
            }

            domain = [('name', '=', event.get('namespace'))]
            rc = names_pool.search(domain)
            ev_data.update({
                'namespace': rc[0].id
            })

            schema = event.get('data_type', {})
            schema_id = False
            if schema:
                domain = [
                    ('name', '=', schema.get('name')),
                    ('namespace', '=', rc[0].id)
                ]
                candidates = sch_pool.search(domain)
                if candidates:
                    schema_id = candidates[0].id

            ev_data.update({
                'schema': schema_id
            })

            domain = [('name', '=', ev_data.get('name')),
                      ('namespace', '=', ev_data.get('namespace'))]
            candidates = ev_pool.search(domain)
            if not candidates:
                ev_pool.with_context(local=True).create(ev_data)
            else:
                candidates[0].with_context(local=True).write(ev_data)

    @api.model
    def _install_dummy(self, values):
        pass

    @api.model
    def get_collection_data(self, name, version=None):
        cenit_api = self.env['cenit.api']

        args = {
            'name': name,
        }
        if not version:
            args.update({
                'sort_by': 'shared_version',
                'limit': 1
            })
        else:
            args.update({
                'shared_version': version
            })

        path = "/setup/cross_shared_collection"
        rc = cenit_api.get(path, params=args).get("cross_shared_collections", False)

        if not isinstance(rc, list):
            raise exceptions.ValidationError(
                "Hey!! something wicked just happened"
            )
        elif len(rc) != 1:
            raise exceptions.MissingError(
                "Required '%s [%s]' not found in Cenit" % (
                    name, version or "any"
                )
            )
        cross_id = rc[0]['id']
        path = "/setup/cross_shared_collection/%s" % (cross_id)
        rc = cenit_api.get(path)

        return rc

    """
      Pull a shared collection given an identifier
    """

    @api.model
    def pull_shared_collection(self, cenit_id, params=None):
        cenit_api = self.env['cenit.api']

        path = "/setup/cross_shared_collection/%s/pull" % (cenit_id,)

        data = {}
        if params:
            data.update({'pull_parameters': params, 'asynchronous': True, 'skip_pull_review': True})
        else:
            data.update({'asynchronous': True, 'skip_pull_review': True})
        rc = cenit_api.post(path, data)

    """
     Install data from a collection given the identifier or the name
    """

    @api.model
    def install_collection(self, params=None):
        cenit_api = self.env['cenit.api']

        if params:
            key = list(params.keys())[0]
            if key == 'id':
                path = "/setup/collection.json"
                path = "%s/%s" % (path, params.get(key))
            else:
                path = "/setup/collection.json?"
                path = "%s%s=%s" % (path, key, params.get(key))

        rc = cenit_api.get(path)
        if isinstance(rc, list):
            rc = rc[0]
        data = rc
        if 'collections' in data and len(data['collections']):
            data = data['collections'][0]

        if not params:
            raise exceptions.ValidationError(
                "Cenit failed to install the collection")

        self.install_common_data(data)

        return True

    '''
    Install data either from cross shared collection or collection
    '''

    @api.model
    def install_common_data(self, data, basepath=False):

        keys = (
            'translators', 'events',
            'connections', 'webhooks', 'resources', 'connection_roles'
        )

        self._install_namespaces(data.get('namespaces', []),
                                 data.get('data_types', []),
                                 data.get('snippets', []))

        for key in keys:
            values = data.get(key, {})
            {
                'connections': self._install_connections,
                'connection_roles': self._install_connection_roles,
                'events': self._install_events,
                'translators': self._install_translators,
                'webhooks': self._install_webhooks,
                'resources': self._install_resources
            }.get(key, self._install_dummy)(values)

        if data.get('flows', False):
            self._install_flows(data.get('flows'))
        self._install_mapping(basepath)

    '''
       Returns the snippet's code given the name
    '''

    def get_snippetcode(self, name, snippets_list):
        code = None
        found = False
        i = 0
        while i < len(snippets_list) and not found:
            if snippets_list[i]['name'] == name:
                code = snippets_list[i]['code']
                found = True
            else:
                i += 1
        return code

    '''
       Installs default mappings
    '''
    def _install_mapping(self, basepath):
        if basepath:
            filepath = os.path.abspath(os.path.join(basepath, "..", "data/mappings.json"))
            with open(filepath) as json_file:
                cenit_import_export = self.env['cenit.import_export']
                cenit_import_export.import_mappings_data(json.load(json_file))
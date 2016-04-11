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

import logging
import simplejson
import json

from openerp import models, api, exceptions

_logger = logging.getLogger(__name__)


class CollectionInstaller(models.TransientModel):
    _name = "cenit.collection.installer"

    @api.model
    def _install_namespaces(self, values, data_types_list):
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
                nam = namespace_pool.with_context(local=True).create(namespace_data)
            else:
                nam = candidates[0]
                nam.with_context(local=True).write(namespace_data)

            values = (x for x in data_types_list if (x['namespace'] == nam.name))
            for schema in values:
                sch_data = {
                    'cenitID': schema.get('id'),
                    'name': schema.get('name'),
                    'slug': schema.get('slug'),
                    'schema': simplejson.dumps(schema.get('schema')),
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

        for connection in values:
            conn_data = {
                'cenitID': connection.get('id'),
                'name': connection.get('name'),
                # 'namespace': connection.get('namespace'),
                'url': connection.get('url'),
                'key': connection.get('number'),
                'token': connection.get('token'),
            }

            #domain = [('name', '=', conn_data.get('namespace'))]
            # rc = names_pool.search(domain)
            # conn_data.update({
            #     'namespace': rc[0].id
            # })

            domain = [('name', '=', conn_data.get('name'))]
            #          ('namespace', '=', conn_data.get('namespace'))]
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
    def _install_webhooks(self, values):
        webhook_pool = self.env['cenit.webhook']
        names_pool = self.env['cenit.namespace']

        for webhook in values:
            hook_data = {
                'cenitID': webhook.get('id'),
                'name': webhook.get('name'),
                # 'namespace': webhook.get('namespace'),
                'path': webhook.get('path'),
                'method': webhook.get('method'),
                'purpose': webhook.get('purpose'),
            }

            # domain = [('name', '=', hook_data.get('namespace'))]
            # rc = names_pool.search(domain)
            ## hook_data.update({
            #     'namespace': rc[0].id
            # })

            domain = [('name', '=', hook_data.get('name'))]
            #  ('namespace', '=', hook_data.get('namespace'))]
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
        names_pool = self.env['cenit.namespace']

        for role in values:
            role_data = {
                'cenitID': role.get('id'),
                'name': role.get('name')
                # 'namespace': role.get('namespace'),
            }

            # domain = [('name', '=', role_data.get('namespace'))]
            # rc = names_pool.search(domain)
            # role_data.update({
            #     'namespace': rc[0].id
            # })

            domain = [('name', '=', role_data.get('name'))]
            # ('namespace', '=', role_data.get('namespace'))]
            candidates = role_pool.search(domain)

            if not candidates:
                crole = role_pool.with_context(local=True).create(role_data)
            else:
                crole = candidates[0]
                crole.with_context(local=True).write(role_data)

            connections = []
            webhooks = []

            for connection in role.get('connections', []):
                domain = [('name', '=', connection.get('name'))]
                #  ('namespace', '=', connection.get('namespace'))]
                candidates = conn_pool.search(domain)

                if candidates:
                    conn = candidates[0]
                    connections.append(conn.id)

            for webhook in role.get('webhooks', []):
                domain = [('name', '=', webhook.get('name'))]
                #    ('namespace', '=', webhook.get('namespace'))]
                candidates = hook_pool.search(domain)

                if candidates:
                    hook = candidates[0]
                    webhooks.append(hook.id)

            role_members = {
                'connections': [(6, False, connections)],
                'webhooks': [(6, False, webhooks)],
            }
            crole.with_context(local=True).write(role_members)

    @api.model
    def _install_flows(self, values):
        flow_pool = self.env['cenit.flow']
        #lib_pool = self.env['cenit.library']
        names_pool = self.env['cenit.namespace']
        sch_pool = self.env['cenit.schema']
        hook_pool = self.env['cenit.webhook']
        role_pool = self.env['cenit.connection.role']
        ev_pool = self.env['cenit.event']
        trans_pool = self.env['cenit.translator']

        for flow in values:
            flow_data = {
                'cenitID': flow.get('id'),
                'name': flow.get('name'),
                # 'namespace': flow.get('namespace'),
                'enabled': flow.get('active', False),
                'format_': 'application/json',
            }

            #domain = [('name', '=', flow_data.get('namespace'))]
            # rc = names_pool.search(domain)
            #  flow_data.update({
            #      'namespace': rc[0].id
            #  })

            dt = flow.get('custom_data_type', {})
            schema = dt.get('name', '')
            #library = dt.get('library', {})
            #namespace = dt.get('namespace', {})

            dt_deferred = False
            # if not rc:
            #dt_deferred = True

            if not dt_deferred:
                domain = [
                    ('name', '=', schema)
                    #  ('namespace', '=', rc[0].id)
                ]
                rc = sch_pool.search(domain)
                if not rc:
                    continue
                flow_data.update({
                    'schema': rc[0].id
                })

            ev = flow.get('event', {})
            domain = [('name', '=', ev.get('name'))]
            #  ('namespace', '=', ev.get('namespace'))]
            rc = ev_pool.search(domain)
            if not rc:
                continue
            flow_data.update({
                'event': rc[0].id
            })

            trans = flow.get('translator', {})
            domain = [('name', '=', trans.get('name'))]
            # ('namespace', '=', trans.get('namespace'))]
            rc = trans_pool.search(domain)
            if not rc:
                continue

            if dt_deferred:
                if not rc[0].schema:
                    continue
                flow_data.update({
                    'schema': rc[0].schema.id
                })

            flow_data.update({
                'cenit_translator': rc[0].id
            })

            hook = flow.get('webhook', {})
            domain = [('name', '=', hook.get('name'))]
            #  ('namespace', '=', hook.get('namespace'))]
            rc = hook_pool.search(domain)
            if not rc:
                continue
            flow_data.update({
                'webhook': rc[0].id
            })

            role = flow.get('connection_role', {})
            domain = [('name', '=', role.get('name'))]
            #  ('namespace', '=', role.get('namespace'))]
            rc = role_pool.search(domain)
            if rc:
                flow_data.update({
                    'connection_role': rc[0].id
                })

            domain = [
                ('name', '=', flow_data.get('name')),
                # ('namespace', '=', flow_data.get('namespace')),
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

        for translator in values:
            if translator.get('type') not in ('Import', 'Export'):
                continue
            trans_data = {
                'cenitID': translator.get('id'),
                'name': translator.get('name'),
                #  'namespace': translator.get('namespace'),
                'type_': translator.get('type'),
                'mime_type': translator.get('mime_type', False)
            }

            schema = translator.get({
                                        'Import': 'target_data_type',
                                        'Export': 'source_data_type',
                                    }.get(translator.get('type')), {})

            schema_id = False
            if schema:
                domain = [
                    ('name', '=', schema.get('name'))
                    #   ('namespace', '=', schema.get('namespace'))
                ]
                candidates = sch_pool.search(domain)
                if candidates:
                    schema_id = candidates[0].id

            trans_data.update({
                'schema': schema_id
            })

            # domain = [('name', '=', trans_data.get('namespace'))]
            # rc = names_pool.search(domain)
            # trans_data.update({
            #     'namespace': rc[0].id
            # })

            domain = [('name', '=', trans_data.get('name'))]
            #('namespace', '=', trans_data.get('namespace'))]
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
                # 'namespace': event.get('namespace'),
                'type_': event.get('_type'),
            }

            # domain = [('name', '=', ev_data.get('namespace'))]
            # rc = names_pool.search(domain)
            # ev_data.update({
            #     'namespace': rc[0].id
            # })

            schema = event.get('data_type', {})
            schema_id = False
            if schema:
                domain = [
                    ('name', '=', schema.get('name'))
                    # ('library.name', '=', schema.get('library').get('name'))
                ]
                candidates = sch_pool.search(domain)
                if candidates:
                    schema_id = candidates[0].id

            ev_data.update({
                'schema': schema_id
            })

            domain = [('name', '=', ev_data.get('name'))]
            #          ('namespace', '=', ev_data.get('namespace'))]
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

        path = "/setup/shared_collection"
        rc = cenit_api.get(path, params=args).get("shared_collection", False)

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

        rc = rc[0]

        data = {
            'id': rc.get('id'),
            'params': rc.get('pull_parameters', [])
        }

        return data

    @api.model
    def install_collection(self, cenit_id, params=None):
        cenit_api = self.env['cenit.api']

        path = "/setup/shared_collection/%s/pull" % (cenit_id,)

        data = {}
        if params:
            data.update({'pull_parameters': params})
        rc = cenit_api.post(path, data)

        coll_id = rc.get('collection', {}).get('id', False)
        path = "/setup/collection"
        if coll_id:
            path = "%s/%s" % (path, coll_id)

        rc = cenit_api.get(path)
        if isinstance(rc, list):
            rc = rc[0]
        data = rc  #.get('collection', {})[0]

        if not coll_id:
            for entry in rc.get('collection', []):
                if entry.get('name', False) == self.env.context.get("coll_name",
                                                                    None):
                    data = entry
                    break

        keys = (
            'translators', 'events',
            'connections', 'webhooks', 'connection_roles'
        )

        self._install_namespaces(data.get('namespaces'), data.get('data_types', []))

        for key in keys:
            values = data.get(key, {})
            {
                'connections': self._install_connections,
                'connection_roles': self._install_connection_roles,
                'events': self._install_events,
                'translators': self._install_translators,
                'webhooks': self._install_webhooks,
            }.get(key, self._install_dummy)(values)

        if data.get('flows', False):
            self._install_flows(data.get('flows'))

        return True



import logging
import json

from openerp import api, exceptions, http
from openerp.osv import orm, fields

from openerp.http import request
from openerp.addons.web.controllers.main import serialize_exception, content_disposition
import base64

_logger = logging.getLogger(__name__)


class ImportExport(orm.TransientModel):
    _name = "cenit.import_export"

    _columns = {
        'file': fields.binary('File'),
        'filename': fields.char()
    }

    @api.multi
    def export_data_types(self, context={}):
        datatype_pool = self.env['cenit.data_type']

        selected_data = context['active_ids']
        result = []
        for id_data in selected_data:
            domain = [("id", '=', id_data)]
            result.append(datatype_pool.search(domain))

        datatypes = []

        for r in result:
            lines = []
            for line in r.lines:
                lines.append({"name": line.name, "value": line.value, "line_type": line.line_type,
                              "line_cardinality": line.line_cardinality if line.line_cardinality else None,
                              "reference": line.reference.name if line.reference else None,
                              "primary": line.primary, "inlined": line.inlined})

            domains = []
            for domain in r.domain:
                domains.append({"field": domain.field, "value": domain.value, "op": domain.op})

            triggers = []
            for trigger in r.triggers:
                cron_lapse = str(trigger.cron_lapse)
                triggers.append({"name": trigger.name, "cron_name": trigger.cron.name, "cron_lapse": cron_lapse,
                                 "cron_units": trigger.cron_units, "cron_restrictions": trigger.cron_restrictions})

            datatypes.append({"name": r.name, "model": r.model.model, "namespace": r.namespace.name,
                              "schema": r.schema.name, "lines": lines, "domains": domains, "triggers": triggers})

        json_data = json.dumps(datatypes)
        file_c = self.create({
            'filename': 'mappings.json',
            'file': json_data
        })

        return {
             'type' : 'ir.actions.act_url',
             'url': '/web/binary/download_document?file=%s&filename=data_types.json' % (file_c.file),
             'target': 'self',
        }


    @api.model
    def import_data_types(self, context={}):
        data_file = self._context['attachment']
        irmodel_pool = self.env['ir.model']
        schema_pool = self.env['cenit.schema']
        namespace_pool = self.env['cenit.namespace']
        datatype_pool = self.env['cenit.data_type']
        line_pool = self.env['cenit.data_type.line']
        domain_pool = self.env['cenit.data_type.domain_line']
        trigger_pool = self.env['cenit.data_type.trigger']

        data_file = base64.decodestring(data_file)
        json_data = json.loads(data_file)

        for data in json_data:
            odoo_model = data['model']
            namespace = data['namespace']
            schema = data['schema']

            domain = [('model', '=', odoo_model)]
            candidates = irmodel_pool.search(domain)
            if not candidates:
                raise exceptions.MissingError(
                    "There is no %s module installed" % odoo_model
                )
            odoo_model = candidates.id

            domain = [('name', '=', namespace)]
            candidates = namespace_pool.search(domain)
            if not candidates:
                raise exceptions.MissingError(
                    "There is no %s namespace in Namespaces" % namespace
                )
            namespace = candidates.id

            domain = [('name', '=', schema)]
            candidates = schema_pool.search(domain)
            if not candidates:
                raise exceptions.MissingError(
                    "There is no %s schema in Schemas" % schema
                )
            schema = candidates.id

            vals = {'name': data['name'], 'model': odoo_model, 'namespace': namespace, 'schema': schema}
            created_datatype = datatype_pool.create(vals)

            for domain in data['domains']:
                vals = {'data_type': created_datatype.id, 'field': domain['field'], 'value': domain['value'],
                        'op': domain['op']}
                domain_pool.create(vals)

            for trigger in data['triggers']:
                vals = {'data_type': created_datatype.id, 'name': trigger['name'], 'cron_lapse': trigger['cron_lapse'],
                        'cron_units': trigger['cron_units'], 'cron_restrictions': trigger['cron_restrictions'],
                        'cron_name': trigger['cron_name']}
                trigger_pool.create(vals)

            for line in data['lines']:
                domain = [('name', '=', line['reference'])]
                candidate = datatype_pool.search(domain)
                vals = {
                    'data_type': created_datatype.id, 'name': line['name'], 'value': line['value'],
                    'line_type': line['line_type'], 'line_cardinality': line['line_cardinality'],
                    'primary': line['primary'], 'inlined': line['inlined'], 'reference': candidate.id
                }
                line_pool.create(vals)
        return True


class Binary(http.Controller):
    @http.route('/web/binary/download_document', type='http', auth="public")
    @serialize_exception
    def download_document(self, file, filename):
        if not file:
            return request.not_found()
        else:
            return request.make_response(file,
                                             [('Content-Type', 'application/octet-stream'),
                                              ('Content-Disposition', content_disposition(filename))])
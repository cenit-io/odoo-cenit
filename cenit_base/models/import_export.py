import logging
import json

from odoo import models, fields, http, api, exceptions, tools, _

from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition, binary_content
import base64
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ImportExport(models.TransientModel):
    """
      Utility to import and export data mappings in json object
    """
    _name = "cenit.import_export"
    _description = 'Import export'

    b_file = fields.Binary('File', help="JSON file to import")
    filename = fields.Char('File Name')

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

            datatypes.append({"id": r.id, "name": r.name, "model": r.model.model, "namespace": r.namespace.name,
                              "schema": r.schema.name, "lines": lines, "domains": domains, "triggers": triggers})

        json_data = json.dumps(datatypes)
        file_c = self.create({
            'filename': result[0].name + '.json' if len(result) == 1 else 'mappings.json',
            'b_file': json_data
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download/%s/%s/%s/%s' % ('cenit.import_export', file_c.id, 'b_file', 'filename'),
            'target': 'self',
        }

    @api.one
    def import_data_types(self):
        self.ensure_one()
        try:
            data_file = base64.decodebytes(self.b_file).decode("utf-8")
            json_data = json.loads(data_file)
            self.import_mappings_data(json_data)
        except Exception as e:
            _logger.exception('File unsuccessfully imported, due to format mismatch.')
            raise UserError(_(
                'File not imported due to format mismatch or a malformed file. (Valid format is .json)\n\nTechnical Details:\n%s') % tools.ustr(
                e))

    def import_mappings_data(self, json_data):
        irmodel_pool = self.env['ir.model']
        schema_pool = self.env['cenit.schema']
        namespace_pool = self.env['cenit.namespace']
        datatype_pool = self.env['cenit.data_type']
        line_pool = self.env['cenit.data_type.line']
        domain_pool = self.env['cenit.data_type.domain_line']
        trigger_pool = self.env['cenit.data_type.trigger']

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

            domain = [('name', '=', schema), ('namespace', '=', namespace)]
            candidates = schema_pool.search(domain)
            if not candidates:
                raise exceptions.MissingError(
                    "There is no %s schema in Schemas" % schema
                )
            schema = candidates.id

            vals = {'name': data['name'], 'model': odoo_model, 'namespace': namespace, 'schema': schema}
            dt = datatype_pool.search([('name', '=', data['name'])])
            updt = False
            if dt:
                dt.write(vals)
                updt = True
            else:
                dt = datatype_pool.create(vals)

            if updt:
                for d in dt.domain:
                    d.unlink()
                for d in dt.triggers:
                    d.unlink()
                for d in dt.lines:
                    d.unlink()

            for domain in data['domains']:
                vals = {'data_type': dt.id, 'field': domain['field'], 'value': domain['value'],
                        'op': domain['op']}
                domain_pool.create(vals)

            for trigger in data['triggers']:
                vals = {'data_type': dt.id, 'name': trigger['name'], 'cron_lapse': trigger['cron_lapse'],
                        'cron_units': trigger['cron_units'], 'cron_restrictions': trigger['cron_restrictions'],
                        'cron_name': trigger['cron_name']}
                trigger_pool.create(vals)

            for line in data['lines']:
                domain = [('name', '=', line['reference'])]
                candidate = datatype_pool.search(domain)
                vals = {
                    'data_type': dt.id, 'name': line['name'], 'value': line['value'],
                    'line_type': line['line_type'], 'line_cardinality': line['line_cardinality'],
                    'primary': line['primary'], 'inlined': line['inlined'], 'reference': candidate.id
                }
                line_pool.create(vals)
            dt.sync_rules()
        return True


class Binary(http.Controller):
    @http.route('/web/binary/download/<string:model>/<int:record_id>/<string:binary_field>/<string:filename_field>',
                type='http',
                auth="public")
    def download_document(self, model, record_id, binary_field, filename_field, token=None):
        if not record_id:
            return request.not_found()
        else:
            status, headers, content = binary_content(model=model, id=record_id, field=binary_field,
                                                      filename_field=filename_field, download=True)
        if status != 200:
            response = request.not_found()
        else:
            headers.append(('Content-Length', len(content)))
            response = request.make_response(content, headers)
        if token:
            response.set_cookie('fileToken', token)
        return response

# -*- coding: utf-8 -*-

import logging
import simplejson

from openerp import models, api


_logger = logging.getLogger(__name__)


class CenitSerializer(models.TransientModel):
    _name = 'cenit.serializer'

    @api.model
    def _get_checker (self, schema_type):
        return {
            'integer': int,
            'number': float,
            'boolean': bool,
        }.get (schema_type['type'], str)

    @api.model
    def find_reference(self, field, obj):
        model = getattr(obj, field.name)
        names = []
        for record in model:
            name = getattr(record, 'name', False)
            if not name:
                name = False
            names.append (name)

        if field.line_cardinality == "2many":
            return names

        if len(names) > 0:
            return names[0]

        return False

    @api.model
    def serialize(self, obj, data_type):
        vals = {}
        wdt = self.env['cenit.data_type']
        match = data_type.model.model == obj._name

        if match:
            schema = simplejson.loads (data_type.schema.schema) ['properties']
            _reset = []

            columns = self.env[obj._name]._columns
            for field in data_type.lines:
                if field.line_type == 'field' and getattr(obj, field.name):
                    checker = self._get_checker (schema.get (field.value))
                    vals[field.value] = checker (getattr(obj, field.name))
                elif field.line_type == 'model':
                    _reset.append(field.value)
                    relation = getattr(obj, field.name)
                    if field.line_cardinality == '2many':
                        vals[field.value] = [
                            self.serialize(x) for x in relation
                        ]
                    else:
                        vals[field.value] = self.serialize(relation)
                elif field.line_type == 'reference':
                    _reset.append(field.value)
                    vals[field.value] = self.find_reference(field, obj)
                elif field.line_type == 'default':
                    vals[field.value] = field.name

            vals.update ({
                "_reset": _reset
            })
        return vals

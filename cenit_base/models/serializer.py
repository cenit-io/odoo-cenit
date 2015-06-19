# -*- coding: utf-8 -*-

import re
import logging
import simplejson

from openerp import models, api


_logger = logging.getLogger(__name__)
re_key = re.compile("\\{(.*?)\\}")

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
    def _eval(self, obj, name):
        key = name.split(".")[0]
        try:
            rc = getattr(obj, key)
        except:
            rc = name

        return key, rc

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
                if field.line_type == 'field':
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
                    kwargs = dict([
                        (self._eval(obj, key)) for key in re_key.findall(
                            field.name
                        )
                    ])
                    _logger.info("\n\nKwArgs for %s: %s\n", field.value, kwargs)
                    vals[field.value] = field.name.format(**kwargs)

            vals.update ({
                "_reset": _reset
            })
        return vals

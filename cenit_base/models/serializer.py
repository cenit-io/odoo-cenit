# -*- coding: utf-8 -*-

import re
import logging
import simplejson
from datetime import datetime, time, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

from openerp import models, api, tools

_logger = logging.getLogger(__name__)
re_key = re.compile("\\{(.*?)\\}")


class CenitSerializer(models.TransientModel):
    _name = 'cenit.serializer'

    @api.model
    def _get_checker(self, schema_type, inlined=False):
        def get_checker(checker):
            def _do_check(obj):
                if not obj:
                    return None
                return checker(obj)

            return _do_check

        def _dummy(obj):
            return obj

        _checkers = {
            'integer': int,
            'number': float,
            'boolean': bool,
            'array': list,
            'string': str,
            'object': dict,
        }
        type_ = schema_type.get('type', 'other')
        if type_ == 'object' and inlined:
            type_ = schema_type.get('properties', {'type': 'other'}).values()[
                0].get('type', 'other')

        return get_checker(_checkers.get(type_, _dummy))

    @api.model
    def find_reference(self, field, obj):
        model = getattr(obj, field.name)
        names = []
        for record in model:
            name = getattr(record, 'name', False)
            if not name:
                name = False
            names.append(name)

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
    def _match(self, obj, data_type):
        pass

    @api.model
    def serialize(self, obj, data_type):
        vals = {}
        match = data_type.ensure_object(obj)

        if match:
            schema = simplejson.loads(data_type.schema.schema)['properties']
            _reset = []
            _primary = []

            for field in data_type.lines:
                schema_data = schema.get(field.value, {"type": "string"})
                checker = self._get_checker(schema_data, field.inlined)

                if field.primary:
                    _primary.append(field.value)

                if field.line_type == 'field':
                    vals[field.value] = checker(getattr(obj, field.name))
                elif field.line_type == 'model':
                    _reset.append(field.value)
                    relation = getattr(obj, field.name)
                    if field.line_cardinality == '2many':
                        value = [
                            self.serialize(x, field.reference) for x in relation
                        ]
                    else:
                        value = self.serialize(relation, field.reference)
                    vals[field.value] = checker(value)
                elif field.line_type == 'reference':
                    _reset.append(field.value)
                    vals[field.value] = checker(self.find_reference(field, obj))
                elif field.line_type == 'default':
                    kwargs = dict([
                        (self._eval(obj, key)) for key in re_key.findall(
                            field.name
                        )
                    ])
                    final = field.name.format(**kwargs)
                    try:
                        value = simplejson.loads(final)
                    except Exception:
                        value = final
                    vals[field.value] = checker(value)
                elif field.line_type == 'code':
                    vals[field.value] = checker(eval(field.name))

            vals.update({
                "_reset": _reset
            })

            if _primary:
                vals.update({"_primary": _primary})
        return vals

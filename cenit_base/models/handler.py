# -*- coding: utf-8 -*-

import logging

from odoo import models, api


_logger = logging.getLogger(__name__)


class CenitHandler(models.TransientModel):
    """
       Handler
    """
    _name = 'cenit.handler'

    @api.model
    def _get_checker(self, model, field):
        def get_checker(checker):
            def _do_check(obj):
                if not obj:
                    return False
                return checker(obj)

            return _do_check

        def _dummy(obj):
            return obj

        field_type = 'other'
        try:
            field_type = getattr(model, field).to_column()._type
        except:
            pass

        return get_checker({
                               'integer': int,
                               'float': float,
                               'boolean': bool,
                               'char': str,
                               'text': str,
                               'html': str,
                               'selection': str,
                               'binary': str,
                               'date': str,
                               'datetime': str,
                           }.get(field_type, _dummy))

    @api.model
    def find(self, match, params):
        model_obj = self.env[match.model.model]

        fp = [x for x in match.lines if x.primary] or False
        if fp:
            to_search = []
            for entry in fp:
                checker = self._get_checker(model_obj, entry.name)
                value = checker(params.get(entry.value, False))

                if not value:
                    continue
                to_search.append((entry.name, '=', value))

            objs = model_obj.search(to_search)
            if objs:
                return objs[0]

        return False

    @api.model
    def find_reference(self, match, field, params):
        f = [x for x in match.model.field_id if x.name == field.name][0]

        model_pool = self.env["ir.model"]
        model = model_pool.search([('model', '=', f.relation)])[0]
        model_obj = self.env[model.model]

        op = "="
        value = params.get(field.value, False)
        if (field.line_cardinality == "2many") and value:
            op = "in"
        to_search = [('name', op, value)]
        objs = model_obj.search(to_search)

        rc = objs or False
        if rc and (field.line_cardinality == "2one"):
            rc = rc[0].id

        return rc

    @api.model
    def process(self, match, params):
        model_obj = self.env[match.model.model]
        vals = {}

        for field in match.lines:
            if field.name == "id":
                continue
            checker = self._get_checker(model_obj, field.name)
            if field.line_type == 'field':
                if params.get(field.value, False):
                    vals[field.name] = checker(params[field.value])
            elif field.line_type == 'model':
                if field.line_cardinality == '2many':
                    vals[field.name] = []
                    for x in params.get(field.value, []):
                        item = self.process(field.reference, x)

                        rc = self.find(field.reference, x)
                        tup = (0, 0, item)
                        if rc:
                            tup = (1, rc, item)

                        vals[field.name].append(tup)
                elif field.line_cardinality == '2one':
                    x = params.get(field.value, {})
                    rel_ids = self.push(x, field.reference.name)
                    vals[field.name] = rel_ids and rel_ids[0] or False
            elif field.line_type == 'reference':
                vals[field.name] = self.find_reference(match, field, params)
            elif field.line_type == 'default':
                vals[field.value] = checker(field.name)

        return vals

    @api.model
    def trim(self, match, obj, vals):
        vals = vals.copy()
        obj_pool = self.env[match.model.model]

        for field in match.lines:
            if field.line_type in ("model", "reference"):
                if field.line_cardinality == "2many":
                    for record in getattr(obj, field.name):
                        if vals.get(field.name, False):
                            if record.id not in [x[1] for x in
                                                 vals[field.name]]:
                                vals[field.name].append((2, record.id, False))
                        else:
                            vals[field.name] = [(2, record.id, False)]
        return vals

    @api.model
    def get_match(self, root):
        wdt = self.env['cenit.data_type']
        matching = wdt.search([('cenit_root', '=', root)])

        if matching:
            return matching[0]
        return False

    @api.model
    def add(self, params, m_name):
        match = self.get_match(m_name)
        if not match:
            return False

        model_obj = self.env[match.model.model]
        if not isinstance(params, list):
            params = [params]

        obj_ids = []
        for p in params:
            obj = self.find(match, p)
            if not obj:
                vals = self.process(match, p)
                if not vals:
                    continue

                obj = model_obj.create(vals)

            obj_ids.append(obj.id)
        return obj_ids

    @api.model
    def update(self, params, m_name):
        match = self.get_match(m_name)
        if not match:
            return False

        model_obj = self.env[match.model.model]
        if not isinstance(params, list):
            params = [params]

        obj_ids = []
        for p in params:
            obj = self.find(match, p)
            if obj:
                vals = self.process(match, p)
                vals = self.trim(match, obj, vals)
                obj.write(vals)
                obj_ids.append(obj.id)

        return obj_ids

    @api.model
    def push(self, params, m_name):
        match = self.get_match(m_name)
        if not match:
            return False

        if not isinstance(params, list):
            params = [params]

        obj_ids = []
        for p in params:
            obj = self.find(match, p)
            if obj:
                ids = self.update(p, m_name)
            else:
                ids = self.add(p, m_name)

            obj_ids.extend(ids)

        return obj_ids

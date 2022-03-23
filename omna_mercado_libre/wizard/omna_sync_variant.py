# -*- coding: utf-8 -*-

import requests
import base64
import json
import logging
from operator import itemgetter
from itertools import groupby
from datetime import datetime, timezone, time
from odoo.exceptions import ValidationError
from odoo import models, fields, api, exceptions, tools, _

_logger = logging.getLogger(__name__)


class OmnaSyncVariant(models.TransientModel):
    _name = 'omna.sync_variant_wizard'
    _inherit = 'omna.api'

    sync_type = fields.Selection([('all', 'All Variants of all Products'), ('by_product_id', 'All Variants of the Product'),
                                  ('by_omna_id', 'Variant with Omna ID')], 'Import Type',
                                 required=True, default='all')
    integration_id = fields.Many2one('omna.integration', 'Integration')
    template_id = fields.Many2one('product.template', 'Product')
    omna_id = fields.Char('Variant OMNA ID')



    @api.onchange('sync_type')
    def _onchange_sync_type(self):
        self.integration_id = False
        self.template_id = False
        self.omna_id = False


    @api.onchange('integration_id')
    def _onchange_integration_id(self):
        product_obj = self.env['product.template']
        result = product_obj.search([('integration_ids.integration_ids', '=', self.integration_id.id)])
        self.template_id = False
        return {'domain': {'template_id': [('id', 'in', result.ids)]}}


    def sync_variants(self):
        try:
            if self.sync_type == 'all':
                self.all_import_variants()
            if self.sync_type == 'by_product_id':
                self.by_product_id_import_variants()
            # if self.sync_type == 'by_omna_id':
            #     self.by_omna_id_import_variants()
            return {
                'type': 'ir.actions.client',
                'tag': 'reload'
            }
        except Exception as e:
            _logger.error(e)
            raise exceptions.AccessError(e)
        pass



    def all_import_variants(self):
        # https://cenit.io/app/ecapi-v1/integrations/{integration_id}/products/{product_id}/variants
        product_template_obj = self.env['product.template']
        product_list = product_template_obj.search([('omna_product_id', '!=', False)])
        if not product_list:
            raise ValidationError(u"Necesita importar productos y crearlos en la integración. Para luego intentar importar todas las variantes.")
        for item_rec in product_list:
            response = self.get('integrations/%s/products/%s/variants' % (self.integration_id.integration_id, item_rec.omna_product_id), {'limit': 25, 'offset': 0, 'with_details': True})
            products = response.get('data')

        product_obj = self.env['product.product']

        for product in products:
            act_product = product_obj.search([('omna_variant_id', '=', product.get('id'))])

            if act_product:
                data = {
                    'name': product.get('product').get('name'),
                    # 'omna_variant_id': product.get('id'),
                    'description': product.get('description'),
                    'lst_price': product.get('price'),
                    'default_code': product.get('sku'),
                    'standard_price': product.get('cost_price'),
                    'quantity': product.get('quantity'),
                    'product_tmpl_id': item_rec.id,
                    'variant_integrations_data': json.dumps(product.get('integration'), separators=(',', ':')),
                    'peso': product.get('package').get('weight'),
                    'alto': product.get('package').get('height'),
                    'longitud': product.get('package').get('length'),
                    'ancho': product.get('package').get('width'),
                    'custom_description': product.get('package').get('content')
                }
                if len(product.get('images')):
                    url = product.get('images')[0]
                    if url:
                        image = base64.b64encode(requests.get(url.strip()).content).replace(b'\n', b'')
                        data['image_variant_1024'] = image

                if product.get('integration', False):
                    aux = []
                    new_linked = False

                    integration = product.get('integration', False)
                    if integration:
                        linked = next((i for i in act_product.integration_linked_ids if
                                       i.integration_id == self.integration_id.integration_id), False)
                        if not linked:
                            aux.append((0, 0, {'integration_ids': self.integration_id.id,
                                               'remote_variant_id': integration.get('variant').get(
                                                   'remote_variant_id'),
                                               'delete_from_integration': True}))
                            new_linked = True

                    data['integration_linked_ids'] = [(6, 0, [self.integration_id.id])]
                    data['integration_ids'] = aux if new_linked else []

                act_product.with_context(synchronizing=True).write(data)

            # else:
            #     data = {
            #         'name': product.get('product').get('name'),
            #         # 'omna_variant_id': product.get('id'),
            #         'description': product.get('description'),
            #         'lst_price': product.get('price'),
            #         'default_code': product.get('sku'),
            #         'standard_price': product.get('cost_price'),
            #         'quantity': product.get('quantity'),
            #         'product_tmpl_id': item_rec.id,
            #         'variant_integrations_data': json.dumps(product.get('integration'), separators=(',', ':')),
            #         'peso': product.get('package').get('weight'),
            #         'alto': product.get('package').get('height'),
            #         'longitud': product.get('package').get('length'),
            #         'ancho': product.get('package').get('width'),
            #         'custom_description': product.get('package').get('content')
            #     }
            #     if len(product.get('images')):
            #         url = product.get('images')[0]
            #         if url:
            #             image = base64.b64encode(requests.get(url.strip()).content).replace(b'\n', b'')
            #             data['image_variant_1024'] = image
            #
            #     if product.get('integration', False):
            #         aux = []
            #         new_linked = False
            #
            #         integration = product.get('integration', False)
            #         if integration:
            #             linked = next((i for i in act_product.integration_linked_ids if
            #                            i.integration_id == self.integration_id.integration_id), False)
            #             if not linked:
            #                 aux.append((0, 0, {'integration_ids': self.integration_id.id,
            #                                    'remote_variant_id': integration.get('variant').get(
            #                                        'remote_variant_id'),
            #                                    'delete_from_integration': True}))
            #                 new_linked = True
            #
            #         data['integration_linked_ids'] = [(6, 0, [self.integration_id.id])]
            #         data['integration_ids'] = aux if new_linked else []
            #     product_obj.with_context(synchronizing=True).create(data)

            self.env.cr.commit()

        self.env.user.notify_channel('info', _('The process for import variants have been finished.'),
                                             _("Information"), True)


    def by_product_id_import_variants(self):
        # https://cenit.io/app/ecapi-v1/integrations/{integration_id}/products/{product_id}/variants

        response = self.get('integrations/%s/products/%s/variants' % (self.integration_id.integration_id, self.template_id.omna_product_id), {'with_details': True})
        products = response.get('data')

        product_obj = self.env['product.product']
        # product_attribute_list = self.env['product.attribute'].search([('omna_attribute_id', '!=', False)])
        prop_val = []
        prop_val_context = []
        for item in products:
            prop_val.extend([dict(propiedad=X.get('id'), valor=X.get('value')) for X in item.get('integration').get('variant').get('properties') if isinstance(X.get('id'), int)])
            prop_val_context.extend([dict(producto=item.get('id'), propiedad=X.get('id'), valor=X.get('value')) for X in item.get('integration').get('variant').get('properties') if isinstance(X.get('id'), int)])

        prop_val.sort(key=itemgetter('propiedad'))
        res = {k: [y.get('valor') for y in list(v) if y.get('valor')] for k, v in
               groupby(prop_val, itemgetter('propiedad'))}

        prop_val_context.sort(key=itemgetter('producto'))
        res_context = {k: {a: [y.get('valor') for y in list(b)] for a, b in groupby(list(v), itemgetter('propiedad'))} for k, v in groupby(prop_val_context, itemgetter('producto'))}


        list_variant = []

        for key, value in res.items():
            if value:
                product_attribute = self.env['product.attribute'].search([('omna_attribute_id', '=', str(key))])
                product_attribute_value = self.env['product.attribute.value'].search([('attribute_id', '=', product_attribute.id), ('omna_attribute_value_id', 'in', value)])
                # aux = product_attribute.value_ids.filtered(lambda X: X.omna_attribute_value_id in value)
                list_variant.append({'product_tmpl_id': self.template_id.id,
                                     'attribute_id': product_attribute.id,
                                     'value_ids': [(6, 0, product_attribute_value.ids)]
                                     })

        product_template_attribute_line = self.env['product.template.attribute.line'].with_context(omna_import_info=res_context).create(list_variant)

        self.env.cr.commit()

        for product in products:
            act_product = product_obj.search([('omna_variant_id', '=', product.get('id'))])

            if act_product:
                data = {
                    'name': product.get('product').get('name'),
                    # 'omna_variant_id': product.get('id'),
                    'description': product.get('description'),
                    'lst_price': product.get('price'),
                    'default_code': product.get('sku'),
                    'standard_price': product.get('cost_price'),
                    'quantity': product.get('quantity'),
                    'product_tmpl_id': self.template_id.id,
                    'variant_integrations_data': json.dumps(product.get('integration'), separators=(',', ':')),
                    'peso': product.get('package').get('weight'),
                    'alto': product.get('package').get('height'),
                    'longitud': product.get('package').get('length'),
                    'ancho': product.get('package').get('width'),
                    'custom_description': product.get('package').get('content')
                }
                if len(product.get('images')):
                    url = product.get('images')[0]
                    if url:
                        image = base64.b64encode(requests.get(url.strip()).content).replace(b'\n', b'')
                        data['image_variant_1024'] = image

                if product.get('integration', False):
                    aux = []
                    new_linked = False

                    integration = product.get('integration', False)
                    if integration:
                        linked = next((i for i in act_product.integration_linked_ids if
                                       i.integration_id == self.integration_id.integration_id), False)
                        if not linked:
                            aux.append((0, 0, {'integration_ids': self.integration_id.id,
                                               'remote_variant_id': integration.get('variant').get('remote_variant_id'),
                                               'delete_from_integration': True}))
                            new_linked = True

                    data['integration_linked_ids'] = [(6, 0, [self.integration_id.id])]
                    data['integration_ids'] = aux if new_linked else []

                act_product.with_context(synchronizing=True).write(data)

        self.env.cr.commit()
        self.env.user.notify_channel('info', _('The process for import variants have been finished.'),
                                         _("Information"), True)


    # def by_omna_id_import_variants(self):
    #     product = None
    #
    #     # https://cenit.io/app/ecapi-v1/integrations/{integration_id}/products/{product_id}/variants/{variant_id}
    #     response = self.get('integrations/%s/products/%s/variants/%s' % (self.integration_id.integration_id, self.template_id.omna_product_id, self.omna_id), {'with_details': True})
    #     product = response.get('data')
    #
    #
    #     product_obj = self.env['product.product']
    #
    #     prop_val = []
    #     prop_val_context = []
    #     # for item in products:
    #     prop_val.extend([dict(propiedad=X.get('id'), valor=X.get('value')) for X in product.get('integration').get('variant').get('properties') if isinstance(X.get('id'), int)])
    #     prop_val_context.extend([dict(producto=product.get('id'), propiedad=X.get('id'), valor=X.get('value')) for X in product.get('integration').get('variant').get('properties') if isinstance(X.get('id'), int)])
    #
    #     prop_val.sort(key=itemgetter('propiedad'))
    #     res = {k: [y.get('valor') for y in list(v) if y.get('valor')] for k, v in
    #            groupby(prop_val, itemgetter('propiedad'))}
    #
    #     prop_val_context.sort(key=itemgetter('producto'))
    #     res_context = {k: {a: [y.get('valor') for y in list(b)] for a, b in groupby(list(v), itemgetter('propiedad'))} for k, v in groupby(prop_val_context, itemgetter('producto'))}
    #
    #
    #     list_variant = []
    #
    #     for key, value in res.items():
    #         if value:
    #             product_attribute = self.env['product.attribute'].search([('omna_attribute_id', '=', str(key))])
    #             product_attribute_value = self.env['product.attribute.value'].search([('attribute_id', '=', product_attribute.id), ('omna_attribute_value_id', 'in', value)])
    #             # aux = product_attribute.value_ids.filtered(lambda X: X.omna_attribute_value_id in value)
    #             list_variant.append({'product_tmpl_id': self.template_id.id,
    #                                  'attribute_id': product_attribute.id,
    #                                  'value_ids': [(6, 0, product_attribute_value.ids)]
    #                                  })
    #
    #     product_template_attribute_line = self.env['product.template.attribute.line'].with_context(omna_import_info=res_context).create(list_variant)
    #
    #     self.env.cr.commit()
    #
    #     # for product in products:
    #     act_product = product_obj.search([('omna_variant_id', '=', product.get('id'))])
    #
    #     if act_product:
    #         data = {
    #             'name': product.get('product').get('name'),
    #             # 'omna_variant_id': product.get('id'),
    #             'description': product.get('description'),
    #             'lst_price': product.get('price'),
    #             'default_code': product.get('sku'),
    #             'standard_price': product.get('cost_price'),
    #             'quantity': product.get('quantity'),
    #             'product_tmpl_id': self.template_id.id,
    #             'variant_integrations_data': json.dumps(product.get('integration'), separators=(',', ':')),
    #             'peso': product.get('package').get('weight'),
    #             'alto': product.get('package').get('height'),
    #             'longitud': product.get('package').get('length'),
    #             'ancho': product.get('package').get('width'),
    #             'custom_description': product.get('package').get('content')
    #         }
    #         if len(product.get('images')):
    #             url = product.get('images')[0]
    #             if url:
    #                 image = base64.b64encode(requests.get(url.strip()).content).replace(b'\n', b'')
    #                 data['image_variant_1024'] = image
    #
    #         if product.get('integration', False):
    #             aux = []
    #             new_linked = False
    #
    #             integration = product.get('integration', False)
    #             if integration:
    #                 linked = next((i for i in act_product.integration_linked_ids if
    #                                i.integration_id == self.integration_id.integration_id), False)
    #                 if not linked:
    #                     aux.append((0, 0, {'integration_ids': self.integration_id.id,
    #                                        'remote_variant_id': integration.get('variant').get('remote_variant_id'),
    #                                        'delete_from_integration': True}))
    #                     new_linked = True
    #
    #             data['integration_linked_ids'] = [(6, 0, [self.integration_id.id])]
    #             data['integration_ids'] = aux if new_linked else []
    #
    #         act_product.with_context(synchronizing=True).write(data)
    #
    #     self.env.cr.commit()
    #     self.env.user.notify_channel('info', _('The process for import variants have been finished.'),
    #                                  _("Information"), True)

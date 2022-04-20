# -*- coding: utf-8 -*-
import json
from odoo import models, api, _, fields
from odoo.exceptions import ValidationError
from odoo.exceptions import *


class WizardStockItemMov(models.TransientModel):
    _name = "wizard.stock.item.mov"
    _description = "Stock Item Movement"

    cantidad = fields.Integer(string="Cantidad")

    def update_quantity(self):
        self.ensure_one()
        data = {"data": {"quantity": self.cantidad}}
        omna_stock_items = self.env['omna.stock.items']
        omna_stock_item_id = self.env.context.get('omna_stock_item_id')
        integration_id = self.env.context.get('integration_id')
        omna_product_id = self.env.context.get('omna_product_id')
        omna_variant_id = self.env.context.get('omna_variant_id')
        omna_stock_item_result = omna_stock_items.search([('omna_id', '=', omna_stock_item_id)])
        response = omna_stock_items.post('stock/items/%s' % (omna_stock_item_id,), data)
        aux = omna_stock_item_result.count_on_hand
        omna_stock_item_result.write({'count_on_hand': aux + self.cantidad})
        self.env.user.notify_channel('info', _('The quantity was updated.'), _("Information"), True)



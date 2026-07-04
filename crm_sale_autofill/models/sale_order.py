import json

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'



    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        lead_model = self.env['crm.lead']
        product_model = self.env['product.product']
        prepared_vals_list = []
        for vals in vals_list:
            vals = dict(vals)
            lead_id = vals.get('opportunity_id') or self.env.context.get('default_opportunity_id')
            if lead_id and not vals.get('order_line'):
                lead = lead_model.browse(lead_id)
                order_lines = []
                suggested_products = []
                for line in lead.suggested_product_line_ids:
                    product = line.product_id
                    if not product:
                        product_name = (line.name or '').strip()
                        if not product_name:
                            continue
                        product = product_model.search([
                            '|',
                            ('default_code', '=ilike', product_name),
                            ('name', '=ilike', product_name),
                        ], limit=1)

                    if not product:
                        continue
                    
                    order_lines.append((0, 0, {
                        'product_id': product.id,
                        'product_uom_qty': line.quantity,
                        'price_unit': line.price_unit if line.price_unit else product.lst_price,
                        'name': product.display_name,
                    }))
                if order_lines:
                    vals['order_line'] = order_lines
            prepared_vals_list.append(vals)

        records = super().create(prepared_vals_list)
        return records[0] if len(records) == 1 else records

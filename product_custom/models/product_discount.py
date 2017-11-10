from odoo import models, fields, api

class ProductDiscount(models.Model):
    _name       = 'product.discount'
    _inherit    = ['mail.thread', 'ir.needaction_mixin']

    name        = fields.Char(string='Title', required=True)
    date_from   = fields.Date(string='Date From', required=True)
    date_to     = fields.Date(string='Date To')
    line_ids    = fields.One2many('product.discount.line', 'discount_id', string='Discount Lines')

    @api.multi
    def get_product(self):
        product_ids = self.env['product.product'].search([])
        result = []
        for product in product_ids:
            if self.line_ids:
                exist_product = self.line_ids.mapped('product_id')
                if product not in exist_product:
                    result.append((0, 0, {'product_id': product.id, 'price': product.list_price, 'discount': 0}))
            else:
                result.append((0, 0, {'product_id': product.id, 'price': product.list_price, 'discount': 0}))
        self.line_ids = result


class ProductDiscountLine(models.Model):
    _name       = 'product.discount.line'

    discount_id = fields.Many2one('product.discount', string='Discount', required=True)
    product_id  = fields.Many2one('product.product', string='Product', required=True)
    price       = fields.Float(string='Price')
    discount    = fields.Float(string='Discount')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.price = self.product_id.list_price


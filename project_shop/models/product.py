# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
# from datetime import datetime, timedelta

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type        = fields.Selection(default='product')
    width_size  = fields.Char(string='Width/Size')
    color       = fields.Char(string='Color')
    pur_org     = fields.Char(string='PurOrg')
    pur_org_desc = fields.Char(string='Purch. Org. Desc.')
    pur_grp     = fields.Char(string='PURCH GRP')
    mat_grp     = fields.Integer(string='MatGrp')
    mat_group   = fields.Char(string='Material Group')
    size_uk     = fields.Char(string='UK')
    size_eu     = fields.Char(string='Euro')
    size_cm     = fields.Char(string='CM')
    pattern_desc = fields.Html(string='PATTERN DESC')

    @api.multi
    def name_get(self):
        # result = super(ProductTemplate, self).name_get()
        res = []
        for record in self:
            name = record.name
            if record.default_code:
                if record.width_size or record.color:
                    get_size_color = (record.width_size + '/' if record.width_size and record.color else record.width_size) + (record.color or '')
                    name = '[' + record.default_code + '][' + get_size_color + '] ' + record.name
                else:
                    name = '[' + record.default_code + '] ' + record.name
            if record.barcode:
                name = name + ' (' + record.barcode +')'
            res.append((record.id, name))
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def name_get(self):
        # result = super(ProductTemplate, self).name_get()
        res = []
        for record in self:
            name = record.name
            if record.default_code:
                if record.width_size or record.color:
                    get_size_color = (
                                     record.width_size + '/' if record.width_size and record.color else record.width_size) + (
                                     record.color or '')
                    name = '[' + record.default_code + '][' + get_size_color + '] ' + record.name
                else:
                    name = '[' + record.default_code + '] ' + record.name
            if record.barcode:
                name = name + ' (' + record.barcode +')'
            res.append((record.id, name))
        return res


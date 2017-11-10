# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _

class CategoryType(models.Model):
    _name   = 'category.type'

    name    = fields.Char(string='Name')
    code    = fields.Char(string='Code')


class ResDistrict(models.Model):
    _name   = 'res.district'

    name    = fields.Char(string='Name')
    code    = fields.Char(string='Code')
    state_id = fields.Many2one('res.country.state')


class ProductCategory(models.Model):
    _inherit    = 'product.category'

    categ_type  = fields.Selection([('ndt', 'Nhà đầu tư'), ('da', 'Dự án'), ('block', 'Block')], string='Type')
    code_da     = fields.Char(string='Mã dự án')
    floor_count = fields.Integer(string='Số tầng')
    note        = fields.Html(string='Note')
    position    = fields.Html(string='Vị trí')
    csbh        = fields.Html(string='Chính sách bán hàng')
    form_house  = fields.Html(string='Nhà mẫu')
    info_real   = fields.Html(string='Thông tin thưc tế')
    city        = fields.Many2one('res.country.state', string='City')
    district    = fields.Many2one('res.district', string='District')
    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the product, limited to 1024x1024px.")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    attachments = fields.Many2many('ir.attachment', 'category_attachment_rel', 'categ_id', 'attachment_id',
                                   string='Attachments')

    @api.model
    def create(self, vals):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        # TDE FIXME: context brol
        tools.image_resize_images(vals)
        template = super(ProductCategory, self).create(vals)
        return template

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        res = super(ProductCategory, self).write(vals)
        return res
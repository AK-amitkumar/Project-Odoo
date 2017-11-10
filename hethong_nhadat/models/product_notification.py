# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import Warning

class ProductNotification(models.Model):
    _name       = 'product.notification'
    _order      = "id desc"

    product_id  = fields.Many2one('product.product', string='Product')
    date        = fields.Datetime(string='Date')
    user_id     = fields.Many2one('res.users', string='User')
    note        = fields.Char(string='Notification')
    link        = fields.Char(related='product_id.link')


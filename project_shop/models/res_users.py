# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResUsers(models.Model):
    _inherit    = 'res.users'

    wh_id = fields.Many2one('stock.warehouse', string='Warehouse')




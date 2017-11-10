# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResUsers(models.Model):
    _inherit    = 'res.users'

    wh_ids = fields.Many2many('stock.warehouse', 'warehouse_users_rel', 'user_id', 'wh_id', string='Warehouse')




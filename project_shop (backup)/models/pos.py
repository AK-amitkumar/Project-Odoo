# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _

class PosConfig(models.Model):
    _inherit = 'pos.config'

    # def _get_location(self):
    #     if self.user_has_groups('point_of_sale.group_pos_user'):
    #         print self.env['stock.location'].search([('user_ids', 'in', self.env.user.id)]), 111111111111111111111
    #         return self.env['stock.location'].search([('user_ids', 'in', self.env.user.id)])
    #     else:
    #         print 22222222222222222222
    #         return self.env['stock.location'].search([])
    #
    # location_ids = fields.Many2many('stock.location', default=lambda self: self._get_location(), string='Locations')
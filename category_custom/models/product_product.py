# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from datetime import datetime, timedelta

class ProductProduct(models.Model):
    _inherit = 'product.template'

    status = fields.Selection([('sold', 'Đã bán'), ('no_sell', 'Còn trống'), ('hold', 'Giữ chỗ')], string='Trạng thái', default='no_sell', track_visibility='onchange')
    direction = fields.Selection([('west', 'Tây'), ('south', 'Nam'), ('east', 'Đông'), ('north', 'Bắc'), ('northeast', 'Đông bắc'), ('southeast', 'Đông nam'), ('northwest', 'Tây bắc'), ('southwest', 'Tây nam')], string='Hướng nhà', track_visibility='onchange')
    floorth = fields.Integer(string='Tầng sô', track_visibility='onchange')
    area = fields.Float(string='Diện tích', track_visibility='onchange')
    room_no = fields.Integer(string='Số phòng', track_visibility='onchange')
    categ_da = fields.Many2one('product.category', string='Dự án', track_visibility='onchange')
    hold_date = fields.Datetime(string='Hold Date', track_visibility='onchange')
    hold_user = fields.Many2one('res.users', string='Hold User', track_visibility='onchange')
    attachments = fields.Many2many('ir.attachment', 'product_attachment_rel', 'product_id', 'attachment_id', string='Attachments')
    color = fields.Integer('Color Index', compute="change_colore_on_kanban")

    @api.depends('status')
    def change_colore_on_kanban(self):
        for record in self:
            if record.status == 'no_sell':
                color = 0
            elif record.status == 'hold':
                color = 4
            else:
                color = 6
            record.color = color

    @api.model
    def _auto_cancel_hold_product(self):
        products = self.sudo().search([('status', '=', 'hold')])
        for product in products:
            total_second = False
            if product.hold_date:
                total_second = (datetime.now() - datetime.strptime(product.hold_date, "%Y-%m-%d %H:%M:%S")).total_seconds()
            if (total_second and total_second >= 6 * 3600) or not total_second:
                product.write({
                    'status': 'no_sell',
                    'hold_date': False,
                    'hold_user': False,
                })

    @api.multi
    def action_no_sell(self):
        if self.status == 'sold':
            raise Warning(_("Căn hộ đã bán."))
        self.sudo().write({
            'status': 'no_sell',
            'hold_date': False,
            'hold_user': False,
        })

    @api.multi
    def action_hold(self):
        if self.status == 'sold':
            raise Warning(_("Căn hộ đã bán."))
        self.sudo().write({
            'status': 'hold',
            'hold_date': datetime.now(),
            'hold_user': self.env.user.id,
        })

    @api.multi
    def action_sold(self):
        if self.status == 'sold':
            raise Warning(_("Căn hộ đã bán."))
        self.sudo().write({
            'status': 'sold'
        })
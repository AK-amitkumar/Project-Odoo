# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.addons.mail.models.mail_template import format_tz

class StockQuantityUpdate(models.Model):
    _name = 'stock.quantity.update'

    date = fields.Datetime(string='Date')
    location_id = fields.Many2one('stock.location', string='Location')
    qty = fields.Integer(string='Quantity')

    @api.multi
    def action_update(self):
        locations = self.env['stock.location'].search([('usage', '=', 'internal')])
        if locations:
            for loc in locations:
                quants = self.env['stock.quant'].search([('location_id', '=', loc.id)])
                if quants:
                    # current_date = format_tz(self.env, datetime.now().strftime('%Y-%m-%d 01:00:00'), tz=self.env.user.tz, format='%Y-%m-%d %H:%M:%S')
                    total = sum(quant.qty for quant in quants)
                    self.create({
                        'date': (datetime.now() + timedelta(hours=7)).strftime('%Y-%m-%d 01:00:00'),
                        'location_id': loc.id,
                        'qty': total or 0
                    })
                    # prev_date = format_tz(self.env, (datetime.now() + timedelta(hours=7) - timedelta(days=1)).strftime('%Y-%m-%d 23:59:00'), tz=self.env.user.tz, format='%Y-%m-%d %H:%M:%S')
                    self.create({
                        'date': (datetime.now() + timedelta(hours=7) - timedelta(days=1)).strftime('%Y-%m-%d 23:59:00'),
                        'location_id': loc.id,
                        'qty': total or 0
                    })
                else:
                    self.create({
                        'date': (datetime.now() + timedelta(hours=7)).strftime('%Y-%m-%d 01:00:00'),
                        'location_id': loc.id,
                        'qty': 0
                    })
                    # prev_date = format_tz(self.env, (datetime.now() + timedelta(hours=7) - timedelta(days=1)).strftime('%Y-%m-%d 23:59:00'), tz=self.env.user.tz, format='%Y-%m-%d %H:%M:%S')
                    self.create({
                        'date': (datetime.now() + timedelta(hours=7) - timedelta(days=1)).strftime('%Y-%m-%d 23:59:00'),
                        'location_id': loc.id,
                        'qty': 0
                    })


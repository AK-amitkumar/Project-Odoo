# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class PosReprint(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def pos_reprint(self):
        return self.env['report'].get_action(self, 'product_custom.pos_reprint')

    @api.multi
    def get_total_wo_tax(self):
        if self.lines:
            total = 0
            for line in self.lines:
                total += line.qty * line.price_unit
            return total

    @api.multi
    def get_total_w_tax(self):
        if self.lines:
            total = 0
            for line in self.lines:
                total += line.price_subtotal_incl
            return total
            # return sum([line.price_subtotal_incl] for line in self.lines) or 0

    @api.multi
    def get_tax_detail(self):
        dict = {}
        values = {}
        for line in self.lines:
            if line.tax_ids:
                for tax in line.tax_ids:
                    if tax in dict:
                        dict[tax] += line.qty * line.price_unit
                    else:
                        dict[tax] = line.qty * line.price_unit
        if dict:
            for key in dict:
                values[key.name] = dict[key] * key.amount / 100
        print dict, values
        return values

    @api.multi
    def get_discount(self):
        if self.lines:
            total = 0
            for line in self.lines:
                total += line.qty * line.price_unit * line.discount / 100
            return total
            # return sum([line.price_subtotal] for line in self.lines) or 0

    @api.multi
    def get_cash(self):
        if self.statement_ids:
            if len(self.statement_ids) == 1:
                return self.statement_ids[0].amount
            else:
                return max(self.statement_ids.mapped('amount'))

    @api.multi
    def get_change(self):
        if self.statement_ids:
            if len(self.statement_ids) == 1:
                return 0
            else:
                return min(self.statement_ids.mapped('amount'))




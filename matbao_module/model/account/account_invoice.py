# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2017 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def unlink(self):
        ctx = self._context
        if ctx.get('force_unlink'):
            for invoice in self:
                if invoice.state not in ('draft', 'cancel'):
                    raise UserError(_(""" You cannot delete an invoice which is
                     not draft or cancelled. You should refund it instead."""))
            return super(models.Model, self).unlink()
        return super(AccountInvoice, self).unlink()

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        for inv in self:
            if inv.type == 'out_invoice':
                sale_ids = inv.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
                if sale_ids:
                    for order in sale_ids:
                        order.write({
                            'invisible_match_payment': True
                        })
        return res

    @api.multi
    def write(self, vals):
        if 'state' in vals:
            if vals.get('state') == 'paid':
                sale_ids = self.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
                if sale_ids:
                    for order in sale_ids:
                        order.write({
                            'fully_paid': True
                        })
        return super(AccountInvoice, self).write(vals)

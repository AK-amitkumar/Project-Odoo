# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, Warning
from datetime import datetime

def get_order_reference(session_id):
    def zero_pad(number, size):
        s = "" + str(number)
        while len(s) < size:
            s = "0" + s
        return s
    return 'Order ' + zero_pad(session_id, 5) + '-' + zero_pad(datetime.now().hour, 3) + '-' + zero_pad(str(datetime.now().minute) + str(datetime.now().second), 4)

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


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.onchange('order_id.location_id', 'qty')
    def get_product(self):
        quants = self.env['stock.quant'].search([('location_id', '=', self.order_id.location_id.id)])
        print quants, 2222222222222222222
        if quants:
            if self.qty > 0:
                quants = quants.filtered(lambda quant: quant.qty > 0)
            return {
                'domain': {
                    'product_id': [('id', 'in', quants.mapped('product_id').ids)],
                }
            }


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.depends('child_ids')
    def get_return(self):
        for record in self:
            if record.child_ids:
                record.is_return = True
            else:
                record.is_return = False

    parent_id = fields.Many2one('pos.order', string='Parent Order')
    child_ids = fields.One2many('pos.order', 'parent_id', string="Return Orders")
    is_return = fields.Boolean(string="Return Orders?", compute="get_return")


    def get_url(self):
        param = self.env['ir.config_parameter'].sudo().search([('key', '=', 'web.base.url')])
        return param and param.value or ''

    @api.multi
    def pos_reprint(self):
        return self.env['report'].get_action(self, 'project_shop.pos_reprint')

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

    @api.multi
    def refund(self):
        """Create a copy of order  for refund order"""
        PosOrder = self.env['pos.order']
        current_session = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self.env.uid)],
                                                         limit=1)
        if not current_session:
            raise UserError(
                _('To return product(s), you need to open a session that will be used to register the refund.'))
        for order in self:
            clone = order.copy({
                # ot used, name forced by create
                'name': order.name + _(' REFUND'),
                'session_id': current_session.id,
                'date_order': fields.Datetime.now(),
                'pos_reference': order.pos_reference,
                'parent_id': order.id
            })
            PosOrder += clone

        for clone in PosOrder:
            for order_line in clone.lines:
                order_line.write({'qty': -order_line.qty})
        return {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': PosOrder.ids[0],
            'view_id': False,
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.model
    def create(self, vals):
        if not vals.get('pos_reference'):
            current_session = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self.env.uid)],
                                                         limit=1)
            vals.update({'pos_reference': get_order_reference(current_session.id)})
        res = super(PosOrder, self).create(vals)
        if res.amount_total < 0:
            raise Warning(_("Amount Order must be larger than 0"))
        return res

    @api.multi
    def write(self, vals):
        res = super(PosOrder, self).write(vals)
        if self.amount_total < 0:
            raise Warning(_("Amount Order must be larger than 0"))
        return res

    @api.model
    def default_get(self, fields):
        vals = super(PosOrder, self).default_get(fields)
        current_session = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self.env.uid)], limit=1)
        if not current_session:
            raise UserError(
                _('To return product(s), you need to open a session that will be used to register the refund.'))
        vals.update({'session_id': current_session.id})
        return vals

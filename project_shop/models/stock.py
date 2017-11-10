# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from odoo.exceptions import Warning, UserError
from datetime import datetime, timedelta
import logging

class StockLocation(models.Model):
    _inherit = 'stock.location'

    user_ids = fields.Many2many('res.users', 'stock_location_res_users_rel', 'location_id', 'user_id', string='Access Users')

    @api.model
    def create(self, vals):
        res = super(StockLocation, self).create(vals)
        logging.info("--------------- %s ----------- %s -------------" % (res, res.usage))
        if res.usage == 'internal' and res.active == True:
            self.env['stock.quantity.update'].create({
                'date': (datetime.now() + timedelta(hours=7)).strftime('%Y-%m-%d 01:00:00'),
                'location_id': res.id,
                'qty': 0
            })
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # picking_type_id = fields.Many2one(
    #     'stock.picking.type', 'Picking Type',
    #     required=True, copy=False,
    #     states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    def _get_location(self):
        # if self.user_has_groups('project_shop.group_inventory_receipts') or self.user_has_groups('project_shop.group_inventory_delivery')\
        #     or self.user_has_groups('project_shop.group_inventory_receipts') or self.user_has_groups('project_shop.group_inventory_shop_manager'):
        if self.user_has_groups('project_shop.group_inventory_receipts') or self.user_has_groups('project_shop.group_inventory_shop_manager'):
            wh_main = self.env['stock.warehouse'].search([('code', '=', 'WH')]).mapped('lot_stock_id')
            return self.env['stock.location'].search([('user_ids', 'in', self.env.user.id)]) | wh_main
        else:
            return self.env['stock.location'].search([])

    @api.model
    def _default_location_id(self):
        if self.user_has_groups('project_shop.group_inventory_receipts') or self.user_has_groups('project_shop.group_inventory_shop_manager'):
            location = self.env['stock.location'].search([('user_ids', 'in', self.env.user.id)])
            if location:
                return location[0].id
            else:
                raise UserError(_('You must add user into stock location.'))
        else:
            return self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id

    location_ids = fields.Many2many('stock.location', default=lambda self: self._get_location())
    location_id = fields.Many2one(
        'stock.location', "Source Location Zone",
        default=lambda self: self._default_location_id(),
        readonly=True, required=True,
        states={'draft': [('readonly', False)]})
    end_location_dest_id = fields.Many2one('stock.location', "End Destination Location", track_visibility='onchange',
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id)
    first_location_id = fields.Many2one('stock.location', "First Source Location", track_visibility='onchange',
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,)
    receipt_status = fields.Selection([('waiting', 'Waiting'), ('received', 'Received')], track_visibility='onchange', string='Receipt Status')
    receive_date = fields.Datetime(string='Received Date')
    total = fields.Float(string='Total', compute="_compute_total", store=True)

    @api.depends('move_lines')
    def _compute_total(self):
        for picking in self:
            picking.total = 0
            if picking.move_lines:
                picking.total = sum(move.product_uom_qty for move in picking.move_lines)

    @api.onchange('picking_type_id')
    def onchange_picking_type_id(self):
        location = self._get_location()
        if self.picking_type_id:
            if self.picking_type_id.code == 'incoming':
                return {
                    'domain': {
                        'location_id': [('id', 'in', location.ids)]
                    }
                }
            elif self.picking_type_id.code == 'internal':
                return {
                    'domain': {
                        'location_dest_id': [('id', 'in', location.ids)]
                    }
                }
            else:
                return {
                    'domain': {
                        'location_dest_id': [('usage', '=', 'transit')],
                        'end_location_dest_id': [('usage', '=', 'internal')],
                    }
                }

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if 'picking_type_id' not in default:
            location_ids = self._get_location()
            if self.sudo().picking_type_id.code == 'incoming':
                picking_type_ids = self.env['stock.picking.type'].search([('default_location_dest_id', 'in', location_ids.ids)])
                picking_ids = picking_type_ids
            elif self.sudo().picking_type_id.code == 'outgoing':
                picking_type_ids = self.env['stock.picking.type'].search([('default_location_src_id', 'in', location_ids.ids)])
                picking_ids = picking_type_ids
            else:
                picking_ids = self.env['stock.picking.type'].search(['|', ('default_location_src_id', 'in', location_ids.ids), ('default_location_dest_id', 'in', location_ids.ids)])
            default['picking_type_id'] = picking_ids and picking_ids[0].id
        return super(StockPicking, self).copy(default=default)

    @api.multi
    def do_new_transfer(self):
        res = super(StockPicking, self).do_new_transfer()
        for pick in self:
            if pick.location_id.usage == 'supplier' and pick.location_dest_id.usage == 'internal' and pick.state == 'done':
                pick.write({
                    'receipt_status': 'received'
                })
            else:
                pick.write({
                    'receipt_status': 'waiting'
                })
        return res

    @api.multi
    def action_confirm_receipt(self):
        if (not self.user_has_groups('stock.group_stock_manager') and not self.user_has_groups('base.group_system')) \
            and self.env.user.id not in self.env['stock.location'].search([('id', '=', self.end_location_dest_id.id)]).user_ids.ids:
            raise Warning(_("Bạn không thể Confirm. Chỉ quản lý shop %s mới có thể confirm.") % self.end_location_dest_id.location_id.name)

        self.write({
            'receipt_status': 'received',
            'receive_date': self.receive_date or datetime.now()
        })
        for pick in self.sudo():
            picking_type_id = self.env['stock.picking.type'].sudo().search([('default_location_dest_id', '=', pick.end_location_dest_id.id), ('code', '=', 'incoming')])
            location_id = pick.location_dest_id.id
            first_location_id = pick.picking_type_id.default_location_src_id.id
            receipt_id = pick.copy()
            receipt_id.sudo().write({
                'picking_type_id': picking_type_id and picking_type_id.id or receipt_id.picking_type_id.id,
                'location_id': location_id or receipt_id.location_id.id,
                'location_dest_id': pick.end_location_dest_id and pick.end_location_dest_id.id or receipt_id.location_dest_id.id,
                'first_location_id': first_location_id or (receipt_id.location_id and receipt_id.location_id.id or False),
                'receipt_status': 'received'
            })
            # If still in draft => confirm and assign
            if receipt_id.state == 'draft':
                receipt_id.action_confirm()
                if receipt_id.state != 'assigned':
                    receipt_id.action_assign()
                    if receipt_id.state != 'assigned':
                        raise UserError(_(
                            "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for pack in receipt_id.pack_operation_ids:
                if pack.product_qty > 0:
                    pack.write({'qty_done': pack.product_qty})
                else:
                    pack.unlink()
            receipt_id.sudo().do_transfer()

    # @api.onchange('picking_type_id', 'partner_id')
    # def onchange_picking_type(self):
    #     res = super(StockPicking, self).onchange_picking_type()
    #     if self.picking_type_id and self.picking_type_id.code == 'outgoing':
    #     return res, {'domain': {
    #         'payment_method_id': [('payment_type', '=', 'outbound'), ('id', 'in', payment_methods.ids)]}}

    # @api.multi
    # def do_transfer(self):
    #     for pick in self:
    #         if pick.move_line

    @api.onchange('state')
    def onchange_state(self):
        if self.state == 'done' and self.location_dest_id.usage == 'internal' and self.location_id.usage == 'supplier':
            self.receipt_status = 'received'
        elif self.state == 'assigned' and self.location_dest_id.usage == 'internal' and self.location_id.usage == 'supplier':
            self.receipt_status = 'waiting'


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def _get_location(self):
        if self.user_has_groups('project_shop.group_inventory_receipts') or self.user_has_groups('project_shop.group_inventory_shop_manager'):
            print self.env['stock.location'].search([('user_ids', 'in', self.env.user.id)])
            return self.env['stock.location'].search([('user_ids', 'in', self.env.user.id)])
        else:
            return self.env['stock.location'].search([])

    @api.model
    def _default_location_id(self):
        if self.user_has_groups('project_shop.group_inventory_receipts') or self.user_has_groups('project_shop.group_inventory_shop_manager'):
            location = self.env['stock.location'].search([('user_ids', 'in', self.env.user.id)])
            if location:
                return location[0].id
            else:
                raise UserError(_('You must add user into stock location.'))
        else:
            return super(StockInventory, self)._default_location_id()

    location_ids = fields.Many2many('stock.location', default=lambda self: self._get_location())
    location_id = fields.Many2one(
        'stock.location', 'Inventoried Location',
        readonly=True, required=True,
        states={'draft': [('readonly', False)]},
        default=_default_location_id)


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    def _get_location(self):
        if self.user_has_groups('project_shop.group_inventory_receipts') or self.user_has_groups('project_shop.group_inventory_shop_manager'):
            return self.env['stock.location'].search([('user_ids', 'in', self.env.user.id)])
        else:
            return self.env['stock.location'].search([])

    @api.model
    def _get_default_location_id(self):
        if self.user_has_groups('project_shop.group_inventory_receipts') or self.user_has_groups('project_shop.group_inventory_shop_manager'):
            location = self.env['stock.location'].search([('user_ids', 'in', self.env.user.id)])
            if location:
                return location[0].id
            else:
                raise UserError(_('You must add user into stock location.'))
        else:
            return super(StockScrap, self)._get_default_location_id()

    location_ids = fields.Many2many('stock.location', default=lambda self: self._get_location())
    location_id = fields.Many2one('stock.location', 'Location', domain="[('usage', '=', 'internal')]",
        required=True, states={'done': [('readonly', True)]}, default=_get_default_location_id)


class StockMove(models.Model):
    _inherit = 'stock.move'

    end_location_dest_id = fields.Many2one('stock.location', "End Destination Location", related="picking_id.end_location_dest_id")
    first_location_id = fields.Many2one('stock.location', "First Source Location", related="picking_id.first_location_id")
    receipt_status = fields.Selection([('waiting', 'Waiting'), ('received', 'Received')], related="picking_id.receipt_status")

    @api.multi
    def action_done(self):
        for move in self:
            if move.product_id and move.picking_type_id.code == 'outgoing':
                quants = self.env['stock.quant'].search([('product_id', '=', move.product_id.id), ('location_id', '=', move.location_id.id)])
                if quants:
                    total = sum(quant.qty for quant in quants)
                    if move.product_uom_qty > total:
                        raise Warning(_("You can't delivery out stock. Quantiy must be less than %s") % total)
                else:
                    raise Warning(_("%s not exist in %s.") % (move.product_id.complete_name, move.location_id.display_name))
        return super(StockMove, self).action_done()

    @api.onchange('state')
    def onchange_state(self):
        if self.state == 'done':
            if self.location_dest_id.usage == 'internal' and self.location_id.usage == 'supplier':
                self.receipt_status = 'received'
                
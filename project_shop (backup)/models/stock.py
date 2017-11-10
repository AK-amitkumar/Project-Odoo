# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _

class StockLocation(models.Model):
    _inherit = 'stock.location'

    user_ids = fields.Many2many('res.users', 'stock_location_res_users_rel', 'location_id', 'user_id', string='Access Users')


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

    @api.onchange('picking_type_id')
    def onchange_picking_type_id(self):
        location = self._get_location()
        if self.picking_type_id and self.picking_type_id.code == 'incoming':
            return {
                'domain': {
                    'location_id': [('id', 'in', location.ids)]
                }
            }
        elif self.picking_type_id and self.picking_type_id.code == 'internal':
            return {
                'domain': {
                    'location_dest_id': [('id', 'in', location.ids)]
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
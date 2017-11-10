# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line', 'order_line.qty_received', 'order_line.qty_coming', 'order_line.qty_waiting', 'order_line.product_qty')
    def _get_quantity(self):
        for order in self:
            order.qty_total = 0
            order.qty_received = 0
            order.qty_shipped = 0
            order.qty_outstanding = 0
            # outstanding = sum(line.qty_waiting for line in order.order_line)
            if order.order_line:
                order.qty_total = sum(line.product_qty for line in order.order_line)
                order.qty_received = sum(line.qty_received for line in order.order_line)
                order.qty_shipped = sum(line.qty_coming for line in order.order_line)
                order.qty_outstanding = sum(line.qty_waiting for line in order.order_line)

    qty_total = fields.Float(string='Qty Total', compute='_get_quantity')
    qty_received = fields.Float(string='Qty Received', compute='_get_quantity')
    qty_shipped = fields.Float(string='Qty Shipped', compute='_get_quantity')
    qty_outstanding = fields.Float(string='Qty Outstanding', compute='_get_quantity')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('product_qty', 'order_id.state', 'move_ids.state', 'order_id.picking_ids.pack_operation_product_ids.qty_done')
    def _compute_qty_coming(self):
        for line in self:
            if line.order_id.state not in ['purchase', 'done']:
                line.qty_received = 0.0
                continue
            if line.product_id.type not in ['consu', 'product']:
                line.qty_received = line.product_qty
                continue
            total_coming = 0.0
            picking_ids = line.order_id.picking_ids
            for pick in picking_ids:
                if pick.state == 'assigned':
                    if pick.pack_operation_product_ids:
                        total_coming += sum(pack.qty_done for pack in pick.pack_operation_product_ids if pack.product_id == line.product_id)

            line.qty_waiting = line.product_qty - line.qty_received - total_coming
            line.qty_coming = total_coming

    qty_coming = fields.Float(compute='_compute_qty_coming', string="Coming Qty", store=True)
    qty_waiting = fields.Float(compute='_compute_qty_coming', string="Waiting Qty", store=True)


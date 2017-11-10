# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class PurchaseReport(models.Model):
    _name = "shop.purchase.report"
    _description = "Purchases Orders"
    _auto = False
    _order = 'date_order desc'

    order_id = fields.Many2one('purchase.order', readonly=True, string="Purchase Order")
    date_order = fields.Datetime('Order Date', readonly=True, help="Date on which this document has been created", oldname='date')
    state = fields.Selection([
        ('draft', 'Draft RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
        ], 'Order Status', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Vendor', readonly=True)
    product_qty = fields.Float('Product Quantity', readonly=True)
    qty_received = fields.Float('Quantity Received', readonly=True)
    qty_coming = fields.Float('Quantity Coming', readonly=True)
    qty_waiting = fields.Float('Quantity Waiting', readonly=True)
    price_unit = fields.Float('Price Unit', readonly=True)
    price_subtotal = fields.Float('Total', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'shop_purchase_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW shop_purchase_report AS (
                SELECT pol.id, pol.order_id, po.date_order, po.partner_id, po.picking_type_id, po.state,
                       pol.product_id, pol.product_qty, pol.qty_received, pol.price_unit, pol.price_subtotal,
                       pol.qty_coming, pol.qty_waiting
                FROM purchase_order_line pol 
                    LEFT JOIN purchase_order po ON po.id = pol.order_id
                    LEFT JOIN stock_move sm ON sm.purchase_line_id = pol.id
                    LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                    LEFT JOIN stock_pack_operation spo ON spo.picking_id = sp.id
                GROUP BY pol.id, pol.order_id, po.date_order, po.partner_id, po.picking_type_id, po.state,
                       pol.product_id, pol.product_qty, pol.qty_received, pol.price_unit, pol.price_subtotal,
                       pol.qty_coming, pol.qty_waiting
                ORDER BY pol.order_id
            )
        """)

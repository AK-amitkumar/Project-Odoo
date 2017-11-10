# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
import time
from dateutil import relativedelta
from datetime import datetime


class DeliveryStockReport(models.Model):
    _name               = "shop.delivery.stock.report"
    _description        = "Delivery Stock"
    _auto               = False
    _order              = 'date desc'

    product_id          = fields.Many2one('product.product', readonly=True, string="Product")
    date                = fields.Date('Date', readonly=True, help="Date on which this document has been created")
    state               = fields.Selection([
                            ('draft', 'New'), ('cancel', 'Cancelled'),
                            ('waiting', 'Waiting Another Move'), ('confirmed', 'Waiting Availability'),
                            ('assigned', 'Available'), ('done', 'Done')], string='Status', readonly=True)
    picking_id          = fields.Many2one('stock.picking', 'Picking', readonly=True)
    partner_id          = fields.Many2one('res.partner', 'Vendor', readonly=True)
    qty                 = fields.Float('Quantity', readonly=True)
    location_id         = fields.Many2one('stock.location', string='Source Location', readonly=True)
    location_dest_id    = fields.Many2one('stock.location', string='Destination Location', readonly=True)
    end_loc_dest_id     = fields.Many2one('stock.location', string='End Destination Location', readonly=True)
    # note                = fields.Text('Notes', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'shop_delivery_stock_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW shop_delivery_stock_report AS (
                SELECT sm.id, pp.id AS product_id, sm.date::DATE, sm.product_uom_qty AS qty, sp.id AS picking_id, sl.id AS location_id, 
                el.id AS location_dest_id, eel.id AS end_loc_dest_id, sm.state, sp.note, sp.partner_id
                FROM stock_move sm 
                    LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                    LEFT JOIN product_product pp ON pp.id = sm.product_id
                    LEFT JOIN product_template pl ON pl.id = pp.product_tmpl_id
                    LEFT JOIN stock_picking_type spt ON spt.id = sm.picking_type_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS source_location, sl.usage 
                               FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS sl ON sl.id = sp.location_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS dest_location, sl.usage 
                           FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS el ON el.id = sp.location_dest_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS end_dest_location, sl.usage 
                           FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS eel ON eel.id = sp.end_location_dest_id
                WHERE spt.code = 'outgoing' AND sl.usage = 'internal' AND el.usage IN ('transit', 'internal'))""")


class ReceiptStockReport(models.Model):
    _name               = "shop.receipt.stock.report"
    _description        = "Receipt Stock"
    _auto               = False
    _order              = 'date desc'

    date = fields.Date(string='Date', readonly=1)
    location = fields.Many2one('stock.location', string='Location', readonly=1)
    qty = fields.Integer(string='Quantity', readonly=1)
    type = fields.Selection([('receipt', 'Receipt'), ('delivery', 'Delivery'), ('pos', 'Pos'), ('repos', 'Return Pos')],
                            string='Type', readonly=1)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'shop_receipt_stock_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW shop_receipt_stock_report AS (
                select min(u.id) * -1 id, u.date::date, u.location_id as location, u.qty, '1. Total' as type
                from (select qu.id, qu.date, qu.location_id, qu.qty
                          from stock_quantity_update qu
                            join (select min(id) id, date::DATE, location_id
                                  from stock_quantity_update
                                  group by date::DATE, location_id) a on a.id = qu.id
                         ) u  left join stock_move m on u.date::date = m.date::date and (u.location_id = m.location_id or u.location_id = m.location_dest_id)
                group by u.date::date, u.location_id, u.qty
                union              
                /* select min(u.id) id, u.date::date, u.location_id as location, u.qty, '6. Remain' as type
                from (select qu.id, qu.date, qu.location_id, qu.qty
                          from stock_quantity_update qu
                            join (select max(id) id, date, location_id
                                  from stock_quantity_update
                                  group by date, location_id) a on a.id = qu.id
                         ) u  left join stock_move m on u.date::date = m.date::date and (u.location_id = m.location_id or u.location_id = m.location_dest_id)
                group by u.date::date, u.location_id, u.qty */
                select min(u.id) * -1 id, u.date::date, u.location_id as location, case when b.count > 1 then u.qty else 0 end as qty, '6. Remain' as type
                from (select qu.id, qu.date, qu.location_id, qu.qty
                      from stock_quantity_update qu
                          join (select max(id) id, date::DATE, location_id
                                from stock_quantity_update
                                group by date::DATE, location_id) a on a.id = qu.id
                      ) u left join stock_move m on u.date::date = m.date::date and (u.location_id = m.location_id or u.location_id = m.location_dest_id)
                          left join (select max(id) as id, date::date, location_id, count(*) count
                                     from stock_quantity_update 
                                     group by date::date, location_id) b on b.id = u.id
                      group by u.date::date, u.location_id, b.count, u.qty
                UNION
                select min(m.id) id, m.date::date, m.location_dest_id as location, sum(m.product_uom_qty) as qty, '2. Receipt' as type
                from stock_move m
                    left join stock_picking p on p.id = m.picking_id
                    left join stock_picking_type t on t.id = p.picking_type_id
                    left join stock_location l on l.id = m.location_dest_id
                where t.code = 'incoming' and m.state = 'done' and l.usage = 'internal'
                group by m.date::date, m.location_dest_id
                union all
                select min(m.id) id, m.date::date, m.location_id as location, sum(m.product_uom_qty) as qty, '3. Delivery' as type
                from stock_move m
                    left join stock_picking p on p.id = m.picking_id
                    left join stock_picking_type t on t.id = p.picking_type_id
                    left join stock_location l on l.id = m.location_id
                where t.code = 'outgoing' and m.state = 'done' and l.usage = 'internal'
                group by m.date::date, m.location_id
                union
                select min(m.id) id, m.date::date, m.location_id as location, sum(m.product_uom_qty) as qty, '4. Pos' as type
                from stock_move m
                    left join stock_picking_type t on t.id = m.picking_type_id
                    left join stock_location l on l.id = m.location_id
                    left join stock_location l1 on l1.id = m.location_dest_id
                where m.state = 'done' and l.usage = 'internal' and l1.usage = 'customer'
                group by m.date::date, m.location_id
                union
                select min(m.id) id, m.date::date, m.location_dest_id as location, sum(m.product_uom_qty) as qty, '5. Return Pos' as type
                from stock_move m
                    left join stock_picking_type t on t.id = m.picking_type_id
                    left join stock_location l on l.id = m.location_id
                    left join stock_location l1 on l1.id = m.location_dest_id
                where m.state = 'done' and l1.usage = 'internal' and l.usage = 'customer'
                group by m.date::date, m.location_dest_id
                )""")


class StockReportWizard(models.TransientModel):
    _name = 'stock.report.wizard'

    start_date = fields.Date(string='Start Date', default=lambda *a: time.strftime('%Y-%m-01'))
    end_date = fields.Date(string='End Date', default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    type = fields.Selection([('delivery', 'Delivery'), ('receipt', 'Receipt')], string='Type')
    location_id = fields.Many2one('stock.location', string='Location')

    @api.multi
    def open_report(self):
        self.ensure_one()
        tree_view_ref = self.env.ref('project_shop.shop_picking_tree', False)
        form_view_ref = self.env.ref('stock.view_picking_form', False)
        args = []
        # if not action:
        action = {
            'name': '%s Stock Report' % self.type,
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
            'context': {"create": False, "edit": False, "delete": False},
        }
        # else:
        #     action = action[0].read()[0]
        if self.type == 'delivery':
            query = """
                SELECT sp.id
                FROM stock_picking sp 
                    LEFT JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS source_location, sl.usage 
                               FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS sl ON sl.id = sp.location_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS dest_location, sl.usage 
                           FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS el ON el.id = sp.location_dest_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS end_dest_location, sl.usage 
                           FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS eel ON eel.id = sp.end_location_dest_id
                WHERE spt.code = 'outgoing' AND sl.usage = 'internal' AND el.usage IN ('transit', 'internal')
                        """
            if self.start_date:
                if self.end_date:
                    query += """ AND sp.date::DATE >= %s AND sp.date::DATE <= %s"""
                    args += [self.start_date, self.end_date]
                else:
                    query += """ AND sp.date::DATE >= %s"""
                    args += [self.start_date]
            if self.location_id:
                query += """ AND sp.location_id = %s"""
                args += [self.location_id.id]
            self.env.cr.execute(query, tuple(args))
        else:
            query1 = """
                SELECT sp.id, 'received' as receipt_status
                FROM stock_picking sp
                    LEFT JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS source_location, sl.usage 
                           FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS sl ON sl.id = sp.location_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS dest_location, sl.usage 
                       FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS el ON el.id = sp.location_dest_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS end_dest_location, sl.usage 
                       FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS eel ON eel.id = sp.end_location_dest_id
                WHERE el.usage = 'internal' AND ((sl.usage = 'transit' AND sp.receipt_status = 'received' AND sp.state = 'done') OR 
                    (sl.usage = 'supplier' AND sp.state = 'done') OR (sl.usage = 'internal' AND sp.state = 'done'))"""
            query2 = """
                SELECT sp.id, 'waiting' as receipt_status
                FROM stock_picking sp
                    LEFT JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS source_location, sl.usage 
                           FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS sl ON sl.id = sp.location_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS dest_location, sl.usage 
                       FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS el ON el.id = sp.location_dest_id
                    LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS end_dest_location, sl.usage 
                       FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS eel ON eel.id = sp.end_location_dest_id
                WHERE ((el.usage = 'internal' AND ((sl.usage = 'transit' AND sp.state = 'assigned') OR 
                                                  (sl.usage = 'supplier' AND sp.state = 'assigned') OR 
                                                  (sl.usage = 'internal' AND sp.state = 'assigned')))
                      OR 
                      (el.usage = 'transit' AND sl.usage = 'internal' AND sp.state = 'done' AND sp.receipt_status = 'waiting'))
                                    """
            if self.start_date:
                if self.end_date:
                    query1 += """ AND sp.date::DATE >= %s AND sp.date::DATE <= %s"""
                    args += [self.start_date, self.end_date]
                else:
                    query1 += """ AND sp.date::DATE >= %s"""
                    args += [self.start_date]
            if self.location_id:
                query1 += """ AND sp.location_dest_id = %s"""
                args += [self.location_id.id]
            if self.start_date:
                if self.end_date:
                    query2 += """ AND sp.date::DATE >= %s AND sp.date::DATE <= %s"""
                    args += [self.start_date, self.end_date]
                else:
                    query2 += """ AND sp.date::DATE >= %s"""
                    args += [self.start_date]
            if self.location_id:
                query2 += """ AND (el.usage = 'transit' AND sp.end_location_dest_id = %s)"""
                args += [self.location_id.id]
            self.env.cr.execute(query1 + """ UNION ALL""" + query2, tuple(args))
            print query1 + """ UNION ALL""" + query2, tuple(args)
        pickings = self.env.cr.fetchall()
        # print pickings
        action['domain'] = pickings and str([('id', 'in', [rec[0] for rec in pickings])]) or str([('id', '=', False)])
        action['name'] = '%s Stock Report' % (self.type[:1].upper() + self.type[1:])
        print action
        return action

    # @api.multi
    # def open_report(self):
    #     self.ensure_one()
    #
    #     # action = self.env['ir.model.data'].xmlid_to_object('stock.stock_move_action')
    #     tree_view_ref = self.env.ref('project_shop.view_shop_stock_move_inherit_tree', False)
    #     form_view_ref = self.env.ref('stock.view_move_form', False)
    #     # if not action:
    #     action = {
    #         'name': '%s Stock Report' % self.type,
    #         'view_type': 'form',
    #         'view_mode': 'tree',
    #         'res_model': 'stock.move',
    #         'type': 'ir.actions.act_window',
    #         'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
    #         'context': {"create": False, "edit": False, "delete": False},
    #     }
    #     # else:
    #     #     action = action[0].read()[0]
    #
    #     if self.type == 'delivery':
    #         query = """
    #             SELECT sm.id
    #             FROM stock_move sm
    #                 LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
    #                 LEFT JOIN stock_picking_type spt ON spt.id = sm.picking_type_id
    #                 LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS source_location, sl.usage
    #                            FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS sl ON sl.id = sp.location_id
    #                 LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS dest_location, sl.usage
    #                        FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS el ON el.id = sp.location_dest_id
    #                 LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS end_dest_location, sl.usage
    #                        FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS eel ON eel.id = sp.end_location_dest_id
    #             WHERE spt.code = 'outgoing' AND sl.usage = 'internal' AND el.usage IN ('transit', 'internal')
    #                     """
    #         if self.start_date:
    #             if self.end_date:
    #                 query += """ AND sm.date::DATE >= %s AND sm.date::DATE <= %s"""
    #                 self.env.cr.execute(query, (self.start_date, self.end_date))
    #             else:
    #                 query += """ AND sm.date::DATE >= %s"""
    #                 self.env.cr.execute(query, (self.start_date,))
    #         else:
    #             self.env.cr.execute(query)
    #     else:
    #         query1 = """
    #             SELECT sm.id, 'received' as receipt_status
    #             FROM stock_move sm
    #                 LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
    #                 LEFT JOIN stock_picking_type spt ON spt.id = sm.picking_type_id
    #                 LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS source_location, sl.usage
    #                        FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS sl ON sl.id = sp.location_id
    #                 LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS dest_location, sl.usage
    #                    FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS el ON el.id = sp.location_dest_id
    #                 LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS end_dest_location, sl.usage
    #                    FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS eel ON eel.id = sp.end_location_dest_id
    #             WHERE el.usage = 'internal' AND ((sl.usage = 'transit' AND sp.receipt_status = 'received' AND sm.state = 'done') OR
    #                 (sl.usage = 'supplier' AND sm.state = 'done') OR (sl.usage = 'internal' AND sm.state = 'done'))"""
    #         query2 = """
    #             SELECT sm.id, 'waiting' as receipt_status
    #             FROM stock_move sm
    #                 LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
    #                 LEFT JOIN stock_picking_type spt ON spt.id = sm.picking_type_id
    #                 LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS source_location, sl.usage
    #                        FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS sl ON sl.id = sp.location_id
    #                 LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS dest_location, sl.usage
    #                    FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS el ON el.id = sp.location_dest_id
    #                 LEFT JOIN (SELECT sl.id, CASE WHEN sl.location_id IS NULL THEN sl.name ELSE slp.name || '/' || sl.name END AS end_dest_location, sl.usage
    #                    FROM stock_location sl LEFT JOIN stock_location slp ON slp.id = sl.location_id) AS eel ON eel.id = sp.end_location_dest_id
    #             WHERE (el.usage = 'internal' AND ((sl.usage = 'transit' AND sm.state = 'assigned') OR
    #                                               (sl.usage = 'supplier' AND sm.state = 'assigned') OR
    #                                               (sl.usage = 'internal' AND sm.state = 'assigned')))
    #                   OR
    #                   (el.usage = 'transit' AND sl.usage = 'internal' AND sm.state = 'done' AND sp.receipt_status = 'waiting')
    #                                 """
    #         if self.start_date:
    #             if self.end_date:
    #                 query1 += """ AND sm.date::DATE >= %s AND sm.date::DATE <= %s"""
    #                 query2 += """ AND sm.date::DATE >= %s AND sm.date::DATE <= %s"""
    #                 self.env.cr.execute(query1 + """ UNION ALL """ + query2, (self.start_date, self.end_date, self.start_date, self.end_date))
    #             else:
    #                 query1 += """ AND sm.date::DATE >= %s"""
    #                 query2 += """ AND sm.date::DATE >= %s"""
    #                 self.env.cr.execute(query1 + """ UNION ALL """ + query2, (self.start_date, self.start_date))
    #         else:
    #             self.env.cr.execute(query1 + """ UNION ALL""" + query2)
    #     moves = self.env.cr.fetchall()
    #     print moves
    #     action['domain'] = moves and str([('id', 'in', [rec[0] for rec in moves])]) or "[('id', '=', " + False + ")]"
    #     action['name'] = '%s Stock Report' % (self.type[:1].upper() + self.type[1:])
    #     print action
    #     return action


# class StockReportDateAnalysis(models.Model):
#     _name = 'stock.report.date.analysis'
#
#     date = fields.Date(string='Date', readonly=1)
#     location_id = fields.Many2one('stock.location', string='Location', readonly=1)
#     qty = fields.Integer(string='Quantity', readonly=1)
#     type = fields.Selection([('receipt', 'Receipt'), ('delivery', 'Delivery'), ('pos', 'Pos'), ('repos', 'Return Pos')],
#                             string='Type', readonly=1)
#
#     @api.model_cr
#     def init(self):
#         tools.drop_view_if_exists(self._cr, 'stock_report_date_analysis')
#         self._cr.execute("""
#                 CREATE OR REPLACE VIEW stock_report_date_analysis AS (
#                     select min(m.id) id, m.date::date, m.location_dest_id as location, sum(m.product_uom_qty) as qty, 'Receipt' as type
#                     from stock_move m
#                         left join stock_picking p on p.id = m.picking_id
#                         left join stock_picking_type t on t.id = p.picking_type_id
#                         left join stock_location l on l.id = m.location_dest_id
#                     where t.code = 'incoming' and m.state = 'done' and l.usage = 'internal'
#                     group by m.date::date, m.location_dest_id
#                     union all
#                     select min(m.id) id, m.date::date, m.location_id as location, sum(m.product_uom_qty) as qty, 'Delivery' as type
#                     from stock_move m
#                         left join stock_picking p on p.id = m.picking_id
#                         left join stock_picking_type t on t.id = p.picking_type_id
#                         left join stock_location l on l.id = m.location_id
#                     where t.code = 'outgoing' and m.state = 'done' and l.usage = 'internal'
#                     group by m.date::date, m.location_id
#                     union all
#                     select min(m.id) id, m.date::date, m.location_id as location, sum(m.product_uom_qty) as qty, 'Pos' as type
#                     from stock_move m
#                         left join stock_picking_type t on t.id = m.picking_type_id
#                         left join stock_location l on l.id = m.location_id
#                         left join stock_location l1 on l1.id = m.location_dest_id
#                     where m.state = 'done' and l.usage = 'internal' and l1.usage = 'customer'
#                     group by m.date::date, m.location_id
#                     union all
#                     select min(m.id) id, m.date::date, m.location_dest_id as location, sum(m.product_uom_qty) as qty, 'Return Pos' as type
#                     from stock_move m
#                         left join stock_picking_type t on t.id = m.picking_type_id
#                         left join stock_location l on l.id = m.location_id
#                         left join stock_location l1 on l1.id = m.location_dest_id
#                     where m.state = 'done' and l1.usage = 'internal' and l.usage = 'customer'
#                     group by m.date::date, m.location_dest_id
#                    )""")
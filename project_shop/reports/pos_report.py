# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
import time
from dateutil import relativedelta
from datetime import datetime


class PosReport(models.Model):
    _name = "pos.session.report"
    _description = "Pos Session Analysis"
    _auto = False
    _order = 'start_at desc'

    payment_date = fields.Date(string='Payment Date', readonly=True)
    start_at = fields.Date(string='Date Open', readonly=True)
    session_id = fields.Many2one('pos.session', string='Session', readonly=True)
    state = fields.Selection(
        [('opening_control', 'Opening Control'),  # method action_pos_session_open
        ('opened', 'In Progress'),               # method action_pos_session_closing_control
        ('closing_control', 'Closing Control'),  # method action_pos_session_close
        ('closed', 'Closed & Posted')],
        string='Status')
    payment_status = fields.Selection([('open', 'New'), ('confirm', 'Validated')], string='Payment Status')
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Payment Method')
    config_id = fields.Many2one('pos.config', string='Point of Sale', readonly=True)
    amount = fields.Float(string='Amount', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'pos_session_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW pos_session_report AS (                
                SELECT b.id, bl.date AS payment_date, SUM(bl.amount) AS amount, ps.id as session_id, 
                       b.journal_id, ps.config_id, ps.user_id, ps.start_at::DATE, ps.state, b.state AS payment_status
                FROM account_bank_statement_line bl 
                    LEFT JOIN account_bank_statement b ON b.id = bl.statement_id
                    LEFT JOIN pos_session ps ON ps.id = b.pos_session_id
                GROUP BY ps.id, bl.date, b.id , b.journal_id, ps.config_id, ps.user_id, ps.start_at::DATE, ps.state, b.state
            )
        """)


class PosReportFinalAnalysis(models.Model):
    _name = "pos.report.final.analysis"
    _description = "Final Pos Analysis"
    _auto = False
    _order = 'start_at desc'

    material = fields.Char(string='Material Code', readonly=True)
    qty = fields.Integer(string='Quantity')
    price_avg = fields.Float(string='Price Average')
    # session_id = fields.Many2one('pos.session', string='Session', readonly=True)
    # state = fields.Selection(
    #     [('draft', 'New'), ('cancel', 'Cancelled'), ('paid', 'Paid'), ('done', 'Posted'), ('invoiced', 'Invoiced')],
    #     string='Status', readonly=True)
    # user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    # location_id = fields.Many2one('stock.location', string='Location', readonly=True)
    # config_id = fields.Many2one('pos.config', string='Point of Sale', readonly=True)
    amount = fields.Float(string='Total', readonly=True)
    date_order = fields.Date(string='Date Order', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'pos_report_final_analysis')
        self._cr.execute("""
            CREATE OR REPLACE VIEW pos_report_final_analysis AS (                
                SELECT MIN(pt.id) AS id, pt.name || ' (' || pt.default_code || ')' AS material, po.date_order::DATE, SUM(pol.qty) AS qty, SUM(pol.price_unit)/COUNT(*) AS price_avg, SUM(pol.qty) * SUM(pol.price_unit)/COUNT(*) AS amount
                FROM product_product pp
                    LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    LEFT JOIN pos_order_line pol ON pol.product_id = pp.id
                    LEFT JOIN pos_order po ON po.id = pol.order_id
                    LEFT JOIN pos_session ps ON ps.id = po.session_id
                GROUP BY pt.name || ' (' || pt.default_code || ')', po.date_order::DATE 	
            )
        """)


class PosOrderMaterial(models.TransientModel):
    _name = 'pos.order.material'

    material = fields.Char(string='Material Code')
    qty = fields.Integer(string='Quantity')
    pur_price = fields.Float(string='Purchase Price')
    sale_price = fields.Float(string='Sale Price Avg')
    amount = fields.Float(string='Amount')
    profit = fields.Float(string='Profit')
    stock = fields.Float(string='In Stock')
    shop = fields.Float(string='In Shop')
    transit = fields.Float(string='Transit')
    total = fields.Float(string='Stock Total')
    parent_id = fields.Many2one('pos.report.final', string='Parent')


class PosReportFinal(models.TransientModel):
    _name = 'pos.report.final'

    material_ids = fields.One2many('pos.order.material', 'parent_id', string='Material Analysis')


class PosReportWizard(models.TransientModel):
    _name = 'pos.report.wizard'

    date_start = fields.Date(string='Start Date', default=lambda *a: time.strftime('%Y-%m-01'))
    date_end = fields.Date(string='End Date', default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])

    @api.multi
    def open_report(self):
        self.ensure_one()
        tree_view_ref = self.env.ref('project_shop.custom_pos_order_material_tree', False)

        args = []
        # if not action:
        action = {
            'name': 'Pos Report',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'pos.order.material',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_ref.id, 'tree')],
            'context': {"create": False, "edit": False, "delete": False},
        }

        query1 = """
            select sale.default_code, sale.qty, sale.sale_price, pur.pur_price, sale.sale_price * sale.qty as amount, 
                sale.qty * (sale.sale_price - pur.pur_price) as profit, total.total AS stock, shop.total as shop, transit.total as transit
            from (
                select pp.default_code, sum(pol.qty) qty, sum(pol.price_unit) / count(*) as sale_price, count(*) count
                from pos_order_line pol 
                    left join pos_order po on po.id = pol.order_id
                    left join product_product pp on pp.id = pol.product_id
                    left join purchase_order_line pul on pul.product_id = pp.id"""
        query2 = """
                group by pp.default_code
            ) sale 
            left join (
                select pp.default_code, sum(price_unit) / count(*) as pur_price
                from purchase_order_line pul 
                    left join purchase_order po on po.id = pul.order_id
                    left join product_product pp on pp.id = pul.product_id
                where po.state = 'purchase'"""
        query3 = """
                group by pp.default_code
            ) pur on pur.default_code = sale.default_code
            left join (
                select pp.default_code, sum(sq.qty) total
                from stock_quant sq 
                    left join stock_location sl on sl.id = sq.location_id
                    left join stock_location sl1 on sl1.id = sl.location_id
                    left join product_product pp on pp.id = sq.product_id
                where sl.usage = 'internal' and sl1.name = 'WH'
                group by pp.default_code
            ) total on total.default_code = sale.default_code
            left join (
                select pp.default_code, sum(sq.qty) total
                from stock_quant sq 
                    left join stock_location sl on sl.id = sq.location_id
                    left join stock_location sl1 on sl1.id = sl.location_id
                    left join product_product pp on pp.id = sq.product_id
                where sl.usage = 'internal' and sl1.name <> 'WH'
                group by pp.default_code
            ) shop on shop.default_code = sale.default_code
            left join (
                select pp.default_code, sum(sm.product_uom_qty) total
                from stock_move sm 
                    left join stock_location sl on sl.id = sm.location_dest_id
                    left join product_product pp on pp.id = sm.product_id
                where sl.usage = 'transit' and sm.state = 'done'
                group by pp.default_code
            ) transit on transit.default_code = sale.default_code
        """
        if self.date_start:
            if self.date_end:
                query1 += """ where po.date_order::DATE >= %s AND po.date_order::DATE <= %s"""
                query2 += """ and po.date_order::DATE >= %s AND po.date_order::DATE <= %s"""
                args += [self.date_start, self.date_end, self.date_start, self.date_end]
            else:
                query1 += """ where po.date_order::DATE >= %s"""
                query2 += """ and po.date_order::DATE >= %s"""
                args += [self.date_start, self.date_start]

        self.env.cr.execute(query1 + query2 + query3, tuple(args))

        pickings = self.env.cr.fetchall()
        materials = []
        if pickings:
            for pick in pickings:
                mat = self.env['pos.order.material'].create({'material': pick[0], 'qty': pick[1],
                                     'sale_price': pick[2], 'pur_price': pick[3],
                                     'amount': pick[4], 'profit': pick[5],
                                     'stock': pick[6], 'shop': pick[7], 'transit': pick[8]})
                materials.append(mat.id)

        # print pickings
        action['domain'] = pickings and str([('id', 'in', materials)]) or str([('id', '=', False)])
        action['name'] = 'Pos Report Final'
        print action
        return action

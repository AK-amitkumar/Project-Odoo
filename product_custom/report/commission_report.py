from odoo import models, fields, api, tools

class AnalysisCommission(models.Model):
    _name = "analysis.commission.report"
    _auto = False
    _description = "Commission Analysis"

    order_id    = fields.Many2one('pos.order', string='Order', readonly=True)
    user_id     = fields.Many2one('res.users', string='Salesperson', readonly=True)
    product_id  = fields.Many2one('product.product', string='Product', readonly=True)
    qty         = fields.Float(string='Quantity', readonly=True)
    date_order  = fields.Date(string='Date Order', readonly=True)
    discount    = fields.Float(string='Discount', readonly=True)
    commission  = fields.Float(string='Commission', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'analysis_commission_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW analysis_commission_report AS (
                SELECT pol.id, pol.order_id, po.user_id, pol.product_id, SUM(pol.qty) qty, po.date_order::DATE, pdl.discount, SUM(pol.qty * pdl.discount) commission
                FROM pos_order_line pol
                    LEFT JOIN pos_order po ON po.id = pol.order_id
                    LEFT JOIN product_product pp ON pp.id = pol.product_id
                    LEFT JOIN product_discount_line pdl ON pdl.product_id = pp.id
                    LEFT JOIN product_discount pd ON pd.id = pdl.discount_id AND po.date_order::DATE >= pd.date_from and po.date_order::DATE <= pd.date_to
                GROUP BY pol.id, pol.order_id, po.user_id, pol.product_id, po.date_order, pdl.discount
            )""")
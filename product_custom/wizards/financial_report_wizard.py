# -*- coding: utf-8 -*-
from odoo import models, fields, api
import time
from datetime import datetime
from dateutil import relativedelta

class FinancialReportWizard(models.TransientModel):
    _name       = 'financial.report.wizard'

    date_from   = fields.Date(string='Date from', default=lambda *a: time.strftime('%Y-%m-01'))
    date_to     = fields.Date(string='Date to', default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    type        = fields.Selection([('financial', 'Financial'), ('revenue', 'Revenue')], string='Report Type', default='financial')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if self.date_from and self.date_to and  self.date_from > self.date_to:
            raise ValidationError(_("The Date from must be lower than Date to."))

    @api.multi
    def get_sales_revenue(self):
        cr = self.env.cr
        result = []
        # pos = self.env['pos.order'].search([('date_order', '>=', self.date_from + ' 00:00:00'), ('date_order', '<=', self.date_to + ' 23:59:59'), ('state', '=', 'done')])
        cr.execute("""  SELECT pol.id, pol.product_id, po.date_order::DATE , pol.qty, pol.price_unit, pol.discount, string_agg(atx.name, ', ') AS tax
                        FROM pos_order_line pol 
                            LEFT JOIN pos_order po ON po.id = pol.order_id
                            LEFT JOIN account_tax_pos_order_line_rel apr ON apr.pos_order_line_id = pol.id
                            LEFT JOIN account_tax atx ON atx.id = apr.account_tax_id
                        WHERE po.date_order::DATE >= %s AND po.date_order::DATE <= %s AND state = 'done'
                        GROUP BY pol.id, pol.product_id, po.date_order::DATE , pol.qty, pol.price_unit, pol.discount""",
                   (self.date_from, self.date_to))
        pos = cr.dictfetchall()
        if pos:
            for order in pos:
                item = {
                    'name': order['product_id'] and self.env['product.product'].search([('id', '=', order['product_id'])]).name or False,
                    'date': datetime.strptime(order['date_order'], '%Y-%m-%d').strftime('%d-%m-%Y'),
                    'quantity': order['qty'],
                    'price_unit': order['price_unit'],
                    'discount': order['discount'],
                    'tax': order['tax'],
                    'amount': self.env['pos.order.line'].search([('id', '=', order['id'])]).price_subtotal
                }
                result.append(item)
        cr.execute("""  SELECT ail.product_id, am.date, ail.quantity, ail.price_unit, ail.discount, string_agg(atx.name, ', ') AS tax, ail.price_subtotal
                        FROM account_move am
                            LEFT JOIN account_move_line aml ON aml.move_id = am.id
                            LEFT JOIN account_invoice_account_move_line_rel imr ON imr.account_move_line_id = aml.id
                            LEFT JOIN account_invoice ai ON ai.id = imr.account_invoice_id
                            LEFT JOIN account_invoice_line ail ON ail.invoice_id = ai.id
                            LEFT JOIN account_invoice_line_tax ait ON ait.invoice_line_id = ail.id
                            LEFT JOIN account_tax atx ON atx.id = ait.tax_id
                        WHERE am.date::DATE >= %s AND am.date::DATE <= %s AND ai.state = 'paid' AND ai.type IN ('out_invoice', 'out_refund')
                        GROUP BY ail.product_id, am.date, ail.quantity, ail.price_unit, ail.discount, ail.price_subtotal""",
                   (self.date_from, self.date_to))
        sale_orders = cr.dictfetchall()
        if sale_orders:
            for order in sale_orders:
                item = {
                    'name': order['product_id'] and self.env['product.product'].search([('id', '=', order['product_id'])]).name or False,
                    'date': datetime.strptime(order['date'], '%Y-%m-%d').strftime('%d-%m-%Y'),
                    'quantity': order['quantity'],
                    'price_unit': order['price_unit'],
                    'discount': order['discount'],
                    'tax': order['tax'],
                    'amount': order['price_subtotal']
                }
                result.append(item)
        return result

    @api.multi
    def get_total_revenue(self):
        cr = self.env.cr
        sum = 0
        pos = self.env['pos.order'].search([('date_order', '>=', self.date_from + ' 00:00:00'), ('date_order', '<=', self.date_to + ' 23:59:59'),('state', '=', 'done')])
        if pos:
            for order in pos:
                sum += order.amount_total
        # sales = self.env['account.invoice'].search([('date_invoice', '>=', self.date_from), ('date_invoice', '<=', self.date_to),
        #                                             ('state', '=', 'paid'), ('type', 'in', ['out_invoice', 'in_refund'])])
        cr.execute("""  SELECT COALESCE(SUM(am.amount), 0) AS amount
                        FROM account_move am
                            LEFT JOIN account_move_line aml ON aml.move_id = am.id
                            LEFT JOIN account_invoice_account_move_line_rel imr ON imr.account_move_line_id = aml.id
                            LEFT JOIN account_invoice ai ON ai.id = imr.account_invoice_id
                        WHERE am.date::DATE >= %s AND am.date::DATE <= %s AND ai.state = 'paid' AND ai.type IN ('out_invoice', 'out_refund')""",
                   (self.date_from, self.date_to))
        sum += cr.fetchone()[0]
        return sum

    @api.multi
    def get_costs(self):
        cr = self.env.cr
        result = []
        # bills = self.env['account.invoice'].search([('date_invoice', '>=', self.date_from), ('date_invoice', '<=', self.date_to),
        #                                             ('state', '=', 'paid'), ('type', 'in', ['in_invoice', 'out_refund'])])
        cr.execute("""  SELECT ail.product_id, am.date, ail.quantity, ail.price_unit, ail.discount, string_agg(atx.name, ', ') AS tax, ail.price_subtotal
                        FROM account_move am
                            LEFT JOIN account_move_line aml ON aml.move_id = am.id
                            LEFT JOIN account_invoice_account_move_line_rel imr ON imr.account_move_line_id = aml.id
                            LEFT JOIN account_invoice ai ON ai.id = imr.account_invoice_id
                            LEFT JOIN account_invoice_line ail ON ail.invoice_id = ai.id
                            LEFT JOIN account_invoice_line_tax ait ON ait.invoice_line_id = ail.id
                            LEFT JOIN account_tax atx ON atx.id = ait.tax_id
                        WHERE am.date::DATE >= %s AND am.date::DATE <= %s AND ai.state = 'paid' AND ai.type IN ('in_invoice', 'in_refund')
                        GROUP BY ail.product_id, am.date, ail.quantity, ail.price_unit, ail.discount, ail.price_subtotal""",
                   (self.date_from, self.date_to))
        bills = cr.dictfetchall()
        if bills:
            for order in bills:
                item = {
                    'name': order['product_id'] and self.env['product.product'].search([('id', '=', order['product_id'])]).name or False,
                    'date': datetime.strptime(order['date'], '%Y-%m-%d').strftime('%d-%m-%Y'),
                    'quantity': order['quantity'],
                    'price_unit': order['price_unit'],
                    'discount': order['discount'],
                    'tax': order['tax'],
                    'amount': order['price_subtotal']
                }
                result.append(item)
        return result

    @api.multi
    def get_total_costs(self):
        cr = self.env.cr
        sum = 0
        # bills = self.env['account.invoice'].search([('date_invoice', '>=', self.date_from), ('date_invoice', '<=', self.date_to),
        #                                             ('state', '=', 'paid'), ('type', 'in', ['in_invoice', 'out_refund'])])
        cr.execute("""  SELECT COALESCE(SUM(am.amount), 0) AS amount
                        FROM account_move am
                            LEFT JOIN account_move_line aml ON aml.move_id = am.id
                            LEFT JOIN account_invoice_account_move_line_rel imr ON imr.account_move_line_id = aml.id
                            LEFT JOIN account_invoice ai ON ai.id = imr.account_invoice_id
                        WHERE am.date::DATE >= %s AND am.date::DATE <= %s AND ai.state = 'paid' AND ai.type IN ('in_invoice', 'in_refund')""",
                    (self.date_from, self.date_to))
        sum += cr.fetchone()[0]
        return sum

    @api.multi
    def get_salary(self):
        result = []
        payslips = self.env['hr.payslip'].search([('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to), ('state', '=', 'done')])
        if payslips:
            for payslip in payslips:
                item = {
                    'name': payslip.employee_id.name,
                    'date': datetime.strptime(payslip.date_from, '%Y-%m-%d').strftime('%d-%m-%Y'),
                    'amount': payslip.line_ids and payslip.line_ids[-1].amount or 0
                }
                result.append(item)
        return result

    @api.multi
    def get_total_payslips(self):
        sum = 0
        payslips = self.env['hr.payslip'].search([('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to), ('state', '=', 'done')])
        if payslips:
            for ps in payslips:
                sum += ps.line_ids and ps.line_ids[-1].amount or 0
        return sum


    @api.multi
    def convert_type(self, total):
        return '{0:,.0f}'.format(int(total)) if total <> 0 else 0

    @api.multi
    def print_report(self):
        return self.env['report'].get_action(self, 'product_custom.financial_report')
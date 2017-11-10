# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HrHolidaysStatus(models.Model):
    _inherit    = 'hr.holidays.status'

    code        = fields.Char(string='Code')


class HrPayroll(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        res = super(HrPayroll, self).get_inputs(contract_ids, date_from=date_from, date_to=date_to)
        for item in res:
            if item['code'] == 'HH':
                if item['contract_id']:
                    employee = self.env['hr.contract'].browse(item['contract_id']).employee_id
                    if employee and employee.user_id:
                        self._cr.execute("""SELECT SUM(pol.qty * pdl.discount)
                                            FROM pos_order_line pol 
                                                LEFT JOIN pos_order po ON po.id = pol.order_id
                                                LEFT JOIN product_discount_line pdl ON pdl.product_id = pol.product_id
                                                LEFT JOIN product_discount pd ON pd.id = pdl.discount_id and pd.date_from <= po.date_order::DATE AND pd.date_to >= po.date_order::DATE 
                                            WHERE po.user_id = %s AND po.date_order::DATE >= %s AND po.date_order::DATE <= %s""", (employee.user_id.id, date_from, date_to))
                        result = self._cr.fetchone()
                        amount = result and result[0] or 0
                        item.update({
                            'amount': amount,
                        })
        return res

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        res = super(HrPayroll, self).get_worked_day_lines(contract_ids, date_from=date_from, date_to=date_to)
        contract = self.env['hr.contract'].browse(contract_ids)
        worked_month = {
            'name': _("Ngày công chuẩn"),
            'sequence': 3,
            'code': 'WORK_MONTH',
            'number_of_days': 26,
            'number_of_hours': 0.0,
            'contract_id': contract.id,
        }
        work_time = {
            'name': _("Ngày công thực tế"),
            'sequence': 4,
            'code': 'WORK_TIME',
            'number_of_days': 0.0,
            'number_of_hours': 0.0,
            'contract_id': contract.id,
        }
        res += [worked_month] + [work_time]
        holidays = self.env['hr.holidays'].search([('employee_id', '=', self.employee_id.id), ('date_from', '>=', date_from), ('date_to', '<=', date_to), ('state', '=', 'validate')])
        unpaid = sum([l.number_of_days_temp for l in holidays if l.holiday_status_id.code.upper() == 'UNPAID']) if holidays else 0
        # if unpaid:
        unpaid_wk = {
            'name': _("Nghỉ không lương"),
            'sequence': 10,
            'code': 'UNPAID',
            'number_of_days': unpaid,
            'number_of_hours': 0.0,
            'contract_id': contract.id,
        }
        res += [unpaid_wk]
        return res
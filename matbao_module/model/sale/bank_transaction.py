# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2017 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BankTransaction(models.Model):
    _name = 'bank.transaction'
    _description = 'Bank Transaction'
    _rec_name = 'code'

    code = fields.Char("Code", required=False, readonly=True)
    amount = fields.Float("Amount", required=True)
    journal_id = fields.Many2one(
        'account.journal', string="Payment Method",
        required=True, readonly=False, domain="[('type', '=', 'bank')]")
    is_reconciled = fields.Boolean(
        'Is Reconciled', readonly=True)
    description = fields.Text('Description')
    order_id = fields.Many2one(
        'sale.order', string="Sale Order", readonly=True)
    invoice_id = fields.Many2one('account.invoice', 'Invoice', readonly=True)
    payment_id = fields.Many2one('account.payment', 'Payment', readonly=True)
    account_move_id = fields.Many2one('account.move', 'Journal Entry')
    writeoff_journal_id = fields.Many2one('account.move',
                                          'Writeoff Journal Entry')

    @api.model
    def create(self, vals):
        bank_tns = super(BankTransaction, self).create(vals)

        AccountMove = self.env['account.move']

        ir_values_obj = self.env['ir.values']
        partner_id = ir_values_obj.get_default('sale.config.settings',
                                               'partner_id')

        move_vals = {
            'journal_id': bank_tns.journal_id.id,
            'date': bank_tns.create_date,
            'reference': bank_tns.code,
            'bank_transaction_id': bank_tns.id,
            }
        debit_vals = {
            'account_id': bank_tns.journal_id.default_debit_account_id.id,
            'debit': bank_tns.amount,
            'name': 'Khách hàng thanh toán online',
            'bank_transaction_id': bank_tns.id,
            'partner_id': partner_id or False,
            }
        credit_vals = {'account_id': int(self.env['ir.property'].with_context(force_company=bank_tns.journal_id.company_id.id).get(
            'property_account_receivable_id', 'res.partner')),
                   'credit': bank_tns.amount,
                   'name': 'Khách hàng thanh toán online',
                   'bank_transaction_id': bank_tns.id,
                   'partner_id': partner_id or False,
                   }
        move_vals.update({'line_ids': [(0, 0, debit_vals),
                                       (0, 0, credit_vals)]})
        journal = AccountMove.create(move_vals)
        journal.post()
        bank_tns.account_move_id = journal.id
        return bank_tns

    @api.multi
    def button_unreconcile(self):
        bank_trs_ids = self.with_context(
            force_unlink=True, force_update=True).filtered(
                lambda r: r.is_reconciled is True)

        ir_values_obj = self.env['ir.values']
        partner_id = ir_values_obj.get_default('sale.config.settings',
                                               'partner_id')
        for bank_trs in bank_trs_ids:
            if not bank_trs.is_reconciled:
                continue

            domain = [('order_id', '=', bank_trs.order_id.id)]
            trs_ids = self.env['bank.transaction'].search(domain)

            # unreconcile bank transaction move line
            # and customer invoice (journal entry) move line
            invoice = bank_trs.invoice_id
            default_acc_id = int(self.env['ir.property'].get(
                'property_account_receivable_id', 'res.partner'))
            inv_move_line = invoice.move_id.line_ids.filtered(
                lambda r: r.account_id.id == default_acc_id)
            trs_move_line = bank_trs.account_move_id.line_ids.filtered(
                lambda r: r.account_id.id == default_acc_id)
            write_off_lines = bank_trs.writeoff_journal_id.line_ids.filtered(
                lambda r: r.account_id.id == default_acc_id)
            (trs_move_line + inv_move_line + write_off_lines).remove_move_reconcile()

            if bank_trs.writeoff_journal_id:
                # delete writeoff journal entry if exists
                bank_trs.writeoff_journal_id.with_context(
                    force_update=True).write({'state': 'draft'})
                partial_ids = self.env['account.partial.reconcile'].search(
                    ["|",
                     ('debit_move_id', 'in', bank_trs.writeoff_journal_id.line_ids.ids),
                     ('credit_move_id', 'in', bank_trs.writeoff_journal_id.line_ids.ids)])
                partial_ids.unlink()
                bank_trs.writeoff_journal_id.unlink()

            # remove customer invoice
            invoice.move_id.with_context(force_update=True).write(
                    {'state': 'draft'})
            partial_ids = self.env['account.partial.reconcile'].search(
                    ["|",
                     ('debit_move_id', 'in', invoice.move_id.line_ids.ids),
                     ('credit_move_id', 'in', invoice.move_id.line_ids.ids)])
            partial_ids.unlink()
            move_id = invoice.move_id
            invoice.move_id = False
            move_id.unlink()
            invoice.write({'state': 'cancel'})
            invoice.with_context(force_unlink=True).unlink()

            vals = {'is_reconciled': False,
                    'order_id': False,
                    'invoice_id': False,
                    }
            domain = [('order_id', '=', bank_trs.order_id.id)]
            trs_ids = self.env['bank.transaction'].search(domain)
            trs_ids.write(vals)
            trs_move_ids = trs_ids.mapped('account_move_id.line_ids')
            trs_move_ids.write({
                'partner_id': partner_id or False})

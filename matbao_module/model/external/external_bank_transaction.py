# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare
import json


class ExternalBankTransaction(models.AbstractModel):
    _description = 'External Bank Transaction API'
    _name = 'external.bank.transaction'

    @api.model
    def process_bt(self, code, amount, journal_id, description):
        res = {'code': 0, 'msg': ''}
        AccountJournal = self.env['account.journal']
        if not code:
            res['msg'] = "Code could not be empty"
            return res
        if amount == 0:
            res['msg'] = "Amount must be difference 0"
            return res
        payment_method_id = AccountJournal.search(
            [('name', '=', journal_id), ('type', '=', 'bank')])
        if not payment_method_id:
            res['msg'] = "Payment method must be Bank"
            return res
        # Create Bank Transaction
        bank_transaction_id = self.env['bank.transaction'].create({
            'code': code,
            'amount': amount,
            'journal_id': payment_method_id.id,
            'description': description,
        })
        if bank_transaction_id:
            res['code'] = 1
        return res
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, DEFAULT_SERVER_DATE_FORMAT as DF
from ..sale.sale_order_line import REGISTER_TYPE
import re
from odoo.exceptions import UserError
import logging as _logger
# _logger = logging.getLogger(__name__)

class ExternalMixFunction(models.AbstractModel):
    _name = 'external.mix.function'

    @api.model
    def mix_function(self, name, coupon, date_order, saleteam_code, order_type, customer, status, company_id,
                     payment_amount, payment_journal, payment_date, memo, lines=[]):
        # Create Customer, SO
        print 22222222222222222222222222
        _logger.info('1111111111111111111111')
        try:
            create_so = self.env['external.so'].create_so_fix(name, coupon, date_order, saleteam_code, order_type, customer, status, company_id, lines=lines)
        except:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Order name can`t create"'}
        if type(create_so) is not dict or create_so.get('code') <> 1:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Order name can`t create 1: %s"' % (type(create_so) is dict and create_so.get('msg') or 'Func create_so_fix not return dict')}
        order_id = create_so.get('data')
        _logger.info('22222222222222222222222222')
        if payment_amount > 0:
            try:
                receive_money = self.env['external.receive.money'].receive_money(order_id.partner_id.ref, payment_amount, payment_journal, payment_date, memo)
            except:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"Cant`t add funds for customer %s"' % order_id.partner_id.name}
            if type(receive_money) is not dict or receive_money.get('"code"') <> 1:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"Cant`t add funds for customer %s 1: %s"' % (order_id.partner_id.name, (type(receive_money) is dict and receive_money.get('"msg"')))}
        _logger.info('3333333333333333333333')
        try:
            subtract_money = self.env['external.subtract.money.so'].subtract_money_so(order_id.name)
        except:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t subtract money for SO %s"' % order_id.name}
        if type(subtract_money) is not dict or subtract_money.get('"code"') <> 1:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t subtract money for SO %s 1: %s"' % (order_id.name, (type(subtract_money) is dict and subtract_money.get('"msg"')))}
        _logger.info('44444444444444444444')
        try:
            if order_id.fully_paid:
                active_service = self.env['external.active.service'].active_service(order_id.name)
            else:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"SO %s have not yet fully paid"' % order_id.name}
        except:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t active service for SO %s"' % order_id.name}
        if type(active_service) is not dict or active_service.get('code') <> 1:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t active service for SO %s 1: %s"' % (order_id.name, active_service.get('msg'))}
        return {'"code"': 1, '"msg"': '"Successfully!!!"'}
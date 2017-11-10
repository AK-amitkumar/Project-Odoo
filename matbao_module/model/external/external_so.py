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

from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, DEFAULT_SERVER_DATE_FORMAT as DF
from ..sale.sale_order_line import REGISTER_TYPE
import re
from odoo.exceptions import UserError
import logging as _logger


class ExternalSO(models.AbstractModel):
    _description = 'External SO API'
    _name = 'external.so'

    @api.multi
    def _validate_email(self, email_list):
        """
            TO DO:
            - Validate the format of emails
        """

        if any(re.match(
            "^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\"
            ".([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$",
                email) == None for email in email_list):
            return False
        return True

    def _convert_str(self, value):
        if type(value) is str:
            return (unicode(value, "utf-8")).strip()
        else:
            return value

    def _create_customer(self, vals):
        """
            TO DO:
            - Check and create customer
        """
        # Check type of data
        if type(vals) is not dict:
            return {'msg': "Invalid CustomerEntity"}

        ResCountyState = self.env['res.country.state']
        ResPartner = self.env['res.partner']
        ResCountry = self.env['res.country']
        _logger.info('9999999999999999999999999999999999')
        msg = ""
        customer_vals = {'customer': True}

        if vals.get('ref'):
            ref = vals.get('ref')
            customer = ResPartner.search([('ref', '=', ref)], limit=1)
            if customer:
                return {'customer': customer, 'msg': msg}
        else:
            ref = self.env['ir.sequence'].next_by_code('res.partner') or '/'
        name = self._convert_str(vals.get('name'))
        if not name:
            return {'msg': "Customer name could not be empty"}

        customer_vals.update({'name': name, 'ref': ref})
        list_fields = ['street', 'state_code', 'email',
                       'mobile', 'website', 'vat',
                       'indentify_number', 'function', 'phone', 'fax',
                       'sub_email_1', 'sub_email_2', 'main_account',
                       'promotion_account', 'representative', 'company_id']
        for field in list_fields:
            if not vals.get(field):
                continue
            if field in ['email', 'sub_email_1', 'sub_email_2']:
                if not self._validate_email([vals[field]]):
                    return {'msg': 'Invalid email {} : {} .'.
                            format(field, vals[field])}
            customer_vals.update({field: vals[field]})
        _logger.info('88888888888888888888888888888')
        # Get state id
        if customer_vals.get('state_code'):
            state_id = ResCountyState.search(
                [('code', '=', customer_vals['state_code'])], limit=1)
            if state_id:
                customer_vals.update({'state_id': state_id.id})
            else:
                return {'msg': 'State Code {} is not found'.
                        format(customer_vals['state_code'])}
        _logger.info('777777777777777777777777777777777')
        try:
            if vals.get('date_of_birth'):
                date_of_birth = datetime.strptime(
                    str(vals['date_of_birth']), DF)
                customer_vals.update({'date_of_birth': date_of_birth})
            if vals.get('date_of_founding'):
                date_of_founding = datetime.strptime(
                    str(vals['date_of_founding']),
                    DF)
                customer_vals.update({'date_of_founding': date_of_founding})
        except ValueError:
            return {
                'code': 0, 'msg':
                'Invalid date_of_birth or date_of_founding yyyy-mm-dd',
                'data': {}}

        # Get Country id
        country_code = self._convert_str(customer_vals.get('country_code'))
        if country_code:
            country_id = ResCountry.search(
                [('code', '=', country_code)], limit=1)
            if country_id:
                customer_vals.update({'country_id': country_id.id})
            else:
                return {'msg': 'Country Code {} is not found'.
                        format(country_code)}
        _logger.info('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        # Get company type
        if vals.get('company_type'):
            if vals['company_type'] not in \
                    ['person', 'company', 'contact', 'agency']:
                return {
                    'msg': ("Company type must be in "
                            "['person', 'company', 'contact', 'agency']")
                        }
            customer_vals.update({'company_type': vals['company_type']})

        # Check gender value
        if vals.get('gender'):
            if vals['gender'] not in ['male', 'female']:
                return {
                    'msg': ("Gender must be in "
                            "['male', 'female']")
                        }
            customer_vals.update({'gender': vals['gender']})

        # Check company
        if not vals.get('company_id'):
            return {
                'msg': "Company ID is not found."
                    }
        customer_vals.update({'company_id': vals['company_id']})

        # Check source
        if vals.get('source'):
            source_id = self.env['res.partner.source'].search(
                [('code', '=', vals['source'])], limit=1)
            if not source_id:
                return {
                    'msg': ("Customer source '%s' is not found.  " %
                            (vals['source']))
                        }
            customer_vals.update({'source_id': source_id.id})
        _logger.info('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb %s' % customer_vals)
        # Check exits customer
        # customer = ResPartner.search([('ref', '=', ref)], limit=1)
        # if not customer:
        customer = ResPartner.create(customer_vals)
        _logger.info('mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm')
        return {'customer': customer, 'msg': msg}

    def create_order_lines(self, vals):
        """
            TO DO:
            - Checking Order line vals
        """
        # Check type of data
        if type(vals) is not list:
            return {'msg': "Invalid OrderLineEntity"}

        ProductProduct = self.env['product.product']
        ProductCategory = self.env['product.category']
        ProductUom = self.env['product.uom']
        AccountTax = self.env['account.tax']

        error_msg = ''
        order_lines = []
        line_num = 1

        required_arguments = [
            'register_type', 'categ_code', 'product_code', 'product_name',
            'qty', 'uom', 'reg_price_wot', 'reg_price_wt', 'reg_tax_amount',
            'ren_price_wot', 'ren_price_wt', 'ren_tax_amount', 'tax',
            'sub_total', 'company_id']
        non_required_arguments = ['parent_product_code', 'parent_product_name']

        for line in vals:
            if type(line) is not dict:
                return {
                    'msg': "Invalid OrderLineEntity"}
            argument_error = ''
            line_vals = {}
            parent_product = False

            # Check required arguments
            for argument in required_arguments:
                if argument in line:
                    line_vals[argument] = line[argument]
                    continue
                argument_error += "'%s', " % (argument)

            if argument_error:
                error_msg += ("### The required arguments: %s of"
                              " order line at line %s are not found! ") % (
                                   argument_error, line_num)
                return {'msg': error_msg}

            # Get non required arguments
            for argument in non_required_arguments:
                if line.get(argument):
                    line_vals[argument] = line.get(argument)

            # Check Register type
            if line_vals['register_type'] not in \
                    [re_type[0] for re_type in REGISTER_TYPE]:
                error_msg += ("### Please check 'register_type' of"
                              " order line at line %s ") % (line_num)

            # Check Product Category
            if not self._convert_str(line_vals['categ_code']):
                error_msg += "### Can't find product category at line %s " % \
                    (line_num)
            product_categ = ProductCategory.search(
                [('code', '=', line_vals['categ_code'])])
            if not product_categ:
                error_msg += "### Can't find product category at line %s " % \
                    (line_num)
            if not line_vals['company_id']:
                error_msg += "### Company ID '%s' at line %s is not found! " % line_num

            # Check Product Uom
            product_uom = self._convert_str(line_vals['uom'])
            if not product_uom:
                error_msg += (
                        "### Product Uom '%s' at line %s is not found! ") % \
                        (product_uom, line_num)
            else:
                product_uom = ProductUom.search(
                    [('name', '=', product_uom)], limit=1)
                if not product_uom:
                    error_msg += (
                        "### Product Uom '%s' at line %s is not found! ") % \
                        (product_uom, line_num)

            product_ids = ProductProduct
            # Check Product Code
            product_code = self._convert_str(line_vals['product_code'])
            if product_code:
                product_ids = ProductProduct.search(
                    [('default_code', '=', line_vals['product_code'])],
                    limit=1)
            else:
                product_code = self.env['ir.sequence'].next_by_code('product.product')

            # check tax
            tax_id = AccountTax.search([
                ('amount', '=', float(line_vals['tax']))], limit=1)
            if not tax_id:
                error_msg += "### Can't find Tax at line %s " % (line_num)

            product_name = self._convert_str(line['product_name'])
            if not product_name:
                error_msg += "### Invalid product name at line %s " % (
                    line_num)

            # Check parent product
            if line_vals.get('parent_product_code', False):
                parent_product = ProductProduct.search([
                    ('default_code', '=',
                     line_vals.get('parent_product_code'))], limit=1)

                if not parent_product:
                    error_msg += ("### Can't find parent product with code"
                                  " '%s' at line %s ") % \
                        (line_vals.get('parent_product_code'), line_num)

            # Create new product
            if not product_ids and not error_msg:
                new_product_vals = {
                    'default_code': product_code,
                    'name': product_name,
                    'uom_id': product_uom.id,
                    'uom_po_id': product_uom.id,
                    'categ_id': product_categ.id,
                    'minimum_register_time':
                        product_categ.minimum_register_time,
                    'billing_cycle': product_categ.billing_cycle,
                    'type': 'service'
                    }
                product_ids = ProductProduct.create(new_product_vals)

            # Create oder lines
            if product_ids and not error_msg:
                new_line_vals = {
                    'register_type': line_vals['register_type'],
                    'product_id': product_ids.id,
                    'parent_product_id': parent_product and
                    parent_product.id or False,
                    'product_category_id': product_categ.id,
                    'time': line_vals['qty'],
                    'tax_id': tax_id and [(6, 0, [tax_id.id])] or False,
                    'register_untaxed_price': line_vals['reg_price_wot'],
                    'register_taxed_price': line_vals['reg_price_wt'],
                    'renew_untaxed_price': line_vals['ren_price_wot'],
                    'renew_taxed_price': line_vals['ren_price_wt'],
                    'register_taxed_amount': line_vals['reg_tax_amount'],
                    'renew_taxed_amount': line_vals['ren_tax_amount'],
                    'fix_subtotal': line_vals['sub_total'],
                    'company_id': line_vals['company_id']
                    }
                # order_line = SaleOrderLine.create(new_line_vals)
                order_lines.append((0, 0, new_line_vals))
            line_num += 1
        return {'line_ids': order_lines, 'msg': error_msg, 'data': {}}

    @api.model
    def create_so(self, name, coupon, date_order, saleteam_code, order_type, customer, status, company_id, lines=[]):
        """
        TO DO:
            - Create New Sale Order and Customer in Odoo
        """
        # Objects
        CrmTeam = self.env['crm.team']
        SaleOrder = self.env['sale.order']

        # variables
        error_msg = ''
        order_type = order_type
        customer_vals = customer
        team_id = False

        if not name:
            return {'code': 0, 'msg': 'Order name could not be empty',
                    'data': {}}
        else:
            order = SaleOrder.search([('name', '=', name)], limit=1)
            if order:
                return {'code': 0, 'msg': 'Order name already exits',
                        'data': {}}
        if not date_order:
            return {'code': 0, 'msg': 'Order Date could not be empty',
                    'data': {}}
        if not company_id:
            return {'code': 0, 'msg': 'Company ID could not be empty',
                    'data': {}}
        if not order_type or order_type not in ['normal', 'renewed']:
            return {'code': 0,
                    'msg': 'Order Type must be `normal` or `renewed`',
                    'data': {}}
        if not customer:
            return {'code': 0, 'msg': 'Customer info could not be empty',
                    'data': {}}
        if not status or status not in ('draft', 'not_received', 'sale', 'completed', 'done', 'cancel'):
            return {'"code"': 0,
                    '"msg"': '"Status info could not be empty. "'
                           '\n"Status must be `not_received`(Not Received), `draft`(Quotation), `sale`(In Progress), `completed`(Wait Contract), `done`(Completed) or `cancel`(Cancelled)"',
                    '"data"': {}}
        if not lines:
            return {'code': 0, 'msg': 'Order detail could not be empty',
                    'data': {}}
        # Check date_order
        try:
            date_order = datetime.strptime(date_order, DTF) + \
                timedelta(hours=-7)
        except ValueError:
            return {'code': 0, 'msg': 'Invalid order date yyyy-mm-dd h:m:s',
                    'data': {}}

        # check sale team code
        if saleteam_code:
            team_id = CrmTeam.search([('code', '=', saleteam_code)], limit=1)
            if not team_id:
                return {'code': 0,
                        'msg': 'Saleteam {} is not found'.format(saleteam_code
                                                                 ),
                        'data': {}}
        try:

            # Prepare Order lines:
            order_lines = self.create_order_lines(lines)
            if order_lines['msg']:
                error_msg += order_lines['msg']

            # Check Customer exits or create a new customer
            customer_result = self._create_customer(customer_vals)
            if customer_result.get('msg'):
                return {'code': 0, 'msg': customer_result['msg'], 'data': {}}
            customer = customer_result['customer']

            if error_msg:
                return {'code': 0, 'msg': error_msg, 'data': {}}

            so_vals = {'partner_id': customer.id,
                       'date_order': date_order,
                       'user_id': False,
                       'team_id': team_id and team_id.id or False,
                       # 'state': order_type == 'normal' and 'draft' or 'not_received',
                       'state': status,
                       'type': order_type,
                       'coupon': coupon,
                       'name': name,
                       'company_id': company_id,
                       'order_line': order_lines['line_ids']
                       }
            SaleOrder.with_context(force_company=company_id).create(so_vals)
            return {'code': 1, 'msg': "Create Order Successful!"}
        except ValueError:
            return {'code': 0, 'msg': 'Unknow Error!', 'data': {}}\

    @api.model
    def create_so_fix(self, name, coupon, date_order, saleteam_code, order_type, customer, status, company_id, lines=[]):
        """
        TO DO:
            - Create New Sale Order and Customer in Odoo
        """
        _logger.info('1111111111111111111111')
        # Objects
        CrmTeam = self.env['crm.team']
        SaleOrder = self.env['sale.order']

        # variables
        error_msg = ''
        order_type = order_type
        customer_vals = customer
        team_id = False

        if not name:
            return {'code': 0, 'msg': 'Order name could not be empty',
                    'data': {}}
        else:
            order = SaleOrder.search([('name', '=', name)], limit=1)
            if order:
                return {'code': 0, 'msg': 'Order name already exits',
                        'data': {}}
        if not date_order:
            return {'code': 0, 'msg': 'Order Date could not be empty',
                    'data': {}}
        if not company_id:
            return {'code': 0, 'msg': 'Company ID could not be empty',
                    'data': {}}
        if not order_type or order_type not in ['normal', 'renewed']:
            return {'code': 0,
                    'msg': 'Order Type must be `normal` or `renewed`',
                    'data': {}}
        if not customer:
            return {'code': 0, 'msg': 'Customer info could not be empty',
                    'data': {}}
        if not status or status not in ('draft', 'not_received', 'sale', 'completed', 'done', 'cancel'):
            return {'"code"': 0,
                    '"msg"': '"Status info could not be empty. "'
                           '\n"Status must be `not_received`(Not Received), `draft`(Quotation), `sale`(In Progress), `completed`(Wait Contract), `done`(Completed) or `cancel`(Cancelled)"',
                    '"data"': {}}
        if not lines:
            return {'code': 0, 'msg': 'Order detail could not be empty',
                    'data': {}}
        # Check date_order
        try:
            date_order = datetime.strptime(date_order, DTF) + \
                timedelta(hours=-7)
        except ValueError:
            return {'code': 0, 'msg': 'Invalid order date yyyy-mm-dd h:m:s',
                    'data': {}}

        # check sale team code
        if saleteam_code:
            team_id = CrmTeam.search([('code', '=', saleteam_code)], limit=1)
            if not team_id:
                return {'code': 0,
                        'msg': 'Saleteam {} is not found'.format(saleteam_code
                                                                 ),
                        'data': {}}
        _logger.info('22222222222222222222222222222222')
        try:
            # Prepare Order lines:
            order_lines = self.create_order_lines(lines)
            _logger.info('333333333333333333333333333333333333')
            if order_lines['msg']:
                error_msg += order_lines['msg']

            # Check Customer exits or create a new customer
            customer_result = self._create_customer(customer_vals)
            _logger.info('44444444444444444444444444444')
            if customer_result.get('msg'):
                return {'code': 0, 'msg': customer_result['msg'], 'data': {}}
            customer = customer_result['customer']

            if error_msg:
                return {'code': 0, 'msg': error_msg, 'data': {}}

            so_vals = {'partner_id': customer.id,
                       'date_order': date_order,
                       'user_id': False,
                       'team_id': team_id and team_id.id or False,
                       # 'state': order_type == 'normal' and 'draft' or 'not_received',
                       'state': status,
                       'type': order_type,
                       'coupon': coupon,
                       'name': name,
                       'company_id': company_id,
                       'order_line': order_lines['line_ids']
                       }
            _logger.info('555555555555555555555555555555')
            order_id = SaleOrder.create(so_vals)
            _logger.info('6666666666666666666666666666666666')
            return {'code': 1, 'msg': "Create Order Successful!", 'data': order_id}
        except ValueError:
            return {'code': 0, 'msg': 'Unknow Error!', 'data': {}}

    @api.model
    def update_so(self, name, vals={}):
        res = {'code': 0, 'msg': ''}
        SaleOrder = self.env['sale.order']
        CrmTeam = self.env['crm.team']
        sale_order = SaleOrder.search([('name', '=', name)], limit=1)
        if not sale_order:
            res['msg'] = 'SALE ORDER `{}` is not found'.format(name)
            return res
        if 'saleteam_code' in vals:
            team = CrmTeam.search([('code', '=', vals['saleteam_code'])],
                                  limit=1)
            if not team:
                res['msg'] = '''TEAM with CODE `{}` is not found'''.\
                    format(vals['saleteam_code'])
                return res
            sale_order.team_id = team
            res['code'] = 1
            return res
        else:
            res['msg'] = 'Vals has some invalid key(s)'
            return res

    @api.model
    def get_not_receive_so(self, date_from=False, date_to=False,
                           limit=None, order='date_order'):
        """
            TO DO:
            - [API] MB call Odoo to get the list of "Not Received" orders
        """
        res = {'code': 0, 'msg': '', 'data': []}
        data = []
        SaleOrder = self.env['sale.order']
        error_msg = ''
        args = [('state', '=', 'not_received')]

        if date_from:
            try:
                system_date_from = \
                    self.env['ir.fields.converter']._str_to_datetime(
                        None, None, str(date_from))
                args += [('date_order', '>=', system_date_from[0])]
            except ValueError:
                error_msg += 'Wrong DATE FROM format, '
        if date_to:
            try:
                system_date_to = \
                    self.env['ir.fields.converter']._str_to_datetime(
                        None, None, str(date_to))
                args += [('date_order', '<=', system_date_to[0])]
            except ValueError:
                error_msg += 'Wrong DATE TO format, '
        try:
            if not isinstance(limit, int) or int(limit) < 1:
                limit = None
        except ValueError:
            limit = None
            error_msg += 'Invalid limit'

        if error_msg:
            res.update({'code': 0, 'msg': error_msg, 'data': data})
            return res

        try:
            so_recs = SaleOrder.search(args=args, limit=limit, order=order)
        except UserError, e:
            error_msg += e[0]
            res['msg'] = error_msg
            return res
        except ValueError, e:
            error_msg += e[0]
            res['msg'] = error_msg
            return res
        except:
            error_msg += 'Unknow Error, '
            res['msg'] = error_msg
            return res
        for so in so_recs:
            data.append(so.name)
        res.update({'code': 1, 'msg': error_msg, 'data': data})
        return res

    # @api.model
    # def get_so_by_state(
    #         self, state=False, date_from=False, date_to=False,
    #         limit=None, order='date_order'):
    #     """
    #         TO DO:
    #         - Get Sale Order from Odoo by state
    #     """
    #     res = {'code': 0, 'msg': 'Process SO Successful!', 'data': []}
    #     SaleOrder = self.env['sale.order']
    #     error_msg = ''
    #     args = [('type', '=', 'renewed')]
    #
    #     # Check state
    #     invalid_states = \
    #         ['not_received', 'draft', 'sale', 'completed', 'done', 'cancel']
    #     if state and state not in invalid_states:
    #         error_msg += 'Invalid state, '
    #     if state and not error_msg:
    #         args += [('state', '=', state)]
    #
    #     # Check date from
    #     if date_from:
    #         try:
    #             system_date_from = \
    #                 self.env['ir.fields.converter']._str_to_datetime(
    #                     None, None, str(date_from))
    #             args += [('date_order', '>=', system_date_from[0])]
    #         except ValueError:
    #             error_msg += 'Wrong DATE FROM format, '
    #
    #     # Check Date to
    #     if date_to:
    #         try:
    #             system_date_to = \
    #                 self.env['ir.fields.converter']._str_to_datetime(
    #                     None, None, str(date_to))
    #             args += [('date_order', '<=', system_date_to[0])]
    #         except ValueError:
    #             error_msg += 'Wrong DATE TO format, '
    #
    #     # Check limit argument
    #     try:
    #         if limit:
    #             if not isinstance(limit, int) or int(limit) < 1:
    #                 error_msg += 'Invalid limit'
    #     except ValueError:
    #         error_msg += 'Invalid limit'
    #
    #     # Return error
    #     if error_msg:
    #         res.update({'msg': error_msg})
    #         return res
    #
    #     # If arguments are ok
    #     try:
    #         so_recs = SaleOrder.search(args, limit=limit, order=order)
    #         if not so_recs:
    #             res.update({'code': 1, 'msg': '', 'data': []})
    #             return res
    #
    #         # Parse data
    #         data = []
    #         for so in so_recs:
    #             data_append = ['service_name: ' + '\"' + so.name + '\"',
    #                            'date_order: ' + '\"' + so.date_order + '\"',
    #                            'state: ' + '\"' + so.state + '\"',
    #                            'sale_order_line_id: ' + '\"' + (po.sale_order_line_id and str(so.sale_order_line_id.id) or '') + '\"',
    #                            'is_success: ' + '\"' + (po.is_success and 'True' or 'False') + "\""]
    #
    #             data.append(data_append)
    #         res.update({'code': 1, 'msg': "''", 'data': data})
    #     except UserError, e:
    #         error_msg += e[0]
    #         res['msg'] = error_msg
    #         return res
    #     except ValueError, e:
    #         error_msg += e[0]
    #         res['msg'] = error_msg
    #         return res
    #     except:
    #         error_msg += 'Unknow Error, '
    #         res['msg'] = error_msg
    #         return res
    #     return res
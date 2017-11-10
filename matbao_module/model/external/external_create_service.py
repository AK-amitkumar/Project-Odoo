# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, timedelta

class ExternalActiveService(models.AbstractModel):
    _description = 'Create Product and Service API'
    _name = 'external.create.service'

    @api.model
    def create_service(self, product_name, product_code, product_category_code, customer_code, ip_hosting, ip_email, start_date, end_date, status):
        res = {'code': 0, 'msg': ''}
        IrSequence = self.env['ir.sequence']
        Product = self.env['product.product']
        ProductCategory = self.env['product.category']
        Service = self.env['sale.service']
        if not customer_code:
            res['msg'] = "Customer code could not be empty"
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
        if not customer_id:
            res['msg'] = "Customer not exists"
            return res
        # Create Product
        if not product_name:
            res['msg'] = "Product name could not be empty"
            return res
        if product_code and Product.search([('default_code', '=', product_code)]):
            res['msg'] = "Product already exists."
            return res
        if not product_category_code:
            res['msg'] = "Product category code could not be empty"
            return res
        product_category_id = ProductCategory.search([('code', '=', product_category_code)])
        if not product_category_id:
            res['msg'] = ("Product Category: %s not exists" % product_category_code)
            return res
        try:
            if product_category_code[:2] == 'DM' and product_category_id.name <> product_name[product_name.index('.'):]:
                res['msg'] = "Service not belong Category."
                return res
        except Exception:
            res['msg'] = "Check syntax."
            return res
        product_id = Product.create({
            'default_code': product_code or IrSequence.next_by_code('product.product'),
            'name': product_name,
            'categ_id': product_category_id.id,
            'type': 'service',
            'uom_id': product_category_id.uom_id.id,
            'uom_po_id': product_category_id.uom_id.id,
        })
        if not start_date:
            res['msg'] = "Start Date could not be empty"
            return res
        if not status or status not in ('draft', 'waiting', 'active', 'refused', 'closed'):
            res['msg'] = "Status could not be empty and must belong 'draft', 'waiting', 'active', 'refused' and 'closed'."
            return res
        # Create Service
        Service.create({
            'customer_id': customer_id.id,
            'product_category_id': product_category_id.id,
            'product_id': product_id.id,
            'uom_id': product_id.uom_id.id,
            'ip_hosting': ip_hosting or False,
            'ip_email': ip_email or False,
            'start_date': start_date,
            'end_date': end_date or datetime.now().date(),
            'status': status,
        })
        res['code'] = 1
        return res

    @api.model
    def create_list_service(self, lines=[]):
        res = {'code': 0, 'msg': ''}
        IrSequence = self.env['ir.sequence']
        Product = self.env['product.product']
        ProductCategory = self.env['product.category']
        Service = self.env['sale.service']

        # Check type of data
        if not lines:
            return {'"msg"': '"Lines could not be empty"'}
        if type(lines) is not list:
            return {'"msg"': '"Invalid OrderLineEntity"'}

        for line in lines:
            product_vals = {'type': 'service'}
            service_vals = {}
            # Get Customer for Service
            if not line.get('customer_code',''):
                res['msg'] = "Customer code could not be empty"
                break
            customer_id = self.env['res.partner'].search([('ref', '=', line.get('customer_code',''))])
            if not customer_id:
                res['msg'] = "Customer not exists"
                break
            service_vals.update({'customer_id': customer_id.id})
            # Get Product name
            if not line.get('product_name',''):
                res['msg'] = "Product name could not be empty"
                break
            product_vals.update({'name': line.get('product_name','')})
            # Get product code
            if line.get('product_code','') and Product.search([('default_code', '=', line.get('product_code',''))]):
                res['msg'] = "Product already exists."
                break
            product_vals.update({'default_code': line.get('product_code','') or IrSequence.next_by_code('product.product')})
            # Get product category, product uom, product purchase uom
            if not line.get('product_category_code',''):
                res['msg'] = "Product category code could not be empty"
                break
            product_category_id = ProductCategory.search([('code', '=', line.get('product_category_code',''))])
            if not product_category_id:
                res['msg'] = ("Product Category: %s not exists" % line.get('product_category_code',''))
                break
            product_vals.update({'categ_id': product_category_id.id,
                                 'uom_id': product_category_id.uom_id.id,
                                 'uom_po_id': product_category_id.uom_id.id})
            service_vals.update({'product_category_id': product_category_id.id})
            # try:
            #     if product_category_code[:2] == 'DM' and product_category_id.name <> product_name[product_name.index('.'):]:
            #         res['msg'] = "Service not belong Category."
            #         break
            # except Exception:
            #     res['msg'] = "Check syntax."
            #     break
            # Create Product
            product_id = Product.create(product_vals)
            res['msg'] = "Product %s have create successfully." % product_id.name

            # Get product for service
            service_vals.update({'product_id': product_id.id,
                                 'uom_id': product_id.uom_id.id})
            # Get start date of service
            if not line.get('start_date'):
                res['msg'] = "Start Date could not be empty"
                break
            service_vals.update({'start_date': line.get('start_date')})
            if not line.get('status') or line.get('status','') not in ('draft', 'waiting', 'active', 'refused', 'closed'):
                res['msg'] = "Status could not be empty and must belong 'draft', 'waiting', 'active', 'refused' and 'closed'."
                break
            service_vals.update({'status': line.get('status'),
                                 'ip_hosting': line.get('ip_hosting','') or '',
                                 'ip_email': line.get('ip_email','') or '',
                                 'end_date': line.get('end_date','') or False,})
            # Create Service
            print service_vals
            service_id = Service.create(service_vals)
            res['msg'] = "Service %s have create successfully." % service_id.name
        res['code'] = 1
        return res


    @api.model
    def get_service(self, cus_code, type=False, limit=False):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        ResPartner = self.env['res.partner']
        SaleService = self.env['sale.service']
        data = []

        # Check partner
        if not cus_code:
            res.update({'"msg"': '"Customer code could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', cus_code)])
        if not partner_id:
            res.update({'"msg"': '"Customer not found."'})
            return res
        if type and type not in ('DM', 'HO'):
            res.update({'"msg"': '"Type must be in `DM`, `HO`."'})
            return res

        services = SaleService.search([('customer_id', '=', partner_id.id), ('end_date', '>=', datetime.now().date() - timedelta(days=60))], limit=limit)
        # If arguments are ok
        try:
            # Parse data
            for service in services:
                item = {}
                if type:
                    if type == 'DM' and service.product_category_id.code and service.product_category_id.code[:1] == '.':
                        item.update({
                            '"name"': '\"' + service.name + '\"',
                            '"reference"': '\"' + (service.reference or '') + '\"',
                            '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                            '"product_category_id"': service.product_category_id.id,
                            '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                            '"product_category_name"': '\"' + (service.product_category_id.name or '') + '\"',
                            '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                            '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                            '"start_date"': '\"' + (service.start_date or '') + '\"',
                            '"end_date"': '\"' + (service.end_date or '') + '\"',
                            '"write_date"': '\"' + (service.write_date or '') + '\"',
                            '"status"': '\"' + (service.status or '') + '\"',
                            '"parent_product_id"': '\"' + (service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
                        })
                        data.append(item)
                    elif type == 'HO' and service.product_category_id.code and service.product_category_id.code[:1] <> '.':
                        item.update({
                            '"name"': '\"' + service.name + '\"',
                            '"reference"': '\"' + (service.reference or '') + '\"',
                            '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                            '"product_category_id"': service.product_category_id.id,
                            '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                            '"product_category_name"': '\"' + (service.product_category_id.name or '') + '\"',
                            '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                            '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                            '"start_date"': '\"' + (service.start_date or '') + '\"',
                            '"end_date"': '\"' + (service.end_date or '') + '\"',
                            '"write_date"': '\"' + (service.write_date or '') + '\"',
                            '"status"': '\"' + (service.status or '') + '\"',
                            '"parent_product_id"': '\"' + (service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
                        })
                        data.append(item)
                else:
                    item.update({
                        '"name"': '\"' + service.name + '\"',
                        '"reference"': '\"' + (service.reference or '') + '\"',
                        '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                        '"product_category_id"': service.product_category_id.id,
                        '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                        '"product_category_name"': '\"' + (service.product_category_id.name or '') + '\"',
                        '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                        '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                        '"start_date"': '\"' + (service.start_date or '') + '\"',
                        '"end_date"': '\"' + (service.end_date or '') + '\"',
                        '"write_date"': '\"' + (service.write_date or '') + '\"',
                        '"status"': '\"' + (service.status or '') + '\"',
                        '"parent_product_id"': '\"' + (
                        service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
                    })
                    data.append(item)

            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except:
            res['"msg"'] = '"Can not get services"'
            return res
        return res

    @api.model
    def get_service_info(self, partner_id, reference):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        ResPartner = self.env['res.partner']
        SaleService = self.env['sale.service']
        data = {}

        # Check partner
        if not partner_id and type(partner_id) is not int:
            res.update({'"msg"': '"Customer ID could be not empty and must be number"'})
            return res
        partner = ResPartner.browse(partner_id)
        if not partner:
            res.update({'"msg"': '"Customer not found."'})
            return res

        service = SaleService.search([('customer_id', '=', partner_id), ('reference', '=', reference), ('end_date', '>=', datetime.now().date() - timedelta(days=60))], limit=1)
        if not service:
            res.update({'"msg"': '"Service not found."'})
            return res
        # If arguments are ok
        try:
            # Parse data
            data.update({
                '"name"': '\"' + service.name + '\"',
                '"reference"': '\"' + (service.reference or '') + '\"',
                '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                '"product_category_id"': service.product_category_id.id,
                '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                '"start_date"': '\"' + (service.start_date or '') + '\"',
                '"end_date"': '\"' + (service.end_date or '') + '\"',
                '"write_date"': '\"' + (service.write_date or '') + '\"',
                '"status"': '\"' + (service.status or '') + '\"',
                '"parent_product_id"': '\"' + (service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
            })
            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except:
            res['"msg"'] = '"Can not get service"'
            return res
        return res

    @api.model
    def get_service_info_wo_partner(self, reference):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        ResPartner = self.env['res.partner']
        SaleService = self.env['sale.service']
        data = {}

        service = SaleService.search([('reference', '=', reference)], limit=1)
        if not service:
            res.update({'"msg"': '"Service not found."'})
            return res
        # If arguments are ok
        try:
            # Parse data
            data.update({
                '"name"': '\"' + service.name + '\"',
                '"customer_id"': '\"' + (service.customer_id.ref or '') + '\"',
                '"reference"': '\"' + (service.reference or '') + '\"',
                '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                '"product_category_id"': service.product_category_id.id,
                '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                '"start_date"': '\"' + (service.start_date or '') + '\"',
                '"end_date"': '\"' + (service.end_date or '') + '\"',
                '"write_date"': '\"' + (service.write_date or '') + '\"',
                '"status"': '\"' + (service.status or '') + '\"',
                '"parent_product_id"': '\"' + (
                service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
            })
            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except:
            res['"msg"'] = '"Can not get service"'
            return res
        return res

    @api.model
    def update_service(self, po_name, start_date, end_date, ip_hosting, ip_email):
        res = {'code': 0, 'msg': ''}
        PurchaseOrder = self.env['purchase.order']
        SaleService = self.env['sale.service']
        # Check data
        # Check PO
        if not po_name:
            res['msg'] = "Purchase order name could not be empty"
            return res
        po = PurchaseOrder.search([('name', '=', po_name)], limit=1)
        if not po:
            res['msg'] = "Purchase order '{}' is not found".format(po_name)
            return res
        elif po.state != 'draft':
            res['msg'] = \
                "Status of Purchase Order '{}' must be draft".format(po_name)
            return res
        # Check Date
        if not start_date:
            res['msg'] = "Start Date could not be empty"
            return res
        if not end_date:
            res['msg'] = "End Date could not be empty"
            return res
        try:
            system_start_date = self.env['ir.fields.converter']._str_to_date(None, None, start_date)
        except ValueError:

            res['msg'] = 'Wrong start date format'
            return res
        try:
            system_end_date = self.env['ir.fields.converter']._str_to_date(
                None, None, end_date)
        except ValueError:

            res['msg'] = 'Wrong end date format'
            return res

        if not po.sale_order_line_id:
            res['msg'] = 'Purchase order does not have related sale order line'
            return res
        service = SaleService.search([('product_id', '=', po.order_line and po.order_line.mapped('product_id') and po.order_line.mapped('product_id')[0].id)], limit=1)
        if not service:
            res['msg'] = \
                "Service of purchase order '{}' is not found".format(name)
            return res
        try:
            po.write({'is_active': True})
            service.write({
                'start_date': system_start_date[0],
                'end_date': system_end_date[0],
                'ip_hosting': ip_hosting,
                'ip_email': ip_email,
                'status': 'active'
            })
            res['msg'] = "Update Successfully!!!"
        except:
            res['msg'] = "Can't update service"
            return res
        res['code'] = 1
        return res
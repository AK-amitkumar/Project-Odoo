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
from odoo import api, fields, models, _
from odoo.exceptions import Warning
import urllib2
import urllib
import json


class ServiceAddonOrderLinesWizard(models.TransientModel):
    _name = "service.addon.order.lines.wizard"
    _description = "Wizard to add services/addons to the current active SO"

    line_ids = fields.One2many(
        'order.lines.wizard', 'parent_id', string='Order Lines')

    @api.multi
    def write_service_orders(self):
        # print 1111111111111111111111111
        self.ensure_one()
        if self._context.get('active_model') != 'sale.order':
            return False

        order_id = self.env.context.get('active_id')
        order = self.env['sale.order'].browse(order_id)
        lines = []

        for line in self.line_ids:
            product_uom = line.product_category_id.uom_id.id
            if not product_uom:
                raise Warning(_("Please set UOM for Product Category!"))

            vals = {
                'register_type': line.register_type,
                'product_category_id': line.product_category_id.id,
                'time': line.time,
                'product_uom':  line.product_category_id.uom_id.id,
                'template': line.template,
            }

            product_id = None
            product_name = None
            is_add_service = self._context.get('service')
            if line.register_type in ['register', 'transfer']:
                # ---------------------- Edit and add by Hai 16/10/2017 ---------------------#
                if line.get_parent_product_category(line.product_category_id).code == 'CHILI' and is_add_service:
                    full_url = 'http://core.matbao.net/getdomainchili.aspx?domain=' + line.product_name
                    res_data = urllib2.urlopen(full_url)
                    res_data = res_data.read()
                    line.product_name = res_data
                # ----------------------- end ------------------------#

                product_data = {
                    'name': is_add_service and line.product_name or
                    line.parent_product_id.name,
                    'type': 'service',
                    'categ_id':  line.product_category_id.id,
                    'minimum_register_time':
                        line.product_category_id.minimum_register_time,
                    'billing_cycle':
                        line.product_category_id.billing_cycle,
                    'uom_id': line.product_category_id.uom_id.id,
                    'uom_po_id': line.product_category_id.uom_id.id,
                    'parent_product_id': is_add_service and False or
                        line.parent_product_id.id
                }
                new_prod = self.env['product.product'].create(product_data)
                product_id = new_prod.id
                product_name = is_add_service and line.product_name or \
                    line.parent_product_id.name
            else:
                product_id = line.product_id.id
                product_name = line.product_id.name

            vals.update({
                'product_id': product_id,
                'name': product_name,
                'parent_product_id': is_add_service and False or
                line.parent_product_id.id
            })

            lines.append((0, 0, vals))
        if lines:
            order.write({'order_line': lines})

# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################
from odoo import api, fields, models
from odoo.exceptions import Warning, ValidationError

class POsCustomDiscount(models.Model):
	_name = "pos.custom.discount"

	name = fields.Char(string="Name" , required=1)
	discount_percent = fields.Float(string="Discount Percentage",required=1)
	description = fields.Text(string="Description" )
	allow_custom_discount = fields.Boolean('Allow Custom ')
	available_in_pos = fields.Many2many('pos.config',string="Available In Pos")

	@api.constrains('discount_percent')
	def check_validation_discount_percent(self):
		"""This is to validate discount percentage
		"""
		if self.discount_percent <= 0 or self.discount_percent>100 :
			raise ValidationError("Discount percent must be between 0 and 100.")

class PosConfig(models.Model):
	_inherit = 'pos.config'

	discount_ids = fields.Many2many('pos.custom.discount',string="Discounts")
	allow_custom_discount = fields.Boolean('Allow Customize Discount',default = True)
	allow_security_pin = fields.Boolean('Allow Security Pin')

class PosOrderLine(models.Model):
	_inherit = 'pos.order.line'
	custom_discount_reason = fields.Text('Discount Reason')

	@api.model
	def _order_line_fields(self,line):
		fields_return = super(PosOrderLine,self)._order_line_fields(line)
		fields_return[2].update({'custom_discount_reason':line[2].get('custom_discount_reason','')})
		return fields_return
# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _

class HelpdeskTicket(models.Model):
    _inherit   = 'helpdesk.ticket'

    partner_mobile = fields.Char(string='Customer Phone/Mobile')
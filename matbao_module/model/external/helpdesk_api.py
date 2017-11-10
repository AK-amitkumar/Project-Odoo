# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare

class ExternalHelpdeskTicket(models.AbstractModel):
    _description = 'Helpdesk API'
    _name = 'external.helpdesk.ticket'

    @api.model
    def create_ticket(self, customer_code, subject, service, team, description):
        res = {'"code"': 0, '"msg"': '""'}
        if not customer_code:
            res['"msg"'] = '"Customer code could not be empty"'
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
        if not customer_id:
            res['"msg"'] = '"Customer not exists"'
            return res
        if not subject:
            res['"msg"'] = '"Subject could not be empty"'
            return res
        if not team:
            res['"msg"'] = '"Team Support could not be empty"'
            return res
        team_id = self.env['helpdesk.team'].search([('name', '=', team)])
        if not team_id:
            res['"msg"'] = '"Helpdesk Team not exists"'
            return res
        if not description:
            res['"msg"'] = '"Description could not be empty"'
            return res
        if not service:
            res['"msg"'] = '"Service could not be empty"'
            return res
        service_id = self.env['sale.service'].search([('reference', '=', service)])
        if not service_id:
            res['"msg"'] = '"Service not exists"'
            return res
        ticket_id = self.env['helpdesk.ticket'].create({
            'name': subject,
            'team_id': team_id.id,
            'service_id': service_id.id,
            'partner_id': customer_id.id,
            'partner_name': customer_id.name,
            'partner_email': customer_id.email,
            'description': description,
        })
        if ticket_id:
            res['"code"'] = 1
            res['"ticket_id"'] = ticket_id.id
        else:
            res['"code"'] = 0
        return res

    @api.model
    def all_ticket(self, customer_code):
        res = {'"code"': 0, '"msg"': '""'}
        if not customer_code:
            res['"msg"'] = '"Customer code could not be empty"'
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
        if not customer_id:
            res['"msg"'] = '"Customer not exists"'
            return res
        tickets = self.env['helpdesk.ticket'].search_read([('partner_id', '=', customer_id.id)],
                                   ['name', 'user_id', 'team_id', 'partner_id', 'partner_email', 'service_id',
                                    'ticket_type_id', 'description', 'create_date', 'write_date', 'stage_id'])
        if tickets:
            res['"code"'] = 1
            lst_ticket = []
            for ticket in tickets:
                message = self.env['mail.message'].search([('res_id', '=', ticket.get('id')),
                                                           ('model', '=', 'helpdesk.ticket'),
                                                           ('message_type', '=', 'comment')], order='id desc', limit=1)
                ticket.update({
                    'write_date': message.write_date
                })
                json_ticket = {}
                for key, value in ticket.iteritems():
                    # print key, value, type(value)
                    if key in ('user_id', 'team_id', 'service_id', 'partner_id', 'ticket_type_id', 'stage_id') and value:
                        lst = list(value)
                        lst[1] = '\"' + lst[1] + '\"'
                        json_ticket.update({
                            '\"' + key + '\"': tuple(lst)
                        })
                    elif type(value) == 'integer' or key == 'id':
                        json_ticket.update({
                            '\"' + key + '\"': value
                        })
                    elif key == 'description':
                        json_ticket.update({
                            '\"' + key + '\"': '\'' + (value and str(value.replace("\'","&#39;").encode('utf-8')) or '') + '\''
                        })
                    else:
                        json_ticket.update({
                            '\"' + key + '\"': '\"' + (value or 'False') + '\"'
                        })
                lst_ticket.append(json_ticket)
            tickets = lst_ticket
            # print tickets
        else:
            res['"code"'] = 0
        return tickets

    @api.model
    def ticket_detail(self, ticket_id, customer_code):
        res = {'"code"': 0, '"msg"': '""'}
        if not customer_code:
            res['"msg"'] = '"Customer code could not be empty"'
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
        if not customer_id:
            res['"msg"'] = '"Customer not exists"'
            return res
        if not ticket_id:
            res['"msg"'] = '"Ticket could not be empty"'
            return res
        ticket = self.env['helpdesk.ticket'].search_read([('id', '=', ticket_id), ('partner_id', '=', customer_id.id)],
                                  ['name', 'sla_name', 'team_id', 'user_id', 'priority', 'deadline',
                                   'partner_id', 'partner_email', 'service_id', 'create_date', 'write_date',
                                   'ticket_type_id', 'description', 'message_ids', 'stage_id'])
        if not ticket:
            res['"msg"'] = '"Ticket not exists"'
            return res
        json_ticket = {}
        for key,value in ticket[0].iteritems():
            if key in ('user_id', 'team_id', 'service_id', 'partner_id', 'stage_id', 'ticket_type_id') and value:
                if key == 'ticket_type_id':
                    json_ticket.update({
                        '\"' + key + '\"': '"False"'
                    })
                else:
                    lst = list(value)
                    lst[1] = '\"' + lst[1] + '\"'
                    json_ticket.update({
                        '\"' + key + '\"': tuple(lst)
                    })
            elif key in ('message_ids') or type(value) == 'integer':
                json_ticket.update({
                    '\"' + key + '\"': value
                })
            elif key in ('description'):
                json_ticket.update({
                    '\"' + key + '\"': '\'' + (value and str(value.replace("\'","&#39;").encode('utf-8')) or '') + '\''
                })
            else:
                json_ticket.update({
                    '\"' + key + '\"': '\"' + (value and str(value) or 'False') + '\"'
                })
        ticket = json_ticket
        message = self.env['mail.message'].search_read(
            [('res_id', '=', ticket_id), ('model', '=', 'helpdesk.ticket'), ('message_type', '=', 'comment')],
            ['body', 'attachment_ids', 'create_date', 'write_date', 'create_uid'])
        if message:
            lst_message = []
            # json_message = {}
            for mes in message:
                json_message = {}
                for key, value in mes.iteritems():
                    # print key, value
                    if key == 'attachment_ids':
                        json_message.update({
                            '\"' + key + '\"': value
                        })
                    elif key in ('create_uid',) and value:
                        lst = list(value)
                        lst[1] = '\"' + lst[1] + '\"'
                        json_message.update({
                            '\"' + key + '\"': tuple(lst)
                        })
                    elif key == 'id':
                        json_message.update({
                            '\"' + key + '\"': value
                        })
                    elif key == 'body':
                        json_message.update({
                            '\"' + key + '\"': '\'' + (value and str(value.replace("\'","&#39;").encode('utf-8')) or 'False') + '\''
                        })
                    else:
                        json_message.update({
                            '\"' + key + '\"': '\"' + (str(value.encode('utf-8')) or 'False') + '\"'
                        })
                lst_message.append(json_message)
            message = lst_message
        # attachment = self.env['ir.attachment'].search_read(
        #     [('res_id', '=', ticket_id), ('res_model', '=', 'helpdesk.ticket')],
        #     ['name', 'store_fname', 'checksum', 'datas_fname'])
        return ticket, message

    @api.model
    def update_ticket(self, ticket_id, customer_code, body, link_file=False):
        res = {'"code"': 0, '"msg"': '""'}
        if not customer_code:
            res['"msg"'] = '"Customer code could not be empty"'
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
        if not customer_id:
            res['"msg"'] = '"Customer not exists"'
            return res
        if not ticket_id:
            res['"msg"'] = '"Ticket could not be empty"'
            return res
        if not body:
            res['"msg"'] = '"Content could not be empty"'
            return res
        ticket = self.env['helpdesk.ticket'].search([('id', '=', ticket_id), ('partner_id', '=', customer_id.id)])
        if not ticket:
            res['"msg"'] = '"Ticket not exists"'
            return res
        message_id = self.env['mail.message'].search([('res_id', '=', ticket_id), ('model', '=', 'helpdesk.ticket')], order='id asc', limit=1)
        ticket.write({
            'message_ids': [(0, 0, {'body': body + '\n' + link_file if link_file else body,
                                    'model': 'helpdesk.ticket',
                                    'res_name': ticket.display_name,
                                    'parent_id': message_id.id,
                                    'message_type': 'comment'})]
        })
        res['"code"'] = 1
        return res
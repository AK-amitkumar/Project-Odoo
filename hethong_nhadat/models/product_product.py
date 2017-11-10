# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import Warning

class ProductProduct(models.Model):
    _inherit    = 'product.template'

    def _get_url(self):
        for record in self:
            parameters = self.env['ir.config_parameter'].search([('key', '=', 'url_bds')])
            if parameters:
                record.link = parameters[0].value
                record.link += 'web?#id=%s&view_type=form&model=product.template' % record.id

    status      = fields.Selection([('sold', 'Đã bán'), ('no_sell', 'Còn trống'), ('hold', 'Giữ chỗ')], string='Trạng thái', default='no_sell', track_visibility='onchange')
    # direction = fields.Selection([('west', 'Tây'), ('south', 'Nam'), ('east', 'Đông'), ('north', 'Bắc'), ('northeast', 'Đông bắc'), ('southeast', 'Đông nam'), ('northwest', 'Tây bắc'), ('southwest', 'Tây nam')], string='Hướng nhà', track_visibility='onchange')
    # floorth = fields.Integer(string='Tầng sô', track_visibility='onchange')
    # area = fields.Float(string='Diện tích', track_visibility='onchange')
    # room_no = fields.Integer(string='Số phòng', track_visibility='onchange')
    categ_da    = fields.Many2one('product.category', string='Dự án', track_visibility='onchange')
    hold_date   = fields.Datetime(string='Hold Date', track_visibility='onchange')
    hold_user   = fields.Many2one('res.users', string='Hold User', track_visibility='onchange')
    attachments = fields.Many2many('ir.attachment', 'product_attachment_rel', 'product_id', 'attachment_id', string='Bảng giá, CSBH...')
    color       = fields.Integer('Color Index', compute="change_colore_on_kanban")
    attch_da    = fields.Many2many('ir.attachment', compute='_get_attachments', string='Bảng giá, CSBH...(DA)')
    attch_block = fields.Many2many('ir.attachment', compute='_get_attachments', string='Bảng giá, CSBH...(Block)')
    link        = fields.Char(string='URL Product', compute='_get_url')

    @api.depends('categ_id.attachments_block', 'categ_id.parent_id.attachments_da')
    def _get_attachments(self):
        self.attch_block = [(6, 0, self.categ_id.attachments_block.ids)]
        self.attch_da = [(6, 0, self.categ_id.attach_da.ids)]

    @api.depends('status')
    def change_colore_on_kanban(self):
        for record in self:
            if record.status == 'no_sell':
                color = 0
            elif record.status == 'hold':
                color = 4
            else:
                color = 6
            record.color = color

    @api.model
    def _auto_cancel_hold_product(self):
        products = self.sudo().search([('status', '=', 'hold')])
        for product in products:
            total_second = False
            if product.hold_date:
                total_second = (datetime.now() - datetime.strptime(product.hold_date, "%Y-%m-%d %H:%M:%S")).total_seconds()
            if (total_second and total_second >= 6 * 3600) or not total_second:
                product.write({
                    'status': 'no_sell',
                    'hold_date': False,
                    'hold_user': False,
                })

    @api.multi
    def action_no_sell(self):
        # if self.status == 'sold':
        #     raise Warning(_("Căn hộ đã bán."))
        self.sudo().write({
            'status': 'no_sell',
            'hold_date': False,
            'hold_user': False,
        })

    @api.multi
    def action_hold(self):
        if self.search_count([('hold_user', '=', self.env.user.id), ('status', '=', 'hold')]) >= 5:
            raise Warning("Bạn chỉ được giữ tối đa 5 căn.")
        if self.status == 'sold':
            raise Warning(_("Căn hộ đã bán."))
        self.sudo().write({
            'status': 'hold',
            'hold_date': datetime.now(),
            'hold_user': self.env.user.id,
        })
        # Track notification
        nof = {
            'product_id': self.id,
            'date': datetime.now(),
            'user_id': self.env.user.id,
            'note': self.env.user.name + u" vừa giữ chỗ căn hộ " + self.name
        }
        self.env['product.notification'].create(nof)
        # Send Email
        url = u'<a href="%s"><strong>tại đây</strong></a>' % self.link
        header = u'<p>Dear,</p>'
        footer = u'<p>Vui lòng truy cập %s để xem thông tin.</p>' % (url,)
        body = u'<p>Căn hộ: <b><i>%s</i></b> vừa được giữ chỗ bởi: <b>%s</b></p>' % (self.name,self.env.user.name,)
        msg = header + body + footer
        # self.message_post(body=body, subtype="mt_comment")
        partner_ids = [mail.partner_id and mail.partner_id.id for mail in self.message_follower_ids]
        mail_values = {
            'email_from': self.env.user.email,
            'email_to': self.env.user.company_id.email,
            'recipient_ids': [(6, 0, partner_ids)],
            'subject': " [Notification]" + self.name,
            'body_html': msg,
            'body': msg,
            'notification': True,
            'author_id': self.env.user.partner_id.id,
            'message_type': "email",
        }
        mail_id = self.env['mail.mail'].create(mail_values)
        mail_id.send()


    @api.multi
    def action_sold(self):
        if self.status == 'sold':
            raise Warning(_("Căn hộ đã bán."))
        self.sudo().write({
            'status': 'sold'
        })
        # Track notification
        nof = {
            'product_id': self.id,
            'date': datetime.now(),
            'user_id': self.env.user.id,
            'note': u"Căn hộ " + self.name + u" đã bán và được cập nhật bởi " + self.env.user.name
        }
        self.env['product.notification'].create(nof)
        # Send Email
        url = u'<a href="%s"><strong>tại đây</strong></a>' % self.link
        header = u'<p>Dear,</p>'
        footer = u'<p>Vui lòng truy cập %s để xem thông tin.</p>' % (url,)
        body = u"<p>Căn hộ: <b><i>%s</i></b> đã bán và được cập nhật bởi: <b>%s</b></p>" % (self.name, self.env.user.name)
        msg = header + body + footer
        # self.message_post(body=body, subtype="mt_comment")
        partner_ids = [mail.partner_id and mail.partner_id.id for mail in self.message_follower_ids]
        mail_values = {
            'email_from': self.env.user.email,
            'email_to': self.env.user.company_id.email,
            'recipient_ids': [(6, 0, partner_ids)],
            'subject': " [Notification]" + self.name,
            'body_html': msg,
            'body': msg,
            'notification': True,
            'author_id': self.env.user.partner_id.id,
            'message_type': "email",
        }
        mail_id = self.env['mail.mail'].create(mail_values)
        mail_id.send()
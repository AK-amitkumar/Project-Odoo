from odoo import fields, api, models, _


class pos_config(models.Model):
    _inherit = "pos.config"

    promotion_ids = fields.Many2many('pos.promotion', 'pos_config_promotion_rel', 'config_id', 'promotion_id',
                                     string='Program')
    allow_promotion = fields.Boolean('Run promotion')

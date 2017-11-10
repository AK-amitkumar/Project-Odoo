from openerp import api, fields, models, _

class pos_order(models.Model):

    _inherit = "pos.order"

    promotion_ids = fields.Many2many('pos.promotion', 'pos_order_promotion_rel', 'order_id', 'promotion_id',
                                     string='Promotions program')


class pos_order_line(models.Model):

    _inherit = "pos.order.line"

    promotion = fields.Boolean('Promotion', readonly=1)


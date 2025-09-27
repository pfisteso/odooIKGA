from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class RoomCategory(models.Model):
    _name = 'ikga.room_category'

    name = fields.Char(string='Name', required=True)
    capacity = fields.Integer(string='Capacity', default=0)

    product_id = fields.Many2one('product.product', string='Product', required=True)

    @api.constrains('capacity')
    def _constrain_capacity(self):
        for rec in self:
            if rec.capacity < 1:
                raise ValidationError('Capacity must be greater than 0')
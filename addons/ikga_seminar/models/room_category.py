from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class RoomCategory(models.Model):
    _name = 'ikga.room_category'

    name = fields.Char(string='Name', required=True)
    capacity = fields.Integer(string='Capacity', default=0)

    product_id = fields.Many2one('product.product', string='Product', required=True)

    price_per_guest = fields.Float(string='Price per Participant', compute='_compute_price')

    @api.constrains('capacity')
    def _constrain_capacity(self):
        for rec in self:
            if rec.capacity < 1:
                raise ValidationError('Capacity must be greater than 0')

    @api.depends('product_id', 'capacity')
    def _compute_price(self):
        for rec in self:
            rec.price_per_guest = rec.product_id.product_tmpl_id.price_amount_taxed / rec.capacity
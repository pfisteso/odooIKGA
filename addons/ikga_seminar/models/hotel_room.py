from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

HOTELS = [('SOH', 'Swiss Olympic House'), ('BEL', 'Hotel Bellavista'), ('GHO', 'Grand Hotel'), ('SEE', 'Seehaus')]

class HotelRoom(models.Model):
    _name = 'ikga.hotel_room'
    _description = 'Hotel Room'

    name = fields.Char(string='Name', required=True)
    hotel = fields.Selection(string='Hotel', selection=HOTELS, required=True)
    room_number = fields.Char(string='Room Number', default=0)

    n_guests = fields.Integer('# Guests', default=0)  # during registration
    room_category_id = fields.Many2one('ikga.room_category', string='Room Category', required=True, index=True)

    country_manager_id = fields.Many2one('res.partner', string='Country Manager', index=True)
    guest_ids = fields.One2many('res.partner', inverse_name='room_id',
                                domain="[('partner_type', '=', 'registration')]", index=True)

    # computed and related fields
    is_full = fields.Boolean('Full', compute='_compute_full')
    capacity = fields.Integer(string='Capacity', related='room_category_id.capacity',store=True)
    price_per_guest = fields.Float(string='Price per Guest', related='room_category_id.price_per_guest',store=True)
    product_id = fields.Many2one('product.product', string='Product', related='room_category_id.product_id', store=True,
                                 index=True)

    @api.depends('capacity', 'n_guests')
    def _compute_full(self):
        for rec in self:
            rec.is_full = rec.capacity == rec.n_guests

    @api.constrains('n_guests', 'guest_ids')
    def _constrain_inhibitants(self):
        for rec in self:
            if rec.n_guests > rec.capacity:
                raise ValidationError('You cannot overbook room {}'.format(rec.name))

            if len(rec.guest_ids) > rec.capacity:
                raise ValidationError('You cannot overbook room {}'.format(rec.name))

    @api.model
    def create(self, vals):
        # Ensure field starts unset if not provided
        vals.setdefault('country_manager_id', False)
        return super().create(vals)

    def write(self, vals):
        if 'country_manager_id' in vals:
            for record in self:
                if record.country_manager_id and record.country_manager_id.id != vals.get('country_manager_id'):
                    raise UserError("The country manager is already set and cannot be changed.")
        return super(HotelRoom, self).write(vals)

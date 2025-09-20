from operator import index

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

ROOM_TYPES = [('SINGLE', 'Single Room'), ('DOUBLE', 'Double Room'), ('THREE BED', 'Three Bed Room'),
              ('FOUR BED', 'Four Bed Room')]

HOTELS = [('SOH', 'Swiss Olympic House'), ('BEL', 'Hotel Bellavista'), ('GHO', 'Grand Hotel'), ('SEH', 'Seehaus')]

class HotelRoom(models.Model):
    _name = 'ikga.hotel_room'
    _description = 'Hotel Room'

    name = fields.Char(string='Name', required=True)
    hotel = fields.Selection(string='Hotel', selection=HOTELS, required=True, index=True)
    room_number = fields.Char(string='Room Number', default=0)

    capacity = fields.Integer(string='Capacity', default=0)
    n_guests = fields.Integer('# Guests', default=0)  # during registration
    room_type = fields.Selection(string='Tech. Name', selection=ROOM_TYPES, index=True, required=True)

    country_manager_id = fields.Many2one('res.partner', string='Country Manager', index=True)
    product_id = fields.Many2one('product.product', string='Product', index=True)
    guest_ids = fields.One2many('res.partner', inverse_name='room_id',
                                domain="[('partner_type', '=', 'registration')]", index=True)

    # computed fields
    is_full = fields.Boolean('Full', compute='_compute_full')

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

from odoo import models, fields, api
from odoo.exceptions import ValidationError

AIRPORTS = [('EPA', 'EuroAirport Basel Mulhouse Freiburg'), ('ZRH', 'Zurich'), ('GVA', 'Geneva'), ('NAN', 'N/A')]
ROOM_TYPES = [('SINGLE', 'Single Room'), ('DOUBLE', 'Double Room'), ('THREE BED', 'Three Bed Room'),
              ('FOUR BED', 'Four Bed Room')]


class ResPartner(models.Model):
    _name = 'res.partner'
    _description = 'Registration Entry for the IKGA Seminar'
    _inherit = 'res.partner'

    partner_type = fields.Selection(string='Partner Type',
                                    selection=[('user', 'User'), ('registration', 'Registration')],
                                    default='user')

    birthdate = fields.Date('Birthdate', required=True)

    # seminar information
    participates_in_seminar = fields.Boolean('Participates in the Seminar?', default=False)
    grade_label = fields.Selection(string='Label', selection=[('KYU', 'Kyu'), ('DAN', 'Dan')], default='KYU')
    grade_number = fields.Integer('Grade Number', default=1)

    # accommodation
    room_preference = fields.Selection(string='Room Preference', selection=ROOM_TYPES, required=True)
    room_id = fields.Many2one(comodel_name='ikga.hotel_room', string='Hotel Room')

    # food & beverages
    is_vegetarian = fields.Boolean('Vegetarian', default=False)
    is_vegan = fields.Boolean('Vegan', default=False)
    has_allergies = fields.Boolean('Food Allergies', default=False)
    allergen_list = fields.Text('Allergen')

    # travel
    interested_in_shuttle_service = fields.Boolean(string='Shuttle Service', default=False)
    airport = fields.Selection(string='Airport', selection=AIRPORTS, default='NAN')
    arrival_datetime = fields.Datetime(string='ETA')
    departure_datetime = fields.Datetime(string='DST')
    need_parking_lot = fields.Boolean('Parking Lot', default=False)

    # computed amd related fields
    grade_description = fields.Char('Grade Description', compute='_compute_grade_description')

    @api.constrains('grade_number')
    def _constrain_grade_number(self):
        for record in self:
            if record.participates_in_seminar:
                if record.grade_number < 1 or record.grade_number > 9:
                    raise ValidationError('Grade must be between 9. Kyu and 9. Dan')

    @api.constrains('has_allergies', 'allergen_list')
    def _constrain_allergies(self):
        for rec in self:
            if rec.has_allergies and len(rec.allergen_list) == 0:
                raise ValidationError('Please list all allergens for the participant.')

    @api.depends('grade_label', 'grade_number')
    def _compute_grade_description(self):
        for record in self:
            record.grade_description = '{}. {}'.format(str(record.grade_number),
                                                       record.grade_label) if record.participates_in_seminar else ''
    @api.model
    def create(self, vals):
        # ToDo: thread lock
        # ToDo: create / adjust sale order - add a room to allocate room resources
        record = super().create(vals)
        if 'partner_type' in vals:
            record.partner_type = vals['partner_type']
        else:
            record.partner_type = self.env.context.get('partner_type', 'user')

        record.country_id = record.create_uid.country_id
        return record

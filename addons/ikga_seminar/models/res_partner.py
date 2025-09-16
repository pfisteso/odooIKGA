from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
    grade_label = fields.Selection(string='Label', selection=[('KYU', 'Kyu'), ('DAN', 'Dan')])
    grade_number = fields.Integer('Grade Number')

    grade_description = fields.Char('Grade Description', compute='_compute_grade_description')

    # accommodation
    room_preference = fields.Selection(string='Room Preference', selection=[('SINGLE', 'Single Room'),
                                                                            ('DOUBLE', 'Double Room'),
                                                                            ('THREE BED', 'Three Bed Room'),
                                                                            ('FOUR BED', 'Four Bed Room')],
                                       required=True)

    # food & beverages
    is_vegetarian = fields.Boolean('Vegetarian', default=False)
    is_vegan = fields.Boolean('Vegan', default=False)
    has_allergies = fields.Boolean('Food Allergies', default=False)
    allergen_list = fields.Text('Allergen')

    # arrival
    interested_in_shuttle_service = fields.Boolean(string='Shuttle Service', default=False)
    airport = fields.Selection(string='Airport', selection=[('LFSB', 'EuroAirport Basel Mulhouse Freiburg'),
                                                            ('ZRH', 'Zurich'), ('GVA', 'Geneva')])
    need_parking_lot = fields.Boolean('Parking Lot', default=False)


    @api.constrains('grade_number')
    def _constrain_grade_number(self):
        for record in self:
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
                                                       record.grade_label) if record.seminar_participation else ''

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

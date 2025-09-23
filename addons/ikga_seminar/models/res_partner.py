import csv
from odoo import models, fields, api
from odoo.exceptions import ValidationError

AIRPORTS = [('EPA', 'EuroAirport Basel Mulhouse Freiburg'), ('ZRH', 'Zurich'), ('GVA', 'Geneva'), ('NAN', 'N/A')]
ROOM_TYPES = [('SINGLE', 'Single Room'), ('DOUBLE', 'Double Room'), ('THREE BED', 'Three Bed Room'),
              ('FOUR BED', 'Four Bed Room')]


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    partner_type = fields.Selection(string='Partner Type',
                                    selection=[('user', 'User'), ('registration', 'Registration')],
                                    default='user')

    birthdate = fields.Date('Birthdate', required=True)

    # seminar information
    country_manager_id = fields.Many2one('res.partner', string='Country Manager', )
    participates_in_seminar = fields.Boolean('Participates in the Seminar?', default=False)
    grade_label = fields.Selection(string='Grade Label', selection=[('KYU', 'Kyu'), ('DAN', 'Dan')], default='KYU')
    grade_number = fields.Integer('Grade Number', default=1)

    # accommodation
    room_preference = fields.Selection(string='Room Preference', selection=ROOM_TYPES, required=True)
    room_id = fields.Many2one(comodel_name='ikga.hotel_room', string='Hotel Room')

    # food & beverages
    is_vegetarian = fields.Boolean('Vegetarian', default=False)
    is_vegan = fields.Boolean('Vegan', default=False)
    has_allergies = fields.Boolean('Food Allergies', default=False)
    allergen_list = fields.Text('Allergens')

    # travel
    needs_shuttle = fields.Boolean(string='Shuttle Service', default=False)
    airport = fields.Selection(string='Airport', selection=AIRPORTS, default='NAN')
    arrival_datetime = fields.Datetime(string='Arrival')
    departure_datetime = fields.Datetime(string='Departure')
    needs_parking_lot = fields.Boolean('Parking Lot', default=False)

    # back up
    exported = fields.Boolean('Exported', default=False)
    updated = fields.Boolean('Updated', default=False)

    # compute price amounts
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_seminar = fields.Monetary('Seminar Fee', currency_field='currency_id')
    amount_hotel_room = fields.Monetary('Room & Board', currency_field='currency_id')

    # computed amd related fields
    grade_description = fields.Char('Grade', compute='_compute_grade_description')
    amount_total = fields.Monetary('Total', currency_field='currency_id', compute='_compute_amount_total')

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

    @api.depends('amount_seminar', 'amount_hotel_room')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = rec.amount_seminar + rec.amount_hotel_room

    def cron_action_export_backup(self):
        file = []

        header = ['Type', 'Partner Type', 'Name', 'Birthdate', 'Country',
                  'Country Manager', 'Participates in Seminar', 'Grade Number', 'Grade Label',
                  'Room Preference', 'Vegetarian', 'Vegan', 'Allergies', 'Allergens',
                  'Shuttle', 'Airport', 'Arrival', 'Departure', 'Parking Lot',
                  'Currency', 'Seminar Fee', 'Room & Board']
        file.append(header)

        updated_records = self.env['res.partner'].search([('partner_type', '=', 'registration'),
                                                          ('updated', '=', True),
                                                          ('exported', '=', True)])
        for rec in updated_records:
            row = ['UPDATE', rec.partner_type, rec.name, rec.birthdate.strftime('%d/%m/%Y'), rec.country_id.name,
                   rec.country_manager_id.name, rec.participates_in_seminar, rec.grade_number, rec.grade_label,
                   rec.room_preference, rec.is_vegetarian, rec.is_vegan, rec.has_allergies, rec.allergen,
                   rec.needs_shuttle, rec.airport, rec.arrival_datetime, rec.departure_datetime, rec.needs_parking_lot,
                   rec.currency_id, rec.amount_seminar, rec.amount_hotel_room]

        # ToDo: send updated to backup address
        # if len (file) > 1
        updated_records.write({'exported': True, 'updated': False})

        file = [header]
        new_records = self.env['res.partner'].search([('partner_type', '=', 'registration'),
                                                     ('exported', '=', False)])
        for rec in new_records:
            row = ['NEW', rec.partner_type, rec.name, rec.birthdate.strftime('%d/%m/%Y'), rec.country_id.name,
                   rec.country_manager_id.name, rec.participates_in_seminar, rec.grade_number, rec.grade_label,
                   rec.room_preference, rec.is_vegetarian, rec.is_vegan, rec.has_allergies, rec.allergen,
                   rec.needs_shuttle, rec.airport, rec.arrival_datetime, rec.departure_datetime, rec.needs_parking_lot,
                   rec.currency_id, rec.amount_seminar, rec.amount_hotel_room]
            file.append(row)

        # ToDo: send new records to backup address
        # if len(file) > 1
        new_records.write({'exported': True, 'updated': False})


    @api.model
    def create(self, vals):
        record = super().create(vals)
        if 'partner_type' not in vals:
            record.partner_type = self.env.context.get('partner_type', 'user')

        if 'country_manager_id' not in vals:
            record.country_manager_id = record.create_uid.partner_id
        if 'country_id' not in vals:
            record.country_id = record.country_manager_id.country_id
        record.currency_id = record.create_uid.company_id.currency_id
        return record

    def write(self, vals):
        if 'exported' not in vals and 'updated' not in vals:
            vals.update({'updated': True})
        super(ResPartner, self).write(vals)

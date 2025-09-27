import csv
from datetime import date
from io import StringIO

from odoo import models, fields, api
from odoo.exceptions import ValidationError

AIRPORTS = [('EPA', 'EuroAirport Basel Mulhouse Freiburg'), ('ZRH', 'Zurich'), ('GVA', 'Geneva'), ('NAN', 'N/A')]


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    is_registration = fields.Boolean('Is Registration', default=False)

    birthdate = fields.Date('Birthdate', required=True)

    # seminar information
    country_manager_id = fields.Many2one('res.partner', string='Country Manager',
                                         domain=['&', ('parent_id', '!=', False), ('is_registration', '=', False)])
    participates_in_seminar = fields.Boolean('Participates in the Seminar?', default=False)
    grade_label = fields.Selection(string='Grade Label', selection=[('KYU', 'Kyu'), ('DAN', 'Dan')], default='KYU')
    grade_number = fields.Integer('Grade Number', default=1)

    # room & board
    room_category_id = fields.Many2one('ikga.room_category', string='Room Category', required=True)
    room_id = fields.Many2one(comodel_name='ikga.hotel_room', string='Hotel Room')
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
        name_pattern = date.today().strftime('%Y-%m-%d_{}.csv')

        header = ['Type', 'Is Registration', 'Name', 'Birthdate', 'Country',
                  'Country Manager', 'Participates in Seminar', 'Grade Number', 'Grade Label',
                  'Room Preference', 'Vegetarian', 'Vegan', 'Allergies', 'Allergens',
                  'Shuttle', 'Airport', 'Arrival', 'Departure', 'Parking Lot',
                  'Seminar Fee', 'Room & Board']

        file = [header]
        new_records = self.env['res.partner'].search([('is_registration', '=', True),
                                                      ('exported', '=', False)])
        for rec in new_records:
            row = ['NEW', rec.is_registration, rec.name, rec.birthdate.strftime('%d/%m/%Y'), rec.country_id.name,
                   rec.country_manager_id.name, rec.participates_in_seminar, rec.grade_number, rec.grade_label,
                   rec.room_category_id.name, rec.is_vegetarian, rec.is_vegan, rec.has_allergies, rec.allergen_list,
                   rec.needs_shuttle, rec.airport, rec.arrival_datetime, rec.departure_datetime, rec.needs_parking_lot,
                   rec.amount_seminar, rec.amount_hotel_room]
            file.append(row)

        if len(file) > 1:
            attachment = self._create_attachment(name_pattern.format('NEW'), file)
            self._send_email(attachment)
            new_records.write({'exported': True, 'updated': False})

        file = [header]
        updated_records = self.env['res.partner'].search([('is_registration', '=', True),
                                                          ('updated', '=', True),
                                                          ('exported', '=', True)])
        for rec in updated_records:
            row = ['UPDATE', rec.is_registration, rec.name, rec.birthdate.strftime('%d/%m/%Y'), rec.country_id.name,
                   rec.country_manager_id.name, rec.participates_in_seminar, rec.grade_number, rec.grade_label,
                   rec.room_category_id.name, rec.is_vegetarian, rec.is_vegan, rec.has_allergies, rec.allergen_list,
                   rec.needs_shuttle, rec.airport, rec.arrival_datetime, rec.departure_datetime, rec.needs_parking_lot,
                   rec.amount_seminar, rec.amount_hotel_room]
            file.append(row)

        if len(file) > 1:
            attachment = self._create_attachment(name_pattern.format('UPDATE'), file)
            self._send_email(attachment)
        updated_records.write({'exported': True, 'updated': False})

    def _create_attachment(self, name, rows):
        csv_data = StringIO()
        writer = csv.writer(csv_data)
        writer.writerows(rows)

        attachment = self.env['ir.attachment'].create({
            'name': name,
            'description': name,
            'res_model': self._name,
            'type': 'binary',
            'public': False,
            'db_datas': csv_data.getvalue().encode('utf-8'),
            'mimetype': 'text/csv'
        })
        csv_data.close()
        return attachment

    def _send_email(self, attachment):
        email_template = self.env.ref('ikga_seminar.registration_backup_email_template')
        email_template.attachment_ids = [attachment.id]
        email_template.send_mail(self.id, raise_exception=False, force_send=True)

    @api.model
    def create(self, vals):
        records = super().create(vals)
        for rec in records:
            if 'country_manager_id' not in vals:
                rec.country_manager_id = rec.create_uid.partner_id
            if 'country_id' not in vals:
                rec.country_id = rec.country_manager_id.country_id
            if 'currency_id' not in vals:
                if not rec.is_registration:
                    if rec.specific_property_product_pricelist is not None:
                        rec.currency_id = rec.specific_property_product_pricelist.currency_id.id
                    else:
                        rec.currency_id = rec.country_manager_id.currency_id.id
        return records

    def write(self, vals):
        if 'exported' not in vals and 'updated' not in vals:
            vals.update({'updated': True})
        return super(ResPartner, self).write(vals)

from datetime import date

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
    seminar_participation = fields.Boolean('Participates in the Seminar?', default=False)

    grade_label = fields.Selection(string='Label', selection=[('KYU', 'Kyu'), ('DAN', 'Dan')])
    grade_number = fields.Integer('Grade Number')

    # date_arrival = fields.Date('Arrival Date', required=True)
    # date_departure = fields.Date('Departure Date', required=True)

    grade_description = fields.Char('Grade Description', compute='_compute_grade_description')
    room_assignment_id = fields.One2many('ikga_seminar.room_assignment', 'guest_id')

    @api.constrains('grade_number')
    def _constrain_grade_number(self):
        for record in self:
            if record.grade_number < 1 or record.grade_number > 9:
                raise ValidationError('Grade must be between 9. Kyu and 9. Dan')

    @api.constrains('date_arrival', 'date_departure')
    def _constrain_date_arrival(self):
        for record in self:
            if record.date_arrival > date.fromisoformat('2026-08-12') or record.date_departure < date.fromisoformat(
                    '2026-08-10'):
                raise ValidationError('Arrival is only possible between August 10 and August 12, 2026')
            if record.date_departure < date.fromisoformat('2026-08-16'):
                raise ValidationError('Departure is only possible as of August 16, 2026')

    @api.depends('grade_label', 'grade_number')
    def _compute_grade_description(self):
        for record in self:
            record.grade_description = '{}. {}'.format(str(record.grade_number),
                                                       record.grade_label) if record.seminar_participation else ''

    # def _create_sale_order(self):
    #     pass

    def create(self, vals):
        record = super().create(vals)
        if 'partner_type' in vals:
            record.partner_type = vals['partner_type']
        else:
            record.partner_type = self.env.context.get('partner_type', 'user')

        record.country_id = record.create_uid.country_id
        return record

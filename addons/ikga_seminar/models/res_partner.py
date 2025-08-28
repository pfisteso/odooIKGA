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

    grade_description = fields.Char('Grade Description', compute='_compute_grade_description')

    @api.constrains('grade_number')
    def _constrain_grade_number(self):
        for record in self:
            if record.grade_number < 1 or record.grade_number > 9:
                raise ValidationError('Grade must be between 9. Kyu and 9. Dan')

    @api.depends('grade_label', 'grade_number')
    def _compute_grade_description(self):
        for record in self:
            record.grade_description = '{}. {}'.format(str(record.grade_number), record.grade_label) if record.seminar_participation else ''

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


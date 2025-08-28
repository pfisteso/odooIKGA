from datetime import date

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Room(models.Model):
    _name = 'ikga_seminar.room'
    _description = 'IKGA Seminar Room'
    _rec_name = 'room_number'

    room_number = fields.Integer(string='Room Number', unique=True)
    max_capacity = fields.Integer(string='Max Capacity', required=True)
    child_bed_available = fields.Boolean(string='Child Bed Available')

    room_category = fields.Selection(string='Room Category', required=True, default='DOUBLE',
                                     selection=[('SINGLE', 'Single Room'), ('DOUBLE', 'Double Room')])

    adults_ids = fields.One2many(string='Guests', comodel_name='ikga_seminar.room_assignment',
                                inverse_name='room_id', domain='[["guest_category", "=", "ADULT"]]')
    children_ids = fields.One2many(string='Children', comodel_name='ikga_seminar.room_assignment',
                                   inverse_name='room_id', domain='[["guest_category", "=", "CHILD"]]')

    reserved = fields.Boolean(string='Reserved', compute='_compute_reserved')
    n_adults = fields.Integer(string='Adults', compute='_count_adults')
    n_children = fields.Integer(string='Children', compute='_count_children')

    @api.depends('n_adults')
    def _compute_reserved(self):
        for room in self:
            room.reserved = room.n_adults > 0

    @api.depends('adults_ids')
    def _count_adults(self):
        for room in self:
            room.n_adults = len(room.adults_ids)

    @api.depends('children_ids')
    def _count_children(self):
        for room in self:
            room.n_children = len(room.children_ids)

    @api.constrains('n_adults')
    def _constrain_adults(self):
        for room in self:
            if room.n_adults > room.max_capacity:
                raise ValidationError(
                    'Cannot assign {} adults to room No. {}.'.format(room.n_adults, room.room_number) +
                    'Max Capacity is {}.'.format(room.max_capacity)
                )

    @api.constrains('n_children', 'child_bed_available')
    def _constrain_children(self):
        for room in self:
            if room.n_children > 0 and not room.child_bed_available:
                raise ValidationError('Room No. {} cannot host children.'.format(room.room_number))

            if room.n_children > 0 and room.n_adults == 0:
                raise ValidationError('Cannot assign a child to a room without adults.')



class RoomAssignment(models.Model):
    _name = 'ikga_seminar.room_assignment'
    _rec_name = 'rec_name'

    room_id = fields.Many2one('ikga_seminar.room', string='Room', required=True, index=True, ondelete='cascade')
    guest_id = fields.Many2one('res.partner', string='Guest', required=True, index=True, unique=True, ondelete='cascade')
    guest_category = fields.Selection(string='Category', selection=[('ADULT', 'Adult'), ('CHILD', 'Child')],
                                      required=True, default='ADULT')

    rec_name = fields.Char(string='Name', compute='_compute_rec_name')

    guest_name = fields.Char(string='Name', related='guest_id.name')
    guest_country = fields.Char(string='Country', related='guest_id.country_id.name')

    @api.depends('guest_id')
    def _compute_rec_name(self):
        for assignment in self:
            assignment.rec_name = '{}, {}'.format(assignment.guest_id.name, assignment.guest_id.country_id.name)

    @api.constrains('guest_category')
    def _constrain_guest_category(self):
        for assignment in self:
            if assignment.guest_category == 'CHILD':
                # ToDo: Bis zu welchem Alter können Gäste im Kinderbett schlafen?
                if assignment.guest_id.birthdate > date.fromisoformat('2022-08-12'):
                    raise ValidationError('Only children younger than 4 years old can sleep in a child bed.')
            else:  # adults
                # ToDo: Bis zu welchem Alter können Gäste im Kinderbett schlafen?
                if assignment.guest_id.birthdate < date.fromisoformat('2022-08-12'):
                    raise ValidationError('Children younger than 4 years must share a room with their parent.')
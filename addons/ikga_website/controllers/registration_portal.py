from datetime import date, datetime

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):

    @http.route(['/my/registrations'], type='http', auth="user", website=True)
    def portal_my_registrations(self, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user

        ResPartner = request.env['res.partner']
        domain = [
            ('create_uid', '=', user.id),
            ('partner_type', '=', 'registration'),
        ]

        registrations = ResPartner.search(domain, order='create_date desc')

        values.update({
            'registrations': registrations,
        })

        return request.render('ikga_website.portal_registration_list', values)

    @http.route(['/my/registrations/create'], type='http', auth="user", website=True)
    def portal_create_registration(self, **kw):
        values = self._prepare_portal_layout_values()
        # ToDo: check available rooms and add to values
        values.update({
            'title': 'New Registration',
            'available_room_types': [('SINGLE', 'Single Room'),
                                     ('DOUBLE', 'Double Room'),
                                     ('THREE BED', 'Three-Bed Room'),
                                     ('FOUR BED', 'Four-Bed Room')],
            'airports': [('EPA', 'EuroAirport Basel Mulhouse Freiburg'), ('ZRH', 'Zurich'), ('GVA', 'Geneva'),
                         ('NAN', 'N/A')]
        })

        if 'reg_first_name' in kw:
            # ToDo: load values from kw
            pass
        else:
            values.update({
                'error': False,
                # personal information
                'reg_first_name': '',
                'reg_last_name': '',
                'reg_birthdate': date.fromisoformat('1900-01-01'),
                # seminar
                'reg_seminar_participation': False,
                'reg_grade_number': 1,
                'reg_grade_label': 'KYU',
                # room & board
                'reg_room_preference': ' ',  # ToDo
                'reg_is_vegetarian': False,
                'reg_is_vegan': False,
                'reg_has_allergies': False,
                'reg_allergen_list': '',
                # travel
                'reg_shuttle_service': False,
                'reg_airport': 'NAN',
                'reg_arrival_datetime': datetime.fromisoformat('2026-08-12T08:00:00'),  # ToDo: evtl. Zeitzone anpassen
                'reg_departure_datetime': datetime.fromisoformat('2026-08-16T18:00:00'),
                # ToDo: evtl. Zeitzone anpassen
                'reg_parking_lot': False
            })

        return request.render('ikga_website.portal_registration_form', values)

        # @http.route(['/my/registrations/edit/<int:reg_id>'], type='http', auth="user", website=True)
        # def portal_edit_registration(self, reg_id, **kw):
        #    values = self._prepare_portal_layout_values()
        ResPartner = request.env['res.partner']
        registration = ResPartner.search([('id', '=', reg_id)])
        if registration.create_uid == request.env.user:
            values.update({
                'title': 'Edit Registration',
                'registration': registration
            })
            return request.render('ikga_website.portal_registration_form', values)
        else:
            # ToDo: add error message to values
            return request.redirect('/my/registrations')

    @http.route(['/my/registrations/delete/<int:reg_id>'], type='http', auth="user", website=True)
    def portal_delete_registration(self, reg_id, **kw):
        values = self._prepare_portal_layout_values()
        ResPartner = request.env['res.partner']
        registration = ResPartner.search([('id', '=', reg_id)])
        if registration.create_uid == request.env.user:
            registration.unlink()
        else:
            # ToDo: add error message to values
            print("ABC")
        return request.redirect('/my/registrations')

    @http.route(['/my/registrations/save_create'], type='http', auth="user", website=True)
    def portal_save_registration(self, first_name: str, last_name: str, birthdate: date,
                                 grade_number: int, grade_label: str,
                                 room_preference: str, allergen_list: str, airport: str,
                                 arrival_datetime: datetime, departure_datetime: datetime,
                                 participates_in_seminar: bool = False, is_vegetarian: bool = False,
                                 is_vegan: bool = False, has_allergies: bool = False, needs_shuttle: bool = False,
                                 needs_parking_lot: bool = False, **kw):
        #     registration_seminar_participation = True if 'registration_seminar_participation' in kw else False
        #     partner_type = 'registration'
        #
        #     if int(registration_id) < 0:
        #         self._create_registration(name=registration_name, birthdate=registration_birthdate,
        #                                   seminar_participation=registration_seminar_participation,
        #                                   grade_number=registration_grade_number, grade_label=registration_grade_label)
        #
        #     else:
        #         self._update_registration(id=registration_id, name=registration_name, birthdate=registration_birthdate,
        #                                   seminar_participation=registration_seminar_participation,
        #                                   grade_number=registration_grade_number, grade_label=registration_grade_label)
        #
        return request.redirect('/my/registrations')

    def _create_registration(self, name, birthdate, seminar_participation, grade_number, grade_label):
        values = self._get_registration_values(name, birthdate, seminar_participation, grade_number, grade_label)
        ResPartner = request.env['res.partner']
        partner_record = ResPartner.create(values)

    def _update_registration(self, id, name, birthdate, seminar_participation, grade_number, grade_label):
        values = self._get_registration_values(name, birthdate, seminar_participation, grade_number, grade_label)

        ResPartner = request.env['res.partner']
        partner_record = ResPartner.search(domain=[['id', '=', id]])
        if partner_record:
            partner_record.write(values)

    def _get_registration_values(self, name, birthdate, seminar_participation, grade_number, grade_label):
        values = {
            'name': name,
            'birthdate': birthdate,
            'seminar_participation': seminar_participation,
            'grade_number': grade_number,
            'grade_label': grade_label,
            'partner_type': 'registration',
        }
        return values

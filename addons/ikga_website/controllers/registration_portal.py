from datetime import date

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
        values.update({
            'title': 'New Registration',
            'registration': False
        })

        return request.render('ikga_website.portal_registration_form', values)

    @http.route(['/my/registrations/edit/<int:reg_id>'], type='http', auth="user", website=True)
    def portal_edit_registration(self, reg_id, **kw):
        values = self._prepare_portal_layout_values()
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



    @http.route(['/my/registrations/save'], type='http', auth="user", website=True)
    def portal_save_registration(self, registration_id: int, registration_name: str, registration_birthdate: date,
                                 registration_grade_number: int,
                                 registration_grade_label:str, **kw):
        registration_seminar_participation = True if 'registration_seminar_participation' in kw else False
        if int(registration_id) < 0:
            self._create_registration(name=registration_name, birthdate=registration_birthdate,
                                      seminar_participation=registration_seminar_participation,
                                      grade_number=registration_grade_number, grade_label=registration_grade_label)

        else:
            self._update_registration(id=registration_id, name=registration_name, birthdate=registration_birthdate,
                                      seminar_participation=registration_seminar_participation,
                                      grade_number=registration_grade_number, grade_label=registration_grade_label)

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
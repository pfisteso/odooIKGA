import json
from datetime import date, datetime, timedelta

from odoo import http
from odoo.http import request
from odoo.exceptions import UserError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):

    @http.route(['/my/registrations'], type='http', auth="user", website=True)
    def portal_my_registrations(self, **kw):
        ts = datetime.now()
        deadline = request.env['res.config.settings'].sudo().get_values()['registration_deadline']

        values = self._prepare_portal_layout_values()
        user = request.env.user

        ResPartner = request.env['res.partner']
        domain = [('is_registration', '=', True)]
        registrations = ResPartner.search(domain, order='create_date desc')

        values.update({
            'registrations': registrations,
            'registration_closed': ts > deadline,
        })

        return request.render('ikga_website.portal_registration_list', values)

    @http.route(['/my/registrations/create'], type='http', auth="user", website=True)
    def portal_create_registration(self, **kw):
        # check deadline
        deadline = request.env['res.config.settings'].sudo().get_values()['registration_deadline']
        ts = datetime.now()
        if ts > deadline:
            return request.redirect('/my/registrations')

        values = self._prepare_portal_layout_values()

        values.update({
            'title': 'New Registration',
            'available_room_types': self._fetch_available_room_types(),
            'airports': [('EPA', 'EuroAirport Basel Mulhouse Freiburg'),
                         ('ZRH', 'Zurich'), ('GVA', 'Geneva'),
                         ('NAN', 'N/A')]
        })

        if 'reg_first_name' in kw:
            values.update(kw)
        else:
            values.update({
                'err': False,
                # personal information
                'reg_first_name': '',
                'reg_last_name': '',
                'reg_birthdate': date.fromisoformat('2000-12-31'),
                # seminar
                'reg_seminar_participation': False,
                'reg_grade_number': 1,
                'reg_grade_label': 'KYU',
                # room & board
                'reg_room_preference': '',
                'reg_is_vegetarian': False,
                'reg_is_vegan': False,
                'reg_has_allergies': False,
                'reg_allergen_list': '',
                # travel
                'reg_shuttle_service': False,
                'reg_airport': 'NAN',
                'reg_arrival_datetime': datetime.fromisoformat('2026-08-12T08:00:00'),
                'reg_departure_datetime': datetime.fromisoformat('2026-08-16T18:00:00'),
                'reg_parking_lot': False
            })

        return request.render('ikga_website.portal_registration_form', values)


    @http.route(['/my/registrations/save_create'], type='http', auth="user", website=True)
    def portal_save_registration(self, first_name: str, last_name: str, birthdate: date,
                                 grade_number: int, grade_label: str, room_preference: int, allergen_list: str,
                                 airport: str, arrival_datetime: str, departure_datetime: str,
                                 participates_in_seminar: bool = False, is_vegetarian: bool = False,
                                 is_vegan: bool = False, has_allergies: bool = False, needs_shuttle: bool = False,
                                 needs_parking_lot: bool = False, **kw):

        # prepare all values for the registration
        participant_name = '{} {}'.format(first_name, last_name.upper())
        registration_vals = {
            'is_registration': True,
            'name': participant_name,
            'birthdate': birthdate,
            'participates_in_seminar': participates_in_seminar,

            'room_category_id': int(room_preference),
            'is_vegetarian': is_vegetarian,
            'is_vegan': is_vegan,
            'has_allergies': has_allergies,
            'needs_shuttle': needs_shuttle,
            'needs_parking_lot': needs_parking_lot,
        }
        if participates_in_seminar:
            registration_vals.update({
                'grade_number': grade_number,
                'grade_label': grade_label,
            })
        if has_allergies:
            registration_vals.update({'allergen_list': allergen_list})
        if needs_shuttle:
            registration_vals.update({
                'airport': airport,
                'arrival_datetime': datetime.fromisoformat(arrival_datetime) - timedelta(hours=2),  # adjust timezone!
                'departure_datetime': datetime.fromisoformat(departure_datetime) - timedelta(hours=2) # adjust timezone!
            })

        # fetch or create sale order and products
        sale_order = self._fetch_or_create_sale_order()
        seminar_fee_product = self._fetch_seminar_fee()
        update_values = {'currency_id': sale_order.currency_id.id,}

        registration = None
        try:
            registration = request.env['res.partner'].create(registration_vals)
            room, new_booking = self._fetch_room(room_preference)

        except Exception as e:
            if registration is not None:
                registration.sudo().unlink()

            return self.portal_create_registration(**{
                'err': str(e),
                # personal information
                'reg_first_name': first_name,
                'reg_last_name': last_name,
                'reg_birthdate': birthdate,
                # seminar
                'reg_seminar_participation': participates_in_seminar,
                'reg_grade_number': grade_number,
                'reg_grade_label': grade_label,
                # room & board
                'reg_room_preference': room_preference,
                'reg_is_vegetarian': is_vegetarian,
                'reg_is_vegan': is_vegan,
                'reg_has_allergies': has_allergies,
                'reg_allergen_list': allergen_list,
                # travel
                'reg_shuttle_service': needs_shuttle,
                'reg_airport': airport,
                'reg_arrival_datetime': arrival_datetime,
                'reg_departure_datetime': departure_datetime,
                'reg_parking_lot': needs_parking_lot
            })

        if participates_in_seminar:
            so_line = request.env['sale.order.line'].search([('order_id', '=', sale_order.id),
                                                             ('product_id', '=', seminar_fee_product.id)])
            if len(so_line) > 0:
                so_line.write({'product_uom_qty': so_line.product_uom_qty + 1})
            else:
                so_line = request.env['sale.order.line'].create({
                    'name': seminar_fee_product.product_tmpl_id.name,
                    'order_id': sale_order.id,
                    'product_id': seminar_fee_product.id,
                    'product_uom_qty': 1,
                    'sequence': 100
                })
            update_values.update({'amount_seminar': so_line.price_unit})

        if new_booking:
            so_line = request.env['sale.order.line'].search([('order_id', '=', sale_order.id),
                                                             ('product_id', '=', room.product_id.id)])
            if len(so_line) > 0:
                so_line.write({'product_uom_qty': so_line.product_uom_qty + 1})
            else:
                so_line = request.env['sale.order.line'].create({
                    'name': room.product_id.product_tmpl_id.name,
                    'order_id': sale_order.id,
                    'product_id': room.product_id.id,
                    'product_uom_qty': 1
                })
            update_values.update({'amount_hotel_room': so_line.price_unit / room.capacity})
        else:
            so_line = request.env['sale.order.line'].search([('order_id', '=', sale_order.id),
                                                             ('product_id', '=', room.product_id.id)])
            update_values.update({'amount_hotel_room': so_line.price_unit / room.capacity})


        registration.write(update_values)
        return request.redirect('/my/registrations')

    def _fetch_or_create_sale_order(self):
        country_manager = request.env.user.partner_id
        # is there an "open" sale order?
        sale_order = request.env['sale.order'].search([('partner_id', '=', country_manager.id),
                                                       ('state', '=', 'draft')])

        if len(sale_order) == 0:
            sale_order = request.env['sale.order'].create({
                'partner_id': country_manager.id
            })
        return sale_order

    def _fetch_seminar_fee(self):
        product_id = request.env['res.config.settings'].sudo().get_values()['seminar_fee_product_id']
        if not product_id:
            raise Exception('The system is misconfigured. Please contact us at info@ikgaswitzerland.ch.')
        return product_id

    def _fetch_room(self, room_preference: int):
        country_manager = request.env.user.partner_id
        # try to find an already booked with open capacity
        booked_rooms = request.env['ikga.hotel_room'].sudo().search([('country_manager_id', '=', country_manager.id),
                                                              ('room_category_id', '=', int(room_preference))])

        for room in booked_rooms:
            if not room.is_full:
                room.write({'n_guests': room.n_guests + 1})
                return room, False
        else:
            while True:
                try:
                    # look for an empty room
                    room = request.env['ikga.hotel_room'].sudo().search([('room_category_id', '=', int(room_preference)),
                                                                  ('country_manager_id', '=', False)], limit=1)
                    if not room or room is None or len(room) == 0:
                        rooms = request.env['ikga.hotel_room'].sudo().search([('room_category_id','=', int(room_preference))])
                        raise Exception(
                            'Unfortunately, all rooms of the desired type are booked. Please select a different category. {}'.format(rooms.room_category_id))

                    room.write({'country_manager_id': country_manager.id, 'n_guests': 1})
                    return room, True
                except UserError as e:
                    # retry
                    print('retry')

    def _fetch_available_room_types(self):
        available_rooms = []
        country_manager = request.env.user.partner_id
        room_categories = request.env['ikga.room_category'].search(domain=[])
        for rt in room_categories:
            rooms = request.env['ikga.hotel_room'].search([('room_category_id', '=', rt.id),
                                                           ('country_manager_id', '=', False)])
            if rooms and rooms is not None and len(rooms) > 0:
                available_rooms.append((rt.id, rt.name))
            else:
                rooms = request.env['ikga.hotel_room'].search([('room_category_id', '=', rt.id),
                                                               ('country_manager_id', '=', country_manager.id)])
                for r in rooms:
                    if not r.is_full:
                        available_rooms.append((rt.id, rt.name))
                        break
        return available_rooms

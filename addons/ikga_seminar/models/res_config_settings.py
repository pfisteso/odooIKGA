from datetime import datetime
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    registration_deadline = fields.Datetime(string='Registration Deadline')
    seminar_fee_product_id = fields.Many2one('product.product', string='Seminar Fee')

    def set_values(self):
        super().set_values()
        # config fields: store ir.config_parameters
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_param('ikga.registration_deadline',
                                    self.registration_deadline.strftime('%Y-%m-%dT%H:%M:%S'))
        IrConfigParameter.set_param('ikga.seminar_fee_product_id', str(self.seminar_fee_product_id.id))


    def get_values(self):
        values = super().get_values()
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        deadline_string = IrConfigParameter.get_param('ikga.registration_deadline', '2026-03-01T05:00:00')

        values.update({'registration_deadline': datetime.fromisoformat(deadline_string)})

        product_id = IrConfigParameter.get_param('ikga.seminar_fee_product_id', False)
        if product_id != 'False':
            values['seminar_fee_product_id'] = self.env['product.product'].sudo().search([('id', '=', int(product_id))])
        else:
            values['seminar_fee_product_id'] = False


        return values


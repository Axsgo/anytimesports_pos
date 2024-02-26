# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ProductCategory(models.Model):
    _inherit = "product.category"

    def name_get(self):
        res = []
        for field in self:
            res.append((field.id, '%s' % field.complete_name))
        return res


ProductCategory()


class ProductTemplate(models.Model):
    _inherit = "product.template"

    usd_currency_id = fields.Many2one('res.currency', string='USD Currency', compute='get_usd_currency')
    rp_aed = fields.Monetary('RP AED', currency_field='currency_id')
    rp_usd = fields.Monetary('RP USD', currency_field='usd_currency_id')
    uc_usd = fields.Monetary('UC USD', currency_field='usd_currency_id')

    @api.depends('type', 'currency_id')
    def get_usd_currency(self):
        usd_currency = self.env['res.currency'].sudo().search([('name','=','USD')], limit=1)
        for record in self:
            record.usd_currency_id = usd_currency and usd_currency.id


ProductTemplate()

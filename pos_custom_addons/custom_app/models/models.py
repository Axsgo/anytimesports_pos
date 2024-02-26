# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductInherited(models.Model):
    _inherit = "product.template"

    hot_deals = fields.Boolean(string="Hot Sale")
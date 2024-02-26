# -*- coding: utf-8 -*-
from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    receipt_qr_image = fields.Image("QR Image", max_width=128, max_height=128)
    qr_image_filename = fields.Char('QR Image File Name')
    receipt_qr_content = fields.Text("QR Content")

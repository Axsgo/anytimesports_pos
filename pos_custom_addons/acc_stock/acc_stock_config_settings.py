### import file ###
from odoo import api,models,fields

class AccProductSettings(models.TransientModel):
	_inherit = "res.config.settings"

	# group_temp_product = fields.Boolean("Enable Temporary Product",implied_group='acc_stock.group_temp_product')
	enable_auto_lot = fields.Boolean("Enable Automatic Serial No")
	customer_journal_id = fields.Many2one('account.journal', string='Customer Journal',
	                                  config_parameter='stock_move_invoice.customer_journal_id')
	vendor_journal_id = fields.Many2one('account.journal', string='Vendor Journal',
	                                config_parameter='stock_move_invoice.vendor_journal_id')

	@api.onchange('enable_auto_lot')
	def create_lot_seq(self):
		if self.enable_auto_lot == True:
			product_ids = self.env['product.template'].search([('tracking','=','serial')])
			for line in product_ids:
				line.enable_auto_lot = True
		else:
			product_ids = self.env['product.template'].search([('tracking','=','serial')])
			for line in product_ids:
				line.enable_auto_lot = False

	@api.model
	def get_values(self):
		res = super(AccProductSettings, self).get_values()
		params = self.env['ir.config_parameter'].sudo()
		enable_auto_lot = params.get_param('enable_auto_lot',default=False)
		res.update(enable_auto_lot=enable_auto_lot)
		return res

	def set_values(self):
		super(AccProductSettings, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param("enable_auto_lot",self.enable_auto_lot)
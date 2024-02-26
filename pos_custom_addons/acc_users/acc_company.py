from odoo import models,fields

class AccCompany(models.Model):
	_inherit = "res.company"

	erp_email = fields.Char("ERP Email")
	war_street = fields.Char("Street")
	war_street2 = fields.Char("Street 2")
	war_city = fields.Char("City")
	war_state_id = fields.Many2one('res.country.state','State')
	war_zip = fields.Char("Zipcode")
	war_country_id = fields.Many2one('res.country','Country')
	war_phone = fields.Char("Warehouse Phone")
	war_email = fields.Char("Warehouse Email")
	company_seal = fields.Binary("Company Seal")
	brand_footer = fields.Binary("Brand Footer")
	fax = fields.Char("Fax")

	def name_get(self):
		res = []
		for field in self:
			if field.state_id:
				res.append((field.id, '%s - %s' %(field.name,field.state_id.name)))
			else:
				res.append((field.id, '%s' %(field.name)))
		return res
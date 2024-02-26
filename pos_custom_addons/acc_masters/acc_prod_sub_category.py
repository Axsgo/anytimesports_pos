### import file ###
from odoo import api,models,fields
import time
from odoo.exceptions import UserError

class AccProductSubCategory(models.Model):
	_name = "acc.product.sub.category"
	_description = "Product Sub-Category"

	def name_get(self):
		res = []
		for field in self:
			if field.categ_id:
				res.append((field.id, '%s - %s' %(field.name,field.categ_id.name)))
			else:
				res.append((field.id, '%s' %(field.name)))
		return res

	name = fields.Char("Name")
	categ_id = fields.Many2one('product.category','Brand')
	company_id = fields.Many2one('res.company','Company')
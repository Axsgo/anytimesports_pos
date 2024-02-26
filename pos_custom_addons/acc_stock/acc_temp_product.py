from odoo import api,models,fields
import time

class AccTempProduct(models.Model):
	_name = "acc.temp.product"

	def write(self, vals):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
		return super(AccTempProduct, self).write(vals)

	name = fields.Char("Name")
	default_code = fields.Char("Product Code",size=10)
	type = fields.Selection([('product','Storable Product'),('consu','Consumable'),('service','Service')],'Product Type',default='product')
	categ_id = fields.Many2one("product.category",'Brand')
	uom_id = fields.Many2one("uom.uom",'Unit of Measure')
	standard_price = fields.Float("Cost Price",digits=(12,2))
	list_price = fields.Float("Sale Price",digits=(12,2))
	company_id = fields.Many2one("res.company",'Company',default= lambda self:self.env.company.id)
	product_id = fields.Many2one('product.product','Product')
	crt_date = fields.Datetime(
	'Creation Date',
	readonly = True,
	default = lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'))
	user_id = fields.Many2one(
	'res.users',
	'Created By',
	readonly = True,
	default = lambda self: self.env.user.id)
	update_date = fields.Datetime(
	'Last Update On',
	readonly = True,
	default = lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'))
	update_user_id = fields.Many2one(
	'res.users',
	'Last Update By',
	readonly = True,
	default = lambda self: self.env.user.id)

	def entry_convert(self):
		product_id = self.env['product.product'].create({
			'name':self.name,
			'default_code':self.default_code,
			'type':self.type,
			'categ_id':self.categ_id.id,
			'uom_id':self.uom_id.id,
			'standard_price':self.standard_price,
			'list_price':self.list_price,
		})
		if product_id:
			self.product_id = product_id.id
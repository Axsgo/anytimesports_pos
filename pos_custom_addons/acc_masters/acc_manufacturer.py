### import file ###
from odoo import api,models,fields
import time
from odoo.exceptions import UserError

class AccManufacturer(models.Model):
	_name = "acc.manufacturer"
	_description = "Manufacturer"
	_order = "crt_date desc"

	# @api.model
	# def create(self, vals):
	# 	vals['name'] = self.env['ir.sequence'].next_by_code('acc.followup.mail')
	# 	return super(AccLocation, self).create(vals)

	def write(self, vals):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
		return super(AccManufacturer, self).write(vals)

	def name_get(self):
		res = []
		for field in self:
			if field.country_id:
				res.append((field.id, '%s - %s' %(field.name,field.country_id.code)))
			else:
				res.append((field.id, '%s' %(field.name)))
		return res

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		if args is None:
			args = []
		context = self.env.context
		domain = []
		if name:
			domain = ['|','|',('name', operator, name),('country_id', operator, name),('country_id.code', operator, name)]
		recs = self.search(domain + args, limit=limit)
		return recs.name_get()

	name = fields.Char('Name')
	code = fields.Char('Code')
	street = fields.Char("Street")
	street2 = fields.Char("street2")
	city = fields.Char("City")
	zip = fields.Char("Zip")
	state_id = fields.Many2one('res.country.state','State')
	country_id = fields.Many2one('res.country','Country')
	partner_id = fields.Many2one("res.partner",'Supplier')
	company_id = fields.Many2one('res.company','Company')
	notes = fields.Text("Notes")
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

	@api.constrains('name','code')
	def _check_duplicate_contrains(self):
		if self.name:
			name=self.name.upper()  
			name=name.replace("'", "")
			self.env.cr.execute(""" select upper(name) from acc_manufacturer where upper(name)  = '%s' and id != '%s'""" %(name,self.id))
			data = self.env.cr.dictfetchall()
			if data:
				raise UserError("Warning!!, You are not able to create multiple record in same Name !!")
		if self.code:
			code=self.code.upper()  
			code=code.replace("'", "")
			self.env.cr.execute(""" select upper(code) from acc_manufacturer where upper(code)  = '%s' and id != '%s'""" %(code,self.id))
			data = self.env.cr.dictfetchall()
			if data:
				raise UserError("Warning!!, You are not able to create multiple record in same Code !!")
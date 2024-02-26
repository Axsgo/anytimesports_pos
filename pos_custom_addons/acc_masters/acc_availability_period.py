### import file ###
from odoo import api,models,fields
import time
from odoo.exceptions import UserError

class AccAvailabilityPeriod(models.Model):
	_name = "acc.availability.period"
	_description = "Stock Availability Period"
	_order = "crt_date desc"

	def write(self, vals):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
		return super(AccAvailabilityPeriod, self).write(vals)

	name = fields.Char("Name")
	code = fields.Integer("Days Count")
	notes = fields.Char('Notes')
	company_id = fields.Many2one('res.company','company')
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

	# def unlink(self):
	# 	""" Unlink """
	# 	for rec in self:
	# 		if rec.state != 'draft':
	# 			raise UserError('Warning!, You can not delete this entry !!')
	# 		else:
	# 			return super(AccSourceEnquiry, self).unlink()

	# @api.constrains('name','code')
	# def _check_duplicate_contrains(self):
	# 	if self.name:
	# 		name=self.name.upper()  
	# 		name=name.replace("'", "")
	# 		self.env.cr.execute(""" select upper(name) from acc_availability_period where upper(name)  = '%s' and id != '%s'""" %(name,self.id))
	# 		data = self.env.cr.dictfetchall()
	# 		if data:
	# 			raise UserError("Warning!!, You are not able to create multiple record in same Name !!")
	# 	if self.code:
	# 		code=self.code.upper()  
	# 		code=code.replace("'", "")
	# 		self.env.cr.execute(""" select upper(code) from acc_availability_period where upper(code)  = '%s' and id != '%s'""" %(code,self.id))
	# 		data = self.env.cr.dictfetchall()
	# 		if data:
	# 			raise UserError("Warning!!, You are not able to create multiple record in same Code !!")
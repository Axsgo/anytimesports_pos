### import file ###
from odoo import api,models,fields
import time
from odoo.exceptions import UserError

class AccDeliveryterms(models.Model):
	_name = "acc.delivery.term"
	_description = "Delivery Terms"
	_order = "crt_date desc"

	def write(self, vals):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
		return super(AccDeliveryterms, self).write(vals)

	name = fields.Char("Delivery Terms")
	# code = fields.Char("Code")
	note = fields.Char('Notes')
	is_add_location = fields.Boolean("Add Location in Order / Invoice?")
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

	# @api.constrains('name')
	# def _check_duplicate_contrains(self):
	# 	if self.name:
	# 		name=self.name.upper()  
	# 		name=name.replace("'", "")
	# 		self.env.cr.execute(""" select upper(name) from acc_delivery_term where upper(name)  = '%s' and id != '%s'""" %(name,self.id))
	# 		data = self.env.cr.dictfetchall()
	# 		if data:
	# 			raise UserError("Warning!!, You are not able to create multiple record in same Name !!")
		# if self.code:
		# 	code=self.code.upper()  
		# 	code=code.replace("'", "")
		# 	self.env.cr.execute(""" select upper(code) from acc_delivery_period where upper(code)  = '%s' and id != '%s'""" %(code,self.id))
		# 	data = self.env.cr.dictfetchall()
		# 	if data:
		# 		raise UserError("Warning!!, You are not able to create multiple record in same Code !!")

class PaymentTerms(models.Model):
	_inherit = "account.payment.term"

	def write(self, vals):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
		return super(PaymentTerms, self).write(vals)

	company_id = fields.Many2one('res.company','company',default=lambda self: self.env.company.id)
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

	# @api.constrains('name')
	# def _check_duplicate_contrains(self):
	# 	if self.name:
	# 		name=self.name.upper()  
	# 		name=name.replace("'", "")
	# 		self.env.cr.execute(""" select upper(name) from account_payment_term where upper(name)  = '%s' and id != '%s'""" %(name,self.id))
	# 		data = self.env.cr.dictfetchall()
	# 		if data:
	# 			raise UserError("Warning!!, You are not able to create multiple record in same Name !!")
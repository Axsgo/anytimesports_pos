### import file ###
from odoo import api,models,fields
import time
from odoo.exceptions import UserError

class AccLocation(models.Model):
	_name = "acc.location"
	_description = "Location Master"
	_order = "crt_date desc"

	# @api.model
	# def create(self, vals):
	# 	vals['name'] = self.env['ir.sequence'].next_by_code('acc.followup.mail')
	# 	return super(AccLocation, self).create(vals)

	def write(self, vals):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
		return super(AccLocation, self).write(vals)

	def name_get(self):
		res = []
		for field in self:
			if field.code:
				res.append((field.id, '%s - %s' %(field.code,field.name)))
			else:
				res.append((field.id, '%s' %(field.name)))
		return res

	name = fields.Char("Name")
	code = fields.Char("Code")
	state_id = fields.Many2one('Emirates / States')
	country_id = fields.Many2one("Country")
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
	# ap_rej_date = fields.Datetime('Approved Date', readonly = True)
	# ap_rej_user_id = fields.Many2one(
	# 'res.users', 'Approved By', readonly = True)
	# cancel_date = fields.Datetime('Approved Date', readonly = True)
	# cancel_user_id = fields.Many2one(
	# 'res.users', 'Cancelled By', readonly = True)
	# company_id = fields.Many2one('res.company','Company',default = lambda self: self.env.company.id)
	# state = fields.Selection([('draft','Draft'),('approved','Approved'),('cancel','Cancelled')],'Status',default='draft')

	# def unlink(self):
	# 	""" Unlink """
	# 	for rec in self:
	# 		if rec.state != 'draft':
	# 			raise UserError('Warning!, You can not delete this entry !!')
	# 		else:
	# 			return super(AccLocation, self).unlink()

	@api.constrains('name')
	def _NameValidation(self):
		if self.name:
			### Special Character Checking ##
			name_special_char = ''.join( c for c in self.name if  c in '!@#$%^~*{}?+=' )
			if name_special_char:
				raise UserError('Warning!!, Special Character Not Allowed !!!')
		return True

	@api.onchange('name')
	def upper_name(self):
		if self.name:
			self.name = self.name.upper()

	@api.onchange('code')
	def upper_code(self):
		if self.code:
			self.code = self.code.upper()

	@api.constrains('code')
	def _CodeValidation(self):
		if self.code:
			### Special Character Checking ##
			name_special_char = ''.join( c for c in self.code if  c in '!@#$%^~*{}?+=' )
			if name_special_char:
				raise UserError('Warning!!, Special Character Not Allowed !!!')
		return True

	@api.constrains('name','code')
	def _check_duplicate_contrains(self):
		if self.name:
			name=self.name.upper()  
			name=name.replace("'", "")
			self.env.cr.execute(""" select upper(name) from acc_location where upper(name)  = '%s' and id != '%s'""" %(name,self.id))
			data = self.env.cr.dictfetchall()
			if data:
				raise UserError("Warning!!, You are not able to create multiple record in same Name !!")
		if self.code:
			code=self.code.upper()  
			code=code.replace("'", "")
			self.env.cr.execute(""" select upper(code) from acc_location where upper(code)  = '%s' and id != '%s'""" %(code,self.id))
			data = self.env.cr.dictfetchall()
			if data:
				raise UserError("Warning!!, You are not able to create multiple record in same Code !!")

	# def entry_draft(self):
	# 	self.write({'state': 'draft'})

	# def entry_approve(self):
	# 	if self.state == 'draft':
	# 		self.write({'state': 'approved',
 #                        'ap_rej_user_id': self.env.user.id,
 #                        'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})

	# def entry_cancel(self):
	# 	self.write({'state': 'cancel',
 #                        'cancel_user_id': self.env.user.id,
 #                        'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
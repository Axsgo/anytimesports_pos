### import file ###
from odoo import api,models,fields
import time
from odoo.exceptions import UserError

class AccQuoteValidity(models.Model):
	_name = "acc.quote.validity"
	_description = "Quotation Validity Periods"
	_order = "crt_date desc"

	def write(self, vals):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
		return super(AccQuoteValidity, self).write(vals)

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
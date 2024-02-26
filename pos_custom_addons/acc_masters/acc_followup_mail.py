### import file ###
from odoo import api,models,fields
import time
from odoo.exceptions import UserError

class AccFollowupMail(models.Model):
	_name = "acc.followup.mail"
	_description = "Followup Mails"
	_order = "crt_date desc"

	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('acc.followup.mail')
		return super(AccFollowupMail, self).create(vals)

	def write(self, vals):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
		return super(AccFollowupMail, self).write(vals)

	name = fields.Char("Name")
	entry_date = fields.Date("Date",default=fields.Date.today)
	partner_id = fields.Many2one("res.partner",'Customer')
	phone = fields.Char("Phone")
	alert_date = fields.Date("Alert Date")
	alert_by = fields.Many2one("res.users","Followup By")
	alert_by_mail = fields.Char("Followup User Mail")
	alert_subject = fields.Char("Subject")
	alert_msg = fields.Html("Followup Message")
	mailto_ids = fields.One2many('acc.followup.mail.line','header_id')
	model_id = fields.Many2one("ir.model",'Form Name')
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
	ap_rej_date = fields.Datetime('Approved Date', readonly = True)
	ap_rej_user_id = fields.Many2one(
	'res.users', 'Approved By', readonly = True)
	cancel_date = fields.Datetime('Approved Date', readonly = True)
	cancel_user_id = fields.Many2one(
	'res.users', 'Cancelled By', readonly = True)
	company_id = fields.Many2one('res.company','Company',default = lambda self: self.env.company.id)
	state = fields.Selection([('draft','Draft'),('approved','Approved'),('cancel','Cancelled')],'Status',default='draft')

	def unlink(self):
		""" Unlink """
		for rec in self:
			if rec.state != 'draft':
				raise UserError('Warning!, You can not delete this entry !!')
			else:
				return super(AccFollowupMail, self).unlink()

	@api.onchange('partner_id')
	def update_phone(self):
		if self.partner_id:
			self.mailto_ids = False
			self.phone = ''
			if self.partner_id.phone:
				self.phone = self.partner_id.phone
			else:
				self.phone = self.partner_id.mobile
			if self.partner_id.email:
				self.env['acc.followup.mail.line'].create({
					'email':self.partner_id.email,
					'is_to':True,
					'header_id':self.id,
				})

	@api.onchange('alert_by')
	def onchange_alert_by(self):
		if self.alert_by:
			self.alert_by_mail = ''
			self.alert_by_mail = self.alert_by.email

	def entry_draft(self):
		self.write({'state': 'draft'})

	def entry_approve(self):
		if self.state == 'draft':
			if self.mailto_ids or self.parent_id:
				self.write({'state': 'approved',
	                        'ap_rej_user_id': self.env.user.id,
	                        'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise UserError('Warning!!, Email is mandatory to send Followup Mail.')

	def entry_cancel(self):
		self.write({'state': 'cancel',
                        'cancel_user_id': self.env.user.id,
                        'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})

	def entry_send_mail(self):
		self._entry_send_followup_mail('all',self.id)

	def _entry_send_followup_mail(self,state=None,rec_id=None):
		from datetime import datetime
		if state == 'all' and rec_id:
			partner_name = ''
			followup_id = self.env['acc.followup.mail'].browse(rec_id)
			email_to = []
			email_cc = []
			if followup_id.mailto_ids:
				for line in followup_id.mailto_ids:
					if line.is_to == True:
						email_to.append(line.email)
					if line.is_cc == True:
						email_cc.append(line.email)
			if email_to:
				context = {
					'partner_name':followup_id.partner_id.name,
					'email':", ".join(email_to),
					'email_cc':", ".join(email_cc),
				}
				template = self.env['ir.model.data'].get_object('acc_masters', 'email_template_acc_followup_mail')
				self.env['mail.template'].browse(template.id).with_context(context).send_mail(followup_id.id,force_send=True)
			else:
				raise UserError('Warning!!, Email is mandatory to send Followup Mail.')
		else:
			followup_ids = self.env['acc.followup.mail'].search([('state','=','approved'),('alert_date','>=',datetime.now().date()),('alert_date','<=',datetime.now().date())])
			if followup_ids:
				for rec in followup_ids:
					partner_name = ''
					email_to = []
					email_cc = []
					if rec.mailto_ids:
						for line in rec.mailto_ids:
							if line.is_to == True:
								email_to.append(line.email)
							if line.is_cc == True:
								email_cc.append(line.email)
					if email_to:
						context = {
							'partner_name':rec.partner_id.name,
							'email':", ".join(email_to),
							'email_cc':", ".join(email_cc),
						}
						template = self.env['ir.model.data'].get_object('acc_masters', 'email_template_acc_followup_mail')
						self.env['mail.template'].browse(template.id).with_context(context).send_mail(rec.id,force_send=True)
					else:
						raise UserError('Warning!!, Email is mandatory to send Followup Mail.')

class AccFollowupMailLine(models.Model):
	_name = "acc.followup.mail.line"
	_description = "Followup Mails To"

	header_id = fields.Many2one("acc.followup.mail",'Header')
	email = fields.Char("Email")
	is_to = fields.Boolean("To")
	is_cc = fields.Boolean("CC")
### import file ###
from odoo import api,models,fields
from odoo.exceptions import UserError
import time

class AccCountries(models.Model):
	_inherit = "res.country"

	code = fields.Char(
        string='Country Code', size=10,
        help='The ISO country code in two chars. \nYou can use this field for quick search.')

class AccCities(models.Model):
	_inherit = "res.city"

	code = fields.Char("Code")

class AccState(models.Model):
	_inherit = "res.country.state"

	# is_emirates = fields.Boolean("Is ")
	c_code = fields.Integer('Customer Code')
	# s_code = fields.Integer("Supplier Code")

class AccPartner(models.Model):
	_inherit = "res.partner"

	def name_get(self):
		res = []
		for field in self:
			if field.partner_no and field.partner_acc_no:
				res.append((field.id, '[%s] %s - %s' %(field.partner_acc_no,field.partner_no,field.name)))
			elif field.partner_no:
				res.append((field.id, '%s - %s' %(field.partner_no,field.name)))
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
			domain = ['|','|','|',('name', operator, name),('partner_no', operator, name),('partner_acc_no', operator, name),('parent_id',operator,name)]
		recs = self.search(domain + args, limit=limit)
		return recs.name_get()

	# @api.model
	# def _get_customer_type(self):
	# 	params = self.env['ir.config_parameter'].sudo()
	# 	enable_temp_partner = params.get_param('enable_temp_partner')
	# 	if enable_temp_partner:
	# 		return [('trader','Reseller / Trader'),('enduser','Enduser (Direct Sale)'),('temporary','Walk-in Customer')]
	# 	else:
	# 		return [('trader','Reseller / Trader'),('enduser','Enduser (Direct Sale)')]

	partner_type = fields.Selection([('local','Local (U.A.E)'),('gcc','Local Exports (within GCC)'),('export','Local Exports (outside GCC)'),('overseas','Direct Exports')],string="Sales Type")
	partner_no = fields.Char('No.',compute='_get_partner_no',store=True)
	customer_type = fields.Selection([('trader','Reseller / Trader'),('enduser','Enduser (Direct Sale)')],string='Customer Type')
	product_categ_id = fields.Many2one("product.category",'Commodity Code')
	fax = fields.Char("Fax")
	vat_document = fields.Binary("VAT Document")
	partner_acc_no = fields.Char("Old Acc No")
	vat_document_filename = fields.Char("VAT Document Filename")
	customer_payment_term_id = fields.Many2one('account.payment.term','Customer Payment Term',related='property_payment_term_id',store=True)
	supplier_payment_term_id = fields.Many2one('account.payment.term','Supplier Payment Term',related='property_supplier_payment_term_id',store=True)
	property_payment_due_days = fields.Integer("Payment Due Days")
	# settlement_due_days = fields.Float("Settlement Due Days",digits=(12,1))
	property_supplier_payment_due_days = fields.Integer("Payment Due Days")
	# supplier_settlement_due_days = fields.Float("Settlement Due Days",digits=(12,1))
	# email1 = fields.Char("Email 2")
	# email2 = fields.Char("Email 3")
	attachment_ids = fields.Many2many('ir.attachment','res_partner_attachment_rel','partner_id','attachment_id','Attachments')
	is_temp_partner = fields.Boolean("Walk-in Customer",default=False)
	direct_sale_margin = fields.Float("Direct Export Sales Margin",digits=(12,2),default=30)
	company_id = fields.Many2one('res.company', 'Company', index=True, default=lambda self:self.env.company.id)
	duns_no = fields.Char("DUNS No.")
	tax_code = fields.Char("Tax Code")
	crt_date = fields.Datetime(
	'Creation Date',
	readonly = True,
	default = lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'))
	# trader_name = fields.Char("Trader Name")

	# @api.depends('customer_type')
	# def _get_temp_partner(self):
	# 	for rec in self:
	# 		if rec.customer_type == 'temporary':
	# 			rec.is_temp_partner = True
	# 		else:
	# 			rec.is_temp_partner = False

	def entry_move_permanent(self):
		for rec in self:
			if not rec.customer_type:
				raise UserError("Warning!!, Select Customer Type before Move to Permanent.")
			if not rec.partner_type:
				raise UserError("Warning!!, Select Sales Type before Move to Permanent.")
			if not rec.country_id:
				raise UserError("Warning!!, Select Country before Move to Permanent.")
			elif rec.country_id and rec.country_id.name == 'United Arab Emirates' and not rec.state_id:
				raise UserError("Warning!!, Select Emirates / States before Move to Permanent.")
			rec.is_temp_partner = False
			rec.partner_no = ''
			self._get_partner_no()

	@api.onchange('currency_dummy_id')
	def update_pricelist(self):
		if self.currency_dummy_id:
			self.property_product_pricelist = self.env['product.pricelist'].search([('currency_id','=',self.currency_dummy_id.id)],limit=1).id or False

	@api.onchange("state_id",'country_id','partner_type')
	def upadte_fiscal_position(self):
		# if self.country_id.name == 'United Arab Emirates' and self.state_id:
		# 	self.property_account_position_id = self.env['account.fiscal.position'].search([('name','=',self.state_id.name),('company_id','=',self.company_id.id)],limit=1).id or False
		if self.partner_type == 'local':
			self.property_account_position_id = self.env['account.fiscal.position'].search([('name','=',self.env.company.state_id.name),('company_id','=',self.company_id.id)],limit=1).id or False
		else:
			self.property_account_position_id = self.env['account.fiscal.position'].search([('name','=','VAT 0%'),('company_id','=',self.company_id.id)],limit=1).id or False

	# @api.constrains('state_id','country_id')
	# def state_warning(self):
	# 	if self.is_temp_partner == False and self.country_id and self.country_id.name == "United Arab Emirates":
	# 		if not self.state_id:
	# 			raise UserError("Warning!!, Kindly select Emirates / States.")

	def _get_company_currency(self):
		for partner in self:
			if partner.currency_dummy_id:
				partner.currency_id = partner.currency_dummy_id.id
			elif partner.company_id:
				partner.currency_id = partner.sudo().company_id.currency_id
			else:
				partner.currency_id = self.env.company.currency_id

	@api.constrains('name','customer_type')
	def partner_duplicate_constrain(self):
		for rec in self:
			if rec.name and rec.company_id:
				name=rec.name.upper()  
				name=name.replace("'", "")
				self.env.cr.execute(""" select upper(name) from res_partner where upper(name)  = '%s' and id != '%s' and company_id = '%s' and is_temp_partner = 'f'""" %(name,rec.id,rec.company_id.id))
				data = self.env.cr.dictfetchall()
				if data:
					raise UserError("Warning!!, You are not able to create multiple record in same Name !! - %s"%(data[0]['upper']))

	@api.depends('partner_type','customer_type','state_id','state_id.code','customer_rank','supplier_rank','is_temp_partner','name','company_id')
	def _get_partner_no(self):
		for rec in self:
		# partner_ids = self.env['res.partner'].search([])
		# for rec in partner_ids:
			if not rec.partner_no and rec.id:
				if rec.customer_rank == 0 and rec.supplier_rank == 0:
					rec.partner_no = self.env['ir.sequence'].next_by_code('res.partner')
				elif rec.customer_rank == 0 and rec.supplier_rank > 0:
					rec.partner_no = self.env['ir.sequence'].next_by_code('res.supplier')
				elif rec.supplier_rank == 0 and rec.customer_rank > 0:
					rec.partner_no = self.env['ir.sequence'].next_by_code('res.customer')
				else:
					rec.partner_no = ''
			else:
				rec.partner_no = ''
			rec._compute_display_name()


	@api.onchange('partner_type')
	def update_country(self):
		if self.partner_type:
			if self.partner_type == 'local':
				self.country_id = self.env['res.country'].search([('code','=','AE')]).id
				self.state_id = self.env['res.country.state'].search([('name','=','Dubai')]).id
			else:
				self.country_id = False
				self.state_id = False
### import file ###
from odoo import api,models,fields
import time
from odoo.exceptions import UserError

class AccProductTemplate(models.Model):
	_inherit = "product.template"
	_name = "product.template"
	_description = "Product Template"
	_order = "id desc"

	@api.model
	def _get_default_auto_lot(self):
		params = self.env['ir.config_parameter'].sudo()
		enable_auto_lot = params.get_param('enable_auto_lot',default=False)
		if enable_auto_lot == 'True':
			return True
		else:
			return False

	parent_categ_id = fields.Many2one("product.category",'Commodity Code',related='categ_id.parent_id',store=True)
	manufacturer_id = fields.Many2one('acc.manufacturer','Manufacturer',copy=False)
	country_id = fields.Many2one('res.country','Origin',default=lambda self:self.manufacturer_id.country_id.id)
	hs_code = fields.Char("HS Code",copy=False)
	supplier_part_no = fields.Char("Supplier Product Code",copy=False)
	old_product_code = fields.Char("Old Product Code",copy=False)
	enable_auto_lot = fields.Boolean("Enable Automatic Serial No", default=lambda self: self._get_default_auto_lot())
	pricelist_alert = fields.Boolean("PriceList Alert",compute='_get_pricelist_alert')
	pricelist_alert_msg = fields.Char("PriceList Alert Msg",compute='_get_pricelist_alert')
	sub_categ_id = fields.Many2one('acc.product.sub.category','Sub-Category',copy=False)
	stock_moving_type = fields.Selection([('fast','Fast Moving Product'),('slow','Slow Moving Product'),('non','Non Moving Product')],'Stock Sales Type')
	is_supplier_code_updated = fields.Boolean("Supplier Code Updated",default=False,copy=False)

	@api.depends('default_code','name','supplier_part_no')
	def _get_pricelist_alert(self):
		from datetime import datetime
		for rec in self:
			rec.pricelist_alert = False
			rec.pricelist_alert_msg = ''
			pricelists = self.env['product.supplierinfo'].search([('product_tmpl_id','=',rec.id)])
			if pricelists:
				for pricelist in pricelists:
					if pricelist.date_start and pricelist.date_start > datetime.now().date():
						rec.pricelist_alert = True
						rec.pricelist_alert_msg = "Pricelist available only for future date - %s"%(pricelist.date_start.strftime("%d/%b/%Y"))
					elif pricelist.date_end and pricelist.date_end < datetime.now().date():
						rec.pricelist_alert = True
						rec.pricelist_alert_msg = "Pricelist Expired !"
					else:
						rec.pricelist_alert = False
						rec.pricelist_alert_msg = 'Pricelist available.'
			else:
				pricelists = self.env['product.supplierinfo'].search([('product_code','=',rec.supplier_part_no),('product_tmpl_id','=',False)])
				if pricelists:
					for pricelist in pricelists:
						rec.pricelist_alert = True
						rec.pricelist_alert_msg = "Pricelist available for this Supplier Product Code, Kindly link the Product with the surresponding Pricelist"
				else:
					rec.pricelist_alert = True
					rec.pricelist_alert_msg = "Pricelist not available for this Product!"

	@api.onchange('tracking')
	def update_auto_lot(self):
		if self.tracking in ('serial','lot'):
			params = self.env['ir.config_parameter'].sudo()
			enable_auto_lot = params.get_param('enable_auto_lot',default=False)
			if enable_auto_lot == 'True':
				self.enable_auto_lot = True
			else:
				self.enable_auto_lot = False
		else:
			self.enable_auto_lot = False

	@api.onchange('manufacturer_id')
	def update_country(self):
		if self.manufacturer_id:
			self.country_id = self.manufacturer_id.country_id.id

	@api.constrains('default_code')
	def duplicate_default_code_contrains(self):
		for rec in self:
			# if rec.name:
			# 	name=rec.name.upper()  
			# 	name=name.replace("'", "")
			# 	self.env.cr.execute(""" select upper(name) from product_template where upper(name)  = '%s' and id != '%s'""" %(name,rec.id))
			# 	data = self.env.cr.dictfetchall()
			# 	if data:
			# 		raise UserError(("Warning!!, Product Name - %s must be unique !")%(rec.name))
			if rec.default_code:
				code=rec.default_code.upper()  
				code=code.replace("'", "")
				self.env.cr.execute(""" select upper(default_code) from product_template where upper(default_code)  = '%s' and id != '%s'""" %(code,rec.id))
				data = self.env.cr.dictfetchall()
				if data:
					raise UserError(("Warning!!, Product Code - %s should not be unique !")%(rec.default_code))

	def update_origin(self):
		for rec in self:
			if rec.manufacturer_id:
				rec.country_id = rec.manufacturer_id.country_id.id

	def _old_product_code_update(self):
		for rec in self:
			if rec.default_code:
				rec.old_product_code = rec.default_code

class AccProduct(models.Model):
	_inherit = "product.product"
	_name = "product.product"
	_description = "Product"
	_order = "id desc"

	parent_categ_id = fields.Many2one("product.category",'Commodity Code',related='product_tmpl_id.parent_categ_id',store=True)
	manufacturer_id = fields.Many2one('acc.manufacturer','Manufacturer',related='product_tmpl_id.manufacturer_id',store=True)
	country_id = fields.Many2one('res.country','Origin',related='product_tmpl_id.country_id',store=True)
	hs_code = fields.Char("HS Code",related='product_tmpl_id.hs_code',store=True)
	supplier_part_no = fields.Char("Supplier Part No",related='product_tmpl_id.supplier_part_no',store=True)
	old_product_code = fields.Char("Old Product Code",related='product_tmpl_id.old_product_code',store=True)
	enable_auto_lot = fields.Boolean("Enable Automatic Serial No",related='product_tmpl_id.enable_auto_lot',store=True)
	sub_categ_id = fields.Many2one('acc.product.sub.category','Sub-Category',related='product_tmpl_id.sub_categ_id',store=True)
	stock_moving_type = fields.Selection([('fast','Fast Moving Product'),('slow','Slow Moving Product'),('non','Non Moving Product')],'Stock Sales Type',related='product_tmpl_id.stock_moving_type',store=True)
	is_supplier_code_updated = fields.Boolean("Supplier Code Updated",related='product_tmpl_id.is_supplier_code_updated',store=True)

	@api.constrains('default_code')
	def duplicate_default_code_contrains(self):
		if self.default_code:
			name=self.default_code.upper()  
			name=name.replace("'", "")
			self.env.cr.execute(""" select upper(default_code) from product_product where upper(default_code)  = '%s' and id != '%s'""" %(name,self.id))
			data = self.env.cr.dictfetchall()
			if data:
				raise UserError(("Warning!!, Product Code - %s should not be unique !")%(self.default_code))

class AccProductCategory(models.Model):
	_inherit = "product.category"
	_order = "id desc"

	nrml_sale_margin = fields.Float("Normal Sales Margin %",digits=(12,2),default=30)
	show_nrml_sale_margin = fields.Boolean("Show Normal Sales Margin")
	trade_margin = fields.Float("Trading Margin %",digits=(12,2),default=30)
	enduser_margin = fields.Float("Enduser Margin %",digits=(12,2),default=30)
	seq_no = fields.Integer('Sequence Order')
	# direct_sale_margin = fields.Float("Direct Export Sales Margin %",digits=(12,2),default=30)
	# show_direct_sale_margin = fields.Boolean("Show Direct Sales Margin")
	min_margin = fields.Float("Minimum Margin %",digits=(12,2),default=25)
	# show_min_margin = fields.Boolean("Show Minimum Margin")
	code = fields.Char("Code",size=2)
	seq_id = fields.Many2one('ir.sequence','Sequence')
	employee_ids = fields.Many2many('hr.employee',string='Employee')

	def name_get(self):
		res = []
		for field in self:
			if field.parent_id:
				res.append((field.id, '%s / %s' %(field.name,field.parent_id.name)))
			else:
				res.append((field.id, '%s' %(field.name)))
		return res

	@api.onchange("code")
	def upper_code(self):
		if self.code:
			self.code = self.code.upper()

	def entry_create_seq(self):
		for rec in self:
			if rec.code:
				if rec.code.isalpha():
					pass
				else:
					raise UserError("Warning!!, Enter only characters.")
				value = rec.code.upper()
				name = "Dubai Shipment - %s"%(value)
				code = "purchase.order.%s"%(value)
				seq_id = self.env['ir.sequence'].create({
					'name':name,
					'code':code,
					'prefix':'%s'%(value),
					'suffix':'/%(range_y)s',
					'padding':4,
					'implementation':'no_gap',
					'use_date_range':True,
				})
				if seq_id:
					self.seq_id = seq_id.id
				else:
					raise UserError("Warning!!, Cannot able to create sequence, kindly create it manually.")

	@api.onchange('nrml_sale_margin')
	def show_nrml_sale_margin_update(self):
		if self.nrml_sale_margin > 0:
			self.show_nrml_sale_margin = True
		else:
			self.show_nrml_sale_margin = False

	# @api.onchange('direct_sale_margin')
	# def show_direct_sale_margin_update(self):
	# 	if self.direct_sale_margin > 0:
	# 		self.show_direct_sale_margin = True
	# 	else:
	# 		self.show_direct_sale_margin = False

	# @api.onchange('min_margin')
	# def show_min_margin_update(self):
	# 	if self.min_margin > 0:
	# 		self.show_min_margin = True
	# 	else:
	# 		self.show_min_margin = False

	def update_nrml_sale_margin(self):
		product_tmpl_id = self.env['product.template'].search([('categ_id','=',self.id)])
		if product_tmpl_id:
			for line in product_tmpl_id:
				line.sale_percent = self.nrml_sale_margin

	# def update_direct_sale_margin(self):
	# 	print('*******')

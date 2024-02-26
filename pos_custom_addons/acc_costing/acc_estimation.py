from odoo import fields,api,models
from odoo.exceptions import UserError

class AccEstimation(models.TransientModel):
	_name = "acc.estimation"
	_description = "Costing Estimation"

	@api.depends('bill_ids.price_total')
	def _get_vendor_bill_amount(self):
		for order in self:
			amount_untaxed = amount_tax = 0.0
			for line in order.bill_ids:
				line._compute_amount()
				amount_untaxed += line.price_subtotal
				amount_tax += line.price_tax
			order.update({
				'vendor_amount_untaxed': amount_untaxed,
				'vendor_amount_tax': amount_tax,
				'vendor_amount_total': amount_untaxed + amount_tax,
			})

	@api.depends('clearance_bill_ids.price_total')
	def _get_clearance_bill_amount(self):
		for order in self:
			amount_untaxed = amount_tax = 0.0
			for line in order.clearance_bill_ids:
				line._compute_amount()
				amount_untaxed += line.price_subtotal
				amount_tax += line.price_tax
			order.update({
				'landed_amount_untaxed': amount_untaxed,
				'landed_amount_tax': amount_tax,
				'landed_amount_total': amount_untaxed + amount_tax,
			})

	partner_id = fields.Many2one('res.partner','Purchase Vendor')
	landed_partner_id = fields.Many2one("res.partner",'Clearance Vendor')
	type = fields.Selection([('manual','Manual'),('from_po','From PO')],'Type',default='from_po')
	po_ids = fields.Many2many('purchase.order','acc_estimation_po_rel','po_id','estimation_id',"PO's")
	entry_date = fields.Date("Date",default=fields.Date.today)
	bill_ids = fields.One2many('acc.estimation.vendor.bill','header_id')
	clearance_bill_ids = fields.One2many('acc.estimation.clearance.bill','header_id')
	product_estimation_ids = fields.One2many('acc.estimation.product.line','header_id')
	landed_cost_factor = fields.Float('Factor Value',digits=(12,6),compute="get_factor_value")
	company_id = fields.Many2one("res.company",'Company',default=lambda self:self.env.company.id)
	vendor_amount_untaxed = fields.Float("Untaxed Amount",digits=(12,2),compute='_get_vendor_bill_amount')
	vendor_amount_tax = fields.Float("Taxes",digits=(12,2),compute='_get_vendor_bill_amount')
	vendor_amount_total = fields.Float("Total",digits=(12,2),compute='_get_vendor_bill_amount')
	landed_amount_untaxed = fields.Float("Untaxed Amount",digits=(12,2),compute='_get_clearance_bill_amount',currency_field='company_currency_id')
	landed_amount_tax = fields.Float("Taxes",digits=(12,2),compute='_get_clearance_bill_amount',currency_field='company_currency_id')
	landed_amount_total = fields.Float("Total",digits=(12,2),compute='_get_clearance_bill_amount',currency_field='company_currency_id')
	currency_id = fields.Many2one('res.currency','Purchase Currency')
	company_currency_id = fields.Many2one('res.currency','Currency',default=lambda self:self.env.company.currency_id.id)
	currency_rate = fields.Float('Currency Rate',digits='Product Price',compute='_get_currency_rate')

	@api.depends('currency_id','company_id','entry_date','company_currency_id')
	def _get_currency_rate(self):
		from datetime import date
		for rec in self:
			if rec.currency_id:
				rec.currency_rate = self.env['res.currency']._get_conversion_rate(rec.company_currency_id, rec.currency_id, rec.company_id, rec.entry_date or datetime.now())
			else:
				rec.currency_rate = 0

	@api.onchange('type')
	def refresh_date(self):
		self.partner_id = False
		self.bill_ids = False
		self.clearance_bill_ids = False
		self.po_ids = False
		self.landed_partner_id = False

	@api.onchange('partner_id')
	def onchange_partner(self):
		self.po_ids = False
		self.bill_ids = False

	@api.onchange('landed_partner_id')
	def onchange_landed_partner(self):
		self.clearance_bill_ids = False

	def update_po_details(self):
		self.bill_ids = False
		if self.po_ids:
			for rec in self.po_ids:
				if rec.state == 'purchase':
					for line in rec.order_line:
						self.env['acc.estimation.vendor.bill'].create({
							'header_id':self.id,
							'product_id':line.product_id.id,
							'name':line.name,
							'product_qty':line.product_qty,
							'product_uom':line.product_uom.id,
							'price_unit':line.price_unit,
							'taxes_id':[(6,0,line.taxes_id.ids)],
							'currency_id':line.currency_id.id,
						})

	@api.depends('vendor_amount_total','landed_amount_total')
	def get_factor_value(self):
		for rec in self:
			if rec.vendor_amount_total > 0 and rec.landed_amount_total > 0:
				vendor_amount_total = self.currency_id._convert(
					self.vendor_amount_total,
					self.company_currency_id,
					self.company_id,
					self.entry_date or fields.Date.today(),
				)
				rec.landed_cost_factor = (vendor_amount_total + rec.landed_amount_total) / vendor_amount_total
			else:
				rec.landed_cost_factor = 0

	def compute_estimation(self):
		self.product_estimation_ids = False
		if self.bill_ids and self.clearance_bill_ids and self.landed_cost_factor > 0:
			landed_cost_factor = self.currency_id._convert(
					self.landed_cost_factor,
					self.company_currency_id,
					self.company_id,
					self.entry_date or fields.Date.today(),
				)
			for line in self.bill_ids:
				self.env['acc.estimation.product.line'].create({
					'header_id':self.id,
					'product_id':line.product_id.id,
					'std_price':line.product_id.standard_price,
					'estimated_price':line.price_unit * landed_cost_factor,
					'list_price':line.product_id.list_price,
					'estimated_list_price': (line.price_unit * landed_cost_factor) / ((100 - line.product_id.sale_percent)/100)
				})

class AccEstimationVendorBill(models.TransientModel):
	_name = "acc.estimation.vendor.bill"
	_description = "Vendor Bills Costing Estimation"

	header_id = fields.Many2one("acc.estimation")
	partner_id = fields.Many2one('res.partner','Vendor',related='header_id.partner_id')
	product_id = fields.Many2one("product.product",'Product')
	name = fields.Text("Description")
	product_qty = fields.Float("Quantity",digits=(12,2),default=1)
	product_uom = fields.Many2one('uom.uom',"UoM",related='product_id.uom_id')
	price_unit = fields.Float('Unit Price',digits="Product Price")
	taxes_id = fields.Many2many("account.tax",'acc_estamtion_vendor_tax_rel','tax_id','estimation_id',"Taxes")
	price_tax = fields.Float("Tax Total",digits=(12,2),compute='_compute_amount',store=True)
	price_total = fields.Float("Total",digits=(12,2),compute='_compute_amount',store=True)
	price_subtotal = fields.Float("Subtotal",digits=(12,2),compute='_compute_amount',store=True)
	currency_id = fields.Many2one('res.currency','Currency',related='header_id.currency_id',store=True)

	@api.onchange('product_qty', 'product_uom','product_id')
	def _onchange_quantity(self):
		self.name = self.product_id.name
		if not self.product_id:
			return
		params = {'order_id': self.header_id}
		seller = self.product_id._select_seller(
			partner_id=self.header_id.partner_id,
			quantity=self.product_qty,
			date=self.header_id.entry_date,
			uom_id=self.product_uom,
			params=params)

		# if seller or not self.date_planned:
		# 	self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

		# If not seller, use the standard price. It needs a proper currency conversion.
		if not seller:
			po_line_uom = self.product_uom or self.product_id.uom_po_id
			price_unit = self.env['account.tax']._fix_tax_included_price_company(
				self.product_id.uom_id._compute_price(self.product_id.standard_price, po_line_uom),
				self.product_id.supplier_taxes_id,
				self.taxes_id,
				self.header_id.company_id,
			)
			if price_unit and self.currency_id and self.header_id.company_id.currency_id != self.currency_id:
				price_unit = self.header_id.company_id.currency_id._convert(
					price_unit,
					self.currency_id,
					self.header_id.company_id,
					self.header_id.entry_date or fields.Date.today(),
				)

			self.price_unit = price_unit
			return

		price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, self.product_id.supplier_taxes_id, self.taxes_id, self.header_id.company_id) if seller else 0.0
		if price_unit and seller and self.currency_id and seller.currency_id != self.currency_id:
			price_unit = seller.currency_id._convert(
				price_unit, self.currency_id, self.header_id.company_id, self.header_id.entry_date or fields.Date.today())

		if seller and self.product_uom and seller.product_uom != self.product_uom:
			price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

		self.price_unit = price_unit

	@api.depends('product_qty', 'price_unit', 'taxes_id')
	def _compute_amount(self):
		for line in self:
			vals = line._prepare_compute_all_values()
			taxes = line.taxes_id.compute_all(
				vals['price_unit'],
				vals['currency_id'],
				vals['product_qty'],
				vals['product'],
				vals['partner'])
			line.update({
				'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})

	def _prepare_compute_all_values(self):
		self.ensure_one()
		return {
			'price_unit': self.price_unit,
			'currency_id': self.currency_id,
			'product_qty': self.product_qty,
			'product': self.product_id,
			'partner': self.header_id.partner_id,
		}

class AccEstimationLandedBill(models.TransientModel):
	_name = "acc.estimation.clearance.bill"
	_description = "Clearance Bills Costing Estimation"

	header_id = fields.Many2one("acc.estimation")
	partner_id = fields.Many2one('res.partner','Vendor',related='header_id.landed_partner_id')
	product_id = fields.Many2one("product.product",'Product')
	name = fields.Text("Description")
	product_qty = fields.Float("Quantity",digits=(12,2),default=1)
	product_uom = fields.Many2one('uom.uom',"UoM",related='product_id.uom_id')
	price_unit = fields.Float('Unit Price',digits="Product Price")
	taxes_id = fields.Many2many("account.tax",'acc_estamtion_clearance_tax_rel','tax_id','estimation_id',"Taxes")
	price_tax = fields.Float("Tax Total",digits=(12,2),compute='_compute_amount',store=True)
	price_total = fields.Float("Total",digits=(12,2),compute='_compute_amount',store=True)
	price_subtotal = fields.Float("Subtotal",digits=(12,2),compute='_compute_amount',store=True)
	currency_id = fields.Many2one('res.currency','Currency',default=lambda self:self.env.company.currency_id.id)

	@api.onchange('product_qty', 'product_uom','product_id')
	def _onchange_quantity(self):
		self.name = self.product_id.name
		if not self.product_id:
			return
		params = {'order_id': self.header_id}
		seller = self.product_id._select_seller(
			partner_id=self.header_id.partner_id,
			quantity=self.product_qty,
			date=self.header_id.entry_date,
			uom_id=self.product_uom,
			params=params)

		# if seller or not self.date_planned:
		# 	self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

		# If not seller, use the standard price. It needs a proper currency conversion.
		if not seller:
			po_line_uom = self.product_uom or self.product_id.uom_po_id
			price_unit = self.env['account.tax']._fix_tax_included_price_company(
				self.product_id.uom_id._compute_price(self.product_id.standard_price, po_line_uom),
				self.product_id.supplier_taxes_id,
				self.taxes_id,
				self.header_id.company_id,
			)
			if price_unit and self.currency_id and self.header_id.company_id.currency_id != self.currency_id:
				price_unit = self.header_id.company_id.currency_id._convert(
					price_unit,
					self.currency_id,
					self.header_id.company_id,
					self.header_id.entry_date or fields.Date.today(),
				)

			self.price_unit = price_unit
			return

		price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, self.product_id.supplier_taxes_id, self.taxes_id, self.header_id.company_id) if seller else 0.0
		if price_unit and seller and self.currency_id and seller.currency_id != self.currency_id:
			price_unit = seller.currency_id._convert(
				price_unit, self.currency_id, self.header_id.company_id, self.header_id.entry_date or fields.Date.today())

		if seller and self.product_uom and seller.product_uom != self.product_uom:
			price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

		self.price_unit = price_unit

	@api.depends('product_qty', 'price_unit', 'taxes_id')
	def _compute_amount(self):
		for line in self:
			vals = line._prepare_compute_all_values()
			taxes = line.taxes_id.compute_all(
				vals['price_unit'],
				vals['currency_id'],
				vals['product_qty'],
				vals['product'],
				vals['partner'])
			line.update({
				'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})

	def _prepare_compute_all_values(self):
		self.ensure_one()
		return {
			'price_unit': self.price_unit,
			'currency_id': self.currency_id,
			'product_qty': self.product_qty,
			'product': self.product_id,
			'partner': self.header_id.partner_id,
		}

class AccEstimationProductLine(models.TransientModel):
	_name = "acc.estimation.product.line"
	_description = "Estimation Product Line"

	header_id = fields.Many2one('acc.estimation','Estimation')
	product_id = fields.Many2one('product.product','Product')
	std_price = fields.Float("Cost Price",digits='Product Price')
	estimated_price = fields.Float('Estimated Cost Price',digits='Product Price')
	list_price = fields.Float("Sales Price",digits='Product Price')
	estimated_list_price = fields.Float('Estimated Sales Price',digits='Product Price')
	currency_id = fields.Many2one('res.currency','Currency',default=lambda self:self.env.company.currency_id.id)
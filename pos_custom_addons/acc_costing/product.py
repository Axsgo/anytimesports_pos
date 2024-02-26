### import file ###
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models,tools, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


class StockQuant(models.Model):
	_inherit = "stock.quant"
	_name = "stock.quant"

	# value = fields.Monetary('Value', compute='_compute_value', groups='stock.group_stock_manager')
	product_tmpl_id = fields.Many2one('product.template','Product Template',related='product_id.product_tmpl_id',store=True)

class ProductTemplate(models.Model):
	_inherit = "product.template"
	_name = "product.template"
	_description = "Product Template"


	# stock_price = fields.Float("Stock Cost Price",digits=(12,2),compute='_get_stock_price',store=True,compute_sudo=False)
	# list_price = fields.Float("Sale Price",digits=(12,2),compute="update_list_price",store=True,compute_sudo=False)
	# sale_percent = fields.Float('Magin %',digits=(12,2),default=30,compute='_compute_magin',inverse='_compute_inverse_magin',store=True)
	sale_percent = fields.Float('Magin %',digits=(12,2),default=30,store=True)
	list_price = fields.Float('Sales Price', digits="Product Price")
	min_margin = fields.Float("Min Margin %",digits=(12,2),default=25)

	@api.onchange('type','landed_cost_ok')
	def update_slipting_method(self):
		if self.type == 'service' and self.landed_cost_ok == True:
			self.split_method_landed_cost = 'by_current_cost_price'

	# @api.depends(
	# 'product_variant_ids','product_variant_ids.stock_quant_ids',
	# 'product_variant_ids.stock_move_ids.product_qty','product_variant_ids.stock_move_ids',
	# 'product_variant_ids.stock_move_ids.state','qty_available','purchased_product_qty',
	# 'product_variant_ids.stock_quant_ids.quantity','product_variant_ids.stock_quant_ids.value'
	# )
	# @api.depends_context('company', 'location', 'warehouse')
	# def _get_stock_price(self):
	# 	for rec in self:
	# 		location_id = self.env['stock.location'].search([('usage','=','internal')])
	# 		if rec.id:
	# 			stock_value = 0
	# 			stock_qty = 0
	# 			for prod in rec.product_variant_ids:
	# 				for line in prod.stock_quant_ids:
	# 					if line.location_id in location_id:
	# 						stock_value += line.value
	# 						stock_qty += line.quantity
	# 			if stock_value > 0 and stock_qty > 0:
	# 				rec.stock_price = stock_value / stock_qty
	# 			else:
	# 				rec.stock_price = 0
	# 			# if len(location_id) == 1:
	# 			# 	self.env.cr.execute(""" select sum(quantity) as qty, sum(value) as value from stock_quant where product_tmpl_id  = '%s' and location_id = '%s'""" %(rec.id,location_id.id))	
	# 			# else:
	# 			# 	self.env.cr.execute(""" select sum(quantity) as qty, sum(value) as value from stock_quant where product_tmpl_id  = '%s' and location_id in %s""" %(rec.id,tuple(location_id.ids)))
	# 			# data = self.env.cr.dictfetchall()
	# 			# print(data,'lllllll')
	# 			# if data and data[0]['value'] and data[0]['qty']:
	# 			# 	rec.stock_price = data[0]['value']/data[0]['qty']
	# 			# else:
	# 			# 	rec.stock_price = 0
	# 		else:
	# 			rec.stock_price = 0

	# @api.depends(
	# 'product_variant_ids',
	# 'product_variant_ids.stock_move_ids.product_qty',
	# 'product_variant_ids.stock_move_ids.state',
	# )
	# @api.depends_context('company', 'location', 'warehouse')
	# def _compute_quantities(self):
	# 	res = self._compute_quantities_dict()
	# 	for template in self:
	# 		template.qty_available = res[template.id]['qty_available']
	# 		template.virtual_available = res[template.id]['virtual_available']
	# 		template.incoming_qty = res[template.id]['incoming_qty']
	# 		template.outgoing_qty = res[template.id]['outgoing_qty']
	# 		template._get_stock_price()

	# @api.depends('list_price','standard_price')
	# def _compute_magin(self):
	# 	for rec in self:
	# 		rec.sale_percent = 0
	# 		if rec.list_price > 0 and rec.standard_price > 0:
	# 			profit = rec.list_price - rec.standard_price
	# 			rec.sale_percent = (profit / rec.list_price) * 100

	# def _compute_inverse_magin(self):
	# 	for rec in self:
	# 		rec.list_price = 0
	# 		if rec.standard_price > 0 and rec.sale_percent > 0:
	# 			rec.list_price = rec.standard_price / ((100 - rec.sale_percent)/100)
	# @api.depends_context('company')
	# @api.depends('standard_price','sale_percent')
	# @api.depends_context('company')
	# @api.depends('product_variant_ids', 'product_variant_ids.standard_price','sale_percent')
	# def _compute_magin(self):
	# 	for rec in self:
	# 		rec.list_price = 0
	# 		if rec.standard_price > 0 and rec.sale_percent > 0:
	# 			rec.list_price = rec.standard_price / ((100 - rec.sale_percent)/100)

class Product(models.Model):
	_inherit = "product.product"
	_name = "product.product"
	_description = "Product"

	# stock_price = fields.Float("Stock Cost Price",digits=(12,2),related='product_tmpl_id.stock_price',store=True,compute_sudo=False)
	list_price = fields.Float("Sale Price", digits="Product Price")
	sale_percent = fields.Float('Sale Profit(%)',digits=(12,2),related='product_tmpl_id.sale_percent',store=True)
	min_margin = fields.Float("Min Margin %",digits=(12,2),related='product_tmpl_id.min_margin',store=True)

	# @api.depends('standard_price','sale_percent')
	# def _compute_magin(self):
	# 	for rec in self:
	# 		rec.list_price = 0
	# 		if rec.standard_price > 0 and rec.sale_percent > 0:
	# 			rec.list_price = rec.standard_price / ((100 - rec.sale_percent)/100)
	#
	# @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state','qty_available','purchased_product_qty',
	# 	'stock_quant_ids.quantity','stock_quant_ids.value','stock_quant_ids','stock_move_ids')
	# @api.depends_context(
	# 'lot_id', 'owner_id', 'package_id', 'from_date', 'to_date',
	# 'location', 'warehouse',
	# )
	# def _get_stock_price(self):
	# 	for rec in self:
	# 		location_id = self.env['stock.location'].search([('usage','=','internal')])
	# 		if rec.id:
	# 			stock_value = 0
	# 			stock_qty = 0
	# 			for line in rec.stock_quant_ids:
	# 				if line.location_id in location_id:
	# 					stock_value += line.value
	# 					stock_qty += line.quantity
	# 			if stock_value > 0 and stock_qty > 0:
	# 				rec.stock_price = stock_value / stock_qty
	# 			else:
	# 				rec.stock_price = 0
	# 			# if len(location_id) == 1:
	# 			# 	self.env.cr.execute(""" select sum(quantity) as qty, sum(value) as value from stock_quant where product_id = '%s' and location_id = '%s'""" %(rec.id,location_id.id))
	# 			# else:	
	# 			# 	self.env.cr.execute(""" select sum(quantity) as qty, sum(value) as value from stock_quant where product_id = '%s' and location_id in %s""" %(rec.id,tuple(location_id.ids)))
	# 			# data = self.env.cr.dictfetchall()
	# 			# if data and data[0]['value'] and data[0]['qty']:
	# 			# 	rec.stock_price = data[0]['value']/data[0]['qty']
	# 			# else:
	# 			# 	rec.stock_price = 0
	# 		else:
	# 			rec.stock_price = 0

	# @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
	# @api.depends_context(
	# 'lot_id', 'owner_id', 'package_id', 'from_date', 'to_date',
	# 'location', 'warehouse',
	# )
	# def _compute_quantities(self):
	# 	products = self.filtered(lambda p: p.type != 'service')
	# 	res = products._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
	# 	for product in products:
	# 		product.qty_available = res[product.id]['qty_available']
	# 		product.incoming_qty = res[product.id]['incoming_qty']
	# 		product.outgoing_qty = res[product.id]['outgoing_qty']
	# 		product.virtual_available = res[product.id]['virtual_available']
	# 		product.free_qty = res[product.id]['free_qty']
	# 		product._get_stock_price()
	# 	# Services need to be set with 0.0 for all quantities
	# 	services = self - products
	# 	services.qty_available = 0.0
	# 	services.incoming_qty = 0.0
	# 	services.outgoing_qty = 0.0
	# 	services.virtual_available = 0.0
	# 	services.free_qty = 0.0

	# @api.depends('sale_percent','standard_price')
	# def update_list_price(self):
	# 	for rec in self:
	# 		# if rec.sale_percent and rec.stock_price:
	# 		# 	rec.list_price = rec.stock_price + (rec.stock_price * rec.sale_percent)/100
	# 		if rec.standard_price:
	# 			rec.list_price = rec.standard_price / 0.7
	# 		else:
	# 			rec.list_price = rec.standard_price

class SaleOrder(models.Model):
	_inherit = "sale.order"
	_name = "sale.order"
	_description = "Sale Order"

	show_sale_percent = fields.Boolean("Show / Hide",default=False)
	exchange_rate = fields.Float("Exchange Rate",digits=(12,2),compute='_get_exchange_rate',store=True)
	currency_id = fields.Many2one("res.currency",'Currency',store=True)

	def action_show_sale_percent(self):
		if self.show_sale_percent == True:
			self.show_sale_percent = False
		else:
			self.show_sale_percent = True

	@api.depends('currency_id','date_order')
	def _get_exchange_rate(self):
		from datetime import date
		for rec in self:
			if rec.currency_id:
				# rec.exchange_rate = rec.currency_id._convert(1, rec.company_id.currency_id, rec.company_id, rec.date_order or date.today())
				rec.exchange_rate = rec.currency_id._get_conversion_rate(rec.company_id.currency_id,rec.currency_id,rec.company_id,rec.date_order or fields.Date.today())
			else:
				rec.exchange_rate = 0

class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"
	_name = "sale.order.line"
	_description = "Sale Order Line"

	sale_percent = fields.Float("Margin %",digits=(12,2),compute='_get_sale_profit')

	@api.depends('product_id','price_unit','product_id.standard_price')
	def _get_sale_profit(self):
		for rec in self:
			if rec.product_id and rec.price_unit > 0:
				# profit = rec.price_subtotal - (rec.product_id.standard_price * rec.product_uom_qty)
				# rec.sale_percent = rec.price_subtotal and (profit/rec.price_subtotal)*100
				rec.sale_percent = rec.margin_percent * 100
			else:
				rec.sale_percent = 0

	@api.onchange('product_id')
	def update_price(self):
		if self.product_id:
			self.price_unit = self.product_id.list_price

	@api.depends('price_subtotal', 'product_uom_qty', 'purchase_price','product_id', 'company_id', 'currency_id', 'product_uom',)
	def _compute_margin(self):
		for line in self:
			line._compute_purchase_price()
			if not line.product_id:
				line.purchase_price = 0.0
				continue
			line = line.with_company(line.company_id)
			product = line.product_id
			product_cost = product.standard_price
			if not product_cost:
				# If the standard_price is 0
				# Avoid unnecessary computations
				# and currency conversions
				if not line.purchase_price:
					line.purchase_price = 0.0
				continue
			fro_cur = product.cost_currency_id
			to_cur = line.currency_id or line.order_id.currency_id
			if line.product_uom and line.product_uom != product.uom_id:
				product_cost = product.uom_id._compute_price(
					product_cost,
					line.product_uom,
				)
			purchase_price = fro_cur._convert(
				from_amount=product_cost,
				to_currency=to_cur,
				company=line.company_id or self.env.company,
				date=line.order_id.date_order or fields.Date.today(),
				round=False,
			) if to_cur and product_cost else product_cost
			line.margin = line.price_subtotal - (purchase_price * line.product_uom_qty)
			line.margin_percent = line.price_subtotal and line.margin/line.price_subtotal

class PurchaseOrder(models.Model):
	_inherit = "purchase.order"
	_name = "purchase.order"
	_description = "Purchase Order"

	exchange_rate = fields.Float("Exchange Rate",digits=(12,6),compute='_get_exchange_rate',store=True)
	company_partner_id = fields.Many2one("res.partner",'Company Partner',related='company_id.partner_id',store=True)
	partner_shipping_id = fields.Many2one(
		'res.partner', string='Delivery Address', required=True,
		domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
	is_shipment_done = fields.Boolean("Is Shipment Done",copy=False)
	currency_rate = fields.Float("Currency Rate", compute='_compute_currency_rate', compute_sudo=True, store=True, readonly=True, 
		help='Ratio between the purchase order currency and the company currency',digits=(12,6))
	company_currency_id = fields.Many2one('res.currency','Company Currency',default=lambda self:self.env.company.currency_id.id)
	amount_total_signed = fields.Monetary('Total',currency_field='company_currency_id',compute='_get_amount_total_signed')

	@api.depends('amount_total','date_planned','currency_id','company_currency_id')
	def _get_amount_total_signed(self):
		for rec in self:
			if rec.amount_total and rec.date_planned and rec.company_currency_id and rec.currency_id:
				rec.amount_total_signed = rec.currency_id._convert(rec.amount_total,rec.company_currency_id, rec.company_id, rec.date_planned or date.today())
			else:
				rec.amount_total_signed = 0

	@api.onchange('company_id','partner_id')
	def update_shipping_address(self):
		self = self.with_company(self.company_id)
		addr = self.company_id.partner_id.address_get(['delivery', 'invoice'])
		values = {
			'partner_shipping_id': addr['delivery'],
		}
		self.update(values)

	@api.onchange('partner_id')
	def update_partner_currency(self):
		for rec in self:
			# rec.currency_id = False
			rec.payment_term_id = False
			if rec.partner_id:
				if rec.partner_id.currency_dummy_id:
					rec.currency_id = rec.partner_id.currency_dummy_id.id
					rec.payment_term_id = rec.partner_id.property_supplier_payment_term_id.id

	@api.depends('currency_id','date_planned')
	def _get_exchange_rate(self):
		from datetime import date
		for rec in self:
			if rec.currency_id:
				# rec.exchange_rate = rec.currency_id._convert(1, rec.company_id.currency_id, rec.company_id, rec.date_order or date.today())
				rec.exchange_rate = rec.currency_id._get_conversion_rate(rec.company_id.currency_id,rec.currency_id,rec.company_id,rec.date_planned or fields.Date.today())
			else:
				rec.exchange_rate = 0

	@api.depends('date_planned', 'currency_id', 'company_id', 'company_id.currency_id')
	def _compute_currency_rate(self):
		for order in self:
			order.currency_rate = self.env['res.currency']._get_conversion_rate(order.company_id.currency_id, order.currency_id, order.company_id, order.date_planned or fields.Date.today())

	def _add_supplier_to_product(self):
		# Add the partner in the supplier list of the product if the supplier is not registered for
		# this product. We limit to 10 the number of suppliers for a product to avoid the mess that
		# could be caused for some generic products ("Miscellaneous").
		for line in self.order_line:
			# Do not add a contact as a supplier
			partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
			if line.product_id and len(line.product_id.seller_ids) <= 10:
				if partner in line.product_id.seller_ids.mapped('name') and line.price_unit not in line.product_id.seller_ids.mapped('price'): 
					pass
				elif partner not in line.product_id.seller_ids.mapped('name'):
					pass
				else:
					break
				# Convert the price in the right currency.
				currency = partner.property_purchase_currency_id or self.env.company.currency_id
				price = self.currency_id._convert(line.price_unit, currency, line.company_id, line.date_order or fields.Date.today(), round=False)
				# Compute the price for the template's UoM, because the supplier's UoM is related to that UoM.
				if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
					default_uom = line.product_id.product_tmpl_id.uom_po_id
					price = line.product_uom._compute_price(price, default_uom)

				supplierinfo = {
					'name': partner.id,
					'sequence': max(line.product_id.seller_ids.mapped('sequence')) + 1 if line.product_id.seller_ids else 1,
					'min_qty': 0.0,
					'price': price,
					'currency_id': currency.id,
					'delay': 0,
				}
				# In case the order partner is a contact address, a new supplierinfo is created on
				# the parent company. In this case, we keep the product name and code.
				seller = line.product_id._select_seller(
					partner_id=line.partner_id,
					quantity=line.product_qty,
					date=line.order_id.date_order and line.order_id.date_order.date(),
					uom_id=line.product_uom)
				if seller:
					supplierinfo['product_name'] = seller.product_name
					supplierinfo['product_code'] = seller.product_code
				vals = {
					'seller_ids': [(0, 0, supplierinfo)],
				}
				try:
					line.product_id.write(vals)
				except AccessError:  # no write access rights -> just ignore
					break

	def _prepare_invoice(self):
		"""Prepare the dict of values to create the new invoice for a purchase order.
		"""
		self.ensure_one()
		move_type = self._context.get('default_move_type', 'in_invoice')
		journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
		if not journal:
			raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

		partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
		invoice_vals = {
			'ref': self.partner_ref or '',
			'move_type': move_type,
			'narration': self.notes,
			'currency_id': self.currency_id.id,
			'invoice_user_id': self.user_id and self.user_id.id,
			'partner_id': partner_invoice_id,
			'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
			'payment_reference': self.partner_ref or '',
			'partner_bank_id': self.partner_id.bank_ids[:1].id,
			'invoice_origin': self.name,
			'invoice_payment_term_id': self.payment_term_id.id,
			'invoice_line_ids': [],
			'company_id': self.company_id.id,
			'purchase_id':self.id,
		}
		return invoice_vals

class AccountMove(models.Model):
	_inherit = "account.move"
	_name = "account.move"
	_description = "Account Move"

	landed_cost_factor = fields.Float("Factor Value",digits=(12,6),compute='_get_landed_cost_factor_value',store=True)
	# purchase_ids = fields.Many2many('purchase.order','account_purchase_order_rel','purchase_id','move_id','Purchase Order',compute='_get_purchase_order',store=True)
	picking_ids = fields.Many2many('stock.picking','account_picking_rel','picking_id','account_id','Stock Picking',compute='_get_stock_picking',store=True)
	exchange_rate = fields.Float("Currency Rate",digits=(12,6),compute='_get_exchange_rate',store=True)
	# currency_rate = fields.Float("Currency Rate",digits=(12,2),compute='_compute_currency_rate',store=True)
	# shipment_no = fields.Char("Shipment No")
	shipment_id = fields.Many2one('ax.shipment.master','Shipment No',copy=False)
	is_landed_cost_bill = fields.Boolean("Shipment Cost Bill?")
	landed_costs_ids = fields.One2many('stock.landed.cost.bill', 'vendor_bill_id', string='Landed Costs')
	purchase_id = fields.Many2one('purchase.order','Purchase Order',store=True)
	purchase_date = fields.Datetime("Purchase Date",related='purchase_id.date_approve',store=True)
	manual_currency_rate = fields.Float("Manual Currency Rate",digits=(12,6))

	# @api.constrains('purchase_id')
	# def shipment_constrains(self):
	# 	if self.purchase_id and not self.shipment_id and self.state == 'done':
	# 		shipment_id = self.env['ax.shipment.master'].search([('po_ids','in',self.purchase_id.id)])
	# 		if shipment_id:
	# 			raise UserError("Warning!!, Shipment No is mandatory for this Bill.")

	def action_post(self):
		res = super(AccountMove, self).action_post()
		if self.purchase_id and not self.shipment_id and self.move_type == 'in_invoice':
			shipment_id = self.env['ax.shipment.master'].search([('po_ids','in',self.purchase_id.id)])
			if shipment_id:
				raise UserError("Warning!!, Shipment No is mandatory for this Bill.")
		return res

	def action_view_landed_costs(self):
		self.ensure_one()
		action = self.env["ir.actions.actions"]._for_xml_id("stock_landed_costs.action_stock_landed_cost")
		landed_costs_ids = [x.header_id.id for x in self.landed_costs_ids]
		domain = [('id', 'in', landed_costs_ids)]
		context = dict(self.env.context, default_vendor_bill_id=self.id)
		views = [(self.env.ref('stock_landed_costs.view_stock_landed_cost_tree2').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)

	# @api.constrains('shipment_no')
	# def _check_duplicate_shipment_no(self):
	# 	if self.shipment_no:
	# 		name=self.shipment_no.upper()  
	# 		name=name.replace("'", "")
	# 		self.env.cr.execute(""" select upper(shipment_no) from account_move where upper(shipment_no)  = '%s' and id != '%s'""" %(name,self.id))
	# 		data = self.env.cr.dictfetchall()
	# 		if data:
	# 			raise UserError("Warning!!, Shipment No must be unique!")

	@api.depends('invoice_line_ids','invoice_line_ids.price_subtotal','amount_total')
	def _get_landed_cost_factor_value(self):
		for rec in self:
			if rec.invoice_line_ids and rec.amount_total > 0:
				goods_tot = sum([x.price_subtotal for x in rec.invoice_line_ids if x.product_id.type != 'service'])
				if goods_tot > 0:
					rec.landed_cost_factor = rec.amount_total / goods_tot
				else:
					rec.landed_cost_factor = 0
			else:
				rec.landed_cost_factor = 0

	@api.depends('invoice_line_ids','invoice_line_ids.purchase_line_id')
	def _get_stock_picking(self):
		for rec in self:
			if rec.invoice_line_ids:
				purchase_ids = list(set([x.purchase_line_id.order_id for x in rec.invoice_line_ids if x.purchase_line_id]))
				picking_ids = [y.id for x in purchase_ids for y in x.picking_ids]
				rec.picking_ids = [(6,0,picking_ids)]
			else:
				rec.picking_ids =  False

	def currency_convert(self,amt):
		from datetime import date
		if self.company_id.currency_id and amt:
			# value = self.company_id.currency_id.compute(amt,self.currency_id)
			value = self.currency_id._convert(amt, self.company_id.currency_id, self.company_id, date.today())
			return round(value,2)

	def currency_inverse_convert(self, amt):
		from datetime import date
		if amt:
			value = self.company_id.currency_id._convert(amt, self.currency_id, self.company_id, date.today())
			return round(value,2)

	def get_inv_value(self, picking_id):
		from datetime import date
		if picking_id:
			value =  sum([(x.purchase_line_id.price_unit * x.quantity_done) for x in picking_id.move_ids_without_package])
			return round(value,2)

	# @api.depends('invoice_date', 'currency_id', 'company_id', 'company_id.currency_id')
	# def _compute_currency_rate(self):
	# 	for order in self:
	# 		order.currency_rate = self.env['res.currency']._get_conversion_rate(order.company_id.currency_id, order.currency_id, order.company_id, order.invoice_date)

	@api.depends('currency_id','company_id','date','company_id.currency_id')
	def _get_exchange_rate(self):
		from datetime import date
		for rec in self:
			if rec.currency_id:
				# rec.exchange_rate = self.env['res.currency']._get_conversion_rate(rec.company_id.currency_id, rec.currency_id, rec.company_id, rec.invoice_date or datetime.now())
				rec.exchange_rate = rec.currency_id._get_conversion_rate(rec.company_id.currency_id,rec.currency_id,rec.company_id,rec.date or fields.Date.today())
			else:
				rec.exchange_rate = 0

	# @api.onchange("shipment_id")
	# def update_clearance_vendor(self):
	# 	if self.shipment_id and self.is_landed_cost_bill == True:
	# 		self.partner_id = self.shipment_id.landed_partner_id.id

class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	is_landed_cost_bill = fields.Boolean('Shipment Cost Bill?',related='move_id.is_landed_cost_bill')

	@api.onchange('is_landed_cost_bill')
	def udpate_costing_domain(self):
		if self.is_landed_cost_bill == True:
			return {'domain':{'product_id':[('type','=','service')]}}

class PurchaseOrder(models.Model):
	_inherit = "purchase.order"

	manual_currency_rate = fields.Float("Manual Currency Rate",digits=(12,6))
	show_manual_currency_update = fields.Boolean("Show Manual Currency Update")

	@api.onchange('currency_id')
	def update_manual_currency_rate(self):
		if self.currency_id:
			self.manual_currency_rate = self.env['res.currency']._get_conversion_rate(self.company_id.currency_id, self.currency_id, 
										self.company_id, self.date_planned or datetime.now())

	@api.onchange('manual_currency_rate')
	def show_manual_rate_update(self):
		if self.manual_currency_rate > 0:
			self.show_manual_currency_update = True
		else:
			self.show_manual_currency_update = False

	def update_prices(self):
		self.update_prices_po()
		# self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id)]).unlink()
		self.env['res.currency.rate'].create({
			'name':self.date_planned,
			'rate':self.manual_currency_rate,
			'company_id':self.company_id.id,
			'currency_id':self.currency_id.id,
		})
		self.currency_id.rate = self.manual_currency_rate
		self._compute_currency_rate()

	def update_prices_po(self):
		for line in self.order_line:
			line._onchange_quantity()
		self.show_manual_currency_update = False

	def _prepare_invoice(self):
		"""Prepare the dict of values to create the new invoice for a purchase order.
		"""
		self.ensure_one()
		move_type = self._context.get('default_move_type', 'in_invoice')
		journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
		if not journal:
			raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))
		# shipment_id = self.env['ax.shipment.master'].search([('po_ids','in',self.id),('state','=','approved')],limit=1)
		partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
		invoice_vals = {
			'ref': self.partner_ref or '',
			'move_type': move_type,
			'narration': self.notes,
			'currency_id': self.currency_id.id,
			'invoice_user_id': self.user_id and self.user_id.id,
			'partner_id': partner_invoice_id,
			'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
			'payment_reference': self.partner_ref or '',
			'partner_bank_id': self.partner_id.bank_ids[:1].id,
			'invoice_origin': self.name,
			'invoice_payment_term_id': self.payment_term_id.id,
			'invoice_line_ids': [],
			'company_id': self.company_id.id,
			'manual_currency_rate':self.manual_currency_rate,
			# 'shipment_id':shipment_id.id if shipment_id else False
		}
		return invoice_vals


class PurchaseOrderLine(models.Model):
	_inherit = "purchase.order.line"
	_description = "Purchase Order Line"

	@api.onchange('product_qty', 'product_uom')
	def _onchange_quantity(self):
		from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
		res = super(PurchaseOrderLine,self)._onchange_quantity()
		if not self.product_id:
			return
		params = {'order_id': self.order_id}
		seller = self.product_id._select_seller(
			partner_id=self.partner_id,
			quantity=self.product_qty,
			date=self.order_id.date_order and self.order_id.date_order.date(),
			uom_id=self.product_uom,
			params=params)

		if seller or not self.date_planned:
			self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

		# If not seller, use the standard price. It needs a proper currency conversion.
		if not seller:
			po_line_uom = self.product_uom or self.product_id.uom_po_id
			price_unit = self.env['account.tax']._fix_tax_included_price_company(
				self.product_id.uom_id._compute_price(self.product_id.standard_price, po_line_uom),
				self.product_id.supplier_taxes_id,
				self.taxes_id,
				self.company_id,
			)
			if price_unit and self.order_id.currency_id and self.order_id.company_id.currency_id != self.order_id.currency_id:
				price_unit = self.order_id.company_id.currency_id._convert(
					price_unit,
					self.order_id.currency_id,
					self.order_id.company_id,
					self.date_order or fields.Date.today(),
					m_rate=self.order_id.manual_currency_rate,
				)

			self.price_unit = price_unit
			return

		price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, self.product_id.supplier_taxes_id, self.taxes_id, self.company_id) if seller else 0.0
		if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
			price_unit = seller.currency_id._convert(
				price_unit, self.order_id.currency_id, self.order_id.company_id, self.date_order or fields.Date.today(),m_rate=self.order_id.manual_currency_rate,)

		if seller and self.product_uom and seller.product_uom != self.product_uom:
			price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

		self.price_unit = price_unit
		return res

	def _prepare_account_move_line(self, move=False):
		self.ensure_one()
		res = {
			'display_type': self.display_type,
			'sequence': self.sequence,
			'name': '%s: %s' % (self.order_id.name, self.name),
			'product_id': self.product_id.id,
			'product_uom_id': self.product_uom.id,
			'quantity': self.qty_to_invoice,
			'price_unit': self.price_unit,
			'tax_ids': [(6, 0, self.taxes_id.ids)],
			'analytic_account_id': self.account_analytic_id.id,
			'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
			'purchase_line_id': self.id,
		}
		if not move:
			return res

		if self.currency_id == move.company_id.currency_id:
			currency = False
		else:
			currency = move.currency_id

		res.update({
			'move_id': move.id,
			'currency_id': currency and currency.id or False,
			'date_maturity': move.invoice_date_due,
			'partner_id': move.partner_id.id,
		})
		return res

class StockPicking(models.Model):
	_inherit = "stock.picking"

	shipment_id = fields.Many2one('ax.shipment.master','Shipment No',copy=False)

class StockLandedCost(models.Model):
	_inherit = "stock.landed.cost"
	_name = "stock.landed.cost"
	_description = "Stock Landed Cost"
	_order = "id desc"

	landed_bill_id = fields.Many2many('account.move','acc_landed_bill_rel','landed_cost_id','move_id','Clearance Bill')
	# vendor_bill_id = fields.Many2many('account.move', 'account_landed_cost_rel', 'account_id', 'landed_cost_id','Vendor Bill', copy=False, domain=[('move_type', '=', 'in_invoice')])
	vendor_bill_id = fields.One2many('stock.landed.cost.bill','header_id')
	landed_bill_type = fields.Selection([('actual','Actual Clearance Bill'),('previous','Previous Clearance Bill')],default='actual',string="Clearance Bill Type")
	previous_bill_id = fields.Many2one('account.move','Previous Clearance Bill')
	shipment_id = fields.Many2one('ax.shipment.master','Shipment No')
	po_ids = fields.Many2many('purchase.order','acc_purchase_costing_rel','costing_id','purchase_id','Purchase Orders')
	# partner_id = fields.Many2one('res.partner','Vendor')
	landed_partner_id = fields.Many2one('res.partner','Clearance Vendor')
	attachment_ids = fields.Many2many('ir.attachment','acc_costing_attachment_rel','costing_id','attachment_id','Attachments')
	# state = fields.Selection([
 #        ('draft', 'Draft'),
 #        ('confirm','Confirmed'),
 #        ('done', 'Posted'),
 #        ('cancel', 'Cancelled')], 'State', default='draft',
 #        copy=False, readonly=True, tracking=True)

	@api.onchange('landed_bill_type')
	def refresh_bill_id(self):
		if self.landed_bill_type:
			self.landed_bill_id = False
			self.previous_bill_id = False

	@api.onchange('shipment_id')
	def update_shipment_details(self):
		self.landed_bill_id = False
		self.picking_ids = False
		self.vendor_bill_id = False
		self.cost_lines = False
		if self.shipment_id:
			landed_bill_id = self.env['account.move'].search([('is_landed_cost_bill','=',True),('shipment_id','=',self.shipment_id.id),('state','=','posted')])
			self.landed_bill_id = [(6,0,landed_bill_id.ids)]
			self.picking_ids = [(6,0,self.shipment_id.picking_ids.ids)]
			bill_ids = []
			for line in self.shipment_id.bill_ids:
				bill_ids.append((0,0,{
					'vendor_bill_id':line.id,
				}))
			self.vendor_bill_id = bill_ids
			self.po_ids = [(6,0,self.shipment_id.po_ids.ids)]
			self.get_landed_cost_products()

	# @api.onchange('shipment_id')
	# def update_partner(self):
	# 	if self.shipment_id:
	# 		self.partner_id = self.shipment_id.partner_id.id
	# 		self.landed_partner_id = self.shipment_id.landed_partner_id.id

	def get_landed_cost_products(self):
		# if self.landed_bill_type == 'actual':
		# 	landed_bill_id = self.landed_bill_id
		# else:
		# 	landed_bill_id = self.previous_bill_id
		if self.landed_bill_id:
			self.cost_lines = False
			products = []
			for rec in self.landed_bill_id:
				for line in rec.invoice_line_ids:
					if line.is_landed_costs_line == True:
						products.append((0,0,{
							'product_id': line.product_id.id,
							'name':line.name,
							'account_id':line.account_id.id,
							'split_method':line.product_id.split_method_landed_cost,
							'price_unit':line.move_id.currency_id._convert(line.price_subtotal,line.move_id.company_id.currency_id, line.move_id.company_id, line.move_id.date)
						}))
			if products != []:
				self.write({'cost_lines':products})
				for line in self.cost_lines:
					line.account_id = line.product_id.categ_id.property_stock_account_input_categ_id.id
			else:
				raise UserError("Warning!!, No Landed Cost Product found.")

	@api.onchange('previous_bill_id','landed_bill_id')
	def refresh_additional_cost(self):
		self.cost_lines = False
		self.get_landed_cost_products()

	# def _check_can_validate(self):
	# 	if any(cost.state not in ('draft','confirm') for cost in self):
	# 		raise UserError(_('Only draft landed costs can be validated'))
	# 	for cost in self:
	# 		if not cost._get_targeted_move_ids():
	# 			target_model_descriptions = dict(self._fields['target_model']._description_selection(self.env))
	# 			raise UserError(_('Please define %s on which those additional costs should apply.', target_model_descriptions[cost.target_model]))

	# def button_validate(self):
	# 	from collections import defaultdict
	# 	self._check_can_validate()
	# 	if self.landed_bill_type != 'actual':
	# 		raise UserError("Warning!!, You are not allowed to Post with Previous Clearance Bill.")
	# 	cost_without_adjusment_lines = self.filtered(lambda c: not c.valuation_adjustment_lines)
	# 	if cost_without_adjusment_lines:
	# 		cost_without_adjusment_lines.compute_landed_cost()
	# 	if not self._check_sum():
	# 		raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

	# 	for cost in self:
	# 		cost = cost.with_company(cost.company_id)
	# 		move = self.env['account.move']
	# 		move_vals = {
	# 			'journal_id': cost.account_journal_id.id,
	# 			'date': cost.date,
	# 			'ref': cost.name,
	# 			'line_ids': [],
	# 			'move_type': 'entry',
	# 		}
	# 		valuation_layer_ids = []
	# 		cost_to_add_byproduct = defaultdict(lambda: 0.0)
	# 		for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
	# 			stock_valuation_layer_id = self.env['stock.valuation.layer'].search([('stock_move_id','=',line.move_id.id),('stock_landed_cost_id','=',cost.id),('product_id','=',line.product_id.id)],order='id desc',limit=1)
	# 			valuation_layer_ids.append(stock_valuation_layer_id.id)
	# 			move_vals['line_ids'] += line._create_accounting_entries(move, line.move_id.product_qty)
	# 		valuation_layer_ids = list(set(valuation_layer_ids))
	# 		move_vals['stock_valuation_layer_ids'] = [(6, None, valuation_layer_ids)]
	# 		move = move.create(move_vals)
	# 		cost.write({'state': 'done', 'account_move_id': move.id})
	# 		move._post()

	# 		for bill in cost.vendor_bill_id:
	# 			if bill.vendor_bill_id and bill.vendor_bill_id.state == 'posted' and cost.company_id.anglo_saxon_accounting:
	# 				all_amls = bill.vendor_bill_id.line_ids | cost.account_move_id.line_ids
	# 				for product in cost.cost_lines.product_id:
	# 					accounts = product.product_tmpl_id.get_product_accounts()
	# 					input_account = accounts['stock_input']
	# 					all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.full_reconcile_id).reconcile()

	# 	return True

	# def button_validate(self):
	# 	for cost in self:
	# 		if cost.landed_bill_type != 'actual':
	# 			raise UserError("Warning!!, You are not allowed to Post with Previous Clearance Bill.")
	# 		if cost.account_move_id != 'cancel':
	# 			cost.write({'state': 'done'})
	# 			move._post()
	# 			for bill in cost.vendor_bill_id:
	# 				if bill.vendor_bill_id and bill.vendor_bill_id.state == 'posted' and cost.company_id.anglo_saxon_accounting:
	# 					all_amls = bill.vendor_bill_id.line_ids | cost.account_move_id.line_ids
	# 					for product in cost.cost_lines.product_id:
	# 						accounts = product.product_tmpl_id.get_product_accounts()
	# 						input_account = accounts['stock_input']
	# 						all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.full_reconcile_id).reconcile()
	# 	return True

	# def calc_landed_cost(self):
	# 	from collections import defaultdict
	# 	if not self.cost_lines:
	# 		raise UserError('Warning!!, Kindly add Additional Cost for Landed Cost Computation.')
	# 	if self.valuation_adjustment_lines:
	# 		stock_valuation_layer_ids = self.env['stock.valuation.layer'].search([('stock_landed_cost_id','=',self.id)])
	# 		if stock_valuation_layer_ids:
	# 			for layer in stock_valuation_layer_ids:
	# 				self.env.cr.execute(""" delete from stock_valuation_layer where id = '%s' """ %(layer.id))
	# 	self.valuation_adjustment_lines = False
	# 	self.compute_landed_cost()
	# 	for cost in self:
	# 		cost_to_add_byproduct = defaultdict(lambda: 0.0)
	# 		valuation_layer_ids = []
	# 		for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
	# 			remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
	# 			linked_layer = line.move_id.stock_valuation_layer_ids[:1]
	# 			cost_to_add = (remaining_qty / line.move_id.product_qty) * line.additional_landed_cost
	# 			if not cost.company_id.currency_id.is_zero(cost_to_add):
	# 				valuation_layer = self.env['stock.valuation.layer'].create({
	# 					'value': cost_to_add,
	# 					'unit_cost': 0,
	# 					'quantity': 0,
	# 					'remaining_qty': 0,
	# 					'stock_valuation_layer_id': linked_layer.id,
	# 					'description': cost.name,
	# 					'stock_move_id': line.move_id.id,
	# 					'product_id': line.move_id.product_id.id,
	# 					'stock_landed_cost_id': cost.id,
	# 					'company_id': cost.company_id.id,
	# 				})					
	# 				linked_layer.remaining_value += cost_to_add
	# 				valuation_layer_ids.append(valuation_layer.id)
	# 			product = line.move_id.product_id
	# 			if product.cost_method == 'average':
	# 				cost_to_add_byproduct[product] += cost_to_add
	# 			qty_out = 0
	# 			if line.move_id._is_in():
	# 				qty_out = line.move_id.product_qty - remaining_qty
	# 			elif line.move_id._is_out():
	# 				qty_out = line.move_id.product_qty
	# 		products = self.env['product.product'].browse(p.id for p in cost_to_add_byproduct.keys())
	# 			if not float_is_zero(product.quantity_svl, precision_rounding=product.uom_id.rounding):
	# 				product.with_company(cost.company_id).sudo().with_context(disable_auto_svl=True).standard_price += cost_to_add_byproduct[product] / product.quantity_svl
	# 		self.shipment_id.is_costing_done = True

	def button_validate(self):
		for cost in self:
			if cost.account_move_id:
				cost.write({'state': 'done'})
				cost.shipment_id.is_costing_done = True
				for po in cost.shipment_id.po_ids:
					if any([x.state not in ('done','cancel') for x in po.picking_ids if x.picking_code != 'outgoing']):
						po.is_shipment_done = False
				for pick in cost.shipment_id.picking_ids:
					pick.shipment_id = cost.shipment_id.id
				for bill in cost.shipment_id.bill_ids:
					bill.shipment_id = cost.shipment_id.id
				cost.account_move_id._post()
				# self.shipment_id.is_costing_done = True
				for bill in cost.vendor_bill_id:
					if bill.vendor_bill_id and bill.vendor_bill_id.state == 'posted' and cost.company_id.anglo_saxon_accounting:
						all_amls = bill.vendor_bill_id.line_ids | cost.account_move_id.line_ids
						for product in cost.cost_lines.product_id:
							accounts = product.product_tmpl_id.get_product_accounts()
							input_account = accounts['stock_input']
							all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.full_reconcile_id).reconcile()
		return True

	def calc_landed_cost(self):
		from collections import defaultdict
		self._check_can_validate()
		cost_without_adjusment_lines = self.filtered(lambda c: not c.valuation_adjustment_lines)
		if cost_without_adjusment_lines:
			cost_without_adjusment_lines.compute_landed_cost()
		if not self._check_sum():
			raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))
		if self.account_move_id:
			self.account_move_id.button_cancel()

		for cost in self:
			cost = cost.with_company(cost.company_id)
			move = self.env['account.move']
			move_vals = {
				'journal_id': cost.account_journal_id.id,
				'date': cost.date,
				'ref': cost.name,
				'line_ids': [],
				'move_type': 'entry',
			}
			valuation_layer_ids = []
			cost_to_add_byproduct = defaultdict(lambda: 0.0)
			for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
				remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
				linked_layer = line.move_id.stock_valuation_layer_ids[:1]

				# Prorate the value at what's still in stock
				cost_to_add = (remaining_qty / line.move_id.product_qty) * line.additional_landed_cost
				if not cost.company_id.currency_id.is_zero(cost_to_add):
					valuation_layer = self.env['stock.valuation.layer'].create({
						'value': cost_to_add,
						'unit_cost': 0,
						'quantity': 0,
						'remaining_qty': 0,
						'stock_valuation_layer_id': linked_layer.id,
						'description': cost.name,
						'stock_move_id': line.move_id.id,
						'product_id': line.move_id.product_id.id,
						'stock_landed_cost_id': cost.id,
						'company_id': cost.company_id.id,
					})
					linked_layer.remaining_value += cost_to_add
					valuation_layer_ids.append(valuation_layer.id)
				# Update the AVCO
				product = line.move_id.product_id
				if product.cost_method == 'average':
					cost_to_add_byproduct[product] += cost_to_add
				# `remaining_qty` is negative if the move is out and delivered proudcts that were not
				# in stock.
				qty_out = 0
				if line.move_id._is_in():
					qty_out = line.move_id.product_qty - remaining_qty
				elif line.move_id._is_out():
					qty_out = line.move_id.product_qty
				move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)

			# batch standard price computation avoid recompute quantity_svl at each iteration
			products = self.env['product.product'].browse(p.id for p in cost_to_add_byproduct.keys())
			for product in products:  # iterate on recordset to prefetch efficiently quantity_svl
				if not float_is_zero(product.quantity_svl, precision_rounding=product.uom_id.rounding):
					product.with_company(cost.company_id).sudo().with_context(disable_auto_svl=True).standard_price += cost_to_add_byproduct[product] / product.quantity_svl

			move_vals['stock_valuation_layer_ids'] = [(6, None, valuation_layer_ids)]
			move = move.create(move_vals)
			cost.write({'account_move_id': move.id})
			self.shipment_id.is_costing_done = True

			# if cost.vendor_bill_id and cost.vendor_bill_id.state == 'posted' and cost.company_id.anglo_saxon_accounting:
			# 	all_amls = cost.vendor_bill_id.line_ids | cost.account_move_id.line_ids
			# 	for product in cost.cost_lines.product_id:
			# 		accounts = product.product_tmpl_id.get_product_accounts()
			# 		input_account = accounts['stock_input']
			# 		all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.full_reconcile_id).reconcile()
		return True

	def compute_landed_cost(self):
		AdjustementLines = self.env['stock.valuation.adjustment.lines']
		AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

		digits = self.env['decimal.precision'].precision_get('Landed Cost Price')
		if not digits:
			raise UserError("Warning!!, Create Decimal Precision for Landed Cost Price with decimal value as 2.")
		towrite_dict = {}
		for cost in self.filtered(lambda cost: cost._get_targeted_move_ids()):
			total_qty = 0.0
			total_cost = 0.0
			total_weight = 0.0
			total_volume = 0.0
			total_line = 0.0
			all_val_line_values = cost.get_valuation_lines()
			for val_line_values in all_val_line_values:
				for cost_line in cost.cost_lines:
					val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
					self.env['stock.valuation.adjustment.lines'].create(val_line_values)
				total_qty += val_line_values.get('quantity', 0.0)
				total_weight += val_line_values.get('weight', 0.0)
				total_volume += val_line_values.get('volume', 0.0)

				former_cost = val_line_values.get('former_cost', 0.0)
				# round this because former_cost on the valuation lines is also rounded
				total_cost += tools.float_round(former_cost, precision_digits=digits) if digits else former_cost

				total_line += 1
			for line in cost.cost_lines:
				value_split = 0.0
				for valuation in cost.valuation_adjustment_lines:
					value = 0.0
					if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
						if line.split_method == 'by_quantity' and total_qty:
							per_unit = (line.price_unit / total_qty)
							value = valuation.quantity * per_unit
						elif line.split_method == 'by_weight' and total_weight:
							per_unit = (line.price_unit / total_weight)
							value = valuation.weight * per_unit
						elif line.split_method == 'by_volume' and total_volume:
							per_unit = (line.price_unit / total_volume)
							value = valuation.volume * per_unit
						elif line.split_method == 'equal':
							value = (line.price_unit / total_line)
						elif line.split_method == 'by_current_cost_price' and total_cost:
							per_unit = (line.price_unit / total_cost)
							value = valuation.former_cost * per_unit
						else:
							value = (line.price_unit / total_line)

						if digits:
							value = tools.float_round(value, precision_digits=digits, rounding_method='UP')
							fnc = min if line.price_unit > 0 else max
							value = fnc(value, line.price_unit - value_split)
							value_split += value

						if valuation.id not in towrite_dict:
							towrite_dict[valuation.id] = value
						else:
							towrite_dict[valuation.id] += value
		for key, value in towrite_dict.items():
			AdjustementLines.browse(key).write({'additional_landed_cost': value})
		return True

	def entry_draft(self):
		self.shipment_id.is_costing_done = False
		self.account_move_id.button_draft()
		self.write({'state':'draft'})

class StockLandedCostLine(models.Model):
	_inherit = "stock.landed.cost.lines"

	@api.onchange('product_id')
	def onchange_product_id(self):
		res = super(StockLandedCostLine,self).onchange_product_id()
		# self.name = self.product_id.name or ''
		# self.split_method = self.product_id.product_tmpl_id.split_method_landed_cost or self.split_method or 'equal'
		# self.price_unit = self.product_id.standard_price or 0.0
		# accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
		self.account_id = self.product_id.categ_id.property_stock_account_input_categ_id.id
		return res

class StockLandedCostBill(models.Model):
	_name = "stock.landed.cost.bill"
	_description = "Stock Landed Cost Bill"

	header_id = fields.Many2one('stock.landed.cost','Landed Cost')
	vendor_bill_id = fields.Many2one('account.move','Bill',copy=False)
	partner_id = fields.Many2one('res.partner','Vendor',related='vendor_bill_id.partner_id')
	shipment_id = fields.Many2one('ax.shipment.master','Shipment No',related='vendor_bill_id.shipment_id')
	bill_date = fields.Date('Bill Date',related='vendor_bill_id.invoice_date')
	amount_total = fields.Monetary("Bill Total",related='vendor_bill_id.amount_total')
	currency_id = fields.Many2one("res.currency",'Currency',related='vendor_bill_id.currency_id')

class ResPartner(models.Model):
	_inherit = "res.partner"
	_description = "Customer/Vendor"

	currency_dummy_id = fields.Many2one('res.currency','Currency')

class ResCurrency(models.Model):
	_inherit = "res.currency"

	def _convert(self, from_amount, to_currency, company, date, round=True, m_rate=None):
		"""Returns the converted amount of ``from_amount``` from the currency
		``self`` to the currency ``to_currency`` for the given ``date`` and
		company.

		:param company: The company from which we retrieve the convertion rate
		:param date: The nearest date from which we retriev the conversion rate.
		:param round: Round the result or not
		"""
		self, to_currency = self or to_currency, to_currency or self
		assert self, "convert amount from unknown currency"
		assert to_currency, "convert amount to unknown currency"
		assert company, "convert amount from unknown company"
		assert date, "convert amount from unknown date"
		# apply conversion rate
		if self == to_currency:
			to_amount = from_amount
		else:
			if m_rate:
				to_amount = from_amount * m_rate
			else:
				to_amount = from_amount * self._get_conversion_rate(self, to_currency, company, date)
		# apply rounding
		return to_currency.round(to_amount) if round else to_amount


# class ResCurrencyRate(models.Model):
# 	_inherit = "res.currency.rate"

# 	_sql_constraints = [
# 		('unique_name_per_day', 'check(1=1)', 'Only one currency rate per day allowed!'),
# 		('currency_rate_check', 'CHECK (rate>0)', 'The currency rate must be strictly positive.'),
# 	]
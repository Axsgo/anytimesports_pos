### import file ###
from odoo import api,models,fields
from odoo.exceptions import UserError

class AxCostingReport(models.TransientModel):
	_name = "ax.costing.report"
	_description = "Costing Report"

	entry_date = fields.Date("Report Date",default=fields.Date.today)
	shipment_id = fields.Many2one('ax.shipment.master','Shipment No')
	bill_id = fields.Many2one('account.move','Clearance Bill')
	company_id = fields.Many2one('res.company','Company',default=lambda self:self.env.company.id)
	line_ids = fields.One2many("ax.ch.costing.product.line",'header_id')
	landed_cost_ids = fields.One2many("ax.ch.landed.cost.line",'header_id')
	currency_id = fields.Many2one('res.currency','Currency',compute="get_currency",store=True)
	landed_cost_factor = fields.Float('Factor Value',digits=(12,6),compute="get_factor_value",store=True)
	# line_ids = fields.Many2many('account.move.line','account_move_line_costing_rel','move_line_id','costing_id','Vendor Products',compute='get_product_details',store=True)
	# landed_cost_ids = fields.Many2many('account.move.line','account_move_line_landed_cost_rel','move_line_id','costing_id','Landed Cost Products',compute='get_product_details',store=True)
	vendor_bill_ids = fields.Many2many('account.move','account_move_costing_rel','account_id','costing_id','Vendor Bills',compute='get_product_details',store=True)
	landed_bill_ids = fields.Many2many('account.move','account_move_landed_costing_rel','account_id','costing_id','Landed Cost Bills',compute='get_product_details',store=True)
	vendor_subtotal = fields.Float('Vendor Subtotal',digits=(12,2),compute="_get_vendor_subtotal")
	vendor_total = fields.Float('Vendor Bill Total',digits=(12,2),compute='_get_vendor_total')
	landed_total = fields.Float("Landed Cost Total",digits=(12,2),compute='_get_landed_cost_total')
	po_ids = fields.Char("PO's",compute="_get_pos",store=True)
	partner_ids = fields.Char("Supplier's",compute="_get_partners",store=True)
	costing_line_ids = fields.One2many("ax.ch.costing.line",'header_id')

	@api.depends('shipment_id')
	def _get_partners(self):
		for rec in self:
			if rec.shipment_id and rec.shipment_id.partner_ids:
				rec.partner_ids = ','.join([x.name for x in rec.shipment_id.partner_ids])
			else:
				rec.partner_ids = ''

	@api.depends('shipment_id')
	def _get_pos(self):
		for rec in self:
			if rec.shipment_id and rec.shipment_id.po_ids:
				rec.po_ids = ','.join([x.name for x in rec.shipment_id.po_ids])
			else:
				rec.po_ids = ''

	@api.onchange('shipment_id')
	def update_bill(self):
		if self.shipment_id:
			landed_cost_id = self.env['stock.landed.cost'].search([('shipment_id','=',self.shipment_id.id)],order='id desc',limit=1)
			if landed_cost_id.landed_bill_type == 'previous':
				self.bill_id = landed_cost_id.previous_bill_id.id

	def convert_abs(self,amt):
		return abc(amt)

	@api.depends('shipment_id')	
	def get_product_details(self):
		from datetime import date
		for rec in self:
			rec.line_ids = False
			rec.vendor_bill_ids = False
			rec.landed_cost_ids = False
			rec.landed_bill_ids = False
			rec.costing_line_ids = False
			if rec.shipment_id:
				account_ids = self.env['account.move'].search([('shipment_id','=',rec.shipment_id.id),('move_type','=','in_invoice'),('state','=','posted')])
				vendor_bills = []
				landed_bills = []
				vendor_move_ids = []
				landed_move_ids = []
				if account_ids:
					for inv in account_ids:
						for line in inv.invoice_line_ids:
							if line.is_landed_costs_line != True:
								vendor_bills.append(line.move_id.id)
								# vendor_move_ids.append(line)
								price = 0
								# if shipment_id.landed_cost_ids:
								# 	for cost in shipment_id.landed_cost_ids:
								# 		layer_id = self.env['stock.valuation.adjustment.lines'].search([('product_id','=',line.product_id.id),('cost_id','=',cost.id)])
								# 		price_sum += sum([x.final_cost for x in layer_id])
								# 	price = price_sum / line.quantity
								move_id = self.env['stock.move'].search([('purchase_line_id','=',line.purchase_line_id.id)])
								if move_id and move_id.filtered(lambda l:l.picking_id in rec.shipment_id.picking_ids):
									move_id = move_id.filtered(lambda l:l.picking_id in rec.shipment_id.picking_ids)
									if len(move_id) == 1:
										layer_id = self.env['stock.valuation.adjustment.lines'].search([('move_id','=',move_id.id)])
									else:
										layer_id = self.env['stock.valuation.adjustment.lines'].search([('move_id','in',move_id.ids)])
									price = (sum([x.additional_landed_cost for x in layer_id])+line.currency_id._convert(line.price_subtotal, rec.company_id.currency_id, rec.company_id, date.today()))/line.quantity or 0
								vendor_move_ids.append((0,0,{
									'product_id':line.product_id.id,
									'qty':line.quantity,
									'uom_id':line.product_uom_id.id,
									'price_unit':line.price_unit,
									'tax_ids':[(6,0,[x.id for x in line.tax_ids])],
									'price_subtotal':line.price_subtotal,
									'currency_id':line.currency_id.id,
									'account_id':line.move_id.id,
									'date':line.move_id.date,
									'move_line_id':line.id,
									'partner_id':line.move_id.partner_id.id,
									'expected_cost_price':price,
									'expected_purchase_price':price / ((100 - line.product_id.sale_percent)/100),
								}))
								# cost_line_ids = self.env['stock.valuation.adjustment.lines'].search([('product_id','=',line.product_id.id),('move_id','')])
								if layer_id:
									price_subtotal_unsigned = line.currency_id._convert(line.price_subtotal, line.move_id.company_id.currency_id, line.move_id.company_id, line.move_id.date)
									costing_price = (sum([x.additional_landed_cost for x in layer_id])+price_subtotal_unsigned)/line.quantity
									print(line.product_id.default_code,line.price_subtotal,price_subtotal_unsigned,sum([x.additional_landed_cost for x in layer_id]),line.quantity,'$$$$$$$$$$$$$$')
									self.env['ax.ch.costing.line'].create({
										'header_id':rec.id,
										'product_id':line.product_id.id,
										'qty':line.quantity,
										'price_unit':line.price_unit,
										'costing_price':line.company_id.currency_id._convert(costing_price, line.move_id.currency_id, line.move_id.company_id, line.move_id.date),
										'price_subtotal':line.company_id.currency_id._convert((costing_price*line.quantity), line.move_id.currency_id, line.move_id.company_id, line.move_id.date),
										'price_subtotal_unsigned':costing_price*line.quantity,
										'cost_price':costing_price,
										'sale_price':costing_price / ((100 - line.product_id.sale_percent)/100),
										'currency_id':line.currency_id.id,
										'company_currency_id':rec.company_id.currency_id.id,
									})
							else:
								landed_bills.append(line.move_id.id)
								# landed_move_ids.append(line)
								landed_move_ids.append((0,0,{
									'product_id':line.product_id.id,
									'qty':line.quantity,
									'uom_id':line.product_uom_id.id,
									'price_unit':line.price_unit,
									'date':line.move_id.date,
									'tax_ids':[(6,0,[x.id for x in line.tax_ids])],
									# 'price_subtotal':line.currency_id._convert(line.price_subtotal,line.move_id.company_id.currency_id,line.move_id.company_id,line.move_id.invoice_date or date.today()),
									'price_subtotal':line.currency_id._convert(line.amount_currency, line.move_id.company_id.currency_id, line.move_id.company_id, line.move_id.date),
									'currency_id':rec.company_id.currency_id.id,
									'account_id':line.move_id.id,
									'move_line_id':line.id,
									'partner_id':line.move_id.partner_id.id,
								}))
					if vendor_bills and vendor_move_ids:
						vendor_bills = list(set(vendor_bills))
						# rec.line_ids = [(6,0,list(vendor_move_ids))]
						rec.line_ids = vendor_move_ids
						rec.vendor_bill_ids = [(6,0,vendor_bills)]

					if landed_move_ids and landed_bills:
						landed_bills = list(set(landed_bills))
						# rec.landed_cost_ids = [(6,0,list(landed_move_ids))]
						rec.landed_cost_ids = landed_move_ids
						rec.landed_bill_ids = [(6,0,landed_bills)]

	@api.depends('line_ids','line_ids.price_subtotal')
	def _get_vendor_subtotal(self):
		for rec in self:
			if rec.shipment_id and rec.line_ids:
				rec.vendor_subtotal = sum([x.price_subtotal for x in rec.line_ids])
			else:
				rec.vendor_subtotal = 0

	@api.depends('line_ids','line_ids.price_subtotal','vendor_subtotal')
	def _get_vendor_total(self):
		from datetime import date
		for rec in self:
			if rec.shipment_id and rec.line_ids and rec.vendor_subtotal:
				rec.vendor_total = rec.currency_id._convert(rec.vendor_subtotal, rec.company_id.currency_id, rec.company_id, date.today())
			else:
				rec.vendor_total = 0

	@api.depends('landed_cost_ids','landed_cost_ids.price_subtotal')
	def _get_landed_cost_total(self):
		from datetime import date
		for rec in self:
			if rec.shipment_id and rec.landed_cost_ids:
				landed_total = sum([x.price_subtotal for x in rec.landed_cost_ids])
				rec.landed_total = landed_total
			else:
				rec.landed_total = 0

	@api.depends('line_ids','landed_cost_ids','vendor_total','landed_total','shipment_id')
	def get_factor_value(self):
		for rec in self:
			if rec.shipment_id and rec.vendor_total > 0 and rec.landed_total > 0:
				rec.landed_cost_factor = (rec.vendor_total + rec.landed_total) / rec.vendor_total
			else:
				rec.landed_cost_factor = 0

	@api.depends('line_ids','line_ids.currency_id','shipment_id')
	def get_currency(self):
		for rec in self:
			if rec.shipment_id and rec.line_ids:
				currency_id = list(set(rec.line_ids.mapped('currency_id')))
				if currency_id and len(currency_id) == 1:
					rec.currency_id = currency_id[0].id
				else:
					rec.currency_id = rec.company_id.currency_id.id

	def currency_convert(self,amt,rec_id):
		from datetime import date
		if self.company_id.currency_id and amt!=0 and rec_id:
			# value = self.company_id.currency_id.compute(amt,self.currency_id)
			value = self.currency_id._convert(amt, self.company_id.currency_id, self.company_id, rec_id.date or date.today())
			return round(value,6)
		else:
			return round(0,6)

	def currency_inverse_convert(self, amt,rec_id):
		from datetime import date
		if amt!=0 and rec_id:
			value = self.company_id.currency_id._convert(amt, self.currency_id, self.company_id, rec_id.date or date.today())
			return round(value,6)
		else:
			return round(0,6)

	def print_report_values(self):
		return self.env.ref('acc_costing.action_costing_bill_report').report_action(self,config=False)

class AxChCostingProductLine(models.TransientModel):
	_name = "ax.ch.costing.product.line"
	_description = "Costing Products"

	header_id = fields.Many2one('ax.costing.report','Costing Report')
	account_id = fields.Many2one('account.move','Bill')
	move_line_id = fields.Many2one('account.move.line','Bill Line')
	partner_id = fields.Many2one('res.partner','Vendor')
	product_id = fields.Many2one("product.product",'Product')
	qty = fields.Float("Qty",digits=(12,2))
	uom_id = fields.Many2one('uom.uom','UoM')
	price_unit = fields.Float("Price",digits=(12,4))
	tax_ids = fields.Many2many('account.tax','ax_account_tax_costing_rel','tax_id','costing_id','Taxes')
	price_subtotal = fields.Float('Subtotal',digits=(12,2))
	expected_cost_price = fields.Float("Expected Cost Price",digits=(12,2))
	expected_purchase_price = fields.Float("Expected Purchase Price",digits=(12,2))
	currency_id = fields.Many2one('res.currency','Currency')
	date = fields.Date("Bill Date")

class AxChLandedCostLine(models.TransientModel):
	_name = "ax.ch.landed.cost.line"
	_description = "Landed Cost Products"

	header_id = fields.Many2one('ax.costing.report','Costing Report')
	account_id = fields.Many2one('account.move','Bill')
	move_line_id = fields.Many2one('account.move.line','Bill Line')
	product_id = fields.Many2one("product.product",'Product')
	partner_id = fields.Many2one('res.partner','Vendor')
	qty = fields.Float("Qty",digits=(12,2))
	uom_id = fields.Many2one('uom.uom','UoM')
	price_unit = fields.Float("Price",digits=(12,4))
	tax_ids = fields.Many2many('account.tax','ax_account_tax_landed_cost_rel','tax_id','costing_id','Taxes')
	price_subtotal = fields.Float('Subtotal',digits=(12,2))
	currency_id = fields.Many2one('res.currency','Currency')
	date = fields.Date("Bill Date")

class AxChCostingLine(models.TransientModel):
	_name = "ax.ch.costing.line"
	_description = "Landed Cost Lines"

	header_id = fields.Many2one("ax.costing.report")
	product_id = fields.Many2one("product.product",'Product')
	qty = fields.Float("Qty",digits=(12,2))
	price_unit = fields.Float("Price in FC",digits=(12,2))
	costing_price = fields.Float('Landed Cost Price',digits=(12,2))
	price_subtotal = fields.Float("Price Subtotal(FC)",digits=(12,2))
	price_subtotal_unsigned = fields.Float("Price Subtotal",digits=(12,2))
	cost_price = fields.Float("Cost Price",digits=(12,2))
	sale_price = fields.Float("Sale Price",digits=(12,2))
	currency_id = fields.Many2one("res.currency",'Currency')
	company_currency_id = fields.Many2one("res.currency",'Company Currency')
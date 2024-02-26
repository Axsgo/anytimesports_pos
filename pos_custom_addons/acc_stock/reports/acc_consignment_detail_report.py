### import file ###
from odoo import api,models,fields
import time
from odoo.exceptions import UserError

class AccConsignmentDetailReport(models.TransientModel):
	_name = "acc.consignment.detail.report"
	_description = "Consignment Detail Report"

	report_type = fields.Selection([('by_sale','By Sale Order'),('by_product','By Product')],default='by_sale',string="Report Type")
	from_date = fields.Date("From Date")
	to_date = fields.Date("To Date")
	product_id = fields.Many2one("product.product",'Product')
	sale_id = fields.Many2one('sale.order','Sale Order')
	transfer_ids = fields.One2many('acc.consignment.detail.report.transfer','header_id',compute='_get_report_values')
	delivery_ids = fields.One2many('acc.consignment.detail.report.deliver','header_id',compute='_get_report_values')
	invoice_ids = fields.One2many('acc.consignment.detail.report.invoice','header_id',compute='_get_report_values')
	company_id = fields.Many2one('res.company','Company',default=lambda self:self.env.company.id)
	currency_id = fields.Many2one('res.currency','Currency',default=lambda self:self.env.company.currency_id.id)

	@api.onchange('report_type')
	def refresh_data(self):
		self.from_date = False
		self.to_date = False
		self.product_id = False
		self.sale_id = False
	
	@api.depends('sale_id','report_type','product_id','from_date','to_date')
	def _get_report_values(self):
		for rec in self:
			rec.transfer_ids = False
			rec.delivery_ids = False
			rec.invoice_ids = False
			if rec.report_type == 'by_sale':
				if rec.sale_id and rec.sale_id.is_consignment == True and rec.sale_id.company_id == rec.company_id:
					if rec.sale_id.picking_ids:
						for pick in rec.sale_id.picking_ids:
							if pick.is_consignment == True:
								self.env['acc.consignment.detail.report.transfer'].create({
									'header_id':rec.id,
									'sale_id':rec.sale_id.id,
									'picking_id':pick.id,
									'date':pick.date_done,
									'ref_no':pick.ref_no,
									'partner_id':rec.sale_id.partner_id.id,
									'qty':sum([line.quantity_done for line in pick.move_ids_without_package]),
								})
							elif pick.picking_type_id.code == 'outgoing':
								self.env['acc.consignment.detail.report.deliver'].create({
									'header_id':rec.id,
									'sale_id':rec.sale_id.id,
									'picking_id':pick.id,
									'date':pick.date_done,
									'ref_no':pick.ref_no,
									'partner_id':rec.sale_id.partner_id.id,
									'qty':sum([line.quantity_done for line in pick.move_ids_without_package]),
								})
						if rec.sale_id.invoice_ids:
							for inv in rec.sale_id.invoice_ids:
								self.env['acc.consignment.detail.report.invoice'].create({
									'header_id':rec.id,
									'sale_id':rec.sale_id.id,
									'move_id':inv.id,
									'date':inv.invoice_date,
									# 'ref_no':pick.ref_no,
									'partner_id':inv.partner_id.id,
									'qty':sum([line.quantity for line in inv.invoice_line_ids]),
									'amount_total':inv.amount_total,
									'currency_id':inv.currency_id.id,
								})
					else:
						raise UserError("Warning!!, No Consignment Transfer or Delivery available for the selected order.")
			elif rec.report_type == 'by_product':
				domain = []
				if rec.from_date and rec.to_date:
					domain = [('order_id.date_order','>=',rec.from_date),('order_id.date_order','<=',rec.to_date)]
				if rec.product_id:
					domain.append(('product_id','=',rec.product_id.id))
				domain.append(('company_id','=',rec.company_id.id))
				domain.append(('order_id.is_consignment','=',True))
				if domain != [] and rec.from_date and rec.to_date and rec.product_id:
					sale_line_ids = self.env['sale.order.line'].search(domain)
					if sale_line_ids:
						sale_ids = list(set([line.order_id for line in sale_line_ids]))
						if sale_ids:
							for sale in sale_ids:
								if sale.picking_ids:
									for pick in sale.picking_ids:
										if pick.is_consignment == True and pick.state == 'done':
											self.env['acc.consignment.detail.report.transfer'].create({
												'header_id':rec.id,
												'sale_id':sale.id,
												'picking_id':pick.id,
												'date':pick.date_done,
												'ref_no':pick.ref_no,
												'partner_id':rec.sale_id.partner_id.id,
												'qty':sum([line.quantity_done for line in pick.move_ids_without_package]),
												})
										elif pick.picking_type_id.code == 'outgoing' and pick.state == 'done':
											self.env['acc.consignment.detail.report.deliver'].create({
												'header_id':rec.id,
												'sale_id':sale.id,
												'picking_id':pick.id,
												'date':pick.date_done,
												'ref_no':pick.ref_no,
												'partner_id':rec.sale_id.partner_id.id,
												'qty':sum([line.quantity_done for line in pick.move_ids_without_package]),
											})
									if sale.invoice_ids:
										for inv in sale.invoice_ids:
											if inv.state != 'cancel':
												self.env['acc.consignment.detail.report.invoice'].create({
													'header_id':rec.id,
													'sale_id':sale.id,
													'move_id':inv.id,
													'date':inv.invoice_date,
													# 'ref_no':pick.ref_no,
													'partner_id':inv.partner_id.id,
													'qty':sum([line.quantity for line in inv.invoice_line_ids]),
													'amount_total':inv.amount_total,
													'currency_id':inv.currency_id.id,
												})
								else:
									raise UserError("Warning!!, No Consignment Transfer or Delivery available for the selected Product and Date.")
					else:
						raise UserError("Warning!!, No Consignment Sale available for the selected Product and Date.")

	def print_report_values(self):
		return self.env.ref('acc_stock.action_acc_consignment_detail_report_pdf').report_action(self,config=False)

	def get_report_name(self):
		if self.report_type == 'by_sale':
			name = "Consignment Detail Report - %s"%(self.sale_id.name)
		else:
			name = "Consignment Detail Report - %s"%(self.product_id.name)
		return name

class AccConsignmentMove(models.TransientModel):
	_name = "acc.consignment.detail.report.transfer"
	_description = "Consignment Transfer Report"

	header_id = fields.Many2one("acc.consignment.detail.report",'Header')
	sale_id = fields.Many2one('sale.order','Sale')
	picking_id = fields.Many2one('stock.picking','Transfer No.')
	date = fields.Date("Date")
	ref_no = fields.Char("Reference No")
	partner_id = fields.Many2one('res.partner','Customer')
	qty = fields.Float("Delivered Qty",digits=(12,2))

class AccConsignmentDeliver(models.TransientModel):
	_name = "acc.consignment.detail.report.deliver"
	_description = "Consignment DO Report"

	header_id = fields.Many2one("acc.consignment.detail.report",'Header')
	sale_id = fields.Many2one('sale.order','Sale')
	picking_id = fields.Many2one('stock.picking','DO No.')
	date = fields.Date("Date")
	ref_no = fields.Char("Reference No")
	partner_id = fields.Many2one('res.partner','Customer')
	qty = fields.Float("Used Qty",digits=(12,2))

class AccConsignmentInvoice(models.TransientModel):
	_name = "acc.consignment.detail.report.invoice"
	_description = "Consignment Invoice Report"

	header_id = fields.Many2one("acc.consignment.detail.report",'Header')
	sale_id = fields.Many2one('sale.order','Sale')
	move_id = fields.Many2one('account.move','Invoice No.')
	date = fields.Date("Date")
	# ref_no = fields.Char("Reference No")
	partner_id = fields.Many2one('res.partner','Customer')
	qty = fields.Float("Invoice Qty",digits=(12,2))
	amount_total = fields.Monetary("Amount Total")
	currency_id = fields.Many2one('res.currency','Currency')
### import file ###
from odoo import api,models,fields
import time
from odoo.exceptions import UserError

class AccConsignmentReport(models.TransientModel):
	_name = "acc.consignment.report"
	_description = "Consignment Stock Report"

	partner_id = fields.Many2one('res.partner','Customer')
	from_date = fields.Date("From Date")
	to_date = fields.Date("To Date")
	user_id = fields.Many2one('res.users','SalesPerson')
	sale_id = fields.Many2one('sale.order','Sale Order')
	product_id = fields.Many2one('product.product','Product')
	# state = fields.Selection([('draft','Draft'),('confirmed','Waiting'),('assigned','Ready'),('done','Done'),('cancel','Cancelled')],string='Status')
	# employee_id = fields.Many2one('hr.employee','Driver')
	report_ids = fields.One2many('acc.consignment.report.line','header_id',compute='_get_report_values')
	company_id = fields.Many2one('res.company','Company',default=lambda self:self.env.company.id)
	currency_id = fields.Many2one('res.currency','Currency',default=lambda self:self.env.company.currency_id.id)

	@api.depends('from_date','to_date','partner_id','user_id','company_id','sale_id','product_id')
	def _get_report_values(self):
		for rec in self:
			domain = []
			rec.report_ids = False
			if rec.from_date and rec.to_date:
				domain = [('picking_id.date_done','>=',rec.from_date),('picking_id.date_done','<=',rec.to_date)]
			if rec.partner_id:
				domain.append(('picking_id.partner_id','=',rec.partner_id.id))
			if rec.sale_id:
				domain.append(('picking_id.sale_id','=',rec.sale_id.id))
			if rec.user_id:
				domain.append(('picking_id.user_id','=',rec.user_id.id))
			if rec.product_id:
				domain.append(('product_id','=',rec.product_id.id))
			# if rec.employee_id:
			# 	domain.append(('employee_id','=',rec.employee_id.id))
			domain.append(('company_id','=',rec.company_id.id))
			# domain.append(('picking_type_code','=','outgoing'))
			domain.append(('picking_id.is_consignment','=',True))
			if domain != [] and rec.from_date and rec.to_date:
				move_ids = self.env['stock.move'].search(domain)
				if move_ids:
					for line in move_ids:
						self.env['acc.consignment.report.line'].create({
							'header_id':rec.id,
							'sale_id':line.picking_id.sale_id.id,
							'product_id':line.product_id.id,
							'picking_id':line.picking_id.id,
							'date':line.picking_id.date_done,
							'partner_id':line.picking_id.partner_id.id,
							'order_qty':line.product_uom_qty,
							'qty':line.quantity_done,
							# 'used_qty': used_qty,
							# 'bal_qty':line.quantity_done - used_qty,
							'user_id':line.picking_id.user_id.id,
							# 'employee_id':line.employee_id.id,
							# 'pick_date':line.pick_datetime,
						})
				else:
					rec.report_ids = False
					raise UserError("Warning!!, No Date available.")
			else:
				rec.report_ids = False

	def print_report_values(self):
		return self.env.ref('acc_stock.action_acc_consignment_report_pdf').report_action(self,config=False)

	def get_report_name(self):
		if self.partner_id:
			name = 'Consignment Stock Report - %s'%(self.partner_id.name)
		else:
			name = 'Consignment Stock Report'
		return name

class AccPickingReportLine(models.TransientModel):
	_name = "acc.consignment.report.line"
	_description = "Consignment Stock Report Line"

	header_id = fields.Many2one('acc.consignment.report','Header')
	sale_id = fields.Many2one('sale.order','Sale No.')
	product_id = fields.Many2one('product.product','Product')
	picking_id = fields.Many2one('stock.picking','Delivery No.')
	date = fields.Date('Date')
	partner_id = fields.Many2one('res.partner','Customer')
	order_qty = fields.Float("Ordered Qty",digits=(12,2))
	qty = fields.Float("Delivered Qty",digits=(12,2))
	used_qty = fields.Float("Used Qty",digits=(12,2),compute='_get_used_qty')
	bal_qty = fields.Float("Balance Qty",digits=(12,2),compute='_get_bal_qty')
	user_id = fields.Many2one('res.users','SalesPerson')
	# employee_id = fields.Many2one('hr.employee','Driver')
	# pick_date = fields.Datetime('Picked Datetime')
	company_id = fields.Many2one('res.company','Company',related='picking_id.company_id',store=True)

	@api.depends('sale_id','product_id')
	def _get_used_qty(self):
		for rec in self:
			if rec.sale_id and rec.sale_id.picking_ids:
				for pick in rec.sale_id.picking_ids:
					if pick.picking_type_id.code == 'outgoing':
						rec.used_qty = sum([line.product_qty for line in pick.move_ids_without_package])
			else:
				rec.used_qty = 0

	@api.depends('qty','used_qty')
	def _get_bal_qty(self):
		for rec in self:
			if rec.qty > 0 and rec.used_qty > 0:
				rec.bal_qty = rec.qty - rec.used_qty
			else:
				rec.bal_qty = 0
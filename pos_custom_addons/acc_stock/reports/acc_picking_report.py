### import file ###
from odoo import api,models,fields
from odoo.exceptions import UserError

class AccPickingReport(models.TransientModel):
	_name = "acc.picking.report"
	_description = "Stock Picking Report"

	partner_id = fields.Many2one('res.partner','Customer')
	from_date = fields.Date("From Date")
	to_date = fields.Date("To Date")
	user_id = fields.Many2one('res.users','SalesPerson')
	state = fields.Selection([('draft','Draft'),('confirmed','Waiting'),('assigned','Ready'),('done','Done'),('cancel','Cancelled')],string='Status')
	driver_id = fields.Many2one('res.users','Driver')
	report_ids = fields.One2many('acc.picking.report.line','header_id',compute='_get_report_values')
	company_id = fields.Many2one('res.company','Company',default=lambda self:self.env.company.id)
	currency_id = fields.Many2one('res.currency','Currency',default=lambda self:self.env.company.currency_id.id)
	delivery_type = fields.Selection([('delivery','Delivery Orders'),('direct','Direct Delivery Orders'),('grn','GRN')],string='Type',default='delivery')

	@api.depends('from_date','to_date','partner_id','user_id','driver_id','company_id','state','delivery_type')
	def _get_report_values(self):
		for rec in self:
			domain = []
			rec.report_ids = False
			if rec.from_date and rec.to_date:
				domain = [('date_done','>=',rec.from_date),('date_done','<=',rec.to_date)]
			if rec.partner_id:
				domain.append(('partner_id','=',rec.partner_id.id))
			if rec.state:
				domain.append(('state','=',rec.state))
			if rec.user_id:
				domain.append(('user_id','=',rec.user_id.id))
			if rec.driver_id:
				domain.append(('driver_id','=',rec.driver_id.id))
			domain.append(('company_id','=',rec.company_id.id))
			if rec.delivery_type:
				if rec.delivery_type == 'delivery':
					domain = [('picking_type_code','=','outgoing'),('is_consignment','!=',True),('is_direct_delivery','=',False)]
				if rec.delivery_type == 'direct':
					domain = [('picking_type_code','=','outgoing'),('is_consignment','!=',True),('is_direct_delivery','=',True)]
				if rec.delivery_type == 'grn':
					domain = [('picking_type_code','=','incoming'),('is_consignment','!=',True)]

			if domain != [] and rec.from_date and rec.to_date:
				picking_ids = self.env['stock.picking'].search(domain)
				if picking_ids:
					for line in picking_ids:
						self.env['acc.picking.report.line'].create({
							'header_id':rec.id,
							'picking_id':line.id,
							'date':line.date_done,
							'partner_id':line.partner_id.id,
							'order_qty':sum([pick.product_uom_qty for pick in line.move_ids_without_package]),
							'qty':sum([pick.quantity_done for pick in line.move_ids_without_package]),
							'user_id':line.user_id.id,
							'driver_id':line.driver_id.id,
							'pick_date':line.pick_datetime,
						})
				else:
					rec.report_ids = False
			else:
				rec.report_ids = False

	def print_report_values(self):
		return self.env.ref('acc_stock.action_acc_picking_report_pdf').report_action(self,config=False)

	def get_report_name(self):
		if self.partner_id:
			name = 'Delivery/GRN Report - %s'%(self.partner_id.name)
		else:
			name = 'Delivery/GRN Report'
		return name

class AccPickingReportLine(models.TransientModel):
	_name = "acc.picking.report.line"
	_description = "Stock Picking Report Line"

	header_id = fields.Many2one('acc.picking.report','Header')
	picking_id = fields.Many2one('stock.picking','Delivery No')
	date = fields.Date('Date')
	partner_id = fields.Many2one('res.partner','Customer')
	order_qty = fields.Float("Ordered Qty",digits=(12,2))
	qty = fields.Float("Delivered Qty",digits=(12,2))
	user_id = fields.Many2one('res.users','SalesPerson')
	driver_id = fields.Many2one('res.users','Driver')
	pick_date = fields.Datetime('Picked Datetime')
	company_id = fields.Many2one('res.company','Company',related='picking_id.company_id',store=True)
	# currency_id = fields.Many2one('res.currency','Currency',related='picking_id.currency_id',store=True)
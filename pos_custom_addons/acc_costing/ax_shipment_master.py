### import file ###
from odoo import api,models,fields
from odoo.exceptions import UserError
import time

class AxShipment(models.Model):
	_name = "ax.shipment.master"
	_description = "Shipment No"
	_order = "crt_date desc, id desc"
	_inherit = ['mail.thread', 'mail.activity.mixin']

	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('ax.shipment.master')
		return super(AxShipment, self).create(vals)

	def write(self, vals):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
		return super(AxShipment, self).write(vals)

	def name_get(self):
		res = []
		for field in self:
			if field.description:
				res.append((field.id, '%s - %s' %(field.name,field.description)))
			else:
				res.append((field.id, '%s' %(field.name)))
		return res

	def currency_convert(self,po,date=None):
		return po.currency_id._convert(
				po.amount_untaxed, po.company_id.currency_id,
				po.company_id or self.env.company, date or fields.Date.today())

	@api.depends('bill_ids')
	def _get_po_amount(self):
		for rec in self:
			if rec.bill_ids:
				rec.vendor_amount_total = sum([abs(line.amount_total_signed) for line in rec.bill_ids])
			elif rec.po_ids:
				rec.vendor_amount_total = sum([abs(line.amount_total_signed) for line in rec.po_ids])
			else:
				rec.vendor_amount_total = 0

	@api.depends('cost_bill_ids')
	def _get_clearance_bill_amount(self):
		for rec in self:
			if rec.cost_bill_ids:
				rec.landed_amount_total = sum([rec.currency_convert(line,line.invoice_date) for line in rec.cost_bill_ids])
			else:
				rec.landed_amount_total = 0

	name = fields.Char("Shipment No")
	description = fields.Char("Description")
	date = fields.Date("Shipment Date",default=fields.Date.today)
	partner_ids = fields.Many2many('res.partner','acc_partner_shipment_rel','shipment_id','partner_id','Vendor')
	landed_partner_id = fields.Many2many("res.partner",'acc_clearance_partner_shipment_rel','shipment_id','partner_id','Clearance Vendor')
	po_ids = fields.Many2many("purchase.order",'acc_purchase_shipment_rel','shipment_id','purchase_id',"PO's")
	po_name = fields.Char("PO's",compute='_get_names')
	partner_name = fields.Char("Vendor's",compute='_get_names')
	landed_partner_name = fields.Char("Clearance Vendor's",compute='_get_names')
	po_count = fields.Integer("PO Count",compute='_get_po_details')
	picking_count = fields.Integer("GRN Count",compute='_get_grn_bill_details')
	bill_count = fields.Integer("Supplier Bill Count",compute='_get_grn_bill_details')
	costing_bill_count = fields.Integer("Costing Bill Count",compute='_get_costing_bill_count')
	landed_cost_count = fields.Integer("Landed Cost Count",compute='_get_landed_cost_count')
	# product_ids = fields.Many2many('product.product','ax_shipment_product_rel','product_id','shipment_id','Products',compute="_get_products")
	picking_ids = fields.Many2many('stock.picking','ax_shipment_picking_rel','picking_id','shipment_id','GRN',compute="_get_grn_bill_details")
	bill_ids = fields.Many2many('account.move','ax_shipment_bill_rel','bill_id','shipment_id','Bills',compute="_get_grn_bill_details")
	cost_bill_ids = fields.Many2many('account.move','ax_shipment_cost_bill_rel','bill_id','shipment_id','Costing Bills',compute="_get_costing_bill_count")
	landed_cost_ids = fields.Many2many('stock.landed.cost','acc_shipment_landed_cost_rel','landed_cost_id','shipment_id','Landed Costing',compute='_get_landed_cost_count')
	is_show_landed_cost = fields.Boolean('Show Landed Cost',compute='_show_landed_cost')
	# ship_bill_ids = fields.Many2many('account.move','ax_shipment_cost_bill_rel','bill_id','shipment_id','Shipment Cost Bills',compute="_get_ship_bill_details")
	notes = fields.Text("Notes")
	is_costing_done = fields.Boolean("Costing Done",default=False)
	shipment_type = fields.Selection([('fcl','FCL (Full Container Load)'),('lcl','LCL (Less than Container Load)')],default='fcl',string='Shipment Type')
	gross_weight = fields.Float("Gross Weight[Kg]",digits=(12,3))
	net_weight = fields.Float("Net Weight[Kg]",digits=(12,3))
	pallet_count = fields.Integer("No. of Pallets")
	dimensions = fields.Char("Dimensions")
	pallet_type = fields.Selection([('20',"20'"),('40',"40'")],'Container Size')
	# packing_ids = fields.One2many('ax.ch.packing.list','header_id','Packing List')
	attachment_ids = fields.Many2many('ir.attachment','res_shipment_attachment_rel','shipment_id','attachment_id','Attachments')
	# stage = fields.Selection([('po_done','PO Done'),('grn_done','GRN Done'),('clearance_bill_done','Clearance Bill Done'),
	# 	('supplier_bill_done','Supplier Bill Done'),('costing_done','Costing Done')],'Shipment Stage',compute='_get_shipment_stage',store=True)
	picking_state = fields.Selection([('open','Pending'),('close','Completed')],'GRN Status',compute='_update_picking_state',store=True)
	po_state = fields.Selection([('open','Pending'),('close','Completed')],'Bill Creation Status',compute='_update_po_state',store=True)
	bill_state = fields.Selection([('open','Pending'),('close','Completed')],'Supplier Bill Status',compute='_update_bill_state',store=True)
	clearance_bill_state = fields.Selection([('open','Pending'),('close','Completed')],'Clearance Bill Status',compute='_update_clearance_bill_state',store=True)
	costing_state = fields.Selection([('open','Pending'),('close','Completed')],'Landed Costing Status',compute='_update_costing_state',store=True)
	company_id = fields.Many2one('res.company','Company',default=lambda self:self.env.company.id)
	costing_attach_id = fields.Many2one('ir.attachment','Costing Report Attachment')
	costing_report_pdf = fields.Binary('Costing Report',related='costing_attach_id.datas')
	costing_report_filename = fields.Char("Costing Report Filename",related='costing_attach_id.name')
	estimation_ids = fields.One2many('acc.shipment.estimation.line','header_id')
	landed_amount_total = fields.Float("Clearance Bill Total",digits=(12,2),compute='_get_clearance_bill_amount')
	vendor_amount_total = fields.Float("PO Total",digits=(12,2),compute='_get_po_amount')
	landed_cost_factor = fields.Float('Factor Value',digits=(12,6),compute="get_factor_value")
	currency_id = fields.Many2one('res.currency','Currency',compute='_get_currency')
	po_grn_ids = fields.Many2many('stock.picking','acc_grn_shipment_rel','picking_id','shipment_id','GRN')
	po_bill_ids = fields.Many2many('account.move','acc_po_bill_shipment_rel','bill_id','shipment_id','Bills')
	po_bills = fields.Many2many('account.move','acc_po_bill_shipment_id_rel','bill_id','shipment_id','Bills',compute='_get_po_details')
	po_grn = fields.Many2many('stock.picking','acc_grn_shipment_id_rel','picking_id','shipment_id','GRN',compute='_get_po_details')
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
	confirm_date = fields.Datetime('Confirmed Date', readonly = True)
	confirm_user_id = fields.Many2one(
	'res.users', 'Confirmed By', readonly = True)
	ap_rej_date = fields.Datetime('Approved Date', readonly = True)
	ap_rej_user_id = fields.Many2one(
	'res.users', 'Approved By', readonly = True)
	cancel_date = fields.Datetime('Cancelled Date', readonly = True)
	cancel_user_id = fields.Many2one(
	'res.users', 'Cancelled By', readonly = True)
	state = fields.Selection([('draft','Draft'),('approved','Approved'),('cancel','Cancelled')],default='draft',string="Status")
	shipment_state = fields.Selection([('draft','Draft'),('grn','GRN In Progress'),('bill','Supplier Bill In Progress'),
		('clearance_bill','Clearance Bill In Progress'),('landed_costing','Landed Costing In Progress'),
		('done','Fully Completed')],compute='_get_costing_state',string="Status",store=True)
	status = fields.Selection([('draft','Draft'),('grn','GRN In Progress'),('bill','Supplier Bill In Progress'),
		('clearance_bill','Clearance Bill In Progress'),('landed_costing','Landed Costing In Progress'),
		('done','Fully Completed')],compute='_get_costing_status',store=True,string="Shipment Progress Status")
	progress_bar = fields.Integer("Progress Bar",compute='_get_progress_value')

	def unlink(self):
		""" Unlink """
		for rec in self:
			if rec.state not in ('draft','cancel'):
				raise UserError('Warning!, You can not delete this entry !!')
			else:
				return super(AxShipment, self).unlink()

	@api.depends('po_ids')
	def _get_currency(self):
		for rec in self:
			if rec.po_ids:
				rec.currency_id = rec.po_ids[0].currency_id.id
			else:
				rec.currency_id = rec.company_id.currency_id.id

	@api.onchange("partner_ids",'date')
	def update_description(self):
		self.description = ''
		self.po_ids = False
		self.po_grn_ids = False
		self.po_bill_ids = False
		if self.partner_ids and self.date:
			self.description = self.date.strftime("%d%b")
			self.description = self.description + ' - ' + ', '.join([x.name.split()[0] for x in self.partner_ids])

	# @api.constrains('po_ids')
	# def duplicate_name_contrains(self):
	# 	if self.po_ids:
	# 		self.env.cr.execute(""" select po_id from ax_shipment_master where po_id  = '%s' and id != '%s' and state != 'cancel'""" %(self.po_id.id,self.id))
	# 		data = self.env.cr.dictfetchall()
	# 		if data:
	# 			raise UserError("Warning!!, Shipment already created for this PO!")

	@api.onchange('po_ids')
	def onchange_po_ids(self):
		self.po_bill_ids = False
		self.po_grn_ids = False
		if self.po_ids and len(self.po_ids.mapped('currency_id')) > 1:
			raise UserError("Warning!!, Select PO's with same Currency.")

	@api.depends('po_ids')
	def _get_products(self):
		for rec in self:
			if rec.po_ids:
				for po in rec.po_ids:
					rec.product_ids = [(6,0,[line.product_id.id for line in po.order_line])]
			else:
				rec.product_ids = False

	@api.depends('po_ids','partner_ids','landed_partner_id')
	def _get_names(self):
		for rec in self:
			rec.po_name = ''
			rec.partner_name = ''
			rec.landed_partner_name = ''
			if rec.po_ids:
				rec.po_name = ', '.join([x.name for x in rec.po_ids])
			if rec.partner_ids:
				rec.partner_name = ', '.join([x.name for x in rec.partner_ids])
			if rec.landed_partner_id:
				rec.landed_partner_name = ', '.join([x.name for x in rec.landed_partner_id])

	@api.depends('po_ids')
	def _get_po_details(self):
		for rec in self:
			if rec.po_ids:
				# rec.picking_ids = [(6,0,[line.id for po in rec.po_ids for line in po.picking_ids if line.state == 'done'])]
				# rec.bill_ids = [(6,0,[line.id for po in rec.po_ids for line in po.invoice_ids if line.state == 'posted'])]
				rec.po_grn = [(6,0,[line.id for po in rec.po_ids for line in po.picking_ids if line.state == 'done' and not line.shipment_id])]
				rec.po_bills = [(6,0,[line.id for po in rec.po_ids for line in po.invoice_ids if line.state == 'posted' and not line.shipment_id])]
				rec.po_count = len(rec.po_ids)
				# rec.picking_count = len([line.id for po in rec.po_ids for line in po.picking_ids if line.state != 'cancel'])
				# rec.bill_count = len(rec.bill_ids)
			else:
				# rec.picking_ids = False
				# rec.bill_ids = False
				rec.po_bills = False
				rec.po_grn = False
				rec.po_count = 0
				# rec.picking_count = 0
				# rec.bill_count = 0

	@api.depends('po_bill_ids','po_grn_ids')
	def _get_grn_bill_details(self):
		for rec in self:
			if rec.po_bill_ids:
				rec.bill_ids = [(6,0,rec.po_bill_ids.ids)]
				rec.bill_count = len(rec.po_bill_ids)
			else:
				rec.bill_ids = False
				rec.bill_count = 0
			if rec.po_grn_ids:
				rec.picking_ids = [(6,0,rec.po_grn_ids.ids)]
				rec.picking_count = len(rec.po_grn_ids)
			else:
				rec.picking_ids = False
				rec.picking_count = 0

	def _get_costing_bill_count(self):
		for rec in self:
			cost_bill_ids = self.env['account.move'].search([('shipment_id','=',rec.id),('is_landed_cost_bill','=',True)])
			if cost_bill_ids:
				rec.cost_bill_ids = [(6,0,cost_bill_ids.ids)]
				rec.costing_bill_count = len(cost_bill_ids)
				rec._update_clearance_bill_state()
			else:
				rec.cost_bill_ids = False
				rec.costing_bill_count = 0

	def _get_landed_cost_count(self):
		for rec in self:
			landed_cost_ids = self.env['stock.landed.cost'].search([('shipment_id','=',rec.id)])
			if landed_cost_ids:
				rec.landed_cost_ids = [(6,0,landed_cost_ids.ids)]
				rec.landed_cost_count = len(landed_cost_ids)
			else:
				rec.landed_cost_ids = False
				rec.landed_cost_count = 0

	@api.depends('po_ids','cost_bill_ids')
	def _show_landed_cost(self):
		for rec in self:
			if rec.po_ids:
				if ((sum([line.qty_invoiced for po in rec.po_ids for line in po.order_line]) ==
					sum([line.qty_received for po in rec.po_ids for line in po.order_line])) and
					(len(rec.cost_bill_ids) >= len(rec.landed_partner_id))):
					rec.is_show_landed_cost = True
				else:
					rec.is_show_landed_cost = False
			else:
				rec.is_show_landed_cost = False

	@api.depends('picking_ids','picking_count')
	def _update_picking_state(self):
		for rec in self:
			if rec.picking_count > 0 and rec.picking_ids:
				if rec.picking_count == len(rec.picking_ids):
					rec.picking_state = 'close'
				else:
					rec.picking_state = 'open'
			else:
				rec.picking_state = 'open'

	@api.depends('po_ids','picking_state')
	def _update_po_state(self):
		for rec in self:
			if rec.po_ids:
				if all([line.invoice_status == 'invoiced' for line in rec.po_ids]) and rec.picking_state == 'close':
					rec.po_state = 'close'
				else:
					rec.po_state = 'open'
			else:
				rec.po_state = 'open'

	@api.depends('bill_ids','bill_count','po_state')
	def _update_bill_state(self):
		for rec in self:
			if rec.bill_count > 0 and rec.bill_ids and rec.po_state == 'close':
				if rec.bill_count == len(rec.bill_ids):
					rec.bill_state = 'close'
				else:
					rec.bill_state = 'open'
			else:
				rec.bill_state = 'open'

	@api.depends('landed_partner_id','cost_bill_ids','bill_state','costing_bill_count')
	def _update_clearance_bill_state(self):
		for rec in self:
			if rec.cost_bill_ids and rec.landed_partner_id:
				if len([line.id for line in rec.cost_bill_ids if line.state == 'posted']) >= len(rec.landed_partner_id):
					rec.clearance_bill_state = 'close'
				else:
					rec.clearance_bill_state = 'open'
			else:
				rec.clearance_bill_state = 'open'

	@api.depends('landed_cost_count','clearance_bill_state','landed_cost_ids')
	def _update_costing_state(self):
		for rec in self:
			if rec.landed_cost_ids and rec.clearance_bill_state == 'close':
				if len(rec.landed_cost_ids) == 1 and rec.landed_cost_ids.state == 'done':
					rec.costing_state = 'close'
				elif len(rec.landed_cost_ids) > 1 and all([line.state == 'done' for line in rec.landed_cost_ids]):
					rec.costing_state = 'close'
				else:
					rec.costing_state = 'open'
			else:
				rec.costing_state = 'open'

	@api.depends('picking_state','po_state','bill_state','clearance_bill_state','costing_state')
	def _get_costing_state(self):
		for rec in self:
			rec.shipment_state = 'draft'
			if rec.picking_state == 'open':
				rec.shipment_state = 'grn'
			elif rec.picking_state == 'close' and (rec.po_state == 'open' or rec.bill_state == 'open'):
				rec.shipment_state = 'bill'
			elif rec.po_state == 'close' and rec.bill_state == 'close' and rec.clearance_bill_state == 'open':
				rec.shipment_state = 'clearance_bill'
			elif rec.clearance_bill_state == 'close' and rec.costing_state == 'open':
				rec.shipment_state = 'landed_costing'
			elif (rec.picking_state == 'close' and rec.po_state == 'close' and rec.bill_state == 'close' and rec.clearance_bill_state == 'close' and rec.costing_state == 'close'):
				rec.shipment_state = 'done'

	@api.depends('shipment_state')
	def _get_costing_status(self):
		for rec in self:
			if rec.shipment_state:
				rec.status = rec.shipment_state
			else:
				rec.status = 'draft'

	@api.depends('shipment_state','state')
	def _get_progress_value(self):
		for rec in self:
			rec.progress_bar = 0
			if rec.state:
				if rec.state == 'draft':
					rec.progress_bar = 0
				elif rec.state == 'approved':
					if rec.shipment_state == 'draft':
						rec.progress_bar = 10
					elif rec.shipment_state == 'grn':
						rec.progress_bar = 20
					elif rec.shipment_state == 'bill':
						rec.progress_bar = 40
					elif rec.shipment_state == 'clearance_bill':
						rec.progress_bar = 60
					elif rec.shipment_state == 'landed_costing':
						rec.progress_bar = 80
					elif rec.shipment_state == 'done':
						rec.progress_bar = 100
				else:
					rec.progress_bar = 0

	def action_view_po(self):
		if self.po_ids:
			if len(self.po_ids) == 1:
				view = self.env.ref('purchase.purchase_order_form')
				return {
					'name': 'Purchase Order',
					'type': 'ir.actions.act_window',
					'view_mode': 'form',
					'res_model': 'purchase.order',
					'views': [(view.id, 'form')],
					'view_id': view.id,
					'target': 'current',
					'res_id': self.po_ids.id,
				}
			else:
				tree_id = self.env.ref('purchase.purchase_order_view_tree')
				form_id = self.env.ref('purchase.purchase_order_form')
				return {
					'name': 'Purchase Order',
					'type': 'ir.actions.act_window',
					'view_mode': 'tree',
					'res_model': 'purchase.order',
					'views': [(tree_id.id, 'tree'),(form_id.id, 'form')],
					'view_id': tree_id.id,
					'target': 'current',
					'domain': [('id','in',self.po_ids.ids)],
				}

	def action_view_picking(self):
		picking_ids = [line.id for po in self.po_ids for line in po.picking_ids if line.state != 'cancel']
		if picking_ids:
			if len(picking_ids) == 1:
				view = self.env.ref('stock.view_picking_form')
				return {
					'name': 'GRN/Receipts',
					'type': 'ir.actions.act_window',
					'view_mode': 'form',
					'res_model': 'stock.picking',
					'views': [(view.id, 'form')],
					'view_id': view.id,
					'target': 'current',
					'res_id': picking_ids[0],
				}
			else:
				tree_id = self.env.ref('stock.vpicktree')
				form_id = self.env.ref('stock.view_picking_form')
				return {
					'name': 'GRN/Receipts',
					'type': 'ir.actions.act_window',
					'view_mode': 'tree',
					'res_model': 'stock.picking',
					'views': [(tree_id.id, 'tree'),(form_id.id, 'form')],
					'view_id': tree_id.id,
					'target': 'current',
					'domain': [('id','in',picking_ids)],
				}

	def action_view_costing_bill(self):
		if self.cost_bill_ids:
			if len(self.cost_bill_ids) == 1:
				view = self.env.ref('account.view_move_form')
				return {
					'name': 'Costing Bills',
					'type': 'ir.actions.act_window',
					'view_mode': 'form',
					'res_model': 'account.move',
					'views': [(view.id, 'form')],
					'view_id': view.id,
					'target': 'current',
					'res_id': self.cost_bill_ids.id,
				}
			else:
				tree_id = self.env.ref('acc_costing.view_costing_bill_tree')
				form_id = self.env.ref('account.view_move_form')
				return {
					'name': 'Costing Bills',
					'type': 'ir.actions.act_window',
					'view_mode': 'tree',
					'res_model': 'account.move',
					'views': [(tree_id.id, 'tree'),(form_id.id, 'form')],
					'view_id': tree_id.id,
					'target': 'current',
					'domain': [('id','in',self.cost_bill_ids.ids)],
				}

	def action_view_invoice(self):
		if self.bill_ids:
			if len(self.bill_ids) == 1:
				view = self.env.ref('account.view_move_form')
				return {
					'name': 'Supplier Bills',
					'type': 'ir.actions.act_window',
					'view_mode': 'form',
					'res_model': 'account.move',
					'views': [(view.id, 'form')],
					'view_id': view.id,
					'target': 'current',
					'res_id': self.bill_ids.id,
				}
			else:
				tree_id = self.env.ref('account.view_in_invoice_tree')
				form_id = self.env.ref('account.view_move_form')
				return {
					'name': 'Supplier Bills',
					'type': 'ir.actions.act_window',
					'view_mode': 'tree',
					'res_model': 'account.move',
					'views': [(tree_id.id, 'tree'),(form_id.id, 'form')],
					'view_id': tree_id.id,
					'target': 'current',
					'domain': [('id','in',self.bill_ids.ids)],
				}

	def action_view_landed_cost(self):
		if not self.landed_cost_ids:
			if not self.bill_ids:
				raise UserError("Warning!!, Kindly add Supplier Bills for this Shipment.")
			elif self.bill_ids and any([x.state!='posted' for x in self.bill_ids]):
				raise UserError("Warning!!, Kindly Confirm the Supplier Bills before Costing.")
			if not self.cost_bill_ids:
				raise UserError("Warning!!, Clearance Bills not found for this Shipment.")
			elif self.cost_bill_ids and any([x.state!='posted' for x in self.cost_bill_ids]):
				raise UserError("Warning!!, Kindly Confirm the Costing Bills before Costing.")
			if not self.picking_ids:
				raise ("Warning!!, Kindly add GRN for this Shipment.")
			elif self.picking_ids and any([x.state!='done' for x in self.picking_ids]):
				raise UserError("Warning!!, Kindly Validate the GRN before Costing.")
			view = self.env.ref('stock_landed_costs.view_stock_landed_cost_form')
			return {
				'name': 'Landed Costing',
				'type': 'ir.actions.act_window',
				'view_mode': 'form',
				'res_model': 'stock.landed.cost',
				'views': [(view.id, 'form')],
				'view_id': view.id,
				'target': 'current',
				'context': {'default_shipment_id':self.id}
			}
		elif self.landed_cost_ids:
			if len(self.landed_cost_ids) == 1:
				view = self.env.ref('stock_landed_costs.view_stock_landed_cost_form')
				return {
					'name': 'Landed Costing',
					'type': 'ir.actions.act_window',
					'view_mode': 'form',
					'res_model': 'stock.landed.cost',
					'views': [(view.id, 'form')],
					'view_id': view.id,
					'target': 'current',
					'res_id': self.landed_cost_ids.id,
				}
			else:
				tree_id = self.env.ref('stock_landed_costs.view_stock_landed_cost_tree')
				form_id = self.env.ref('stock_landed_costs.view_stock_landed_cost_form')
				return {
					'name': 'Landed Costing',
					'type': 'ir.actions.act_window',
					'view_mode': 'tree',
					'res_model': 'stock.landed.cost',
					'views': [(tree_id.id, 'tree'),(form_id.id, 'form')],
					'view_id': tree_id.id,
					'target': 'current',
					'domain': [('id','in',self.landed_cost_ids.ids)],
				}

	def entry_approve(self):
		if self.state == 'draft':
			# if not self.landed_partner_id:
			# 	raise UserError("Warning!!, Kindly select Clearance Vendor")
			# if not self.packing_ids:
			# 	raise UserError("Warning!!, Kindly provide Packing List Details")
			if self.shipment_type == 'lcl':
				if self.pallet_count <= 0:
					raise UserError("Warning!!, No. of Pallets value should be greater than Zero.")
			if self.gross_weight <= 0 or self.net_weight <= 0:
				raise UserError("Warning!!, Gross Weight and Net Weight value should be greater than Zero.")
			self.po_ids.is_shipment_done = True
			self.write({'state':'approved',
						'ap_rej_user_id': self.env.user.id,
						'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})

	def entry_draft(self):
		if self.state == 'approved':
			if self.is_costing_done == False:
				self.po_ids.is_shipment_done = False
				self.write({'state':'draft'})
			else:
				raise UserError("Warning!!, You cannot able to change the state to Draft after Costing completed.")


	def entry_cancel(self):
		self.write({'state':'cancel',
					'cancel_user_id': self.env.user.id,
					'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})

	def entry_get_report(self):
		if self.is_costing_done == True:
			import base64
			wizard_id = self.env['ax.costing.report'].create({'shipment_id':self.id,'currency_id':self.currency_id.id})
			pdf = self.env.ref('acc_costing.action_costing_bill_report')._render_qweb_pdf(wizard_id.id)
			b64_pdf = base64.b64encode(pdf[0])
			name = 'Costing Report - %s'%(self.name)
			attach_id = self.env['ir.attachment'].create({
				'name': name,
				'type': 'binary',
				'datas': b64_pdf,
				# 'datas_fname': name + '.pdf',
				'store_fname': name,
				'res_model': self._name,
				'res_id': self.id,
				'mimetype': 'application/x-pdf'
			})
			self.costing_attach_id = attach_id.id

	@api.depends('vendor_amount_total','landed_amount_total')
	def get_factor_value(self):
		for rec in self:
			if rec.vendor_amount_total > 0 and rec.landed_amount_total > 0:
				rec.landed_cost_factor = (rec.vendor_amount_total + rec.landed_amount_total) / rec.vendor_amount_total
			else:
				rec.landed_cost_factor = 0

	def compute_estimation(self):
		self.estimation_ids = False
		if self.picking_ids and self.cost_bill_ids and self.landed_cost_factor > 0:
			# landed_cost_factor = self.po_ids[0].currency_id._convert(
			# 		self.landed_cost_factor,
			# 		self.company_id.currency_id,
			# 		self.company_id,
			# 		self.date or fields.Date.today(),
			# 	)
			for po in self.picking_ids:
				for line in po.move_ids_without_package:
					if line.quantity_done > 0:
						# stock_quant_ids = self.env['stock.quant'].search([('product_id','=',line.product_id.id),('company_id','=',self.company_id.id)])
						# price = line.product_id.standard_price
						# if stock_quant_ids:
						# stock_price = sum([x.value for x in stock_quant_ids])
						price = 0
						if line.product_uom == line.purchase_line_id.product_uom:
							price = (line.quantity_done*line.purchase_line_id.price_unit)
						else:
							qty = line.product_id.uom_id._compute_quantity(line.quantity_done,line.purchase_line_id.product_uom)
							price = (qty*line.purchase_line_id.price_unit)
						purchase_price = line.purchase_line_id.currency_id._convert(price, self.company_id.currency_id, self.company_id, line.purchase_line_id.order_id.date_planned)
						# stock_qty = sum([x.quantity for x in stock_quant_ids])
						# total_qty = stock_qty + line.product_uom_qty
						amt = purchase_price / self.vendor_amount_total
						cost = amt * self.landed_amount_total
						price = (cost + purchase_price) / line.quantity_done
						# else:
						# 	price = line.product_id.standard_price * self.landed_cost_factor
						self.env['acc.shipment.estimation.line'].create({
							'header_id':self.id,
							'product_id':line.product_id.id,
							'std_price':line.product_id.standard_price,
							'estimated_price':price ,
							'list_price':line.product_id.list_price,
							'estimated_list_price': price / ((100 - line.product_id.sale_percent)/100)
						})
		elif self.po_ids and self.cost_bill_ids and self.landed_cost_factor > 0:
			for po in self.po_ids:
				for line in po.order_line:
					price = 0
					# if line.product_uom == line.purchase_line_id.product_uom:
					# 	price = (line.quantity_done*line.purchase_line_id.price_unit)
					# else:
					# 	qty = line.product_id.uom_id._compute_quantity(line.quantity_done,line.purchase_line_id.product_uom)
					# 	price = (qty*line.purchase_line_id.price_unit)
					purchase_price = line.currency_id._convert(line.price, self.company_id.currency_id, self.company_id, line.order_id.date_planned)
					# stock_qty = sum([x.quantity for x in stock_quant_ids])
					# total_qty = stock_qty + line.product_uom_qty
					amt = purchase_price / self.vendor_amount_total
					cost = amt * self.landed_amount_total
					price = (cost + purchase_price) / line.product_qty
					# else:
					# 	price = line.product_id.standard_price * self.landed_cost_factor
					self.env['acc.shipment.estimation.line'].create({
						'header_id':self.id,
						'product_id':line.product_id.id,
						'std_price':line.product_id.standard_price,
						'estimated_price':price,
						'list_price':line.product_id.list_price,
						'estimated_list_price': price / ((100 - line.product_id.sale_percent)/100)
					})
		else:
			raise UserError("Warning!!, Kindly create Clearance Bills.")


# class AxPackingList(models.Model):
# 	_name = "ax.ch.packing.list"
# 	_description = "Packing List"

# 	header_id = fields.Many2one("ax.shipment.master",'Shipment')
# 	name = fields.Char("Packing No")
# 	entry_date = fields.Date("Packing Date")
# 	product_id = fields.Many2one("product.product",'Product')
# 	unit_no = fields.Char("Handling Unit")
# 	length = fields.Float("Length[m]",digits=(12,3))
# 	width = fields.Float("Width[m]",digits=(12,3))
# 	height = fields.Float("Height[m]",digits=(12,3))
# 	volume = fields.Float("Volume[m3]",digits=(12,3))
# 	weight = fields.Float("Weight[kg]",digits=(12,3))
# 	qty = fields.Float("Qty",digits=(12,2))
# 	uom_id = fields.Many2one("uom.uom",'UOM')

# 	@api.onchange('product_id')
# 	def update_uom(self):
# 		if self.product_id:
# 			self.uom_id = self.product_id.uom_po_id.id

class AccShipmentEstimation(models.Model):
	_name = "acc.shipment.estimation.line"
	_description = "Shipment Estimation"

	header_id = fields.Many2one("ax.shipment.master",'Shipment')
	product_id = fields.Many2one('product.product','Product')
	std_price = fields.Float("Cost Price",digits='Product Price')
	estimated_price = fields.Float('Estimated Cost Price',digits='Product Price')
	list_price = fields.Float("Sales Price",digits='Product Price')
	estimated_list_price = fields.Float('Estimated Sales Price',digits='Product Price')
	currency_id = fields.Many2one('res.currency','Currency',default=lambda self:self.env.company.currency_id.id)
### import file ###
from odoo import api,models,fields
import time

class AccPackingList(models.Model):
	_name = "acc.stock.packing.list"
	_description = "Delivery Packing List"

	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('acc.packing.list')
		return super(AccPackingList, self).create(vals)

	def write(self, vals):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
		return super(AccPackingList, self).write(vals)

	name = fields.Char("Name")
	partner_id = fields.Many2one('res.partner','Customer')
	entry_date = fields.Date('Packing Date',default=fields.Date.today)
	sale_ids = fields.Many2many('sale.order','acc_sale_packing_rel','packing_id','sale_id','Sale Orders')
	picking_ids = fields.Many2many('stock.picking','acc_picking_packing_rel','packing_id','picking_id','Delivery',compute='_get_so_details')
	invoice_ids = fields.Many2many('account.move','acc_invoice_packing_rel','packing_id','invoice_id','Invoice',compute='_get_so_details')
	product_ids = fields.Many2many('product.product','acc_product_packing_rel','packing_id','product_id','Product',compute='_get_so_details')
	verified_by = fields.Many2one('res.users','Verified By')
	pack_type = fields.Selection([('Pallets','Pallets'),('Cartons','Cartons')],'Packing Type')
	verified_date = fields.Date("Verified Date")
	pallet_count = fields.Float("No.of Pallets/Cartons")
	line_ids = fields.One2many('acc.stock.packing.list.line','header_id','Packing List')
	disable_carton = fields.Boolean('Disable Cartons',default=False)
	attachment_ids = fields.Many2many('ir.attachment','acc_attachment_packing_rel','packing_id','attachment_id','Attachments')
	notes = fields.Text("Notes")
	company_id = fields.Many2one('res.company','Company',default=lambda self:self.env.company.id)
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
	state = fields.Selection([('draft','Draft'),('approve','Approved'),('cancel','Cancelled')],default='draft',string='Status')

	def unlink(self):
		""" Unlink """
		for rec in self:
			if rec.state not in ('draft','cancel'):
				raise UserError('Warning!, You can not delete this entry !!')
			else:
				return super(AccPackingList, self).unlink()

	@api.depends('sale_ids')
	def _get_so_details(self):
		for rec in self:
			if rec.sale_ids:
				rec.picking_ids = [(6,0,[line.id for so in rec.sale_ids for line in so.picking_ids if line.state == 'done'])]
				rec.invoice_ids = [(6,0,[line.id for so in rec.sale_ids for line in so.invoice_ids])]
				rec.product_ids = [(6,0,[line.product_id.id for line in rec.sale_ids.order_line])]
			else:
				rec.picking_ids = False
				rec.invoice_ids = False
				rec.product_ids = False

	def _get_so_name(self):
		if self.sale_ids:
			return ','.join([x.name for x in self.sale_ids])

	def _get_do_name(self):
		if self.picking_ids:
			return ','.join([x.name for x in self.picking_ids])

	def _get_inv_name(self):
		if self.invoice_ids:
			return ','.join([x.name for x in self.invoice_ids])

	def get_report_name(self):
		return "%s_%s"%('PACKING_LIST',self.name)

	def entry_approve(self):
		self.write({'state':'approve',
						'ap_rej_user_id': self.env.user.id,
						'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})

	def entry_cancel(self):
		self.write({'state':'cancel',
					'cancel_user_id': self.env.user.id,
					'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})

class AccPackingListLine(models.Model):
	_name = "acc.stock.packing.list.line"
	_description = "Delivery Packing List Line"

	header_id = fields.Many2one('acc.stock.packing.list')
	product_id = fields.Many2one("product.product",'Product')
	product_uom_id = fields.Many2one('uom.uom','UoM')
	qty = fields.Float("Quantity")
	dimension = fields.Char("Dimension")
	cartons_count = fields.Float("No.of. Cartons")
	uom_category_id = fields.Many2one('uom.category','UoM Category',related='product_id.uom_id.category_id')
	pieces_count = fields.Float("No.of. PCS Per Carton")
	net_weight = fields.Float("Net Weight")
	gross_weight = fields.Float("Gross Weight")
	display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note'),
    ], default=False, help="Technical field for UX purpose.")

	@api.onchange('product_id')
	def update_uom(self):
		if self.product_id:
			self.product_uom_id = self.product_id.uom_id.id

	@api.onchange('product_uom_id','qty','product_id')
	def update_qty_uom(self):
		if self.product_uom_id and self.product_id and self.qty > 0:
			self.qty = self.product_uom_id._compute_quantity(self.qty, self.product_id.uom_id)
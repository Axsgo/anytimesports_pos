### import file ###
from odoo import api,models,fields, _
import time
from odoo.exceptions import UserError

class AccConsignmentSale(models.Model):
	_inherit = "sale.order"

	is_consignment = fields.Boolean("Consignment Sale",default=False)
	is_consignment_transfered = fields.Boolean("Consignment Transfered",default=False)

	@api.model
	def create(self, vals):
		if 'company_id' in vals:
			self = self.with_company(vals['company_id'])
		if vals.get('name', _('New')) == _('New'):
			seq_date = None
			if 'date_order' in vals:
				seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
			vals['name'] = self.env['ir.sequence'].next_by_code('ax.sale.order.pos', sequence_date=seq_date) or _('New')

		# Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
		if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
			partner = self.env['res.partner'].browse(vals.get('partner_id'))
			addr = partner.address_get(['delivery', 'invoice'])
			vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
			vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
			vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist.id)
		result = super(AccConsignmentSale, self).create(vals)
		return result

	def entry_create_consignment(self):
		if self.is_consignment == True:
			if self.is_consignment_transfered == False:
				products = []
				picking_type_id = self.env['stock.picking.type'].search([('company_id', '=', self.company_id.id),('code','=','internal'),('name','=','Consignment Transfer')],limit=1)
				if picking_type_id:
					for line in self.order_line:
						products.append((0,0,{
							'name':line.product_id.name,
							'product_id':line.product_id.id,
							'product_uom':line.product_uom.id,
							'product_uom_qty':line.product_uom_qty,
							'picking_type_id':picking_type_id.id or False,
						}))
					transfer_id = self.env['stock.picking'].create({
						'is_consignment':True if picking_type_id.name == 'Consignment Transfer' else False,
						'sale_id':self.id,
						'partner_id':self.partner_id.id,
						'move_ids_without_package':products,
						'location_id':picking_type_id.default_location_src_id.id,
						'location_dest_id':picking_type_id.default_location_dest_id.id,
						'picking_type_id':picking_type_id.id or False,
						'hide_base_fields':True,
						'hide_picking_type':True,
						'origin':self.name,
						'move_type':'direct',
					})
					if transfer_id:
						transfer_id.action_confirm()
						transfer_id.action_assign()
						self.is_consignment_transfered = True
				else:
					raise UserError("Warning!!, Kindly create Consignment Transfer Operation Type.")
			else:
				raise UserError("Warning!!, Consignment Transfer already created.")
		else:
			raise UserError("Warning!!, This is not a Consignment Sale.")

class AccConsignment(models.Model):
	_inherit = "stock.picking"

	is_consignment = fields.Boolean('Consignment Transfer',copy=False,default=False)
	entry_date = fields.Date('Entry Date',default = lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'))
	sale_id = fields.Many2one('sale.order','Sale Order')
	hide_base_fields = fields.Boolean('Hide Base Fields',default=False)

class AccStockRule(models.Model):
	_inherit = "stock.rule"

	def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
		from dateutil.relativedelta import relativedelta
		''' Returns a dictionary of values that will be used to create a stock move from a procurement.
		This function assumes that the given procurement has a rule (action == 'pull' or 'pull_push') set on it.

		:param procurement: browse record
		:rtype: dictionary
		'''
		group_id = False
		if self.group_propagation_option == 'propagate':
		    group_id = values.get('group_id', False) and values['group_id'].id
		elif self.group_propagation_option == 'fixed':
		    group_id = self.group_id.id

		date_scheduled = fields.Datetime.to_string(
		    fields.Datetime.from_string(values['date_planned']) - relativedelta(days=self.delay or 0)
		)
		date_deadline = values.get('date_deadline') and (fields.Datetime.to_datetime(values['date_deadline']) - relativedelta(days=self.delay or 0)) or False
		partner = self.partner_address_id or (values.get('group_id', False) and values['group_id'].partner_id)
		if partner:
		    product_id = product_id.with_context(lang=partner.lang or self.env.user.lang)
		picking_description = product_id._get_description(self.picking_type_id)
		if values.get('product_description_variants'):
		    picking_description += values['product_description_variants']
		# it is possible that we've already got some move done, so check for the done qty and create
		# a new move with the correct qty
		qty_left = product_qty

		move_dest_ids = []
		if not self.location_id.should_bypass_reservation():
		    move_dest_ids = values.get('move_dest_ids', False) and [(4, x.id) for x in values['move_dest_ids']] or []

		sale_line_id = self.env['sale.order.line'].browse(values['sale_line_id'])
		# if sale_line_id.is_foc_line == True:
		# 	qty_left = 0
		# else:
		# 	pass
		if sale_line_id.order_id.is_consignment == True:
			location_src_id = self.env['stock.picking.type'].search([('code','=','internal'),('name','=','Consignment Transfer')],limit=1).default_location_dest_id
		else:
			location_src_id = self.location_src_id
		move_values = {
		    'name': name[:2000],
		    'company_id': self.company_id.id or self.location_src_id.company_id.id or self.location_id.company_id.id or company_id.id,
		    'product_id': product_id.id,
		    'product_uom': product_uom.id,
		    'product_uom_qty': qty_left,
		    'partner_id': partner.id if partner else False,
		    'location_id': location_src_id.id,
		    'location_dest_id': location_id.id,
		    'move_dest_ids': move_dest_ids,
		    'rule_id': self.id,
		    'procure_method': self.procure_method,
		    'origin': origin,
		    'picking_type_id': self.picking_type_id.id,
		    'group_id': group_id,
		    'route_ids': [(4, route.id) for route in values.get('route_ids', [])],
		    'warehouse_id': self.propagate_warehouse_id.id or self.warehouse_id.id,
		    'date': date_scheduled,
		    'date_deadline': False if self.group_propagation_option == 'fixed' else date_deadline,
		    'propagate_cancel': self.propagate_cancel,
		    'description_picking': picking_description,
		    'priority': values.get('priority', "0"),
		    'orderpoint_id': values.get('orderpoint_id') and values['orderpoint_id'].id,
		}
		# else:
		# 	move_values = {}
		for field in self._get_custom_move_fields():
		    if field in values:
		        move_values[field] = values.get(field)
		return move_values

class AccPurchaseOrder(models.Model):
	_inherit = "purchase.order"

	@api.model
	def create(self, vals):
		company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
		# Ensures default picking type and currency are taken from the right company.
		self_comp = self.with_company(company_id)
		if vals.get('name', 'New') == 'New':
			seq_date = None
			if 'date_order' in vals:
				seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
			vals['name'] = self_comp.env['ir.sequence'].next_by_code('ax.purchase.order.pos', sequence_date=seq_date) or '/'
		vals, partner_vals = self._write_partner_values(vals)
		res = super(AccPurchaseOrder, self_comp).create(vals)
		if partner_vals:
			res.sudo().write(partner_vals)  # Because the purchase user doesn't have write on `res.partner`
		return res
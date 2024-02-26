### import file ###
from odoo import api,models,fields,_
from odoo.exceptions import UserError

class UsersView(models.Model):
	_inherit = "res.users"

	location_ids = fields.Many2many('stock.location', 'res_location_rel', 'user_id', 'cid',
        string='Allowed Locations',store=True)
	location_company_id = fields.Many2one('stock.location',string='Default Location',store=True)

	def write(self, values):
		values = self._remove_reified_groups(values)
		res = super(UsersView, self).write(values)
		group_multi_location = self.env.ref('acc_stock.group_multi_location', False)
		if group_multi_location:
			for user in self:
				if len(user.location_ids) <= 1 and user.id in group_multi_location.users.ids:
					user.write({'groups_id': [(3, group_multi_location.id)]})
				elif len(user.location_ids) > 1 and user.id not in group_multi_location.users.ids:
					user.write({'groups_id': [(4, group_multi_location.id)]})
		if 'company_ids' not in values:
			return res
		group_multi_company = self.env.ref('base.group_multi_company', False)
		if group_multi_company:
			for user in self:
				if len(user.company_ids) <= 1 and user.id in group_multi_company.users.ids:
					user.write({'groups_id': [(3, group_multi_company.id)]})
				elif len(user.company_ids) > 1 and user.id not in group_multi_company.users.ids:
					user.write({'groups_id': [(4, group_multi_company.id)]})
		return res

class AccPicking(models.Model):
	_inherit = "stock.picking"
	_order = 'id desc'

	# pick_type = fields.Selection([('outgoing','Delivery'),('incoming','Receipt'),('internal','Internal')],'Pick Type',compute='_get_pick_type',store=True)
	employee_id = fields.Many2one('hr.employee','Employee')
	driver_id = fields.Many2one('res.users','Driver',domain=lambda self: [("groups_id", "=",
                                                  self.env.ref("acc_users.driver_user_group").id)])
	pick_datetime = fields.Datetime('Picking Datetime',default=fields.Date.today)
	ref_no = fields.Char("Reference No")
	ref_date = fields.Date("Reference Date")
	checked_by = fields.Many2one('res.users','Checked By',domain=lambda self: [("groups_id", "=",
                                                  self.env.ref("acc_users.warehouse_user_group").id)])
	checked_datetime = fields.Datetime("Checked Datetime",default=fields.Date.today)
	partner_shipping_id =fields.Many2one('res.partner','Delivery Address',compute='update_shipping_address',store=True)
	backorder_leadtime = fields.Datetime("Backorder Leadtime")
	purchase_id = fields.Many2one('purchase.order','Purchase Order',compute='_get_purchase_order',store=True)
	invoice_count = fields.Integer(string='Invoices', compute='_compute_invoice_count')
	operation_code = fields.Selection(related='picking_type_id.code')
	is_return = fields.Boolean()
	is_direct_delivery = fields.Boolean("Is Direct Delivery Order",default=False)
	picking_code = fields.Selection([('incoming','Receipts'),('outgoing','Delivery'),('internal','Internal')],'Picking Type')

	@api.onchange('picking_type_id','picking_type_code')
	def update_picking_code(self):
		if self.picking_type_id.code == 'incoming':
			self.picking_code = 'incoming'
		elif self.picking_type_id.code == 'outgoing':
			self.picking_code = 'outgoing'
		else:
			self.picking_code = 'internal'

	@api.onchange('picking_code')
	def update_picking_type_domain(self):
		if self.picking_code == 'incoming':
			self.picking_type_id = self.env['stock.picking.type'].search([('code','=','incoming')],limit=1).id
			return {'domain': {'picking_type_id': [('code','=','incoming'),'|',('company_id','=',self.company_id.id),
			('company_id','=',False)]}}
		elif self.picking_code == 'outgoing':
			self.picking_type_id = self.env['stock.picking.type'].search([('code','=','outgoing')],limit=1).id
			return {'domain': {'picking_type_id': [('code','=','outgoing'),'|',('company_id','=',self.company_id.id),
			('company_id','=',False)]}}
		else:
			self.picking_type_id = self.env['stock.picking.type'].search([('code','=','internal')],limit=1).id
			return {'domain': {'picking_type_id': [('code','=','internal'),'|',('company_id','=',self.company_id.id),
			('company_id','=',False)]}}

	@api.onchange('picking_code')
	def update_partner_domain(self):
		if self.picking_code == 'incoming':
			return {'domain': {'partner_id': [('supplier_rank','>',0),('is_company','=',True),
			'|',('company_id','=',self.company_id.id),('company_id','=',False)]}}
		elif self.picking_code == 'outgoing':
			return {'domain': {'partner_id': [('customer_rank','>',0),('is_company','=',True),
			'|',('company_id','=',self.company_id.id),('company_id','=',False)]}}
		else:
			return {'domain': {'partner_id': [('supplier_rank','=',0),('customer_rank','=',0),
			'|',('company_id','=',self.company_id.id),('company_id','=',False)]}}

	@api.depends('partner_id')
	def update_shipping_address(self):
		for rec in self:
			if rec.partner_id:
				addr = rec.partner_id.address_get(['delivery'])
				rec.partner_shipping_id = addr['delivery']
			else:
				rec.partner_id = False

	# @api.depends('picking_type_id')
	# def _get_pick_type(self):
	# 	for rec in self:
	# 		if rec.picking_type_id.code == 'outgoing':
	# 			rec.pick_type = 'outgoing'
	# 		elif rec.picking_type_id.code == 'incoming':
	# 			rec.pick_type = 'incoming'
	# 		else:
	# 			rec.pick_type = 'internal'

	@api.depends('move_ids_without_package')
	def _get_purchase_order(self):
		for rec in self:
			rec.purchase_id = False
			if rec.move_ids_without_package:
				po_ids = list(set([line.purchase_line_id.order_id for line in rec.move_ids_without_package]))
				if po_ids and len(po_ids) == 1:
					rec.purchase_id = po_ids.id

	# @api.depends('move_lines.state', 'move_lines.date', 'move_type')
	# def _compute_scheduled_date(self):
	# 	for picking in self:
	# 		moves_dates = picking.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')).mapped('date')
	# 		if picking.picking_type_code == 'outgoing' and picking.backorder_id:
	# 			picking.scheduled_date = picking.backorder_id.backorder_leadtime
	# 		elif picking.move_type == 'direct':
	# 			picking.scheduled_date = min(moves_dates, default=picking.scheduled_date or fields.Datetime.now())
	# 		else:
	# 			picking.scheduled_date = max(moves_dates, default=picking.scheduled_date or fields.Datetime.now())

	# def _create_backorder(self):
	# 	""" This method is called when the user chose to create a backorder. It will create a new
	# 	picking, the backorder, and move the stock.moves that are not `done` or `cancel` into it.
	# 	"""
	# 	backorders = self.env['stock.picking']
	# 	for picking in self:
	# 		moves_to_backorder = picking.move_lines.filtered(lambda x: x.state not in ('done', 'cancel'))
	# 		if moves_to_backorder:
	# 			backorder_picking = picking.copy({
	# 				'name': '/',
	# 				'move_lines': [],
	# 				'move_line_ids': [],
	# 				'backorder_id': picking.id,
	# 				'checked_by':False,
	# 				'checked_datetime':False,
	# 				'driver_id':False,
	# 				'pick_datetime':False,
	# 				'backorder_leadtime':False
	# 			})
	# 			picking.message_post(
	# 				body=_('The backorder <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> has been created.') % (
	# 				backorder_picking.id, backorder_picking.name))
	# 			moves_to_backorder.write({'picking_id': backorder_picking.id})
	# 			moves_to_backorder.mapped('package_level_id').write({'picking_id':backorder_picking.id})
	# 			moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})
	# 			backorders |= backorder_picking
	# 	return backorders

	def _entry_delivery_alert(self):
		from datetime import datetime
		picking_ids = self.env['stock.picking'].search([('picking_type_code','=','outgoing'),('state','not in',('done','cancel'))])
		if picking_ids:
			for line in picking_ids:
				if line.scheduled_date and line.scheduled_date < datetime.now():
					body = ('Hello %s, <br/>'
						"The below Sale order's delivery is expired, kindly follow <br/>"
						'Sale Order: <b><a href=# data-oe-model=sale.order data-oe-id=%d>%s</a></b><br/>'
						'Delivery  : <b><a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a></b>'
						)%(line.sale_id.user_id.name, line.sale_id.id, line.sale_id.name, line.id, line.name)

					odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
					channel_partners = line.sale_id.user_id.mapped('partner_id').ids
					channel = self.env['mail.channel'].sudo().search(
					[('channel_type', '=', 'chat'), ('channel_partner_ids', 'in', channel_partners),('channel_partner_ids', 'in', [odoobot_id])], limit=1)
					if not channel:
						line.sale_id.user_id.odoobot_state = 'not_initialized'
						channel = self.env['mail.channel'].with_user(line.sale_id.user_id).init_odoobot()
					if channel:
						channel.message_post(
							body=body,
							author_id=odoobot_id,
							message_type="comment",
							subtype_xmlid="mail.mt_comment",
						)
				elif line.scheduled_date <= datetime.now() and line.scheduled_date >= datetime.now():
					body = ('Hello %s, <br/>'
						'The below Sale order is delivery today, kindly follow <br/>'
						'Sale Order: <b><a href=# data-oe-model=sale.order data-oe-id=%d>%s</a></b><br/>'
						'Delivery  : <b><a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a></b>'
						)%(line.sale_id.user_id.name, line.sale_id.id, line.sale_id.name, line.id, line.name)

					odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
					channel_partners = line.sale_id.user_id.mapped('partner_id').ids
					channel = self.env['mail.channel'].sudo().search(
					[('channel_type', '=', 'chat'), ('channel_partner_ids', 'in', channel_partners),('channel_partner_ids', 'in', [odoobot_id])], limit=1)
					if not channel:
						line.sale_id.user_id.odoobot_state = 'not_initialized'
						channel = self.env['mail.channel'].with_user(line.sale_id.user_id).init_odoobot()
					if channel:
						channel.message_post(
							body=body,
							author_id=odoobot_id,
							message_type="comment",
							subtype_xmlid="mail.mt_comment",
						)

	def _set_auto_lot(self):
		"""
		Allows to be called either by button or through code
		"""
		pickings = self.filtered(lambda p: p.picking_type_id.code == 'incoming')
		lines = pickings.mapped("move_line_ids").filtered(
			lambda x: (
			not x.lot_id
			and not x.lot_name
			and x.product_id.tracking in ("serial",'lot')
			and x.product_id.enable_auto_lot
			and x.qty_done != 0
			)
		)
		lines.set_lot_auto()

	def _replace_batch(self):
		pickings = self.filtered(lambda p: p.picking_type_id.code == 'outgoing')
		lines = pickings.mapped("move_line_ids").filtered(
			lambda x: (
			x.lot_id
			and x.product_id.tracking in ("serial",'lot')
			and x.product_id.enable_auto_lot
			and x.serial_no != False
			)
		)
		for l in lines:
			l.lot_id.name = l.serial_no

	# def action_assign(self):
	# 	if self.env.user.has_group('acc_users.driver_user_group'):
	# 		raise UserError("Warning, You are not allowed to Assign Delivery Orders.")
	# 	return super().action_assign()

	def action_cancel(self):
		if self.env.user.has_group('acc_users.driver_user_group'):
			raise UserError("Warning, You are not allowed to Cancel Delivery Orders.")
		return super().action_cancel()

	def button_scrap(self):
		if self.env.user.has_group('acc_users.driver_user_group'):
			raise UserError("Warning, You are not allowed to Scrap Delivery Orders.")
		return super().button_scrap()

	def do_unreserve(self):
		if self.env.user.has_group('acc_users.driver_user_group'):
			raise UserError("Warning, You are not allowed to Unreserve Delivery Orders.")
		return super().do_unreserve()

	def _action_done(self):
		self._set_auto_lot()
		return super()._action_done()

	def button_validate(self):
		if self.env.user.has_group('acc_users.driver_user_group'):
			raise UserError("Warning, You are not allowed to validate Delivery Orders.")
		self._set_auto_lot()
		self._replace_batch()
		return super().button_validate()

	def _compute_invoice_count(self):
		"""This compute function used to count the number of invoice for the picking"""
		for picking_id in self:
			move_ids = picking_id.env['account.move'].search([('invoice_origin', '=', picking_id.name)])
			if move_ids:
				self.invoice_count = len(move_ids)
			else:
				self.invoice_count = 0

	def create_invoice(self):
		"""This is the function for creating customer invoice
		from the picking"""
		for picking_id in self:
			current_user = self.env.uid
			if picking_id.picking_type_id.code == 'outgoing':
				customer_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
					'stock_move_invoice.customer_journal_id') or False
				if not customer_journal_id:
					raise UserError(_("Please configure the journal from settings"))
				invoice_line_list = []
				for move_ids_without_package in picking_id.move_ids_without_package:
					vals = (0, 0, {
						'name': move_ids_without_package.description_picking,
						'product_id': move_ids_without_package.product_id.id,
						'price_unit': move_ids_without_package.product_id.lst_price,
						'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
						else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
						'tax_ids': [(6, 0, [picking_id.company_id.account_sale_tax_id.id])],
						'quantity': move_ids_without_package.quantity_done,
					})
					invoice_line_list.append(vals)
					invoice = picking_id.env['account.move'].create({
						'move_type': 'out_invoice',
						'invoice_origin': picking_id.name,
						'invoice_user_id': current_user,
						'narration': picking_id.name,
						'partner_id': picking_id.partner_id.id,
						'currency_id': picking_id.env.user.company_id.currency_id.id,
						'journal_id': int(customer_journal_id),
						'payment_reference': picking_id.name,
						'picking_id': picking_id.id,
						'invoice_line_ids': invoice_line_list
					})
					return invoice

	def create_bill(self):
		"""This is the function for creating vendor bill
				from the picking"""
		for picking_id in self:
			current_user = self.env.uid
			if picking_id.picking_type_id.code == 'incoming':
				vendor_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
					'stock_move_invoice.vendor_journal_id') or False
				if not vendor_journal_id:
					raise UserError(_("Please configure the journal from the settings."))
				invoice_line_list = []
				for move_ids_without_package in picking_id.move_ids_without_package:
					vals = (0, 0, {
						'name': move_ids_without_package.description_picking,
						'product_id': move_ids_without_package.product_id.id,
						'price_unit': move_ids_without_package.product_id.lst_price,
						'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
						else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
						'tax_ids': [(6, 0, [picking_id.company_id.account_purchase_tax_id.id])],
						'quantity': move_ids_without_package.quantity_done,
					})
					invoice_line_list.append(vals)
					invoice = picking_id.env['account.move'].create({
						'move_type': 'in_invoice',
						'invoice_origin': picking_id.name,
						'invoice_user_id': current_user,
						'narration': picking_id.name,
						'partner_id': picking_id.partner_id.id,
						'currency_id': picking_id.env.user.company_id.currency_id.id,
						'journal_id': int(vendor_journal_id),
						'payment_reference': picking_id.name,
						'picking_id': picking_id.id,
						'invoice_line_ids': invoice_line_list
					})
					return invoice

	def create_customer_credit(self):
		"""This is the function for creating customer credit note
				from the picking"""
		for picking_id in self:
			current_user = picking_id.env.uid
			if picking_id.picking_type_id.code == 'incoming':
				customer_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
					'stock_move_invoice.customer_journal_id') or False
				if not customer_journal_id:
					raise UserError(_("Please configure the journal from settings"))
				invoice_line_list = []
				for move_ids_without_package in picking_id.move_ids_without_package:
					vals = (0, 0, {
						'name': move_ids_without_package.description_picking,
						'product_id': move_ids_without_package.product_id.id,
						'price_unit': move_ids_without_package.product_id.lst_price,
						'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
						else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
						'tax_ids': [(6, 0, [picking_id.company_id.account_sale_tax_id.id])],
						'quantity': move_ids_without_package.quantity_done,
					})
					invoice_line_list.append(vals)
					invoice = picking_id.env['account.move'].create({
						'move_type': 'out_refund',
						'invoice_origin': picking_id.name,
						'invoice_user_id': current_user,
						'narration': picking_id.name,
						'partner_id': picking_id.partner_id.id,
						'currency_id': picking_id.env.user.company_id.currency_id.id,
						'journal_id': int(customer_journal_id),
						'payment_reference': picking_id.name,
						'picking_id': picking_id.id,
						'invoice_line_ids': invoice_line_list
					})
					return invoice

	def create_vendor_credit(self):
		"""This is the function for creating refund
				from the picking"""
		for picking_id in self:
			current_user = self.env.uid
			if picking_id.picking_type_id.code == 'outgoing':
				vendor_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
					'stock_move_invoice.vendor_journal_id') or False
				if not vendor_journal_id:
					raise UserError(_("Please configure the journal from the settings."))
				invoice_line_list = []
				for move_ids_without_package in picking_id.move_ids_without_package:
					vals = (0, 0, {
						'name': move_ids_without_package.description_picking,
						'product_id': move_ids_without_package.product_id.id,
						'price_unit': move_ids_without_package.product_id.lst_price,
						'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
						else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
						'tax_ids': [(6, 0, [picking_id.company_id.account_purchase_tax_id.id])],
						'quantity': move_ids_without_package.quantity_done,
					})
					invoice_line_list.append(vals)
					invoice = picking_id.env['account.move'].create({
						'move_type': 'in_refund',
						'invoice_origin': picking_id.name,
						'invoice_user_id': current_user,
						'narration': picking_id.name,
						'partner_id': picking_id.partner_id.id,
						'currency_id': picking_id.env.user.company_id.currency_id.id,
						'journal_id': int(vendor_journal_id),
						'payment_reference': picking_id.name,
						'picking_id': picking_id.id,
						'invoice_line_ids': invoice_line_list
					})
					return invoice

	def action_open_picking_invoice(self):
		"""This is the function of the smart button which redirect to the
		invoice related to the current picking"""
		return {
			'name': 'Invoices',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'domain': [('invoice_origin', '=', self.name)],
			'context': {'create': False},
			'target': 'current'
		}

class AccStockMove(models.Model):
	_inherit = "stock.move"

	@api.depends(
		"has_tracking",
		"product_id.enable_auto_lot",
		"picking_type_id.use_existing_lots",
		"state",
	)
	def _compute_display_assign_serial(self):
		super()._compute_display_assign_serial()
		moves_not_display = self.filtered(
			lambda m: m.product_id.enable_auto_lot
		)
		for move in moves_not_display:
			move.display_assign_serial = False

	enable_auto_lot = fields.Boolean("Enable Automatic Serial No",compute="_get_product_auto_lot")
	show_lots_text = fields.Boolean("Show Lot",related='picking_id.show_lots_text')
	tracking = fields.Selection([('none','No Batch/Serial No Required'),('lot','Lot/Batch No Required'),('serial','Serial No Required')],
		'Product Tracking',related='product_id.tracking')
	# expiration_date = fields.Datetime("Expiration Date")

	@api.depends("product_id")
	def _get_product_auto_lot(self):
		for rec in self:
			if rec.product_id and rec.product_id.enable_auto_lot == True:
				rec.enable_auto_lot = True
			else:
				rec.enable_auto_lot = False

	def action_update_move_quantity(self):
		if self.next_serial_count <= 0:
			raise UserError("Warning!!, Number of Qty should be greater than Zero.")
		move_lines_commands = self._generate_serial_move_line_commands()
		self.write({'move_line_ids': move_lines_commands})
		return self.action_show_details()

	def _generate_serial_move_line_commands(self, lot_names=None, origin_move_line=None):
		self.ensure_one()
		from datetime import datetime,timedelta
		# Select the right move lines depending of the picking type configuration.
		move_lines = self.env['stock.move.line']
		if self.picking_type_id.show_reserved:
			move_lines = self.move_line_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_name)
		else:
			move_lines = self.move_line_nosuggest_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_name)

		if origin_move_line:
			location_dest = origin_move_line.location_dest_id
		else:
			location_dest = self.location_dest_id._get_putaway_strategy(self.product_id)
		move_line_vals = {
			'picking_id': self.picking_id.id,
			'location_dest_id': location_dest.id or self.location_dest_id.id,
			'location_id': self.location_id.id,
			'product_id': self.product_id.id,
			'product_uom_id': self.product_id.uom_id.id,
			'qty_done': 1 if self.product_id.tracking == 'serial' else self.next_serial_count,
		}
		if origin_move_line:
			# `owner_id` and `package_id` are taken only in the case we create
			# new move lines from an existing move line. Also, updates the
			# `qty_done` because it could be usefull for products tracked by lot.
			move_line_vals.update({
				'owner_id': origin_move_line.owner_id.id,
				'package_id': origin_move_line.package_id.id,
				'qty_done': origin_move_line.qty_done or 1,
			})

		move_lines_commands = []
		if self.enable_auto_lot == True:
			if self.product_id.tracking == 'serial':
				for i in range(0,self.next_serial_count):
					if move_lines:
						move_lines_commands.append((1, move_lines[0].id, {
							'qty_done': 1,
							# 'expiration_date':self.expiration_date,
						}))
						move_lines = move_lines[1:]
					# ... or create a new move line with the serial name.
					else:
						product_id = self.env['product.product'].browse(move_line_vals['product_id'])
						if product_id.use_expiration_date == True:
							move_line_vals['expiration_date'] = fields.Datetime.today() + timedelta(days=product_id.expiration_time)
						move_line_cmd = dict(move_line_vals)
						move_lines_commands.append((0, 0, move_line_cmd))
			elif self.product_id.tracking == 'lot':
				if move_lines:
					move_lines_commands.append((1, move_lines[0].id, {
						'qty_done': self.next_serial_count,
						# 'expiration_date':self.expiration_date,
					}))
					move_lines = move_lines[1:]
				# ... or create a new move line with the serial name.
				else:
					product_id = self.env['product.product'].browse(move_line_vals['product_id'])
					if product_id.use_expiration_date == True:
						move_line_vals['expiration_date'] = fields.Datetime.today() + timedelta(days=product_id.expiration_time)
					move_line_cmd = dict(move_line_vals)
					move_lines_commands.append((0, 0, move_line_cmd))
		else:
			for lot_name in lot_names:
				# We write the lot name on an existing move line (if we have still one)...
				if move_lines:
					move_lines_commands.append((1, move_lines[0].id, {
						'lot_name': lot_name,
						'qty_done': 1,
					}))
					move_lines = move_lines[1:]
				# ... or create a new move line with the serial name.
				else:
					move_line_cmd = dict(move_line_vals, lot_name=lot_name)
					move_lines_commands.append((0, 0, move_line_cmd))
		return move_lines_commands

class ACCStockMoveLine(models.Model):
	_inherit = "stock.move.line"

	serial_no = fields.Char("Supplier Serial No")
	enable_auto_lot = fields.Boolean("Enable Automatic Serial No",compute="_get_product_auto_lot")

	@api.depends("product_id")
	def _get_product_auto_lot(self):
		for rec in self:
			if rec.product_id and rec.product_id.enable_auto_lot == True:
				rec.enable_auto_lot = True
			else:
				rec.enable_auto_lot = False

	def _prepare_auto_lot_values(self):
		"""
		Prepare multi valued lots per line to use multi creation.
		"""
		self.ensure_one()
		return {"product_id": self.product_id.id, "company_id": self.company_id.id}

	def set_lot_auto(self):
		from odoo.fields import first
		"""
		Create lots using create_multi to avoid too much queries
		As move lines were created by product or by tracked 'serial'
		products, we apply the lot with both different approaches.
		"""
		values = []
		production_lot_obj = self.env["stock.production.lot"]
		lots_by_product = dict()
		for line in self:
			values.append(line._prepare_auto_lot_values())
		lots = production_lot_obj.create(values)
		for lot in lots:
			if lot.product_id.id not in lots_by_product:
				lots_by_product[lot.product_id.id] = lot
			else:
				lots_by_product[lot.product_id.id] += lot
		for line in self:
			lot = first(lots_by_product[line.product_id.id])
			line.lot_id = lot
			if lot.product_id.tracking in ("serial",'lot'):
				lots_by_product[line.product_id.id] -= lot

class AccStockProductionLot(models.Model):
	_inherit = "stock.production.lot"

	qty_available = fields.Float('qty_available',related='product_qty',store=True)

class AccPurchaseOrder(models.Model):
	_inherit = "purchase.order"

	warehouse_location_id = fields.Many2one('stock.location',string="Location", domain=[('usage', '=', 'internal'),('active', '=', True)])

	def _get_destination_location(self):
		self.ensure_one()
		if self.warehouse_location_id:
			return self.warehouse_location_id.id
		else:
			if self.dest_address_id:
				return self.dest_address_id.property_stock_customer.id
			return self.picking_type_id.default_location_dest_id.id

class AccSaleStock(models.Model):
	_inherit = "sale.order"

	has_available_route_ids = fields.Boolean(
		'Routes can be selected on this product', compute='_compute_has_available_route_ids',
		default=lambda self: self.env['stock.location.route'].search_count([('product_selectable', '=', True)]))
	warehouse_location_id = fields.Many2one('stock.location',string="Location", domain=[('usage', '=', 'internal'),('active', '=', True)])

	@api.depends('order_line','order_line.product_id','order_line.product_id.type')
	def _compute_has_available_route_ids(self):
		self.has_available_route_ids = self.env['stock.location.route'].search_count([('product_selectable', '=', True)])

	def action_confirm(self):
		res = super(AccSaleStock, self).action_confirm()
		pickings_val = self.mapped('picking_ids')
		for picking in pickings_val:
			if self.warehouse_location_id:
				picking.location_id = self.warehouse_location_id.id
				picking.state = 'confirmed'
				picking.move_line_ids_without_package = False
				picking.action_assign()

class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"
	_name = "sale.order.line"
	_description = "Sale Order Line"

	onhand_qty = fields.Float("OnHand Qty",digits=(12,2),store=True)

	@api.onchange('product_id')
	def update_onhand_qty(self):
		for rec in self:
			rec.onhand_qty = 0
			if rec.product_id and rec.order_id.warehouse_location_id:
				self.env.cr.execute("""select SUM(quantity) from stock_quant where location_id = '%s' and product_id = '%s' and company_id = '%s'""" %
					(rec.order_id.warehouse_location_id.id, rec.product_id.id,rec.order_id.company_id.id))
				data = self.env.cr.dictfetchall()
				rec.onhand_qty = data[0]['sum'] if data else 0
			else:
				rec.onhand_qty = 0

class StockReturnInvoicePicking(models.TransientModel):
	_inherit = 'stock.return.picking'

	def _create_returns(self):
		"""in this function the picking is marked as return"""
		new_picking, pick_type_id = super(StockReturnInvoicePicking, self)._create_returns()
		picking = self.env['stock.picking'].browse(new_picking)
		picking.write({'is_return': True})
		return new_picking, pick_type_id

class AccountMove(models.Model):
	_inherit = 'account.move'

	picking_id = fields.Many2one('stock.picking', string='Picking')

class AccStockQuant(models.Model):
	_inherit = "stock.quant"

	product_pos_categ_id = fields.Many2one('product.category','Product Category',related='product_id.categ_id',store=True)
	product_barcode = fields.Char(string='Barcode', related='product_id.barcode', store=True)
	standard_price = fields.Float('Cost Price AED', related='product_id.standard_price', store=True)
	list_price = fields.Float('Sales Price AED', related='product_id.list_price', store=True)
	usd_currency_id = fields.Many2one('res.currency', string='USD Currency', compute='get_usd_currency')
	rp_aed = fields.Monetary('RP AED', store=True , currency_field='currency_id')
	rp_usd = fields.Monetary('RP USD', store=True , currency_field='usd_currency_id')
	uc_usd = fields.Monetary('UC USD', store=True , currency_field='usd_currency_id')

	@api.depends('value')
	def get_usd_currency(self):
		usd_currency = self.env['res.currency'].sudo().search([('name','=','USD')], limit=1)
		for record in self:
			record.usd_currency_id = usd_currency and usd_currency.id

	def _update_stock_price(self):
		stock_quant_ids = self.env['stock.quant'].sudo().search([ ])
		for rec in stock_quant_ids:
			rec.rp_aed = rec.product_id.product_tmpl_id.rp_aed
			rec.rp_usd = rec.product_id.product_tmpl_id.rp_usd
			rec.uc_usd = rec.product_id.product_tmpl_id.uc_usd

class PosOrder(models.Model):
	_inherit = 'pos.order'

	location_id = fields.Many2one('stock.location', string='Location' ,related='config_id.location_id', store=True)

class PosSession(models.Model):
	_inherit = 'pos.session'

	location_id = fields.Many2one('stock.location', string='Location' ,related='config_id.location_id', store=True)

class PosPayment(models.Model):
	_inherit = 'pos.payment'

	location_id = fields.Many2one('stock.location', string='Location' ,related='pos_order_id.location_id', store=True)

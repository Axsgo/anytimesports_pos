from odoo import fields,api,models
from calendar import monthrange
import calendar,time
from datetime import datetime,date
from odoo.exceptions import UserError,ValidationError

class ProductProfitReport(models.TransientModel):
    _name = 'product.profit.report'
    _description = 'Product Profit Report'
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    report_product_profit_detail_ids = fields.One2many('report.product.profit.details','header_id')
    report_product_wise_detail_ids = fields.One2many('report.product.wise.details','header_id')
    crt_date = fields.Date(
    'Report Date',
    readonly = True,
    default = date.today())

    @api.onchange('from_date','to_date')
    def compute_reports_lines(self):
        self.report_product_profit_detail_ids = False
        self.report_product_wise_detail_ids = False

    def compute_reports_all(self):
        self.report_product_profit_detail_ids = False
        self.report_product_wise_detail_ids = False
        product_list = []
        parent_category_ids = self.env['product.category'].search([('parent_id','=',False),('name','not ilike','Charges')],order='seq_no asc')
        for parent_category in parent_category_ids:
            qty_sold_parent = 0.0
            sales_parent = 0.0
            cost_parent = 0.0
            income_account_id = self.env['account.account'].search([('name','=','Income from Credit Sales')],limit=1).id or False
            chilld_category_ids = self.env['product.category'].search([('parent_id','=',parent_category.id)],order='seq_no asc')
            for chilld_category in chilld_category_ids:
                qty_sold = 0.0
                sales = 0.0
                cost = 0.0
                # for invoices
                if self.to_date <= datetime.strptime('2022-12-31','%Y-%m-%d').date():
                    line_ids = self.env['account.move.line'].search([('move_id.state','=','posted'),('move_id.invoice_date','>=',self.from_date),
                        ('move_id.invoice_date','<=',self.to_date),('product_id.categ_id','=',chilld_category.id),('move_id.move_type','=','out_invoice'),
                        ('move_id.company_id','=',self.company_id.id),('product_id.active','=',True),('account_id','=',income_account_id),('is_foc_product','=',False),('is_foc_line','=',False)])
                else:
                    line_ids = self.env['account.move.line'].search([('move_id.state','=','posted'),('move_id.invoice_date','>=',self.from_date),
                        ('move_id.invoice_date','<=',self.to_date),('product_id.categ_id','=',chilld_category.id),('move_id.move_type','=','out_invoice'),
                        ('move_id.company_id','=',self.company_id.id),('product_id.active','=',True),('account_id','=',income_account_id)])
                for recs in line_ids:
                    if recs.move_id.sale_id:
                        if recs.move_id.sale_id.is_intercompany_sale != True:
                            qty_sold += recs.quantity
                            qty_sold_parent += recs.quantity
                            currency_val = recs.move_id.currency_id._convert(recs.price_subtotal, self.company_id.currency_id,
                                        self.company_id or self.env.company, recs.move_id.invoice_date or fields.Date.today())
                            sales += currency_val
                            sales_parent += currency_val
                            if recs.purchase_cost_price == 0:
                                cost += recs.quantity * recs.product_id.standard_price
                                cost_parent += recs.quantity * recs.product_id.standard_price
                            else:
                                cost += recs.quantity * recs.purchase_cost_price
                                cost_parent += recs.quantity * recs.purchase_cost_price
                    else:
                        qty_sold += recs.quantity
                        qty_sold_parent += recs.quantity
                        currency_val = recs.move_id.currency_id._convert(recs.price_subtotal, self.company_id.currency_id,
                                    self.company_id or self.env.company, recs.move_id.invoice_date or fields.Date.today())
                        sales += currency_val
                        sales_parent += currency_val
                        if recs.purchase_cost_price == 0:
                            cost += recs.quantity * recs.product_id.standard_price
                            cost_parent += recs.quantity * recs.product_id.standard_price
                        else:
                            cost += recs.quantity * recs.purchase_cost_price
                            cost_parent += recs.quantity * recs.purchase_cost_price

                # for Credit Notes
                if self.to_date <= datetime.strptime('2022-12-31','%Y-%m-%d').date():
                    line_ids = self.env['account.move.line'].search([('move_id.state','=','posted'),('move_id.invoice_date','>=',self.from_date),
                        ('move_id.invoice_date','<=',self.to_date),('product_id.categ_id','=',chilld_category.id),('move_id.move_type','=','out_refund'),
                        ('move_id.company_id','=',self.company_id.id),('product_id.active','=',True),('account_id','=',income_account_id),('is_foc_product','=',False),('is_foc_line','=',False)])
                else:
                    line_ids = self.env['account.move.line'].search([('move_id.state','=','posted'),('move_id.invoice_date','>=',self.from_date),
                        ('move_id.invoice_date','<=',self.to_date),('product_id.categ_id','=',chilld_category.id),('move_id.move_type','=','out_refund'),
                        ('move_id.company_id','=',self.company_id.id),('product_id.active','=',True),('account_id','=',income_account_id)])
                for recs in line_ids:
                    if recs.move_id.sale_id:
                        if recs.move_id.sale_id.is_intercompany_sale != True:
                            qty_sold -= recs.quantity
                            qty_sold_parent -= recs.quantity
                            currency_val = recs.move_id.currency_id._convert(recs.price_subtotal, self.company_id.currency_id,
                                        self.company_id or self.env.company, recs.move_id.invoice_date or fields.Date.today())
                            sales -= currency_val
                            sales_parent -= currency_val
                            if recs.purchase_cost_price == 0:
                                cost -= recs.quantity * recs.product_id.standard_price
                                cost_parent -= recs.quantity * recs.product_id.standard_price
                            else:
                                cost -= recs.quantity * recs.purchase_cost_price
                                cost_parent -= recs.quantity * recs.purchase_cost_price
                    else:
                        qty_sold -= recs.quantity
                        qty_sold_parent -= recs.quantity
                        currency_val = recs.move_id.currency_id._convert(recs.price_subtotal, self.company_id.currency_id,
                                    self.company_id or self.env.company, recs.move_id.invoice_date or fields.Date.today())
                        sales -= currency_val
                        sales_parent -= currency_val
                        if recs.purchase_cost_price == 0:
                            cost -= recs.quantity * recs.product_id.standard_price
                            cost_parent -= recs.quantity * recs.product_id.standard_price
                        else:
                            cost -= recs.quantity * recs.purchase_cost_price
                            cost_parent -= recs.quantity * recs.purchase_cost_price
                    
                if qty_sold and sales:
                    margin_val = (sales * qty_sold) - (cost * qty_sold)
                    margin = (margin_val / (sales * qty_sold)) * 100
                    product_list.append((0,0,{
                        'categ_id': chilld_category.id,
                        'qty_sold': "%.2f" % float(qty_sold),
                        'sales': "%.2f" % float(sales),
                        'cost': "%.2f" % float(cost),
                        'profit': "%.2f" % float(sales - cost),
                        'margin': "%.2f" % float(margin),
                    }))
            if qty_sold_parent and sales_parent:
                margin_val_parent = (sales_parent * qty_sold_parent) - (cost_parent * qty_sold_parent)
                margin_parent = (margin_val_parent / (sales_parent * qty_sold_parent)) * 100
                product_list.append((0,0,{
                        'categ_id': parent_category.id,
                        'qty_sold': "%.2f" % float(qty_sold_parent),
                        'sales': "%.2f" % float(sales_parent),
                        'cost': "%.2f" % float(cost_parent),
                        'profit': "%.2f" % float(sales_parent - cost_parent),
                        'margin': "%.2f" % float(margin_parent),
                        'is_parent':True,
                    }))
        if product_list:
            self.update({'report_product_profit_detail_ids':product_list}) 
        else:
            self.report_product_profit_detail_ids = False

        product_list_val = []
        total_categ_ids = self.env['product.category'].search([('parent_id','!=',False),('name','not ilike','Charge')],order='seq_no asc')
        for parent_category in total_categ_ids:
            qty_sold_parent = 0.0
            sales_parent = 0.0
            cost_parent = 0.0
            product_ids = self.env['product.product'].search([('categ_id','=',parent_category.id),('active','=',True)])
            for chilld_category in product_ids:
                qty_sold = 0.0
                sales = 0.0
                cost = 0.0
                # for invoices
                if self.to_date <= datetime.strptime('2022-12-31','%Y-%m-%d').date():
                    line_ids = self.env['account.move.line'].search([('move_id.state','=','posted'),('move_id.invoice_date','>=',self.from_date),
                        ('move_id.invoice_date','<=',self.to_date),('product_id','=',chilld_category.id),('move_id.move_type','=','out_invoice'),
                        ('move_id.company_id','=',self.company_id.id),('account_id','=',income_account_id),('is_foc_line','=',False),('is_foc_product','=',False)])
                else:
                    line_ids = self.env['account.move.line'].search([('move_id.state','=','posted'),('move_id.invoice_date','>=',self.from_date),
                    ('move_id.invoice_date','<=',self.to_date),('product_id','=',chilld_category.id),('move_id.move_type','=','out_invoice'),
                    ('move_id.company_id','=',self.company_id.id),('account_id','=',income_account_id)])
                for recs in line_ids:
                    if recs.move_id.sale_id:
                        if recs.move_id.sale_id.is_intercompany_sale != True:
                            qty_sold += recs.quantity
                            qty_sold_parent += recs.quantity
                            currency_val = recs.move_id.currency_id._convert(recs.price_subtotal, self.company_id.currency_id,
                                        self.company_id or self.env.company, recs.move_id.invoice_date or fields.Date.today())
                            sales += currency_val
                            sales_parent += currency_val
                            if recs.purchase_cost_price == 0:
                                cost += recs.quantity * recs.product_id.standard_price
                                cost_parent += recs.quantity * recs.product_id.standard_price
                            else:
                                cost += recs.quantity * recs.purchase_cost_price
                                cost_parent += recs.quantity * recs.purchase_cost_price
                    else:
                        qty_sold += recs.quantity
                        qty_sold_parent += recs.quantity
                        currency_val = recs.move_id.currency_id._convert(recs.price_subtotal, self.company_id.currency_id,
                                    self.company_id or self.env.company, recs.move_id.invoice_date or fields.Date.today())
                        sales += currency_val
                        sales_parent += currency_val
                        if recs.purchase_cost_price == 0:
                            cost += recs.quantity * recs.product_id.standard_price
                            cost_parent += recs.quantity * recs.product_id.standard_price
                        else:
                            cost += recs.quantity * recs.purchase_cost_price
                            cost_parent += recs.quantity * recs.purchase_cost_price
                # for Credit Notes
                if self.to_date <= datetime.strptime('2022-12-31','%Y-%m-%d').date():
                    line_ids = self.env['account.move.line'].search([('move_id.state','=','posted'),('move_id.invoice_date','>=',self.from_date),
                        ('move_id.invoice_date','<=',self.to_date),('product_id','=',chilld_category.id),('move_id.move_type','=','out_refund'),
                        ('move_id.company_id','=',self.company_id.id),('account_id','=',income_account_id),('is_foc_line','=',False),('is_foc_product','=',False)])
                else:
                    line_ids = self.env['account.move.line'].search([('move_id.state','=','posted'),('move_id.invoice_date','>=',self.from_date),
                        ('move_id.invoice_date','<=',self.to_date),('product_id','=',chilld_category.id),('move_id.move_type','=','out_refund'),
                        ('move_id.company_id','=',self.company_id.id),('account_id','=',income_account_id)])
                for recs in line_ids:
                    if recs.move_id.sale_id:
                        if recs.move_id.sale_id.is_intercompany_sale != True:
                            qty_sold -= recs.quantity
                            qty_sold_parent -= recs.quantity
                            currency_val = recs.move_id.currency_id._convert(recs.price_subtotal, self.company_id.currency_id,
                                        self.company_id or self.env.company, recs.move_id.invoice_date or fields.Date.today())
                            sales -= currency_val
                            sales_parent -= currency_val
                            if recs.purchase_cost_price == 0:
                                cost -= recs.quantity * recs.product_id.standard_price
                                cost_parent -= recs.quantity * recs.product_id.standard_price
                            else:
                                cost -= recs.quantity * recs.purchase_cost_price
                                cost_parent -= recs.quantity * recs.purchase_cost_price
                    else:
                        qty_sold -= recs.quantity
                        qty_sold_parent -= recs.quantity
                        currency_val = recs.move_id.currency_id._convert(recs.price_subtotal, self.company_id.currency_id,
                                    self.company_id or self.env.company, recs.move_id.invoice_date or fields.Date.today())
                        sales -= currency_val
                        sales_parent -= currency_val
                        if recs.purchase_cost_price == 0:
                            cost -= recs.quantity * recs.product_id.standard_price
                            cost_parent -= recs.quantity * recs.product_id.standard_price
                        else:
                            cost -= recs.quantity * recs.purchase_cost_price
                            cost_parent -= recs.quantity * recs.purchase_cost_price

                if qty_sold and sales:
                    margin_val = (sales * qty_sold) - (cost * qty_sold)
                    margin = (margin_val / (sales * qty_sold)) * 100
                    product_list_val.append((0,0,{
                        'code':chilld_category.default_code,
                        'name': chilld_category.name,
                        'qty_sold': "%.2f" % float(qty_sold),
                        'sales': "%.2f" % float(sales),
                        'cost': "%.2f" % float(cost),
                        'profit': "%.2f" % float(sales - cost),
                        'margin': "%.2f" % float(margin),
                    }))
            if qty_sold_parent and sales_parent:
                margin_val_parent = (sales_parent * qty_sold_parent) - (cost_parent * qty_sold_parent)
                margin_parent = (margin_val_parent / (sales_parent * qty_sold_parent)) * 100
                product_list_val.append((0,0,{
                        'name': 'Total / ' + str(parent_category.name),
                        'qty_sold': "%.2f" % float(qty_sold_parent),
                        'sales': "%.2f" % float(sales_parent),
                        'cost': "%.2f" % float(cost_parent),
                        'profit': "%.2f" % float(sales_parent - cost_parent),
                        'margin': "%.2f" % float(margin_parent),
                        'is_parent':True,
                    }))
        if product_list_val:
            self.update({'report_product_wise_detail_ids':product_list_val}) 
        else:
            self.report_product_wise_detail_ids = False
        # return {
        #     'view_mode': 'form',
        #     'res_model': 'product.profit.report',
        #     'res_id': self.id,
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        #     }


    def print_report_values(self):
        self.compute_reports_all()
        return self.env.ref('acc_stock.product_profit_report_pdf').report_action(self)


class ReportProductProfitDetails(models.TransientModel):
    _name = 'report.product.profit.details'
    _description = 'Report Product Profit Details'
    
    header_id = fields.Many2one('product.profit.report')
    categ_id = fields.Many2one('product.category', 'Description')
    qty_sold = fields.Float("Quantity Sold")
    sales = fields.Float("Sales")
    cost = fields.Float("Cost")
    profit = fields.Float("Profit")
    margin = fields.Float("Margin")
    is_parent = fields.Boolean("Is Parent")

class ReportProductWiseDetails(models.TransientModel):
    _name = 'report.product.wise.details'
    _description = 'Report Product Wise Details'
    
    header_id = fields.Many2one('product.profit.report')
    code = fields.Char("Product Code")
    name = fields.Char('Description')
    qty_sold = fields.Float("Quantity Sold")
    sales = fields.Float("Sales")
    cost = fields.Float("Cost")
    profit = fields.Float("Profit")
    margin = fields.Float("Margin")
    is_parent = fields.Boolean("Is Parent")

from odoo import fields,api,models
from calendar import monthrange
import calendar,time
from datetime import datetime,date
from odoo.exceptions import UserError,ValidationError

class TopSellingProducts(models.TransientModel):
    _name = 'top.selling.products'
    _description = 'Top Selling Products'
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    categ_id = fields.Many2one('product.category', 'Commodity')
    brand_id = fields.Many2one('product.category', 'Brand')
    order_by = fields.Selection([
        ('quantity', 'Quantity'),
        ('value', 'Value'),('all', 'All Products')], string='Filter By', default='value')
    count = fields.Float('Count', default=15)
    brand_wise_page_break = fields.Boolean("Brand wise Page-Break")
    report_product_detail_ids = fields.One2many('report.product.details','header_id')
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    crt_date = fields.Date(
    'Report Date',
    readonly = True,
    default = date.today())

    @api.onchange('categ_id')
    def compute_brand_id(self):
        self.brand_id = False
        if self.categ_id:
            return {'domain': {'brand_id': [('parent_id','=',self.categ_id.id)]}}
        else:
            self.brand_id = False
            return {'domain': {'brand_id': [('id','=',False)]}}

    @api.onchange('brand_id','company_id','order_by','count','categ_id')
    def update_details(self):
        self.report_product_detail_ids = False

    def get_brand_list(self):
        brand_list = []
        for lines in self.report_product_detail_ids:
            brand_list.append(lines.brand_id.id)
        brand_list = [i for n, i in enumerate(brand_list) if i not in brand_list[:n]]
        return brand_list

    def get_brand_name(self,brand_id):
        brand_name = ''
        brand_name = self.env['product.category'].search([('id','=',brand_id)]).name
        return brand_name

    def get_quantity_total(self,brand_id):
        total_qty = 0
        for rec in self.report_product_detail_ids:
            if rec.brand_id.id == brand_id:
                total_qty += rec.qty
        return "{:,.2f}".format(total_qty)

    def get_value_total(self,brand_id):
        total_val = 0
        for rec in self.report_product_detail_ids:
            if rec.brand_id.id == brand_id:
                total_val += rec.total_value
        return "{:,.2f}".format(total_val)

    def get_location_val(self,product_id):
        location_val = []
        location_string = ''
        quant_ids = self.env['stock.quant'].search([('product_id','=',product_id),('location_id.usage','=', 'internal'),('company_id','=', self.company_id.id)])
        for rec in quant_ids:
            location_val.append(rec.location_id.complete_name)
        location_val = [*set(location_val)]
        location_string = ' , '.join([str(elem) for elem in location_val])
        return location_string

    def compute_reports_all(self):
        self.report_product_detail_ids = False
        limit_count = self.count
        lines_val = []
        domain = []
        value_ids = ''
        if self.from_date and not self.to_date:
            domain = [('date','>=',self.from_date)]
        if self.to_date and not self.from_date:
            domain = [('date','<=',self.to_date)]
        if self.from_date and self.to_date:
            domain = [('date','>=',self.from_date),('date','<=',self.to_date)]
        if self.order_by == 'all':
            value_ids = self.env['stock.valuation.layer'].read_group(domain, fields=['product_id','value','quantity'], groupby=['product_id'], orderby='value desc')
        if self.order_by == 'value':
            value_ids = self.env['stock.valuation.layer'].read_group([], fields=['product_id','value','quantity'], groupby=['product_id'], orderby='value desc', limit=limit_count)
        if self.order_by == 'quantity':
            value_ids = self.env['stock.valuation.layer'].read_group([], fields=['product_id','value','quantity'], groupby=['product_id'], orderby='quantity desc', limit=limit_count)
            
        for values in value_ids:
            layer_id = self.env['stock.valuation.layer'].search(values['__domain'],limit=1)
            if not self.brand_id:
                lines_val.append((0,0,{
                            'product_id': layer_id.product_id.id,
                            'code':layer_id.product_id.default_code,
                            'description':layer_id.product_id.name,
                            'brand_id':layer_id.product_id.categ_id.id,
                            'qty':values['quantity'],
                            'total_value':values['value'],
                        }))
            else:
                if self.brand_id.id == layer_id.product_id.categ_id.id:
                    lines_val.append((0,0,{
                            'product_id': layer_id.product_id.id,
                            'code':layer_id.product_id.default_code,
                            'description':layer_id.product_id.name,
                            'brand_id':layer_id.product_id.categ_id.id,
                            'qty':values['quantity'],
                            'total_value':values['value'],
                        }))

        if lines_val:
            self.update({'report_product_detail_ids':lines_val}) 
        else:
            self.report_product_detail_ids = False

    def print_report_values(self):
        self.compute_reports_all()
        return self.env.ref('acc_stock.top_selling_products_report_pdf').report_action(self)


class ReportProductDetails(models.TransientModel):
    _name = 'report.product.details'
    _description = 'Report Product Details'
    
    header_id = fields.Many2one('top.selling.products')
    product_id = fields.Many2one('product.product',"Product")
    code = fields.Char('Code')
    description = fields.Char('Description')
    brand_id = fields.Many2one('product.category', 'Brand')
    qty = fields.Float("Quantity")
    total_value = fields.Float("Total Value")

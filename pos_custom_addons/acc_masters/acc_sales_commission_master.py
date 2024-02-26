from odoo import fields,api,models
from calendar import monthrange
import calendar,time
from datetime import datetime,date
from odoo.exceptions import UserError,ValidationError

b = []
for a in range(2020, 2050):
    first = []
    first.append(str(a))
    first.append(str(a))
    b.append(tuple(first))

class AccSalesCommission(models.Model):
    _name = "acc.sales.commission"
    _order = "crt_date desc"

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('acc.sales.commission')
        return super(AccSalesCommission, self).create(vals)

    def write(self, vals):
        vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
        return super(AccSalesCommission, self).write(vals)

    @api.model
    def _get_last_year_name(self):
        from datetime import datetime
        currentMonth = datetime.now().year
        res=str(currentMonth)
        return res

    @api.model
    def _get_last_month_name(self):
        from datetime import datetime
        if datetime.now().month == 1:
            currentMonth = 1
        else:   
            currentMonth = datetime.now().month
        res=str(currentMonth)
        return res

    name = fields.Char('Name')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    total_amt = fields.Float('Total Amount',compute='_get_total_amt',store=True)
    categ_id = fields.Many2one('product.category', 'Commodity')
    sales_person_ids = fields.Many2many('res.users','sale_person_history','user_id_rel','user_id','Sales Person')
    report_category_ids = fields.One2many('report.category.details','header_id')
    report_commision_ids = fields.One2many('report.sale.commission.details','header_id')
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
    date_start = fields.Date(
        'Date From',
        default = False,
        readonly=False,
        required=True,
        compute='_get_date',store=True)
    date_end = fields.Date(
        'Date To',
        default = False,
        readonly=False,
        required=True,
        compute='_get_date',store=True)
    month = fields.Char(
        'Month',
        compute='_get_date',store=True)
    month_name = fields.Selection([('1','January'),('2','February'),('3','March'),('4','April'),('5','May'),('6','June'),('7','July'),
                            ('8','August'),('9','September'),('10','October'),('11','November'),('12','December')],'Starting Month', readonly=False)
                            
    year = fields.Selection(b, 'Year', readonly=False, default=lambda self: self._get_last_year_name())

    @api.depends('report_category_ids')
    def _get_total_amt(self):
        for rec in self:
            rec.total_amt = 0.0
            total_amount = 0.0
            for lines_categ in rec.report_category_ids:
                total_amount += lines_categ.category_amt
            rec.total_amt = total_amount

    @api.depends('month_name','year')
    def _get_date(self):
        from datetime import date
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        for h in self:
            if h.month_name and h.year:
                h.date_start= date(day=1, month=int(h.month_name), year=int(h.year))
                h.month = date(day=1, month=int(h.month_name), year=int(h.year)).strftime('%B-%Y')
                date_end=h.date_start + relativedelta(months=11)
                month_date = date(int(date_end.year), int(date_end.month), 1)
                self.date_end = month_date.replace(day = calendar.monthrange(month_date.year, month_date.month)[1])

    @api.onchange('categ_id')
    def compute_reports_brand_details(self):
        self.report_category_ids = False
        category_list = []
        category_ids = ''
        if self.categ_id:
            category_ids = self.env['product.category'].search([('parent_id','=',self.categ_id.id)])
        if category_ids:
            for category_id in category_ids:
                category_list.append((0,0,{
                            'categ_id': category_id.id,
                        }))
        if category_list:
            self.update({'report_category_ids':category_list}) 
        else:
            self.report_category_ids = False

    @api.onchange('company_id','month_name','year','total_amt','categ_id')
    def onchange_reports(self):
        self.report_commision_ids = False
        self.compute_reports()

    def compute_reports(self):
        from datetime import date
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        month_limit = 1
        update_date = self.date_start
        if not self.report_commision_ids and self.date_start:
            while month_limit <= 12:
                sale_date_start= date(day=1, month=int(update_date.month), year=int(update_date.year))
                if int(update_date.month) == 12:
                    month=1
                    year=int(update_date.year)+1
                else:
                    month=int(update_date.month)+1
                    year=int(update_date.year)
                sale_date_end=date(day=1, month=month, year=year) - timedelta(days=1)
                total_val = 0.0
                line_ids = self.env['sale.order.line'].search([('order_id.state','=','sale'),('order_id.date_order','>=',sale_date_start),
                                ('order_id.date_order','<=',sale_date_end),('categ_id.parent_id','=',self.categ_id.id)])
                for lines in line_ids:
                    currency_val = lines.order_id.currency_id._convert(lines.price_subtotal, self.company_id.currency_id,
                        self.company_id or self.env.company, lines.order_id.date_order or fields.Date.today())
                    total_val += currency_val

                self.env['report.sale.commission.details'].create({
                                        'header_id': self.id,
                                        'commission_date': update_date,
                                        'commission_amt': "%.2f" % float(self.total_amt/12),
                                        'actual_amount': "%.2f" % float(total_val),
                                        'as_on_date': date.today(),
                                        'diff_amt': "%.2f" % float(total_val - (self.total_amt/12)),
                                        'month_name': str(update_date.month),
                                        'year': str(update_date.year),
                                        'state': 'Open',
                                                })
                update_date = update_date + relativedelta(months=1)
                month_limit += 1
        if self.report_commision_ids:
            for target_lines in self.report_commision_ids:
                if target_lines.state == 'Open':
                    sale_date_start= date(day=1, month=int(target_lines.commission_date.month), year=int(target_lines.commission_date.year))
                    if int(target_lines.commission_date.month) == 12:
                        month=1
                        year=int(target_lines.commission_date.year)+1
                    else:
                        month=int(target_lines.commission_date.month)+1
                        year=int(target_lines.commission_date.year)
                    sale_date_end=date(day=1, month=month, year=year) - timedelta(days=1)
                    total_val_new = 0.0
                    line_ids = self.env['sale.order.line'].search([('order_id.state','=','sale'),('order_id.date_order','>=',sale_date_start),
                                    ('order_id.date_order','<=',sale_date_end),('categ_id.parent_id','=',self.categ_id.id)])
                    for lines in line_ids:
                        currency_val = lines.order_id.currency_id._convert(lines.price_subtotal, self.company_id.currency_id,
                            self.company_id or self.env.company, lines.order_id.date_order or fields.Date.today())
                        total_val_new += currency_val

                    target_lines.actual_amount = "%.2f" % float(total_val_new)
                    target_lines.as_on_date = date.today()
                    target_lines.diff_amt = "%.2f" % float(total_val_new - (self.total_amt/12))

class ReportCategoryDetails(models.Model):
    _name = 'report.category.details'
    _description = 'Report Category Details'
    
    header_id = fields.Many2one('acc.sales.commission')
    categ_id = fields.Many2one('product.category', 'Brand')
    category_amt = fields.Float('Target Amount')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.ref('base.main_company').currency_id)

class ReportSaleCommissionDetails(models.Model):
    _name = 'report.sale.commission.details'
    _description = 'Report Sale Commission Details'
    
    header_id = fields.Many2one('acc.sales.commission')
    commission_date = fields.Date(
        'Commission Date',store=True)
    commission_amt = fields.Float('Target Amount')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.ref('base.main_company').currency_id)
    as_on_date = fields.Date(
        'As On Date',store=True)
    actual_amount = fields.Monetary("Actual Amount",store=True)
    diff_amt = fields.Float('Difference Amount')
    month_name = fields.Selection([('1','January'),('2','February'),('3','March'),('4','April'),('5','May'),('6','June'),('7','July'),
                            ('8','August'),('9','September'),('10','October'),('11','November'),('12','December')],'Month', readonly=False)
                            
    year = fields.Char('Year')
    state = fields.Selection([('Open','Open'),('Closed','Closed')],'Status')
      

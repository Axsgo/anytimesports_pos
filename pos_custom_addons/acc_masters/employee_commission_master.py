from odoo import fields,api,models
from calendar import monthrange
import calendar,time
from datetime import datetime,date
from odoo.exceptions import UserError,ValidationError


class EmployeeCommission(models.Model):
    _name = "employee.commission"
    _order = "crt_date desc"

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('employee.commission')
        return super(EmployeeCommission, self).create(vals)

    def write(self, vals):
        vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': self.env.user.id})
        return super(EmployeeCommission, self).write(vals)

    name = fields.Char('Name')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    total_amt = fields.Monetary('Total Amount',compute='_get_total_amt',store=True, currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.ref('base.main_company').currency_id)
    state = fields.Selection([('draft','Draft'),('approved','Approved'),('closed','Closed')],'Status',default='draft')
    report_employee_commision_ids = fields.One2many('report.employee.commission.details','header_id')
    report_employee_commision_line_ids = fields.One2many('report.employee.commission.details.line','header_id')
    enable_line = fields.Boolean("Enable Line",compute='_check_line')
    line_employee_ids = fields.Many2many('hr.employee','report_employee_commision_line_rel','employee_id','report_id','Employees',compute='_get_line_employee')
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
    ap_rej_date = fields.Datetime('Approved/Closed Date', readonly = True)
    ap_rej_user_id = fields.Many2one(
    'res.users', 'Approved/Closed By', readonly = True)
    date_start = fields.Date(
        'Date From',
        default = False,
        required=True,store=True)
    date_end = fields.Date(
        'Date To',
        default = False,
        required=True,store=True)

    def entry_approve(self):
        self.write({'state': 'approved',
                    'ap_rej_user_id': self.env.user.id,
                    'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})

    def entry_close(self):
        self.write({'state': 'closed',
                    'ap_rej_user_id': self.env.user.id,
                    'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})

    def entry_draft(self):
        self.write({'state':'draft'})

    @api.depends('report_employee_commision_ids')
    def _get_total_amt(self):
        for rec in self:
            rec.total_amt = 0.0
            total_amount = 0.0
            for lines in rec.report_employee_commision_ids:
                total_amount += lines.variable_amount
            rec.total_amt = total_amount

    @api.depends('report_employee_commision_ids','report_employee_commision_ids.commission_type','report_employee_commision_ids.employee_id')
    def _check_line(self):
        for rec in self:
            if rec.report_employee_commision_ids and any([x.commission_type == 'sales_range' for x in rec.report_employee_commision_ids]):
                rec.enable_line = True
            else:
                rec.enable_line = False

    @api.depends('report_employee_commision_ids','report_employee_commision_ids.commission_type','report_employee_commision_ids.employee_id','enable_line')
    def _get_line_employee(self):
        for rec in self:
            if rec.report_employee_commision_ids and rec.enable_line == True:
                print([x.id for x in rec.report_employee_commision_ids if x.commission_type == 'sales_range'],'&&&&')
                rec.line_employee_ids = [(6,0,[x.employee_id.id for x in rec.report_employee_commision_ids if x.commission_type == 'sales_range'])]
            else:
                rec.line_employee_ids = False

class ReportEmployeeCommissionDetails(models.Model):
    _name = 'report.employee.commission.details'
    _description = 'Report Employee Commission Details'
    
    header_id = fields.Many2one('employee.commission')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    # is_fixed = fields.Boolean('Is Fixed Commission',default=False)
    commission_type = fields.Selection([('sales','Sales'),('fixed','Fixed'),('combined','Combined Sales'),('sales_range','Individual Sales')])
    variable_amount = fields.Monetary('Commission Target', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.ref('base.main_company').currency_id)
      
class ReportEmployeeCommissionDetailsLine(models.Model):
    _name = 'report.employee.commission.details.line'
    _description = 'Report Employee Commission Details Line'

    header_id = fields.Many2one('employee.commission')
    employee_id = fields.Many2one('hr.employee','Employee')
    # employee_ids = fields.Many2many('hr.employee','Employees',related='header_id.line_employee_ids')
    sales_range = fields.Float("Sales Range")
    variable_amount = fields.Float("Commission Target",currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.ref('base.main_company').currency_id)
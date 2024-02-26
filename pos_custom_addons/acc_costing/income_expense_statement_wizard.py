from odoo import fields,api,models
from calendar import monthrange
import calendar,time
from datetime import datetime,date
from odoo.exceptions import UserError,ValidationError

class IncomeStatementReport(models.TransientModel):
    _name = 'income.statement.report'
    _description = 'Income Statement Report'
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    report_income_ids = fields.One2many('income.details','header_id')
    crt_date = fields.Date(
    'Creation Date',
    readonly = True,
    default = date.today())

    @api.onchange('from_date','to_date')
    def compute_reports(self):
        self.report_income_ids = False
        inv = []
        acc_ids = self.env['account.account'].search([('internal_group','=','income')])
        for acc_id in acc_ids:
            invoice_ids = ''
            if not self.from_date and not self.to_date:
                invoice_ids = self.env['account.move.line'].search([('account_id','=',acc_id.id),('parent_state','=','posted')])
            elif self.from_date and not self.to_date:
                invoice_ids = self.env['account.move.line'].search([('account_id','=',acc_id.id),('parent_state','=','posted'),('date','>=',self.from_date)])
            elif self.from_date and self.to_date:
                invoice_ids = self.env['account.move.line'].search([('account_id','=',acc_id.id),('parent_state','=','posted'),('date','>=',self.from_date),('date','<=',self.to_date)])
            if invoice_ids:
                tot_amt = 0
                for invoice_id in invoice_ids:
                    tot_amt += invoice_id.price_subtotal
                inv.append((0,0,{
                        'category': invoice_id.account_id.user_type_id.name,
                        'account': invoice_id.account_id.code +'-'+invoice_id.account_id.name,
                        'acc_code' : invoice_id.account_id.code,
                        'total':"%.2f" % float(tot_amt),
                    }))

        if inv:
            self.update({'report_income_ids':inv}) 
        else:
            self.report_income_ids = False

    def print_report_values(self):
        return self.env.ref('acc_costing.income_statement_report_pdf').report_action(self)

class IncomeDetails(models.TransientModel):
    _name = 'income.details'
    _description = 'Income Details'
    
    header_id = fields.Many2one('income.statement.report')
    category = fields.Char("Category")
    account = fields.Char("Account")
    acc_code = fields.Char("Account Code")
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.ref('base.main_company').currency_id)
    total = fields.Monetary("Total Amount")


class ExpenseStatementReport(models.TransientModel):
    _name = 'expense.statement.report'
    _description = 'Expense Statement Report'
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    report_expense_ids = fields.One2many('expense.details','header_id')
    crt_date = fields.Date(
    'Creation Date',
    readonly = True,
    default = date.today())

    @api.onchange('from_date','to_date')
    def compute_reports(self):
        self.report_expense_ids = False
        inv = []
        acc_ids = self.env['account.account'].search([('internal_group','=','expense')])
        for acc_id in acc_ids:
            invoice_ids = ''
            if not self.from_date and not self.to_date:
                invoice_ids = self.env['account.move.line'].search([('account_id','=',acc_id.id),('parent_state','=','posted')])
            elif self.from_date and not self.to_date:
                invoice_ids = self.env['account.move.line'].search([('account_id','=',acc_id.id),('parent_state','=','posted'),('date','>=',self.from_date)])
            elif self.from_date and self.to_date:
                invoice_ids = self.env['account.move.line'].search([('account_id','=',acc_id.id),('parent_state','=','posted'),('date','>=',self.from_date),('date','<=',self.to_date)])
            if invoice_ids:
                tot_amt = 0
                for invoice_id in invoice_ids:
                    tot_amt += invoice_id.price_subtotal
                inv.append((0,0,{
                        'category': invoice_id.account_id.user_type_id.name,
                        'account': invoice_id.account_id.code +'-'+invoice_id.account_id.name,
                        'acc_code' : invoice_id.account_id.code,
                        'total':"%.2f" % float(tot_amt),
                    }))

        if inv:
            self.update({'report_expense_ids':inv}) 
        else:
            self.report_expense_ids = False

    def print_report_values(self):
        return self.env.ref('acc_costing.expense_statement_report_pdf').report_action(self)

class ExpenseDetails(models.TransientModel):
    _name = 'expense.details'
    _description = 'Expense Details'
    
    header_id = fields.Many2one('expense.statement.report')
    category = fields.Char("Category")
    account = fields.Char("Account")
    acc_code = fields.Char("Account Code")
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.ref('base.main_company').currency_id)
    total = fields.Monetary("Total Amount")

    




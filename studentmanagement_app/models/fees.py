from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class StudentFees(models.Model):
    _name = "student.fees"
    _description = "Student Fees Model"
    _order = "id desc"

    student_id = fields.Many2one("student.model", string="Student", required=True)
    class_id = fields.Many2one("batch.class", related="student_id.class_id", store=True, readonly=True)

    month = fields.Selection([(str(i), str(i)) for i in range(1, 13)], required=True)
    year = fields.Char(string="Year", default=lambda self: str(date.today().year), required=True)
    monthly_fee = fields.Float(string="Monthly Fee", related="student_id.yearly_fee", store=True, readonly=True)
    due_id = fields.Many2one("edu.fee.due", string="Fee Due")

    def action_generate_fee_due(self):
        """Generate fee due entry for this student & month."""
        FeeDue = self.env["edu.fee.due"]
        for fee in self:
            year = fee.year or str(date.today().year)
            existing = FeeDue.search([
                ('student_id', '=', fee.student_id.id),
                ('month', '=', fee.month),
                ('year', '=', year),
            ], limit=1)
            if existing:
                fee.due_id = existing.id
                continue

            due = FeeDue.create({
                'student_id': fee.student_id.id,
                'class_id': fee.class_id.id,
                'month': fee.month,
                'year': year,
            })
            fee.due_id = due.id



class FeeDue(models.Model):
    _name = "edu.fee.due"
    _description = "Monthly Fee Due"
    _order = "id desc"

    student_id = fields.Many2one("student.model", required=True)
    class_id = fields.Many2one("batch.class", related="student_id.class_id", store=True, readonly=True)

    month = fields.Selection(
        [(str(i), str(i)) for i in range(1, 13)],
        string="Month",
        required=True
    )
    year = fields.Char(string="Year", required=True, default=lambda self: str(date.today().year))

    amount = fields.Float(string="Monthly Amount", compute='_compute_amount', store=True)
    paid_amount = fields.Float(string="Paid", compute="_compute_paid_amount", store=True)
    balance_amount = fields.Float(string="Outstanding", compute="_compute_balance", store=True)

    monthly_status = fields.Selection([
        ('unpaid', "Unpaid"),
        ('paid', "Paid"),
    ], compute="_compute_monthly_status", store=True)

    yearly_status = fields.Selection([
        ('unpaid', "Unpaid"),
        ('partial', "Partial"),
        ('paid', "Paid"),
    ], compute="_compute_yearly_status", store=True)

    payment_ids = fields.One2many("edu.feepayment", "due_id", string="Payments")

    _sql_constraints = [
        ('uniq_due_per_student_month_year',
         'unique(student_id, month, year)',
         'A fee due for this student, month, and year already exists.')
    ]

    @api.depends('student_id.yearly_fee')
    def _compute_amount(self):
        for rec in self:
            yearly = rec.student_id.yearly_fee or 0.0
            rec.amount = yearly / 12.0 if yearly else 0.0

    @api.depends('payment_ids.paid_amount')
    def _compute_paid_amount(self):
        for rec in self:
            rec.paid_amount = sum(rec.payment_ids.mapped('paid_amount')) or 0.0

    @api.depends('amount', 'paid_amount')
    def _compute_balance(self):
        for rec in self:
            rec.balance_amount = (rec.amount or 0.0) - (rec.paid_amount or 0.0)

    @api.depends('amount', 'paid_amount', 'balance_amount')
    def _compute_monthly_status(self):
        for rec in self:
            if not rec.amount:
                rec.monthly_status = None
            elif rec.balance_amount == 0:
                rec.monthly_status = 'paid'
            else:
                rec.monthly_status = 'unpaid'

    @api.depends('student_id', 'year', 'amount', 'paid_amount')
    def _compute_yearly_status(self):
        for rec in self:
            if not rec.student_id or not rec.year:
                rec.yearly_status = None
                continue

            dues = self.search([
                ('student_id', '=', rec.student_id.id),
                ('year', '=', rec.year),
            ])

            total_due = sum(dues.mapped('amount')) or 0.0
            total_paid = sum(dues.mapped('paid_amount')) or 0.0

            if total_due == 0.0:
                rec.yearly_status = None
            elif total_paid == 0.0:
                rec.yearly_status = 'unpaid'
            elif total_paid < total_due:
                rec.yearly_status = 'partial'
            else:
                rec.yearly_status = 'paid'

    @api.constrains('student_id', 'month', 'year')
    def _check_duplicate_due(self):
        for rec in self:
            domain = [
                ('id', '!=', rec.id),
                ('student_id', '=', rec.student_id.id),
                ('month', '=', rec.month),
                ('year', '=', rec.year),
            ]
            if self.search_count(domain):
                raise ValidationError("A fee due for this student, month, and year already exists.")
class FeePayment(models.Model):
    _name = "edu.feepayment"
    _description = "Fee Payment Model"
    _order = "payment_date desc"

    student_id = fields.Many2one("student.model", required=True)
    due_id = fields.Many2one("edu.fee.due", string="Fee Due", required=True)
    class_id = fields.Many2one("batch.class", related="due_id.class_id", store=True, readonly=True)

    payment_date = fields.Date(default=fields.Date.today, required=True)
    paid_amount = fields.Float(string="Paid Amount", required=True)

    @api.constrains('student_id', 'due_id')
    def _check_student_matches_due(self):
        for rec in self:
            if rec.due_id and rec.student_id and rec.due_id.student_id != rec.student_id:
                raise ValidationError("Payment student must match the fee due's student.")

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if rec.due_id:
            rec.due_id.invalidate_recordset(['payment_ids'])
        return rec
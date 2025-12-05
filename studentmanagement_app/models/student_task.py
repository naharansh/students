from odoo import models,fields,api
from odoo.exceptions import ValidationError
from datetime import date
class Student(models.Model):
    _name="student.model"
    _description="Student"
    name=fields.Char(string="Student Name",required=True)
    student_id=fields.Char(string="Student ID",readonly=True)
    dob=fields.Date(string="Date of Birth")
    photo = fields.Binary(string="Photo")
    parent_name = fields.Char(string="Parent Name")
    parent_contact = fields.Char(string="Parent Contact")
    address = fields.Text(string="Address")
    class_id = fields.Many2one('batch.class', string="Class")
    status = fields.Selection([('active','Active'),('inactive','Inactive'),('alumni','Alumni')], default='active')
    yearly_fee=fields.Float(string='Yearly Fee')
    fee_due_ids = fields.One2many(
    'edu.fee.due',
    'student_id',
    string="Fee Due Records"
    )

    remaining_yearly_fee = fields.Float(
        string="Remaining Yearly Fee",
        compute="_compute_remaining_yearly_fee",
        store=True
    )

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            vals['student_id'] = self.env['ir.sequence'].next_by_code('student.model.code') or 'New'
        return super().create(vals_list)
    @api.constrains('class_id')
    def _check_class_capacity(self):
        for rec in self:
            if rec.class_id:
                cls = rec.class_id.sudo()
                count = self.env['student.model'].sudo().search_count([('class_id', '=', cls.id)])
                if cls.capacity and count > cls.capacity:
                    raise ValidationError(f"Cannot assign student to '{cls.name}': capacity of {cls.capacity} exceeded.")
    @api.depends('yearly_fee', 'fee_due_ids.paid_amount')
    def _compute_remaining_yearly_fee(self):
        for student in self:
            total_paid = sum(student.fee_due_ids.filtered(lambda d: d.year == str(date.today().year)).mapped('paid_amount'))
            student.remaining_yearly_fee = (student.yearly_fee or 0.0) - total_paid
   

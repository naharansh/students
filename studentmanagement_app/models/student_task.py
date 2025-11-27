from odoo import models,fields,api
from odoo.exceptions import ValidationError
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
    monthly_fee=fields.Float(string='Monthly Fee')
    # outstanding_fee= fields.Float(string="Outstanding Fee", compute='_compute_outstanding_fee', store=True)
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

    # @api.depends('monthly_fee')
    # def _compute_outstanding_fee(self):
    #     for rec in self :
    #             payments = sum(rec.env['edu.fee'].search([('student_id','=',rec.id)]).mapped('paid_amount'))
    #             rec.outstanding_fee = rec.monthly_fee - payments
    
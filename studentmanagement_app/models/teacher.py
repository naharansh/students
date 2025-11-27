from odoo import models, fields

class Teacher(models.Model):
    _name = 'edu.teacher'
    _description = 'Teacher'
    name = fields.Char(string="Teacher Name", required=True)
    employee_id = fields.Char(string="Employee ID", required=True)
    contact = fields.Char(string="Contact Number")
    email = fields.Char(string="Email")
    photo = fields.Binary(string="Photo")
    subject_ids = fields.Many2many('edu.subject', string="Subjects")
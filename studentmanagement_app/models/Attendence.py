from odoo import models,fields
class Attendence(models.Model):
    _name="edu.attendence"
    _description="Daily Attendence"
    class_id=fields.Many2one('batch.class',string="Class")
    student_id=fields.Many2one('student.model',string="Student")
    date = fields.Date(string="Date", default=fields.Date.today)
    status = fields.Selection([('present','Present'),('absent','Absent')], string="Status")
    notes = fields.Text(string="Notes")
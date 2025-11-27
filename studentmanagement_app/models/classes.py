from odoo import models,fields,api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class ClassBatch(models.Model):
    _name='batch.class'
    _description='Class/Batch'

    name = fields.Char(string='Class Name', required=True)
    code = fields.Char(string='Class Id', readonly=True)
    teacher_id = fields.Many2one('edu.teacher', string="Class Teacher")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    student_count = fields.Integer(
        string="Number of Students",
        compute='_compute_student_count'
    )

    capacity = fields.Integer(string="Capacity")

    student_ids = fields.One2many(
        'student.model',
        'class_id',
        string="Students"
    )

    timetable_ids = fields.One2many(
        'edu.class.timetable',
        'class_id',
        string="Timetable"
    )

    # Auto-generate class code
    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('batch.class.code') or 'New'
        return super().create(vals_list)

    # Compute student count
    @api.depends('student_ids')
    def _compute_student_count(self):
        for rec in self:
            rec.student_count = len(rec.student_ids)

    @api.constrains('capacity')
    def _check_capacity(self):
        for rec in self:
            if rec.capacity < 0:
                raise ValidationError("Capacity must be a positive number.")

    @api.constrains('student_ids', 'capacity')
    def _check_student_capacity(self):
        for rec in self:
            _logger.info("Checking capacity for class: %s", rec.name)
            if rec.capacity and len(rec.student_ids) > rec.capacity:
                raise ValidationError("Number of students cannot exceed class capacity.")

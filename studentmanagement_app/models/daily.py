from odoo import models, fields, api

class DailyRecord(models.Model):
    _name = "edu.daily.record"
    _description = "Daily Record of Student Activities"
    _order = "date desc"

    date = fields.Date(default=fields.Date.today, required=True, string="Date")
    class_id = fields.Many2one('batch.class', string="Class/Batch", required=True)
    subject_id = fields.Many2one('edu.subject', string="Subject", required=True)
    teacher_id = fields.Many2one('edu.teacher', string="Teacher", required=True)
    topic = fields.Char(string="Topic Covered")
    notes = fields.Text(string="Additional Notes")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], default='draft', string="Status")

    student_line_ids = fields.One2many(
        'edu.daily.record.line',
        'record_id',
        string="Student Records"
    )

    @api.onchange('class_id')
    def _onchange_class_id(self):
        if self.class_id:
            self.student_line_ids = [(5, 0, 0)]  # clear existing lines
            lines = []
            for student in self.class_id.student_ids:
                lines.append((0, 0, {
                    'student_id': student.id,
                    'status': 'present'
                }))
            self.student_line_ids = lines

    def action_confirm(self):
        self.state = 'confirmed'

    def action_reset(self):
        self.state = 'draft'


class DailyRecordLine(models.Model):
    _name = "edu.daily.record.line"
    _description = "Daily Record Line for Each Student"

    record_id = fields.Many2one(
        'edu.daily.record',
        string="Daily Record",
        required=True,
        ondelete='cascade'
    )
    student_id = fields.Many2one('student.model', string="Student", required=True)
    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent')
    ], default='present', string="Attendance Status")
    remarks = fields.Text(string="Remarks")
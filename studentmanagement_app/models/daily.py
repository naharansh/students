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
        ('done', 'Done'),
       
    ], default='draft', string="Status")

    student_line_ids = fields.One2many(
        'edu.daily.record.line',
        'record_id',
        string="Student Records"
    )
    student_id = fields.Many2one('student.model', string="Student", help="Used to filter attendance lines for this student")
    @api.onchange('class_id')
    def _onchange_class_id(self):
        lines = []
        if self.class_id:
         for student in self.class_id.student_ids:
            lines.append((0, 0, {
               'record_id': self.id,       
                'student_id': student.id,
                'status': 'present',
           }))
  # Clear existing lines and add new ones safely
        self.student_line_ids = [(5, 0, 0)] + lines
    def action_confirm(self):
        self.state = 'done'

    def action_reset(self):
        self.state = 'draft'
    # @api.model
    # def default_get(self, fields):
    #     res = super().default_get(fields)
    #     student = self.env['student.model'].search([('student_id', '=', self.env.student_id)], limit=1)
    #     if student:
    #          res['student_id'] = student.student_id
    #     return res
    
   


class DailyRecordLine(models.Model):
    _name = "edu.daily.record.line"
    _description = "Daily Record Line for Each Student"

    record_id = fields.Many2one(
        'edu.daily.record',
        string="Daily Record",
        required=True,
        ondelete='cascade'
    )
    student_id = fields.Many2one('student.model', string="Student",)
    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent')
    ], default='present', string="Attendance Status")
    remarks = fields.Text(string="Remarks")
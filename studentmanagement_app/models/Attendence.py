from odoo import models, fields, api

class Attendence(models.Model):
    _name = "edu.attendence"
    _description = "Daily Attendance"

    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'),
        ('07', 'July'), ('08', 'August'), ('09', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string="Month", required=True)
    year = fields.Integer(string="Year", default=lambda self: fields.Date.today().year)

    class_id = fields.Many2one('batch.class', string="Class/Batch", required=True)
    line_ids = fields.One2many('edu.monthly.attendence.line', 'report_id', string="Attendance Lines")

    def action_generate(self):
        self.line_ids = [(5, 0, 0)]  # clear old lines
        query = """
                SELECT l.student_id,
                    SUM(CASE WHEN l.status='present' THEN 1 ELSE 0 END) AS present_days,
                    SUM(CASE WHEN l.status='absent' THEN 1 ELSE 0 END) AS absent_days
                FROM edu_daily_record_line AS l
                INNER JOIN edu_daily_record AS r ON r.id = l.record_id
                WHERE r.class_id = %s
                AND TO_CHAR(r.date, 'MM') = %s
                AND TO_CHAR(r.date, 'YYYY') = %s
                GROUP BY l.student_id
                ORDER BY l.student_id
                """


        self.env.cr.execute(query, (self.class_id.id, self.month, str(self.year)))
        result = self.env.cr.fetchall()
        for row in result:
            self.env['edu.monthly.attendence.line'].create({
                'report_id': self.id,
                'student_id': row[0],
                'present_days': row[1],
                'absent_days': row[2],
            })
    def action_print_pdf(self):
            return self.env.ref(
                 'studentmanagement_app.monthly_attendance_pdf'
             ).report_action(self)



class MonthlyAttendenceLine(models.Model):
    _name = "edu.monthly.attendence.line"
    _description = "Monthly Attendance Line"

    report_id = fields.Many2one("edu.attendence", string="Report", ondelete="cascade",readonly=True)
    student_id = fields.Many2one("student.model", string="Student",readonly=True)
    present_days = fields.Integer(string="Present Days",readonly=True)
    absent_days = fields.Integer(string="Absent Days",readonly=True)
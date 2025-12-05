from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


# ---------------------------
# CLASS TIMETABLE (WEEKLY)
# ---------------------------
class ClassTimetable(models.Model):
    _name = "edu.class.timetable"
    _description = "Class Weekly Timetable"
    _rec_name = "class_id"

    class_id = fields.Many2one("batch.class", string="Class", required=True)

    week_start = fields.Date(
        string="Week Start",
        related="class_id.start_date",
        readonly=True
    )

    week_end = fields.Date(
        string="Week End",
        compute="_compute_end_date",
        store=True
    )

    timetable_line_ids = fields.One2many(
        "edu.class.timetable.line",
        "timetable_id",
        string="Timetable Lines",
        copy=True
    )

    daily_class_ids = fields.One2many(
        "edu.class.daily",
        "timetable_id",
        string="Daily Class Auto Generated",
        copy=True
    )

    # ---------------------------
    # Compute Saturday automatically
    # ---------------------------
    @api.depends("week_start")
    def _compute_end_date(self):
        for rec in self:
            rec.week_end = (
                rec.week_start + timedelta(days=5)
                if rec.week_start else False
            )

    # ---------------------------
    # Auto-create 6 days (Mon-Sat)
    # ---------------------------
    def action_generate_week(self):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        self.ensure_one()
        self.timetable_line_ids.unlink()
        for day in days:
            self.env["edu.class.timetable.line"].create({
                "timetable_id": self.id,
                "day_name": day,
            })

    # ---------------------------
    # Open Daily Classes form
    # ---------------------------
    def action_add_daily_subjects(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Daily Classes",
            "res_model": "edu.class.daily",
            "view_mode": "form",
            "domain": [("timetable_id", "=", self.id)],
            "context": {
                "default_timetable_id": self.id,
                "default_class_id": self.class_id.id,
            },
        }
    def action_sync_daily_classes(self):
        """Auto-sync all timetable sessions into daily classes."""
        Daily = self.env["edu.class.daily"]
        
        for rec in self:
            # 1) Delete old daily classes for this timetable
            rec.daily_class_ids.unlink()

            # 2) Recreate daily classes from timetable sessions
            daily_vals = []

            for day in rec.timetable_line_ids:
                for session in day.session_ids:
                    daily_vals.append({
                        "timetable_id": rec.id,
                        "class_id": rec.class_id.id,
                        "date": day.date_of_day,
                        "teacher_id": session.teacher_id.id,
                        "subject_id": session.subject_id.id,
                        "start_time": session.start_time,
                        "end_time": session.end_time,
                        "room": session.room,
                    })

            Daily.create(daily_vals)

# ---------------------------
# DAILY CLASS
# ---------------------------
class DailyClass(models.Model):
    _name = "edu.class.daily"
    _description = "Daily Class Schedule"
    _order = "date, start_time"

    timetable_id = fields.Many2one("edu.class.timetable", string="Timetable", ondelete="cascade")
    class_id = fields.Many2one("batch.class", string="Class", required=True)
    date = fields.Date(string="Date", required=True, default=fields.Date.today)
    teacher_id = fields.Many2one("edu.teacher", string="Teacher")
    subject_id = fields.Many2one("edu.subject", string="Subject")
    start_time = fields.Float(string="Start Time", required=True)
    end_time = fields.Float(string="End Time", required=True)
    room = fields.Char(string="Room")

    duration = fields.Float(string="Duration (hrs)", compute="_compute_duration", store=True)
    week_range = fields.Char(string="Week Range", compute="_compute_week_range")

    @api.depends("start_time", "end_time")
    def _compute_duration(self):
        for rec in self:
            rec.duration = rec.end_time - rec.start_time if rec.end_time > rec.start_time else 0.0

    @api.depends("timetable_id.week_start", "timetable_id.week_end")
    def _compute_week_range(self):
        for rec in self:
            if rec.timetable_id.week_start and rec.timetable_id.week_end:
                start = rec.timetable_id.week_start.strftime("%b %d")
                end = rec.timetable_id.week_end.strftime("%b %d")
                rec.week_range = f"{start} – {end}"
            else:
                rec.week_range = ""

    @api.constrains("start_time", "end_time")
    def _check_times(self):
        for rec in self:
            if rec.start_time >= rec.end_time:
                raise ValidationError("Start time must be earlier than end time.")


# ---------------------------
# TIMETABLE LINE (DAY)
# ---------------------------
class TimetableLine(models.Model):
    _name = "edu.class.timetable.line"
    _description = "Class Timetable Line"

    timetable_id = fields.Many2one("edu.class.timetable", string="Timetable", required=True)
    day_name = fields.Selection([
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
    ], string="Day", required=True)

    date_of_day = fields.Date(string="Date", compute="_compute_date_of_day", store=True)

    session_ids = fields.One2many(
        'edu.class.timetable.session',
        'line_id',
        string="Sessions"
    )

    @api.depends("day_name", "timetable_id.week_start")
    def _compute_date_of_day(self):
        for rec in self:
            if rec.day_name and rec.timetable_id.week_start:
                weekday_index = [
                    "Monday", "Tuesday", "Wednesday",
                    "Thursday", "Friday", "Saturday"
                ].index(rec.day_name)
                rec.date_of_day = rec.timetable_id.week_start + timedelta(days=weekday_index)
            else:
                rec.date_of_day = False


# ---------------------------
# TIMETABLE SESSION (SUBJECT)
# ---------------------------
class TimetableSession(models.Model):
    _name = "edu.class.timetable.session"
    _description = "Timetable Session"

    line_id = fields.Many2one("edu.class.timetable.line", string="Day Line", required=True)
    teacher_id = fields.Many2one("edu.teacher", string="Teacher")
    subject_id = fields.Many2one("edu.subject", string="Subject")
    start_time = fields.Float(string="Start Time", required=True)
    end_time = fields.Float(string="End Time", required=True)
    room = fields.Char(string="Room")
    calendar_event_id = fields.Many2one("calendar.event", string="Calendar Event", ondelete="cascade")

    @api.model
    def create(self, vals):
        sessions = super(TimetableSession, self).create(vals)
        for session in sessions:
            session._create_or_update_event()
        return sessions

    def write(self, vals):
        res = super(TimetableSession, self).write(vals)
        for rec in self:
            rec._create_or_update_event()
        return res

    def _create_or_update_event(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                vals = {
                    "name": f"{rec.subject_id.name if rec.subject_id else 'Class'} ({rec.line_id.day_name})",
                    "start": rec.start_time,
                    "stop": rec.end_time,
                    "partner_ids": [(6, 0, [rec.teacher_id.id])] if rec.teacher_id else False,
                }
                if rec.calendar_event_id:
                    rec.calendar_event_id.write(vals)
                else:
                    event = self.env["calendar.event"].create(vals)
                    rec.calendar_event_id = event.id
    
    # AUTO SYNC WHEN SESSION CREATED
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        rec.timetable_line_id.timetable_id.action_sync_daily_classes()
        return rec

    # AUTO SYNC WHEN SESSION UPDATED
    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec.timetable_line_id.timetable_id.action_sync_daily_classes()
        return res

    # AUTO SYNC IN UI ONCHANGE
    @api.onchange('teacher_id', 'subject_id', 'start_time', 'end_time', 'room')
    def _onchange_session_fields(self):
        if self.timetable_line_id:
            self.timetable_line_id.timetable_id.action_sync_daily_classes()
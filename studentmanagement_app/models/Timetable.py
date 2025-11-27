from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


# ---------------------------------------------------------
# Timetable Main Model (Per Class / Week)
# ---------------------------------------------------------
class ClassTimetable(models.Model):
    _name = "edu.class.timetable"
    _description = "Class Weekly Timetable"
    _rec_name = "class_id"

    class_id = fields.Many2one("batch.class", string="Class", required=True)
    week_start = fields.Date(string="Week Start", required=True)
    week_end = fields.Date(string="Week End", compute="_compute_end_date", store=True)

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
    @api.depends("week_start")
    def _compute_end_date(self):
        for rec in self:
            rec.week_end = rec.week_start + timedelta(days=5) if rec.week_start else False
    def action_generate_week(self):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        self.ensure_one()
        self.timetable_line_ids.unlink()
        for day in days:
            self.env["edu.class.timetable.line"].create({
                "timetable_id": self.id,
                "day_name": day,
            })

    def action_generate_daily_classes(self):
        """ Auto-create daily sessions from timetable lines """
        self.ensure_one()

        self.daily_class_ids.unlink()

        for line in self.timetable_line_ids:
            for session in line.session_ids:
                self.env["edu.class.daily"].create({
                    "timetable_id": self.id,
                    "class_id": self.class_id.id,
                    "date": line.date_of_day,
                    "teacher_id": session.teacher_id.id,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "room": session.room,
                })



class DailyClass(models.Model):
    _name = "edu.class.daily"
    _description = "Daily Class Schedule"
    _order = "date, start_time"

    timetable_id = fields.Many2one("edu.class.timetable", string="Timetable", ondelete="cascade")
    class_id = fields.Many2one("batch.class", string="Class", required=True, ondelete="restrict")
    date = fields.Date(string="Date", required=True)
    teacher_id = fields.Many2one("edu.teacher", string="Teacher")
    subject_id = fields.Many2one("edu.subject", string="Subject")  # Optional: if subjects are tracked
    start_time = fields.Float(string="Start Time", required=True)
    end_time = fields.Float(string="End Time", required=True)
    room = fields.Char(string="Room / Location")
    duration = fields.Float(string="Duration (hrs)",compute="_compute_duration", store=True)
    week_range = fields.Char(string="Week Range",compute="_compute_week_range")
    @api.depends("timetable_id.week_start", "timetable_id.week_end")
    def _compute_week_range(self):
        for rec in self:
            if rec.timetable_id.week_start and rec.timetable_id.week_end:
                start = rec.timetable_id.week_start.strftime("%b %d")
                end = rec.timetable_id.week_end.strftime("%b %d")
                rec.week_range = f"{start} – {end}"
            else:
                rec.week_range = ""

    @api.depends("start_time", "end_time")
    def _compute_duration(self):
            for rec in self:
                if rec.start_time and rec.end_time and rec.end_time > rec.start_time:
                    rec.duration = rec.end_time - rec.start_time
                else:
                    rec.duration = 0.0

    @api.constrains("start_time", "end_time")
    def _check_times(self):
            for rec in self:
                if rec.start_time >= rec.end_time:
                    raise ValidationError("Start time must be earlier than end time.")
    @api.onchange("start_time", "end_time")
    def _onchange_time_warning(self):
            for rec in self:
                if rec.start_time and rec.end_time and rec.start_time >= rec.end_time:
                    return {
                        "warning": {
                            "title": "Invalid Time Range",
                            "message": "Start time must be earlier than end time."
                        }
                    }

# ---------------------------------------------------------
# Daily Lines (Mon–Sat)
# ---------------------------------------------------------
class TimetableLine(models.Model):
    _name = "edu.class.timetable.line"
    _description = "Class Timetable Line"

    day_name = fields.Selection([
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
    ], string="Day", required=True)

    date_of_day = fields.Date(
        string="Date",
        compute="_compute_date_of_day",
        store=True
    )

    timetable_id = fields.Many2one(
        "edu.class.timetable",
        string="Timetable",
        required=True
    )
    session_ids = fields.One2many(
        'edu.class.timetable.session',string="Sessions")

@api.depends("day_name", "timetable_id.start_date")
def _compute_date_of_day(self):
    for rec in self:
        if not rec.day_name or not rec.timetable_id.start_date:
            rec.date_of_day = False
            continue
            # Convert start_date to Python date
        start_date = fields.Date.from_string(rec.timetable_id.start_date)
        weekday_map = {
                "Monday": 0,
                "Tuesday": 1,
                "Wednesday": 2,
                "Thursday": 3,
                "Friday": 4,
                "Saturday": 5,
            }

        desired_weekday = weekday_map.get(rec.day_name)
        start_weekday = start_date.weekday()          
        diff = (desired_weekday - start_weekday) % 7
        rec.date_of_day = start_date + timedelta(days=diff)
        session_ids = fields.One2many(
                'edu.class.timetable.session',
                'timetable_line_id',
                string="Sessions"
            )
@api.depends('day_name', 'timetable_id.week_start')
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
# ---------------------------------------------------------
# Each period/session
# ---------------------------------------------------------
class TimetableSession(models.Model):
    _name = "edu.class.timetable.session"
    _description = "Timetable Session"

    line_id = fields.Many2one("edu.class.timetable.line", string="Day Line", required=True)

    teacher_id = fields.Many2one("edu.teacher", string="Teacher", required=False)

    start_time = fields.Float(string="Start Time", required=True)
    end_time = fields.Float(string="End Time", required=True)

    room = fields.Char(string="Room")
    calendar_event_id = fields.Many2one(
    "calendar.event",
    string="Calendar Event",
    ondelete="cascade"
)

@api.model
def create(self, vals):
    sessions = super(ClassTimetableSession, self).create(vals)
    for session in sessions:
        session._create_or_update_event()
    return sessions


def write(self, vals):
    res = super(ClassTimetableSession, self).write(vals)
    for rec in self:
        rec._create_or_update_event()
    return res


def _create_or_update_event(self):
      for rec in self:
            if rec.start_time and rec.end_time:
                if rec.calendar_event_id:
                    rec.calendar_event_id.write({
                        "name": f"{rec.subject_id.name} ({rec.line_id.day_name})",
                        "start": rec.start_time,
                        "stop": rec.end_time,
                        "partner_ids": [(6, 0, [rec.teacher_id.id])] if rec.teacher_id else False,
                    })
                else:
                    event = self.env["calendar.event"].create({
                        "name": f"{rec.subject_id.name} ({rec.line_id.day_name})",
                        "start": rec.start_time,
                        "stop": rec.end_time,
                        "partner_ids": [(6, 0, [rec.teacher_id.id])] if rec.teacher_id else False,
                    })
                    rec.calendar_event_id = event.id



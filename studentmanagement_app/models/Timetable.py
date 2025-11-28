from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError
from datetime import timedelta
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

    # def action_generate_daily_classes(self):
    #     self.ensure_one()
 
    #     self.daily_class_ids.unlink()
    #     debug_lines = []
    #     for line in self.timetable_line_ids:
    #         # collect ids and brief details
    #         s_ids = line.session_ids.ids
    #         debug_lines.append(f"Line {line.day_name} ({line.date_of_day}) -> sessions: {s_ids}")
    #         for session in line.session_ids:
    #             # create daily record as normal
    #             self.env["edu.class.daily"].create({
    #                 "timetable_id": self.id,
    #                 "class_id": self.class_id.id,
    #                 "date": line.date_of_day,
    #                 "teacher_id": session.teacher_id.id or False,
    #                 "subject_id": session.subject_id.id if session.subject_id else False,
    #                 "start_time": session.start_time,
    #                 "end_time": session.end_time,
    #                 "room": session.room,
    #             })
    def action_generate_daily_classes(self):
        self.ensure_one()
       # Delete existing daily classes for this timetable
        self.daily_class_ids.unlink()
        daily_class_vals = []
        for line in self.timetable_line_ids:
             if not line.date_of_day:
                 continue  # skip if date not computed
 
             for session in line.session_ids:
                 if not session.start_time or not session.end_time:
                     continue  # skip invalid sessions

                # Critical: validate time order BEFORE creating
                 if session.start_time >= session.end_time:
                    raise ValidationError(
                        f"Invalid time in timetable: {session.start_time} → {session.end_time} "
                        f"on {line.day_name}. Start time must be before end time."
                    )

             daily_class_vals.append({
                    "timetable_id": self.id,
                    "class_id": self.class_id.id,
                    "date": line.date_of_day,
                    "teacher_id": session.teacher_id.id or False,
                    "subject_id": session.subject_id.id or False,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "room": session.room or "",
            })

    # Bulk create outside loop – faster and better error reporting
        if daily_class_vals:
            self.env["edu.class.daily"].create(daily_class_vals)
        else:
            raise UserError("No valid sessions found to generate daily classes.")

class DailyClass(models.Model):
    _name = "edu.class.daily"
    _description = "Daily Class Schedule"
    _order = "date, start_time"

    timetable_id = fields.Many2one("edu.class.timetable", string="Timetable", ondelete="cascade")
    class_id = fields.Many2one("batch.class", string="Class", required=True)
    date = fields.Date(string="Date", required=True)
    teacher_id = fields.Many2one("edu.teacher", string="Teacher")
    subject_id = fields.Many2one("edu.subject", string="Subject")
    start_time = fields.Float(string="Start Time", required=True)
    end_time = fields.Float(string="End Time", required=True)
    room = fields.Char(string="Room")

    duration = fields.Float(string="Duration (hrs)", compute="_compute_duration", store=True)
    week_range = fields.Char(string="Week Range", compute="_compute_week_range")

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
            rec.duration = rec.end_time - rec.start_time if rec.end_time > rec.start_time else 0.0

    @api.constrains("start_time", "end_time")
    def _check_times(self):
        for rec in self:
            if rec.start_time >= rec.end_time:
                raise ValidationError("Start time must be earlier than end time.")



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



class TimetableSession(models.Model):
    _name = "edu.class.timetable.session"
    _description = "Timetable Session"

    line_id = fields.Many2one("edu.class.timetable.line", string="Day Line", required=True)

    teacher_id = fields.Many2one("edu.teacher", string="Teacher")
    subject_id = fields.Many2one("edu.subject", string="Subject")

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



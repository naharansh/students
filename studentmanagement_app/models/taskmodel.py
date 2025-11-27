from odoo import models,fields
class Tasks(models.Model):
    _name='edu.task'
    _description='Internal Task'
    name=fields.Char(required=True,string="Task Name")
    assigned_to=fields.Many2one('edu.teacher',string="Assigned To")
    deadline=fields.Date(string="Deadline")
    priority = fields.Selection([('low','Low'),('medium','Medium'),('high','High')], default='medium')
    stage = fields.Selection([('todo','To Do'),('in_progress','In Progress'),('done','Completed')], default='todo')

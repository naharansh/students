from odoo import  models,fields
class Subject(models.Model):
    _name="edu.subject"
    _description='subject'
    name=fields.Char(string="Subject Name",required=True)
    code=fields.Char(string="Subject Code")
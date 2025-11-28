from odoo import models, fields, api

class Subject(models.Model):
    _name = "edu.subject"
    _description = "Subject"

    name = fields.Char(string="Subject Name", required=True)
    code = fields.Char(string="Subject Code", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('edu.subject.code') or 'SUB-NEW'
        return super(Subject, self).create(vals_list)

from odoo import models,fields,api
class Fee(models.Model):
    _name="edu.fee"
    _destination="Student Fee"
    student_id=fields.Many2one('student.model',string="StudentId")
    month=fields.Selection([(str(i),str(i))for i in range(1,13) ],string="Month")
    total_fee = fields.Float(string="Total Fee")
    paid_amount = fields.Float(string="Paid Amount")
    outstanding = fields.Float(string="Outstanding", compute='_compute_outstanding', store=True)
    status = fields.Selection([('paid','Paid'),('partial','Partial'),('unpaid','Unpaid')], compute='_compute_status', store=True)
    @api.depends('total_fee','paid_amount')
    def _compute_outstanding(self):
        for rec in self:
            rec.outstanding=rec.total_fee-rec.paid_amount
    @api.depends('outstanding')
    def _compute_status(self):
        for rec in self :
            if rec.outstanding == 0:
                rec.status = 'paid'
            elif rec.outstanding < rec.paid_amount:
                 rec.status = 'partial'
            else:
                rec.status = 'unpaid'

            
            
          




    

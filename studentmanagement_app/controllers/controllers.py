# from odoo import http


# class StudentmanagementApp(http.Controller):
#     @http.route('/studentmanagement_app/studentmanagement_app', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/studentmanagement_app/studentmanagement_app/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('studentmanagement_app.listing', {
#             'root': '/studentmanagement_app/studentmanagement_app',
#             'objects': http.request.env['studentmanagement_app.studentmanagement_app'].search([]),
#         })

#     @http.route('/studentmanagement_app/studentmanagement_app/objects/<model("studentmanagement_app.studentmanagement_app"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('studentmanagement_app.object', {
#             'object': obj
#         })


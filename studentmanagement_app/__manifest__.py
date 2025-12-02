{
    'name': "studentmanagement_app",
    'summary': "Manage students, classes, timetables, and daily schedules",
    'description': """
        A complete education management module for handling student records,
        class structures, weekly timetables, and auto-generated daily sessions.
    """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Education',
    'version': '0.1',
    'depends': ['base', 'calendar', 'mail'],  # add calendar/mail if you use those views
    'data': [
        'security/ir.model.access.csv',

        # Sequences FIRST
        'data/edu_sequence.xml',
        'data/edu_classcodesequence.xml',
        'data/edu_teachersequence.xml',
         'data/edu_subjectsequence.xml',   
         


        # Views NEXT

        'views/student.xml',
        'views/classes.xml',
        'views/timetable.xml',
        'views/teacher.xml',
        'views/daily_record.xml',
        'views/attendence.xml',
        
        'views/menu.xml',
        'views/templates.xml',
        'views/reports.xml',
        
    ],
    'demo': ['demo/demo.xml'],
    'installable': True,
    'application': True,
}
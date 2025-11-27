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

        # Menus BEFORE views that reference them


        # Views NEXT
        'views/student.xml',
        'views/classes.xml',
        'views/timetable.xml',
        'views/menu.xml',
    ],
    'demo': ['demo/demo.xml'],
    'installable': True,
    'application': True,
}
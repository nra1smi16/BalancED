"""
UAEU Counseling and Wellbeing Service contact details, shown on the dashboard.
Copied from the service's own page (check it again before the final presentation, details can change):
https://uaeu.ac.ae/en/student-services/scss/contact-us.shtml
"""

# The team's real contact email for the welcome page. Leave it empty until it exists: the box stays hidden.
PROJECT_EMAIL = ''

# Number shown on the welcome page. It is listed under both the female and the male section of the service.
WELCOME_PHONE = ('03 713 5482', '+97137135482')

SOURCE_URL = 'https://uaeu.ac.ae/en/student-services/scss/contact-us.shtml'

COUNSELING = {
    'name': 'UAEU Counseling and Wellbeing Service',
    'phones': [
        # (label shown, number as published, number for tel: links)
        ('Female section', '03 713 5445', '+97137135445'),
        ('Female section', '03 713 5482', '+97137135482'),
        ('Male section', '03 713 5482', '+97137135482'),
    ],
    'emails': ['noura.a@uaeu.ac.ae', 'waala.alahbabi@uaeu.ac.ae'],
    'locations': [
        ('Female campus', 'Building B3, Rooms 1006 and 1008'),
        ('Male campus', 'Building G2, Room 1003'),
    ],
    'source_url': SOURCE_URL,
}

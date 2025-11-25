REPORT_TYPE_CHOICES = [
    ('complaint', 'Complaint'),
    ('suggestion', 'Suggestion'),
]

CATEGORY_CHOICES = [
    ('academic', 'Akademik'),
    ('facility', 'Fasilitas & Sarana'),
    ('financial', 'Keuangan / UKT'),
    ('student_affairs', 'Kemahasiswaan'),
    ('other', 'Lainnya'),
]

STATUS_CHOICES = [
    ('pending', 'Waiting for Verification'),
    ('verified', 'Verified'),
    ('rejected', 'Rejected'),
    ('in_progress', 'In Progress'),
    ('resolved', 'Resolved'),
]

REACTION_CHOICES = [
        ('agree', '👍 Agree'),
        ('support', '🔥 Support'),
        ('sad', '😢 Sad'),
        ('shock', '😱 Shock'),
        ('confused', '🤔 Confused'),
    ]
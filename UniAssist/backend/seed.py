"""Create demo accounts. Run once: python seed.py"""
from app import create_app
from app.extensions import db
from datetime import date
from app.models import Announcement, Role, User
from app.utils.security import hash_password

DEMO = [("Demo Student", "student@uniassist.edu", "student", "Student@123"),
        ("Demo Faculty", "faculty@uniassist.edu", "faculty", "Faculty@123"),
        ("Demo Admin", "admin@uniassist.edu", "admin", "Admin@123")]

app = create_app()
with app.app_context():
    for name, email, role, pw in DEMO:
        if not User.query.filter_by(email=email).first():
            db.session.add(User(full_name=name, email=email, password_hash=hash_password(pw),
                                role_id=Role.query.filter_by(name=role).first().id,
                                department="MCA"))
    db.session.commit()
    admin = User.query.filter_by(email="admin@uniassist.edu").first()
    if not Announcement.query.count():
        # Sample announcements (fictional dates) so the demo UI is not empty. Edit/delete in the app.
        for title, body, cat, when in [
            ("Sample: End-semester exam timetable", "The odd-semester timetable will be published 21 days before the first paper.", "exam", date(2026, 12, 10)),
            ("Sample: Dussehra holidays", "The university will remain closed from 20 to 24 October.", "holiday", date(2026, 10, 20)),
            ("Sample: Project synopsis deadline", "MCA final-year students must submit the synopsis to the department office.", "deadline", date(2026, 12, 1)),
            ("Sample: Technical fest", "Annual technical fest open to all departments.", "event", date(2027, 2, 14))]:
            db.session.add(Announcement(author_id=admin.id, title=title, body=body, category=cat, event_date=when))
        db.session.commit()
    print("Demo accounts and sample announcements ready.")

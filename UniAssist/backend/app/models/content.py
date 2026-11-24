from datetime import datetime
from app.extensions import db


class GeneratedQuestion(db.Model):
    __tablename__ = "generated_questions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="SET NULL"))
    question_type = db.Column(db.String(12), nullable=False)    # mcq | short | long | true_false
    marks = db.Column(db.Integer)
    difficulty = db.Column(db.String(10), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON)
    answer_key = db.Column(db.Text, nullable=False)
    paper_id = db.Column(db.String(40), index=True)
    paper_title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, with_answer=True):
        d = {"id": self.id, "type": self.question_type, "marks": self.marks, "difficulty": self.difficulty,
             "question": self.question_text, "options": self.options}
        if with_answer:
            d["answer"] = self.answer_key
        return d


class Quiz(db.Model):
    __tablename__ = "quizzes"
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="SET NULL"))
    title = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(10), default="medium")
    questions = db.Column(db.JSON, nullable=False)   # [{question, options[], answer_index, explanation}]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class QuizResult(db.Model):
    __tablename__ = "quiz_results"
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    answers = db.Column(db.JSON)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)


class Announcement(db.Model):
    __tablename__ = "announcements"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(10), default="general")  # exam|event|holiday|deadline|circular|general
    audience = db.Column(db.String(10), default="all")      # all|student|faculty
    event_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship("User")

    def to_dict(self):
        return {"id": self.id, "title": self.title, "body": self.body, "category": self.category,
                "audience": self.audience, "author": self.author.full_name, "author_id": self.author_id,
                "event_date": self.event_date.isoformat() if self.event_date else None,
                "created_at": self.created_at.isoformat()}


class Feedback(db.Model):
    __tablename__ = "feedback"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey("chat_messages.id", ondelete="SET NULL"))
    type = db.Column(db.String(20), nullable=False)         # rating | incorrect_report | suggestion
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User")

    def to_dict(self):
        return {"id": self.id, "user": self.user.full_name, "message_id": self.message_id, "type": self.type,
                "rating": self.rating, "comment": self.comment, "created_at": self.created_at.isoformat()}

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from my_clinic import db
from datetime import datetime


class Assistant(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    advisories = relationship('Advisory', backref='assistant', lazy=True)
    account = relationship('AccountAssistant', backref='assistant', lazy=True, uselist=False)
    receipts = relationship('Receipt', backref='assistant', lazy=True)

    type = Column(String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'assistant',
        'polymorphic_on': type
    }

    def __str__(self):
        return self.name


class Doctor(Assistant):
    id = Column(Integer, ForeignKey(Assistant.id), primary_key=True)
    policies = relationship('Policy', backref='doctor', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'doctor'
    }


class Policy(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey(Doctor.id), nullable=False)
    topic = Column(String(100), nullable=False)
    content = Column(String(500), nullable=False)
    value = Column(Float)

    def __str__(self):
        return self.topic


class Customer(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    phone = Column(Integer, nullable=True)
    email = Column(String(100), nullable=False, unique=True)
    questions = relationship('Question', cascade="all,delete", backref='customer', lazy=True)
    books = relationship('Books', cascade="all,delete", backref='customer', lazy=True)

    type = Column(String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'customer',
        'polymorphic_on': type
    }

    def __str__(self):
        return self.name


class Patient(Customer):
    id = Column(Integer, ForeignKey(Customer.id, onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    avatar = Column(String(500), nullable=True)
    clinical_records = relationship('ClinicalRecords', backref='patient', lazy=True)
    account = relationship('AccountPatient', backref='patient', lazy=True, uselist=False)
    receipts = relationship('Receipt', backref='patient', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'patient'
    }


class Question(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    sent_date = Column(DateTime, default=datetime.now())
    customer_id = Column(Integer, ForeignKey(Customer.id, onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    topic = Column(String(50), nullable=False)
    content = Column(String(1000), nullable=False)
    Answer = relationship('Advisory', backref='question', lazy=True)

    def __str__(self):
        return self.topic


class Advisory(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    sent_date = Column(DateTime, default=datetime.now())
    assistant_id = Column(Integer, ForeignKey(Assistant.id), nullable=False)
    question_id = Column(Integer, ForeignKey(Question.id), nullable=False)
    content = Column(String(500), nullable=False)

    def __str__(self):
        return self.content


class Account(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Boolean, default=False)
    joined_date = Column(DateTime, default=datetime.now())
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(100), nullable=False)

    type = Column(String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'Account',
        'polymorphic_on': type
    }

    def __str__(self):
        return self.id


class AccountPatient(Account):
    id = Column(Integer, ForeignKey(Account.id), primary_key=True)
    patient_id = Column(Integer, ForeignKey(Patient.id), nullable=False, unique=True)

    __mapper_args__ = {
        'polymorphic_identity': 'user'
    }


class AccountAssistant(Account):
    id = Column(Integer, ForeignKey(Account.id), primary_key=True)
    assistant_id = Column(Integer, ForeignKey(Assistant.id), nullable=False, unique=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin'
    }


class Disease(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(1000))
    records = relationship('ClinicalRecords', backref='disease', lazy=True)

    def __str__(self):
        return self.name


class ClinicalRecords(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    checked_date = Column(DateTime, default=datetime.now())
    disease_id = Column(Integer, ForeignKey(Disease.id), nullable=False)
    patient_id = Column(Integer, ForeignKey(Patient.id), nullable=False)

    def __str__(self):
        return self.id


class Medicine(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    unit = Column(String(10), nullable=False)
    price = Column(Integer, nullable=False)
    receipt_details = relationship('ReceiptDetails', backref="medicine", lazy=True)

    def __str__(self):
        return self.name


class Receipt(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now())
    status = Column(Integer, default=0)
    assistant_id = Column(Integer, ForeignKey(Assistant.id), nullable=False)
    patient_id = Column(Integer, ForeignKey(Patient.id), nullable=False)
    details = relationship('ReceiptDetails', backref='receipt', lazy=True)

    def __str__(self):
        return self.id


class ReceiptDetails(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)
    medicine_id = Column(Integer, ForeignKey(Medicine.id), nullable=False)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)

    def __str__(self):
        return self.id

class Time(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(20), nullable=False)
    books_times = relationship('Books', backref='time', lazy=True)

    def __str__(self):
        return self.period


class Books(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    booked_date = Column(DateTime, default=datetime.now())
    customer_id = Column(Integer, ForeignKey(Customer.id,  onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    time_id = Column(Integer, ForeignKey(Time.id), nullable=False)

    def __str__(self):
        return self.id



if __name__ == '__main__':
    db.create_all()

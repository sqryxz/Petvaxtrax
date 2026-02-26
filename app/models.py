"""
PetVaxHK - Database Models
SQLAlchemy models for the web application
"""
from datetime import datetime
from app import db


class Pet(db.Model):
    """Pet model."""
    __tablename__ = 'pets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(20), nullable=False)  # 'dog' or 'cat'
    breed = db.Column(db.String(100))
    date_of_birth = db.Column(db.String(10))  # ISO format YYYY-MM-DD
    microchip_number = db.Column(db.String(50), unique=True)
    owner_name = db.Column(db.String(100))
    owner_contact = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vaccinations = db.relationship('PetVaccination', backref='pet', lazy='dynamic')
    
    def __repr__(self):
        return f'<Pet {self.name}>'


class Vaccine(db.Model):
    """Vaccine type model."""
    __tablename__ = 'vaccines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)  # e.g., 'DHPP', 'Rabies'
    species = db.Column(db.String(20), nullable=False)  # 'dog', 'cat', or 'both'
    description = db.Column(db.Text)
    valid_months = db.Column(db.Integer)  # Validity period in months
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    vaccinations = db.relationship('PetVaccination', backref='vaccine', lazy='dynamic')
    
    def __repr__(self):
        return f'<Vaccine {self.name}>'


class PetVaccination(db.Model):
    """Pet vaccination record."""
    __tablename__ = 'pet_vaccinations'
    
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id'), nullable=False)
    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id'), nullable=False)
    date_administered = db.Column(db.String(10), nullable=False)  # ISO format
    due_date = db.Column(db.String(10))  # ISO format
    vet_clinic_id = db.Column(db.Integer, db.ForeignKey('vet_clinics.id'))
    batch_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    clinic = db.relationship('VetClinic', backref='vaccinations')
    
    def __repr__(self):
        return f'<PetVaccination pet={self.pet_id} vaccine={self.vaccine_id}>'


class VetClinic(db.Model):
    """Veterinary clinic model."""
    __tablename__ = 'vet_clinics'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    district = db.Column(db.String(50))  # HK district
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VetClinic {self.name}>'


class Reminder(db.Model):
    """Reminder model."""
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id'), nullable=False)
    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id'))
    reminder_type = db.Column(db.String(20), nullable=False)  # 'due_soon', 'overdue', 'upcoming'
    due_date = db.Column(db.String(10))  # ISO format
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'dismissed'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    pet = db.relationship('Pet', backref='reminders')
    vaccine = db.relationship('Vaccine')
    
    def __repr__(self):
        return f'<Reminder pet={self.pet_id} type={self.reminder_type}>'

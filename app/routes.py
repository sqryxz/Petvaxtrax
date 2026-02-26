"""
PetVaxHK - Routes
Main web application routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Pet, Vaccine, PetVaccination, VetClinic, Reminder

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Home page - dashboard showing pets and upcoming reminders."""
    pets = Pet.query.all()
    upcoming_reminders = Reminder.query.filter(
        Reminder.due_date.isnot(None),
        Reminder.due_date >= db.func.date('now')
    ).order_by(Reminder.due_date).limit(10).all()
    
    overdue_reminders = Reminder.query.filter(
        Reminder.due_date < db.func.date('now'),
        Reminder.status != 'completed'
    ).all()
    
    return render_template('index.html', 
                         pets=pets, 
                         upcoming_reminders=upcoming_reminders,
                         overdue_reminders=overdue_reminders)


@bp.route('/pets')
def pets_list():
    """List all pets."""
    pets = Pet.query.all()
    return render_template('pets/list.html', pets=pets)


@bp.route('/pets/add', methods=['GET', 'POST'])
def pets_add():
    """Add a new pet."""
    if request.method == 'POST':
        pet = Pet(
            name=request.form['name'],
            species=request.form['species'],
            breed=request.form.get('breed'),
            date_of_birth=request.form.get('date_of_birth'),
            microchip_number=request.form.get('microchip_number'),
            owner_name=request.form.get('owner_name'),
            owner_contact=request.form.get('owner_contact')
        )
        db.session.add(pet)
        db.session.commit()
        flash(f'Pet {pet.name} added successfully!', 'success')
        return redirect(url_for('main.pets_list'))
    
    return render_template('pets/add.html')


@bp.route('/pets/<int:pet_id>')
def pets_detail(pet_id):
    """View pet details with vaccination history."""
    pet = Pet.query.get_or_404(pet_id)
    vaccinations = PetVaccination.query.filter_by(pet_id=pet_id).order_by(
        PetVaccination.date_administered.desc()
    ).all()
    return render_template('pets/detail.html', pet=pet, vaccinations=vaccinations)


@bp.route('/pets/<int:pet_id>/edit', methods=['GET', 'POST'])
def pets_edit(pet_id):
    """Edit pet details."""
    pet = Pet.query.get_or_404(pet_id)
    
    if request.method == 'POST':
        pet.name = request.form['name']
        pet.species = request.form['species']
        pet.breed = request.form.get('breed')
        pet.date_of_birth = request.form.get('date_of_birth')
        pet.microchip_number = request.form.get('microchip_number')
        pet.owner_name = request.form.get('owner_name')
        pet.owner_contact = request.form.get('owner_contact')
        db.session.commit()
        flash(f'Pet {pet.name} updated successfully!', 'success')
        return redirect(url_for('main.pets_detail', pet_id=pet.id))
    
    return render_template('pets/edit.html', pet=pet)


@bp.route('/pets/<int:pet_id>/delete', methods=['POST'])
def pets_delete(pet_id):
    """Delete a pet."""
    pet = Pet.query.get_or_404(pet_id)
    db.session.delete(pet)
    db.session.commit()
    flash(f'Pet {pet.name} deleted.', 'info')
    return redirect(url_for('main.pets_list'))


@bp.route('/vaccines')
def vaccines_list():
    """List all vaccine types."""
    vaccines = Vaccine.query.all()
    return render_template('vaccines/list.html', vaccines=vaccines)


@bp.route('/vaccines/add', methods=['GET', 'POST'])
def vaccines_add():
    """Add a new vaccine type."""
    if request.method == 'POST':
        vaccine = Vaccine(
            name=request.form['name'],
            code=request.form['code'],
            species=request.form['species'],
            description=request.form.get('description'),
            valid_months=request.form.get('valid_months', type=int)
        )
        db.session.add(vaccine)
        db.session.commit()
        flash(f'Vaccine {vaccine.name} added successfully!', 'success')
        return redirect(url_for('main.vaccines_list'))
    
    return render_template('vaccines/add.html')


@bp.route('/vaccines/<int:vaccine_id>')
def vaccines_detail(vaccine_id):
    """View vaccine details with vaccination history."""
    vaccine = Vaccine.query.get_or_404(vaccine_id)
    vaccinations = PetVaccination.query.filter_by(vaccine_id=vaccine_id).order_by(
        PetVaccination.date_administered.desc()
    ).all()
    return render_template('vaccines/detail.html', vaccine=vaccine, vaccinations=vaccinations)


@bp.route('/vaccines/<int:vaccine_id>/edit', methods=['GET', 'POST'])
def vaccines_edit(vaccine_id):
    """Edit vaccine details."""
    vaccine = Vaccine.query.get_or_404(vaccine_id)
    
    if request.method == 'POST':
        vaccine.name = request.form['name']
        vaccine.code = request.form['code']
        vaccine.species = request.form['species']
        vaccine.description = request.form.get('description')
        vaccine.valid_months = request.form.get('valid_months', type=int)
        db.session.commit()
        flash(f'Vaccine {vaccine.name} updated successfully!', 'success')
        return redirect(url_for('main.vaccines_detail', vaccine_id=vaccine.id))
    
    return render_template('vaccines/edit.html', vaccine=vaccine)


@bp.route('/vaccines/<int:vaccine_id>/delete', methods=['POST'])
def vaccines_delete(vaccine_id):
    """Delete a vaccine type."""
    vaccine = Vaccine.query.get_or_404(vaccine_id)
    db.session.delete(vaccine)
    db.session.commit()
    flash(f'Vaccine {vaccine.name} deleted.', 'info')
    return redirect(url_for('main.vaccines_list'))


@bp.route('/vaccinations/add', methods=['GET', 'POST'])
def vaccinations_add():
    """Record a new vaccination for a pet."""
    if request.method == 'POST':
        vaccination = PetVaccination(
            pet_id=request.form['pet_id'],
            vaccine_id=request.form['vaccine_id'],
            date_administered=request.form['date_administered'],
            due_date=request.form.get('due_date'),
            vet_clinic_id=request.form.get('vet_clinic_id', type=int),
            batch_number=request.form.get('batch_number'),
            notes=request.form.get('notes')
        )
        db.session.add(vaccination)
        db.session.commit()
        flash('Vaccination recorded successfully!', 'success')
        return redirect(url_for('main.pets_detail', pet_id=request.form['pet_id']))
    
    pets = Pet.query.all()
    vaccines = Vaccine.query.all()
    clinics = VetClinic.query.all()
    return render_template('vaccinations/add.html', 
                         pets=pets, vaccines=vaccines, clinics=clinics)


@bp.route('/vaccinations/<int:vaccination_id>/edit', methods=['GET', 'POST'])
def vaccinations_edit(vaccination_id):
    """Edit a vaccination record."""
    vaccination = PetVaccination.query.get_or_404(vaccination_id)
    
    if request.method == 'POST':
        vaccination.pet_id = request.form['pet_id']
        vaccination.vaccine_id = request.form['vaccine_id']
        vaccination.date_administered = request.form['date_administered']
        vaccination.due_date = request.form.get('due_date')
        vaccination.vet_clinic_id = request.form.get('vet_clinic_id', type=int) or None
        vaccination.batch_number = request.form.get('batch_number')
        vaccination.notes = request.form.get('notes')
        db.session.commit()
        flash('Vaccination updated successfully!', 'success')
        return redirect(url_for('main.pets_detail', pet_id=vaccination.pet_id))
    
    pets = Pet.query.all()
    vaccines = Vaccine.query.all()
    clinics = VetClinic.query.all()
    return render_template('vaccinations/edit.html', 
                         pets=pets, vaccines=vaccines, clinics=clinics,
                         vaccination=vaccination)


@bp.route('/vaccinations/<int:vaccination_id>/delete', methods=['POST'])
def vaccinations_delete(vaccination_id):
    """Delete a vaccination record."""
    vaccination = PetVaccination.query.get_or_404(vaccination_id)
    pet_id = vaccination.pet_id
    db.session.delete(vaccination)
    db.session.commit()
    flash('Vaccination record deleted.', 'info')
    return redirect(url_for('main.pets_detail', pet_id=pet_id))


@bp.route('/reminders')
def reminders_list():
    """Reminders dashboard with statistics and management."""
    status_filter = request.args.get('status')
    type_filter = request.args.get('type')
    
    # Get stats
    total_count = Reminder.query.count()
    pending_count = Reminder.query.filter_by(status='pending').count()
    completed_count = Reminder.query.filter_by(status='completed').count()
    overdue_count = Reminder.query.filter(
        Reminder.due_date < db.func.date('now'),
        Reminder.status != 'completed'
    ).count()
    due_soon_count = Reminder.query.filter(
        Reminder.due_date >= db.func.date('now'),
        Reminder.due_date <= db.func.date('now', '+30 days'),
        Reminder.status == 'pending'
    ).count()
    
    # Build query
    query = Reminder.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if type_filter:
        query = query.filter_by(reminder_type=type_filter)
    reminders = query.order_by(Reminder.due_date).all()
    
    # Separate overdue and upcoming for dashboard view
    overdue_reminders = Reminder.query.filter(
        Reminder.due_date < db.func.date('now'),
        Reminder.status != 'completed'
    ).order_by(Reminder.due_date).all()
    
    due_soon_reminders = Reminder.query.filter(
        Reminder.due_date >= db.func.date('now'),
        Reminder.due_date <= db.func.date('now', '+30 days'),
        Reminder.status == 'pending'
    ).order_by(Reminder.due_date).all()
    
    return render_template('reminders/list.html', 
                         reminders=reminders,
                         stats={
                             'total': total_count,
                             'pending': pending_count,
                             'completed': completed_count,
                             'overdue': overdue_count,
                             'due_soon': due_soon_count
                         },
                         status_filter=status_filter,
                         type_filter=type_filter,
                         overdue_reminders=overdue_reminders,
                         due_soon_reminders=due_soon_reminders)


@bp.route('/reminders/<int:reminder_id>/complete', methods=['POST'])
def reminders_complete(reminder_id):
    """Mark a reminder as completed."""
    reminder = Reminder.query.get_or_404(reminder_id)
    reminder.status = 'completed'
    db.session.commit()
    flash('Reminder marked as completed!', 'success')
    return redirect(url_for('main.reminders_list'))


@bp.route('/reminders/generate', methods=['POST'])
def reminders_generate():
    """Generate reminders from vaccination records."""
    try:
        from app.core.reminders import ReminderEngine, ReminderConfig
        import os
        
        # Get database path
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'outputs', 'pets.db')
        config = ReminderConfig(db_path=db_path)
        
        with ReminderEngine(config) as engine:
            result = engine.generate_reminders()
            flash(f'Generated {result["created"]} reminders. Skipped {result["skipped"]}.', 'success')
    except Exception as e:
        flash(f'Error generating reminders: {str(e)}', 'danger')
    
    return redirect(url_for('main.reminders_list'))


@bp.route('/clinics')
def clinics_list():
    """List all vet clinics."""
    search_query = request.args.get('q', '')
    district_filter = request.args.get('district', '')
    
    query = VetClinic.query
    if search_query:
        query = query.filter(
            (VetClinic.name.ilike(f'%{search_query}%')) |
            (VetClinic.address.ilike(f'%{search_query}%'))
        )
    if district_filter:
        query = query.filter_by(district=district_filter)
    
    clinics = query.all()
    
    # Get unique districts for filter
    districts = [c.district for c in VetClinic.query.with_entities(VetClinic.district).distinct() if c.district]
    
    return render_template('clinics/list.html', clinics=clinics, districts=districts,
                         search_query=search_query, district_filter=district_filter)


@bp.route('/clinics/add', methods=['GET', 'POST'])
def clinics_add():
    """Add a new vet clinic."""
    if request.method == 'POST':
        clinic = VetClinic(
            name=request.form['name'],
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            district=request.form.get('district')
        )
        db.session.add(clinic)
        db.session.commit()
        flash(f'Clinic {clinic.name} added successfully!', 'success')
        return redirect(url_for('main.clinics_list'))
    
    return render_template('clinics/add.html')


@bp.route('/clinics/<int:clinic_id>')
def clinics_detail(clinic_id):
    """View clinic details."""
    clinic = VetClinic.query.get_or_404(clinic_id)
    return render_template('clinics/detail.html', clinic=clinic)


@bp.route('/clinics/<int:clinic_id>/edit', methods=['GET', 'POST'])
def clinics_edit(clinic_id):
    """Edit clinic details."""
    clinic = VetClinic.query.get_or_404(clinic_id)
    
    if request.method == 'POST':
        clinic.name = request.form['name']
        clinic.address = request.form.get('address')
        clinic.phone = request.form.get('phone')
        clinic.email = request.form.get('email')
        clinic.district = request.form.get('district')
        db.session.commit()
        flash(f'Clinic {clinic.name} updated successfully!', 'success')
        return redirect(url_for('main.clinics_detail', clinic_id=clinic.id))
    
    return render_template('clinics/edit.html', clinic=clinic)


@bp.route('/clinics/<int:clinic_id>/delete', methods=['POST'])
def clinics_delete(clinic_id):
    """Delete a clinic."""
    clinic = VetClinic.query.get_or_404(clinic_id)
    db.session.delete(clinic)
    db.session.commit()
    flash(f'Clinic {clinic.name} deleted.', 'info')
    return redirect(url_for('main.clinics_list'))


@bp.route('/health')
def health_check():
    """Health check endpoint."""
    return {'status': 'healthy', 'app': 'PetVaxHK'}


@bp.route('/settings')
def settings():
    """Settings page."""
    # Default settings - in production, these would come from a user preferences table
    settings_data = {
        'language': 'en',
        'timezone': 'Asia/Hong_Kong',
        'date_format': 'YYYY-MM-DD',
        'email_reminders': False,
        'reminder_days_before': 7
    }
    return render_template('settings/list.html', settings=settings_data)


@bp.route('/settings/update', methods=['POST'])
def settings_update():
    """Update settings."""
    # In production, save to user preferences table
    flash('Settings saved successfully.', 'success')
    return redirect(url_for('main.settings'))


@bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@bp.route('/compliance')
def compliance_list():
    """Compliance dashboard showing all pets' compliance status."""
    from app.core.rules import check_compliance, Scenario, PetType, RequirementStatus
    
    pets = Pet.query.all()
    compliance_results = []
    
    for pet in pets:
        # Determine scenario based on pet (default to resident for now)
        scenario = Scenario.HK_RESIDENT
        
        # Get vaccinations for this pet
        vaccinations = PetVaccination.query.filter_by(pet_id=pet.id).all()
        vax_list = []
        for v in vaccinations:
            if v.vaccine and v.date_administered:
                vax_list.append({
                    "vaccine_name": v.vaccine.name,
                    "date_administered": v.date_administered,
                    "next_due_date": v.due_date
                })
        
        # Determine pet type
        pet_type = PetType.DOG if pet.species.lower() == 'dog' else PetType.CAT
        
        # Check compliance
        result = check_compliance(
            pet_id=pet.id,
            pet_name=pet.name,
            scenario=scenario,
            pet_type=pet_type,
            vaccinations=vax_list
        )
        
        # Get counts for each status
        compliant_count = sum(1 for r in result.requirements if r.status == RequirementStatus.COMPLIANT)
        due_soon_count = sum(1 for r in result.requirements if r.status == RequirementStatus.DUE_SOON)
        overdue_count = sum(1 for r in result.requirements if r.status == RequirementStatus.OVERDUE)
        not_done_count = sum(1 for r in result.requirements if r.status == RequirementStatus.NOT_DONE)
        
        compliance_results.append({
            'pet': pet,
            'result': result,
            'compliant_count': compliant_count,
            'due_soon_count': due_soon_count,
            'overdue_count': overdue_count,
            'not_done_count': not_done_count,
            'total_requirements': len(result.requirements)
        })
    
    # Calculate overall stats
    total_pets = len(compliance_results)
    fully_compliant = sum(1 for cr in compliance_results if cr['result'].is_compliant)
    has_issues = total_pets - fully_compliant
    
    return render_template('compliance/list.html', 
                         compliance_results=compliance_results,
                         stats={
                             'total_pets': total_pets,
                             'fully_compliant': fully_compliant,
                             'has_issues': has_issues
                         })


@bp.route('/compliance/<int:pet_id>')
def compliance_detail(pet_id):
    """Detailed compliance view for a specific pet."""
    from app.core.rules import check_compliance, Scenario, PetType, RequirementStatus
    
    pet = Pet.query.get_or_404(pet_id)
    scenario = Scenario.HK_RESIDENT
    
    # Get vaccinations
    vaccinations = PetVaccination.query.filter_by(pet_id=pet.id).all()
    vax_list = []
    for v in vaccinations:
        if v.vaccine and v.date_administered:
            vax_list.append({
                "vaccine_name": v.vaccine.name,
                "date_administered": v.date_administered,
                "next_due_date": v.due_date
            })
    
    pet_type = PetType.DOG if pet.species.lower() == 'dog' else PetType.CAT
    
    result = check_compliance(
        pet_id=pet.id,
        pet_name=pet.name,
        scenario=scenario,
        pet_type=pet_type,
        vaccinations=vax_list
    )
    
    return render_template('compliance/detail.html', 
                         pet=pet, 
                         result=result,
                         RequirementStatus=RequirementStatus)

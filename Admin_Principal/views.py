
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import datetime
import calendar
from django.contrib.auth.decorators import login_required
from Parent.models import LeaveApplication_model
from Teacher.models import Marks_model, Library_issue_model, Attendance_model, LateComing_model, Acknowledgement_model
from datetime import datetime
import json
from .Admin_Principal_Forms import LibraryBook_Form, SchoolCalender_Form
from .models import LibraryBook_model, SchoolCalender_model, \
   TimeTable_model, Notice_model, Exam_model
from datetime import date
from .models import Sibling_model
from django.contrib.auth.models import User
from .models import Teacher_Model, Role_Model
from django.contrib import messages
from django.db import transaction
from .models import Teacher_Model, Class_model, Subject_model




@transaction.atomic
# Create your views here.
def TestView(request):
    return render(request, "AdminPrincipalHome.html")


def AdminPrincipalFrame(request):
    return render(request, "AdminPrincipalFrame.html")


def KrishnaView(request):
    return render(request,"img.html")


# view for student admission

def Student_admission(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section')

    if request.method == 'POST':
        # 1. Extract Student Data
        admission_no = request.POST.get('Admission_no')
        adm_date = request.POST.get('Adm_date') or date.today()
        class_id = request.POST.get('Class')
        student_class = Class_model.objects.get(id=class_id)

        # 2. Create Django User for Student
        student_user = User.objects.create_user(
            username=f'S_{admission_no}',
            password=f'S_{admission_no}'
        )
        Role_Model.objects.create(user_type='Student', Login=student_user)

        # 3. Save Student Instance (Roll_no set to 0 initially)
        student = Student_Model.objects.create(
            Admission_no=admission_no,
            Adm_date=adm_date,
            Class=student_class,
            Roll_no=0,
            Name=request.POST.get('Name'),
            Gender=request.POST.get('Gender'),
            DOB=request.POST.get('DOB'),
            Blood_group=request.POST.get('Blood_group'),
            MobileNumber=request.POST.get('MobileNumber') or None,
            Address=request.POST.get('Address'),
            Category=request.POST.get('Category'),
            Caste=request.POST.get('Caste'),
            Religion=request.POST.get('Religion'),
            APL_BPL=request.POST.get('APL_BPL'),
            Aadhar=request.POST.get('Aadhar'),
            Local_body=request.POST.get('Local_body'),
            Bank_ac=request.POST.get('Bank_ac'),
            Bank_name=request.POST.get('Bank_name'),
            IFSC=request.POST.get('IFSC'),
            Login=student_user
        )

        # 4. Recalculate Roll Numbers alphabetically for all students in this class starting from 1
        class_students = Student_Model.objects.filter(Class=student_class).order_by('Name')
        for index, std in enumerate(class_students, start=1):
            if std.Roll_no != index:
                std.Roll_no = index
                std.save(update_fields=['Roll_no'])

        # 5. Extract and Save Parent Data
        parent_user = User.objects.create_user(
            username=f'P_{admission_no}',
            password=f'P_{admission_no}'
        )
        Role_Model.objects.create(user_type='Parent', Login=parent_user)

        Parent_Model.objects.create(
            Student=student,
            Father_name=request.POST.get('Father_name'),
            Mother_name=request.POST.get('Mother_name'),
            F_occupation=request.POST.get('F_occupation'),
            M_occupation=request.POST.get('M_occupation'),
            F_phone=request.POST.get('F_phone'),
            M_phone=request.POST.get('M_phone'),
            Login=parent_user
        )

        # 6. Save Siblings (Up to 3)
        for i in range(1, 4):
            sibling_id = request.POST.get(f'sibling_{i}_student')
            if sibling_id:
                sibling_student = Student_Model.objects.get(id=sibling_id)

                # Bidirectional mapping
                Sibling_model.objects.create(Student=student, Sibling_student=sibling_student)
                Sibling_model.objects.create(Student=sibling_student, Sibling_student=student)

        return redirect('Student_admission')

    today_date = date.today().strftime('%Y-%m-%d')
    return render(request, 'Student_admission.html', {
        'classes': classes,
        'today_date': today_date
    })

def get_students_by_class(request):
    class_id = request.GET.get('class_id')
    if class_id:
        students = Student_Model.objects.filter(Class_id=class_id).values('id', 'Name', 'Admission_no')
        return JsonResponse(list(students), safe=False)
    return JsonResponse([], safe=False)


from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from .models import Class_model, Student_Model, Parent_Model


@transaction.atomic
def remove_student(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        if student_id:
            student = get_object_or_404(Student_Model, id=student_id)
            target_class = student.Class
            student_user = student.Login

            # 1. Clean up Parent User & Role if associated with this student
            parents = Parent_Model.objects.filter(Student=student)
            for parent in parents:
                if parent.Login:
                    parent_user = parent.Login
                    parent_user.delete()  # Cascades to Role_Model for Parent

            # 2. Delete Student (Cascades to Parent_Model, Sibling_model)
            if student_user:
                # Deleting student user deletes Student_Model and Student Role_Model via CASCADE
                student_user.delete()
            else:
                student.delete()

            # 3. Re-allocate Roll Numbers for remaining students in the same class
            remaining_students = Student_Model.objects.filter(Class=target_class).order_by('Name')
            for index, std in enumerate(remaining_students, start=1):
                if std.Roll_no != index:
                    std.Roll_no = index
                    std.save(update_fields=['Roll_no'])

            return redirect('remove_student')

    return render(request, 'remove_student.html', {'classes': classes})



def Admin_EditStudent(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section')
    selected_class_id = request.GET.get('class_id') or request.POST.get('class_id')
    selected_student_id = request.GET.get('student_id') or request.POST.get('student_id')

    students = []
    selected_student = None
    selected_parent = None
    existing_siblings = []

    if selected_class_id:
        students = Student_Model.objects.filter(Class_id=selected_class_id).order_by('Roll_no', 'Name')

    if selected_student_id:
        selected_student = Student_Model.objects.filter(id=selected_student_id).first()
        if selected_student:
            selected_parent = Parent_Model.objects.filter(Student=selected_student).first()
            existing_siblings = Sibling_model.objects.filter(Student=selected_student)

    if request.method == 'POST' and 'update_student' in request.POST:
        student_id = request.POST.get('student_id')
        student = get_object_or_404(Student_Model, id=student_id)

        old_class = student.Class
        new_class_id = request.POST.get('Class')
        new_class = get_object_or_404(Class_model, id=new_class_id)

        # 1. Update Student Details
        student.Admission_no = request.POST.get('Admission_no')
        student.Adm_date = request.POST.get('Adm_date') or student.Adm_date
        student.Class = new_class
        student.Name = request.POST.get('Name')
        student.Gender = request.POST.get('Gender')
        student.DOB = request.POST.get('DOB')
        student.Blood_group = request.POST.get('Blood_group')
        student.MobileNumber = request.POST.get('MobileNumber') or None
        student.Address = request.POST.get('Address')
        student.Category = request.POST.get('Category')
        student.Caste = request.POST.get('Caste')
        student.Religion = request.POST.get('Religion')
        student.APL_BPL = request.POST.get('APL_BPL')
        student.Aadhar = request.POST.get('Aadhar')
        student.Local_body = request.POST.get('Local_body')
        student.Bank_ac = request.POST.get('Bank_ac')
        student.Bank_name = request.POST.get('Bank_name')
        student.IFSC = request.POST.get('IFSC')
        student.save()

        # 2. Recalculate Roll Numbers if class changed
        if old_class != new_class:
            for cls in [old_class, new_class]:
                cls_students = Student_Model.objects.filter(Class=cls).order_by('Name')
                for idx, std in enumerate(cls_students, start=1):
                    if std.Roll_no != idx:
                        std.Roll_no = idx
                        std.save(update_fields=['Roll_no'])

        # 3. Update Parent Details
        parent = Parent_Model.objects.filter(Student=student).first()
        if parent:
            parent.Father_name = request.POST.get('Father_name')
            parent.Mother_name = request.POST.get('Mother_name')
            parent.F_occupation = request.POST.get('F_occupation')
            parent.M_occupation = request.POST.get('M_occupation')
            parent.F_phone = request.POST.get('F_phone')
            parent.M_phone = request.POST.get('M_phone')
            parent.save()

        # 4. Save Siblings (using Sibling_student foreign key)
        for i in range(1, 4):
            sibling_student_id = request.POST.get(f'sibling_{i}_student')
            if sibling_student_id:
                sibling_obj = Student_Model.objects.filter(id=sibling_student_id).first()
                if sibling_obj and not Sibling_model.objects.filter(Student=student,
                                                                    Sibling_student=sibling_obj).exists():
                    Sibling_model.objects.create(
                        Student=student,
                        Sibling_student=sibling_obj
                    )

        return redirect(f'/Admin_Principal/Admin_EditStudent?class_id={new_class.id}&student_id={student.id}')

    return render(request, 'Admin_EditStudent.html', {
        'classes': classes,
        'students': students,
        'selected_class_id': selected_class_id,
        'selected_student_id': selected_student_id,
        'student': selected_student,
        'parent': selected_parent,
        'existing_siblings': existing_siblings,
    })

def get_student_details(request):
    student_id = request.GET.get('student_id')
    if not student_id:
        return JsonResponse({'error': 'No student selected'}, status=400)

    student = get_object_or_404(Student_Model, id=student_id)
    parent = Parent_Model.objects.filter(Student=student).first()
    siblings = Sibling_model.objects.filter(Student=student)

    sibling_data = []
    for s in siblings:
        sibling_data.append({
            'class_id': s.Sibling_student.Class.id,
            'student_id': s.Sibling_student.id
        })

    data = {
        'student': {
            'id': student.id,
            'Admission_no': student.Admission_no,
            'Adm_date': student.Adm_date.strftime('%Y-%m-%d') if student.Adm_date else '',
            'Class_id': student.Class.id,
            'Class_display': f"{student.Class.Class_no} - {student.Class.Section}",
            'Name': student.Name,
            'Gender': student.Gender,
            'DOB': student.DOB.strftime('%Y-%m-%d') if student.DOB else '',
            'Blood_group': student.Blood_group,
            'MobileNumber': student.MobileNumber or '',
            'Category': student.Category or '',
            'Caste': student.Caste or '',
            'Religion': student.Religion or '',
            'APL_BPL': student.APL_BPL or 'APL',
            'Aadhar': student.Aadhar or '',
            'Local_body': student.Local_body or '',
            'Address': student.Address or '',
            'Bank_ac': student.Bank_ac or '',
            'Bank_name': student.Bank_name or '',
            'IFSC': student.IFSC or '',
        },
        'parent': {
            'Father_name': parent.Father_name if parent else '',
            'Mother_name': parent.Mother_name if parent else '',
            'F_occupation': parent.F_occupation if parent else '',
            'M_occupation': parent.M_occupation if parent else '',
            'F_phone': parent.F_phone if parent else '',
            'M_phone': parent.M_phone if parent else '',
        },
        'siblings': sibling_data
    }

    return JsonResponse(data)  # Corrected line





@transaction.atomic
def Add_new_teacher(request):
    if request.method == 'POST':
        teacher_code = request.POST.get('Code', '').strip()
        name = request.POST.get('Name', '').strip()
        designation = request.POST.get('Designation', '').strip()
        mobile_number = request.POST.get('MobileNumber', '').strip()
        email = request.POST.get('Email', '').strip()

        # 1. Check for duplicate Teacher Code
        if Teacher_Model.objects.filter(Code=teacher_code).exists():
            messages.error(request, 'A teacher with this Teacher Code already exists.')
            return render(request, 'Add_New_Teacher.html', request.POST)

        # 2. Check for duplicate Mobile Number
        if Teacher_Model.objects.filter(MobileNumber=mobile_number).exists():
            messages.error(request, 'A teacher with this Mobile Number already exists.')
            return render(request, 'Add_New_Teacher.html', request.POST)

        # 3. Check for duplicate Email (if provided)
        if email and Teacher_Model.objects.filter(Email=email).exists():
            messages.error(request, 'A teacher with this Email Address already exists.')
            return render(request, 'Add_New_Teacher.html', request.POST)

        # 4. Create Django User Account for Teacher
        teacher_user = User.objects.create_user(
            username=f'T_{teacher_code}',
            password=f'T_{teacher_code}',
            email=email if email else ''
        )

        # 5. Assign Role
        Role_Model.objects.create(
            user_type='Teacher',
            Login=teacher_user
        )

        # 6. Create Teacher Record
        Teacher_Model.objects.create(
            Code=teacher_code,
            Name=name,
            Designation=designation,
            MobileNumber=mobile_number,
            Email=email if email else None,
            Login=teacher_user
        )

        messages.success(request, f'Teacher details of {name} added successfully! User name: T_{teacher_code}, Password: T_{teacher_code}')
        return redirect('Add_new_teacher')

    return render(request, 'Add_New_Teacher.html')



def Remove_Teacher(request):
    teachers = Teacher_Model.objects.all().order_by('Name')
    selected_teacher = None
    linked_class = None
    linked_subjects = []

    teacher_id = request.GET.get('teacher_id') or request.POST.get('teacher_id')

    if teacher_id:
        selected_teacher = get_object_or_404(Teacher_Model, id=teacher_id)
        # Check if teacher is assigned as Class Teacher
        linked_class = Class_model.objects.filter(Class_teacher=selected_teacher).first()
        # Check if teacher is assigned to any Subjects
        linked_subjects = Subject_model.objects.filter(Subject_teacher=selected_teacher)

    if request.method == 'POST' and 'confirm_delete' in request.POST:
        if not selected_teacher:
            messages.error(request, "Please select a teacher to remove.")
            return redirect('Remove_Teacher')

        # 1. Block removal if the teacher is a Class Teacher
        if linked_class:
            messages.error(
                request,
                f"Cannot remove teacher '{selected_teacher.Name}'. Please change the class charge for "
                f"Class {linked_class.Class_no} - Section '{linked_class.Section}' first."
            )
            return render(request, 'Remove_Teacher.html', {
                'teachers': teachers,
                'selected_teacher': selected_teacher,
                'linked_class': linked_class,
                'linked_subjects': linked_subjects,
            })

        # 2. Proceed with deletion of User (which cascades to Teacher_Model and Role_Model)
        teacher_name = selected_teacher.Name
        teacher_user = selected_teacher.Login

        if teacher_user:
            teacher_user.delete()
        else:
            selected_teacher.delete()

        messages.success(request, f"Teacher '{teacher_name}' and their user login account were removed successfully.")
        return redirect('Remove_Teacher')

    return render(request, 'Remove_Teacher.html', {
        'teachers': teachers,
        'selected_teacher': selected_teacher,
        'linked_class': linked_class,
        'linked_subjects': linked_subjects,
    })

@transaction.atomic
def Edit_Teacher(request):
    teachers = Teacher_Model.objects.all().order_by('Name')
    selected_teacher = None
    teacher_id = request.GET.get('teacher_id') or request.POST.get('teacher_id')

    if teacher_id:
        selected_teacher = get_object_or_404(Teacher_Model, id=teacher_id)

    if request.method == 'POST':
        if not selected_teacher:
            messages.error(request, 'Please select a valid teacher to update.')
            return redirect('Edit_Teacher')

        teacher_code = request.POST.get('Code', '').strip()
        name = request.POST.get('Name', '').strip()
        designation = request.POST.get('Designation', '').strip()
        mobile_number = request.POST.get('MobileNumber', '').strip()
        email = request.POST.get('Email', '').strip()

        # Check for duplicate Teacher Code (excluding current teacher)
        if Teacher_Model.objects.filter(Code=teacher_code).exclude(id=selected_teacher.id).exists():
            messages.error(request, 'Another teacher with this Teacher Code already exists.')
            return render(request, 'Edit_Teacher.html', {
                'teachers': teachers,
                'selected_teacher': selected_teacher,
            })

        # Check for duplicate Mobile Number (excluding current teacher)
        if Teacher_Model.objects.filter(MobileNumber=mobile_number).exclude(id=selected_teacher.id).exists():
            messages.error(request, 'Another teacher with this Mobile Number already exists.')
            return render(request, 'Edit_Teacher.html', {
                'teachers': teachers,
                'selected_teacher': selected_teacher,
            })

        # Check for duplicate Email (excluding current teacher)
        if email and Teacher_Model.objects.filter(Email=email).exclude(id=selected_teacher.id).exists():
            messages.error(request, 'Another teacher with this Email Address already exists.')
            return render(request, 'Edit_Teacher.html', {
                'teachers': teachers,
                'selected_teacher': selected_teacher,
            })

        # Update Teacher model fields
        selected_teacher.Code = teacher_code
        selected_teacher.Name = name
        selected_teacher.Designation = designation
        selected_teacher.MobileNumber = mobile_number
        selected_teacher.Email = email if email else None
        selected_teacher.save()

        # Update associated Django User username & email if linked
        if selected_teacher.Login:
            user = selected_teacher.Login
            user.username = f'T_{teacher_code}'
            user.email = email if email else ''
            user.save()

        messages.success(request, f'Teacher details for "{name}" updated successfully!')
        return redirect(f"/Admin_Principal/Edit_Teacher/?teacher_id={selected_teacher.id}")

    return render(request, 'Edit_Teacher.html', {
        'teachers': teachers,
        'selected_teacher': selected_teacher,
    })


@transaction.atomic
def Admin_AddEdit_Class(request):
    classes = Class_model.objects.all().order_by('Section', 'Class_no', 'Division')
    teachers = Teacher_Model.objects.all().order_by('Name')

    # Pre-calculate assigned class teachers for warning
    assigned_teachers = {
        cls.Class_teacher.id: f"{cls.Section} class {cls.Class_no}{cls.Division or ''}"
        for cls in Class_model.objects.select_related('Class_teacher').all()
    }

    # Choices from model definition
    section_choices = Class_model._meta.get_field('Section').choices
    division_choices = Class_model._meta.get_field('Division').choices

    selected_class_id = request.GET.get('class_id') or request.POST.get('class_id')
    selected_class = None
    existing_subjects = []

    if selected_class_id and str(selected_class_id).isdigit():
        selected_class = get_object_or_404(Class_model, id=int(selected_class_id))
        existing_subjects = Subject_model.objects.filter(Class=selected_class).select_related('Subject_teacher')

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- REMOVE CLASS ACTION ---
        if action == 'delete_class':
            if not selected_class:
                messages.error(request, "No valid class selected for removal.")
                return redirect('Admin_AddEdit_Class')

            # Constraint Check: Prevent deletion if students are assigned to this class
            student_count = Student_Model.objects.filter(Class=selected_class).count()
            if student_count > 0:
                messages.error(
                    request,
                    f"Cannot remove '{selected_class.Section} class {selected_class.Class_no}{selected_class.Division}'! "
                    f"There are {student_count} student(s) linked to this class. Reassign or remove students first."
                )
                return redirect(f"/Admin_Principal/Admin_AddEdit_Class/?class_id={selected_class.id}")

            # Safe to delete class (and its subjects due to CASCADE)
            class_name_str = f"{selected_class.Section} class {selected_class.Class_no}{selected_class.Division}"
            selected_class.delete()
            messages.success(request, f"Class '{class_name_str}' has been deleted successfully.")
            return redirect('Admin_AddEdit_Class')

        # --- SAVE / UPDATE CLASS ACTION ---
        class_no = request.POST.get('Class_no', '').strip()
        section = request.POST.get('Section', '').strip()
        division = request.POST.get('Division', '').strip()
        class_teacher_id = request.POST.get('Class_teacher', '').strip()
        subjects_json = request.POST.get('subjects_data', '[]')

        if not class_no or not section or not division or not class_teacher_id:
            messages.error(request,
                           "Please fill in all required fields (Class No, Section, Division, and Class Teacher).")
            return redirect('Admin_AddEdit_Class')

        class_teacher = get_object_or_404(Teacher_Model, id=class_teacher_id)

        # 1. Prevent Duplicate Class
        duplicate_qs = Class_model.objects.filter(
            Class_no=class_no,
            Section=section,
            Division=division
        )
        if selected_class:
            duplicate_qs = duplicate_qs.exclude(id=selected_class.id)

        if duplicate_qs.exists():
            messages.error(request, f"Class '{section} class {class_no}{division}' already exists!")
            return render(request, 'Admin_AddEdit_Class.html', {
                'classes': classes,
                'teachers': teachers,
                'sections': section_choices,
                'divisions': division_choices,
                'selected_class': selected_class,
                'assigned_teachers_json': json.dumps(assigned_teachers),
            })

        # 2. Prevent Duplicate Subject Codes
        try:
            subjects_list = json.loads(subjects_json)
        except json.JSONDecodeError:
            subjects_list = []

        seen_codes = set()
        for subj in subjects_list:
            code = subj.get('code', '').strip().upper()
            if code in seen_codes:
                messages.error(request, f"Duplicate subject code '{code}' detected for this class!")
                return render(request, 'Admin_AddEdit_Class.html', {
                    'classes': classes,
                    'teachers': teachers,
                    'sections': section_choices,
                    'divisions': division_choices,
                    'selected_class': selected_class,
                    'assigned_teachers_json': json.dumps(assigned_teachers),
                })
            seen_codes.add(code)

        # 3. Class Teacher Conflict Check
        other_class = Class_model.objects.filter(Class_teacher=class_teacher)
        if selected_class:
            other_class = other_class.exclude(id=selected_class.id)
        if other_class.exists():
            linked_cls = other_class.first()
            messages.warning(
                request,
                f"Note: Teacher '{class_teacher.Name}' was previously Class Teacher for {linked_cls.Section} class {linked_cls.Class_no}{linked_cls.Division}."
            )

        # 4. Save/Update Class
        if selected_class:
            selected_class.Class_no = class_no
            selected_class.Section = section
            selected_class.Division = division
            selected_class.Class_teacher = class_teacher
            selected_class.save()
            target_class = selected_class
            messages.success(request, f"Class '{section} class {class_no}{division}' updated successfully!")
        else:
            target_class = Class_model.objects.create(
                Class_no=class_no,
                Section=section,
                Division=division,
                Class_teacher=class_teacher
            )
            messages.success(request, f"New Class '{section} class {class_no}{division}' created successfully!")

        # 5. Save Subjects
        Subject_model.objects.filter(Class=target_class).delete()

        for subj in subjects_list:
            code = subj.get('code', '').strip()
            name = subj.get('name', '').strip()
            teacher_id = subj.get('teacher_id')

            subj_teacher = Teacher_Model.objects.filter(id=teacher_id).first() if teacher_id else None
            if code and name:
                Subject_model.objects.create(
                    Code=code,
                    Name=name,
                    Class=target_class,
                    Subject_teacher=subj_teacher
                )

        return redirect(f"/Admin_Principal/Admin_AddEdit_Class/?class_id={target_class.id}")

    return render(request, 'Admin_AddEdit_Class.html', {
        'classes': classes,
        'teachers': teachers,
        'sections': section_choices,
        'divisions': division_choices,
        'selected_class': selected_class,
        'existing_subjects': existing_subjects,
        'assigned_teachers_json': json.dumps(assigned_teachers),
    })
def get_class_details(request):
    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'error': 'No class selected'}, status=400)

    cls = get_object_or_404(Class_model, id=class_id)
    subjects = Subject_model.objects.filter(Class=cls).select_related('Subject_teacher')

    subject_data = []
    for s in subjects:
        subject_data.append({
            'code': s.Code,
            'name': s.Name,
            'teacher_id': s.Subject_teacher.id if s.Subject_teacher else '',
            'teacher_name': s.Subject_teacher.Name if s.Subject_teacher else 'Unassigned'
        })

    return JsonResponse({
        'class_no': cls.Class_no,
        'section': cls.Section,
        'class_teacher_id': cls.Class_teacher.id if cls.Class_teacher else '',
        'subjects': subject_data
    })





@transaction.atomic
def Admin_Student_Transfer(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section', 'Division')
    selected_source_class = None
    students = []
    source_class_id = request.GET.get('source_class_id') or request.POST.get('source_class_id')

    if source_class_id:
        selected_source_class = get_object_or_404(Class_model, id=source_class_id)
        students = Student_Model.objects.filter(Class=selected_source_class).order_by('Roll_no', 'Name')

    if request.method == 'POST' and 'transfer_students' in request.POST:
        target_class_id = request.POST.get('target_class_id')
        selected_student_ids = request.POST.getlist('selected_students')

        if not target_class_id:
            messages.error(request, "Please select a target class to transfer students to.")
            return redirect(f"/Admin_Principal/Admin_Student_Transfer/?source_class_id={source_class_id}")

        if not selected_student_ids:
            messages.error(request, "No students were selected for transfer.")
            return redirect(f"/Admin_Principal/Admin_Student_Transfer/?source_class_id={source_class_id}")

        if str(target_class_id) == str(source_class_id):
            messages.error(request, "Source class and target class cannot be the same.")
            return redirect(f"/Admin_Principal/Admin_Student_Transfer/?source_class_id={source_class_id}")

        target_class = get_object_or_404(Class_model, id=target_class_id)

        # 1. Update Class for selected students
        Student_Model.objects.filter(id__in=selected_student_ids).update(Class=target_class)

        # 2. Recalculate Roll Numbers for Source Class alphabetically
        source_students = Student_Model.objects.filter(Class=selected_source_class).order_by('Name')
        for index, std in enumerate(source_students, start=1):
            if std.Roll_no != index:
                std.Roll_no = index
                std.save(update_fields=['Roll_no'])

        # 3. Recalculate Roll Numbers for Target Class alphabetically
        target_students = Student_Model.objects.filter(Class=target_class).order_by('Name')
        for index, std in enumerate(target_students, start=1):
            if std.Roll_no != index:
                std.Roll_no = index
                std.save(update_fields=['Roll_no'])

        messages.success(
            request,
            f"Successfully transferred {len(selected_student_ids)} student(s) to Class {target_class.Class_no} - {target_class.Section} ({target_class.Division or ''})."
        )
        return redirect(f"/Admin_Principal/Admin_Student_Transfer/?source_class_id={source_class_id}")

    return render(request, 'Admin_Student_transfer.html', {
        'classes': classes,
        'selected_source_class': selected_source_class,
        'students': students,
    })



def Admin_Schedule_Exam(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section')

    selected_class_id = request.GET.get('class_id') or request.POST.get('class_id')
    selected_exam_name = request.GET.get('exam_name') or request.POST.get('exam_name')
    edit_exam_id = request.GET.get('edit_id')

    selected_class = None
    subjects = Subject_model.objects.none()
    existing_exam_names = []
    scheduled_exams = Exam_model.objects.none()
    edit_exam_obj = None

    if selected_class_id:
        selected_class = Class_model.objects.filter(id=selected_class_id).first()
        if selected_class:
            subjects = Subject_model.objects.filter(Class=selected_class)

            # Get distinct existing exam names for the selected class
            existing_exam_names = Exam_model.objects.filter(
                Subject__Class=selected_class
            ).values_list('Name', flat=True).distinct()

            if selected_exam_name:
                scheduled_exams = Exam_model.objects.filter(
                    Subject__Class=selected_class,
                    Name=selected_exam_name
                ).select_related('Subject').order_by('Date', 'TimeFrom')

    # Load object for editing inside table list
    if edit_exam_id:
        edit_exam_obj = Exam_model.objects.filter(id=edit_exam_id).first()

    # Handle Form Submission
    if request.method == 'POST':
        action = request.POST.get('action')

        if action in ['add', 'update']:
            exam_name = request.POST.get('exam_name_input', '').strip() or selected_exam_name
            subject_id = request.POST.get('subject_id')
            exam_date_str = request.POST.get('exam_date')
            time_from = request.POST.get('time_from')
            time_to = request.POST.get('time_to')
            max_mark = request.POST.get('max_mark')

            # Validation
            try:
                max_mark_val = int(max_mark)
                if max_mark_val <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                messages.error(request, "Maximum mark must be a positive integer above zero.")
                return redirect(f"{request.path}?class_id={selected_class_id}&exam_name={selected_exam_name}")

            # School Calendar Validation
            try:
                exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date()
                cal_entry = SchoolCalender_model.objects.filter(CalenderDate=exam_date).first()
                if cal_entry and  not cal_entry.Working_day:
                    messages.error(request,
                                   f"Selected date ({exam_date}) is not a designated working day in the school calendar.")
                    return redirect(f"{request.path}?class_id={selected_class_id}&exam_name={selected_exam_name}")
            except Exception:
                messages.error(request, "Invalid date selection.")
                return redirect(f"{request.path}?class_id={selected_class_id}&exam_name={selected_exam_name}")

            subject_obj = get_object_or_404(Subject_model, id=subject_id)

            if action == 'add':
                Exam_model.objects.create(
                    Name=exam_name,
                    Subject=subject_obj,
                    Date=exam_date,
                    TimeFrom=time_from,
                    TimeTo=time_to,
                    Max_mark=max_mark_val
                )
                messages.success(request, "Exam schedule entry added successfully.")
            elif action == 'update':
                exam_id = request.POST.get('exam_id')
                exam_obj = get_object_or_404(Exam_model, id=exam_id)
                exam_obj.Name = exam_name
                exam_obj.Subject = subject_obj
                exam_obj.Date = exam_date
                exam_obj.TimeFrom = time_from
                exam_obj.TimeTo = time_to
                exam_obj.Max_mark = max_mark_val
                exam_obj.save()
                messages.success(request, "Exam schedule updated successfully.")

            return redirect(f"{request.path}?class_id={selected_class_id}&exam_name={exam_name}")

        elif action == 'delete':
            exam_id = request.POST.get('exam_id')
            Exam_model.objects.filter(id=exam_id).delete()
            messages.success(request, "Exam entry removed.")
            return redirect(f"{request.path}?class_id={selected_class_id}&exam_name={selected_exam_name}")

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'selected_class_id': selected_class_id,
        'existing_exam_names': existing_exam_names,
        'selected_exam_name': selected_exam_name,
        'subjects': subjects,
        'scheduled_exams': scheduled_exams,
        'edit_exam_obj': edit_exam_obj,
    }
    return render(request, 'Admin_Schedule_Exam.html', context)




def Admin_Mark_Verify(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section', 'Division')

    selected_class_id = request.GET.get('class_id') or request.POST.get('class_id')
    selected_exam_name = request.GET.get('exam_name') or request.POST.get('exam_name')

    selected_class = None
    unverified_exam_names = []
    subjects = []
    verification_grid = []

    if selected_class_id:
        selected_class = Class_model.objects.filter(id=selected_class_id).first()
        if selected_class:
            # Get distinct exam names for this class that have UNVERIFIED mark entries
            unverified_exam_names = Exam_model.objects.filter(
                Subject__Class=selected_class,
                marks_model__Principal_verification=False
            ).values_list('Name', flat=True).distinct().order_by('Name')

            # Build matrix if an exam is selected
            if selected_exam_name:
                # Fetch exams & subjects for the class & exam name
                exams = Exam_model.objects.filter(
                    Name=selected_exam_name,
                    Subject__Class=selected_class
                ).select_related('Subject')

                subjects = [exam.Subject for exam in exams]
                exam_by_subject = {exam.Subject.id: exam for exam in exams}

                students = Student_Model.objects.filter(Class=selected_class).order_by('Roll_no', 'Name')

                # Fetch all marks for this class & exam
                marks_qs = Marks_model.objects.filter(
                    Student__Class=selected_class,
                    Exam__Name=selected_exam_name
                ).select_related('Student', 'Exam', 'Exam__Subject')

                # Key mapping: (student_id, subject_id) -> Marks_model instance
                marks_map = {(m.Student.id, m.Exam.Subject.id): m for m in marks_qs}

                for student in students:
                    student_cells = []
                    for subject in subjects:
                        exam = exam_by_subject.get(subject.id)
                        mark_obj = marks_map.get((student.id, subject.id))

                        if mark_obj:
                            student_cells.append({
                                'mark_id': mark_obj.id,
                                'score': mark_obj.Score,
                                'max_mark': exam.Max_mark if exam else 0,
                                'verified': mark_obj.Principal_verification,
                            })
                        else:
                            student_cells.append({
                                'mark_id': None,
                                'score': 'N/A',
                                'max_mark': exam.Max_mark if exam else '-',
                                'verified': False,
                            })

                    verification_grid.append({
                        'student': student,
                        'cells': student_cells,
                    })

    # Handle Bulk Verification Form Submission
    if request.method == 'POST' and 'verify_marks' in request.POST:
        selected_mark_ids = request.POST.getlist('selected_marks')

        if not selected_mark_ids:
            messages.error(request, "Please select at least one student mark record to verify.")
            return redirect(f"{request.path}?class_id={selected_class_id}&exam_name={selected_exam_name}")

        with transaction.atomic():
            updated_count = Marks_model.objects.filter(id__in=selected_mark_ids).update(Principal_verification=True)
            messages.success(request, f"Successfully verified marks for {updated_count} mark entry(ies).")

        return redirect(f"{request.path}?class_id={selected_class_id}")

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'unverified_exam_names': unverified_exam_names,
        'selected_exam_name': selected_exam_name,
        'subjects': subjects,
        'verification_grid': verification_grid,
    }
    return render(request, 'Admin_Mark_Verify.html', context)
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None




@transaction.atomic
def Admin_Set_TimeTable(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section', 'Division')

    # Check POST first, then GET parameter
    selected_class_id = request.POST.get('class_id') or request.GET.get('class_id')

    selected_class = None
    subjects = Subject_model.objects.none()

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = list(range(1, 9))

    # Grid dictionary mapping (day, period_int) -> subject_id
    saved_grid = {}

    if selected_class_id:
        selected_class = Class_model.objects.filter(id=selected_class_id).first()
        if selected_class:
            subjects = Subject_model.objects.filter(Class=selected_class).order_by('Name')

            # Populate existing saved timetable entries
            existing_entries = TimeTable_model.objects.filter(Class=selected_class)
            for entry in existing_entries:
                saved_grid[(entry.Day, int(entry.Period))] = entry.Subject_id

    if request.method == 'POST':
        if not selected_class:
            messages.error(request, "Please select a valid class before saving.")
            return redirect(request.path)

        new_entries = []

        for day in days:
            for p in periods:
                param_name = f"cell_{day}_{p}"
                subject_id = request.POST.get(param_name, '').strip()

                if subject_id:
                    try:
                        subject_id_int = int(subject_id)
                    except ValueError:
                        continue

                    subject_obj = get_object_or_404(Subject_model, id=subject_id_int)
                    new_entries.append(
                        TimeTable_model(
                            Class=selected_class,
                            Day=day,
                            Period=p,
                            Subject=subject_obj
                        )
                    )

        # Clear previous timetable for selected class and bulk insert new choices
        TimeTable_model.objects.filter(Class=selected_class).delete()
        TimeTable_model.objects.bulk_create(new_entries)
        messages.success(request, f"Timetable for Class {selected_class} saved successfully!")
        return redirect(f"{request.path}?class_id={selected_class.id}")

    # Build matrix list for simple iteration in template without custom filters
    # Structure: matrix = [{'day': 'Monday', 'slots': [{'period': 1, 'selected_subject_id': 10}, ...]}, ...]
    timetable_rows = []
    for day in days:
        slots = []
        for p in periods:
            selected_subject_id = saved_grid.get((day, p), None)
            slots.append({
                'period': p,
                'selected_subject_id': selected_subject_id
            })
        timetable_rows.append({
            'day': day,
            'slots': slots
        })

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'selected_class_id': selected_class_id,
        'subjects': subjects,
        'periods': periods,
        'timetable_rows': timetable_rows,
    }
    return render(request, 'Admin_Set_TimeTable.html', context)


def SchoolCalender_Insert(request):
    context = {}
    form = SchoolCalender_Form(request.POST or None,request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect(SchoolCalender_Insert)
    context['f'] = form
    context["dataset"] = SchoolCalender_model.objects.all()

    return render(request, "SchoolCalender_Insert.html", context)



@transaction.atomic
def Admin_LibraryBooks(request):
    library_books = LibraryBook_model.objects.all().order_by('BookNo')

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        book_id = request.POST.get('book_id', '').strip()

        # Handle Deletion
        if action == 'delete':
            if book_id:
                book = get_object_or_404(LibraryBook_model, id=book_id)
                book_name = book.BookName
                book.delete()
                messages.success(request, f'Book "{book_name}" was removed successfully!')
            else:
                messages.error(request, 'Invalid book selected for removal.')
            return redirect('Admin_LibraryBooks')

        # Handle Create/Update (Save)
        book_no = request.POST.get('BookNo', '').strip()
        language = request.POST.get('Language', '').strip()
        book_name = request.POST.get('BookName', '').strip()
        author = request.POST.get('Author', '').strip()
        publisher = request.POST.get('Publisher', '').strip()
        topic = request.POST.get('Topic', '').strip()
        description = request.POST.get('Description', '').strip()

        # Duplicate check for BookNo
        duplicate_qs = LibraryBook_model.objects.filter(BookNo=book_no)
        if book_id:
            duplicate_qs = duplicate_qs.exclude(id=book_id)

        if duplicate_qs.exists():
            messages.error(request, f'A book with Book Number "{book_no}" already exists.')
            return redirect('Admin_LibraryBooks')

        if book_id:
            # Update existing book
            book = get_object_or_404(LibraryBook_model, id=book_id)
            book.BookNo = book_no
            book.Language = language
            book.BookName = book_name
            book.Author = author
            book.Publisher = publisher
            book.Topic = topic
            book.Description = description
            book.save()
            messages.success(request, f'Book details of "{book_name}" updated successfully!')
        else:
            # Create new book
            LibraryBook_model.objects.create(
                BookNo=book_no,
                BookName=book_name,
                Author=author,
                Publisher=publisher,
                Topic=topic,
                Description=description,
                Language=language
            )
            messages.success(request, f'Book details of "{book_name}" added successfully!')

        return redirect('Admin_LibraryBooks')

    return render(request, 'Admin_LibraryBooks.html', {'library_books': library_books})




@transaction.atomic
def Admin_NoticeIssue(request):
    if request.method == 'POST':
        title = request.POST.get('Title', '').strip()
        matter = request.POST.get('Matter', '').strip()
        remark = request.POST.get('Remark', '').strip()
        IssueDate =date.today()

        if not title or not matter:
            messages.error(request, 'Both Title and Matter are required to issue a notice.')
            return redirect('Admin_NoticeIssue')

        #  Create Notice Record
        Notice_model.objects.create(
            Title=title,
            Matter=matter,
            Remark=remark,
            IssueDate=IssueDate
        )

        messages.success(request, f'Notice issued successfully!')
        return redirect('Admin_NoticeIssue')

    return render(request, 'Admin_NoticeIssue.html')




def admin_classinfo(request):
    """Display students filtered by selected class (via GET param 'class_id')
    """
    classes = Class_model.objects.all().order_by('Class_no', 'Section')
    class_id = request.GET.get('class_id')
    students = Student_Model.objects.none()
    subjects = Subject_model.objects.none()
    selected_class = Class_model.objects.none()

    if class_id:
        # Try filter by PK first, fallback to Class_no if ValueError/No match
        try:
            students = Student_Model.objects.filter(Class_id=class_id).order_by('Roll_no')
        except Exception:
            students = Student_Model.objects.filter(Class__Class_no=class_id).order_by('Roll_no')

        try:
            selected_class = Class_model.objects.filter(id=class_id).first()
        except Exception:
            selected_class = None

        try:
            subjects= Subject_model.objects.filter(Class_id=class_id)
        except Exception:
            subjects = None

    return render(request, "admin_classinfo.html", {
        "classes": classes,
        "students": students,
        "selected_id": class_id,
        "selected_class": selected_class,
        "subjects": subjects
    })




def admin_student_info(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section')
    class_id = request.GET.get('class_id') or request.POST.get('class_id')
    student_id = request.GET.get('student_id') or request.POST.get('student_id')
    students = Student_Model.objects.none()
    student = None


    if class_id:
        # Try filter by PK first, fallback to Class_no if ValueError/No match
        try:
            students = Student_Model.objects.filter(Class_id=class_id).order_by('Roll_no')
        except Exception:
            students = Student_Model.objects.filter(Class__Class_no=class_id).order_by('Roll_no')

    if student_id:
        try:
            student = Student_Model.objects.filter(id=student_id).first()
        except Exception:
            student = None

    if student:
        # Retrieve associated parent details
        parent = Parent_Model.objects.filter(Student=student).first()

        # Retrieve sibling details
        sibling_relations = Sibling_model.objects.filter(Student=student).select_related('Sibling_student',
                                                                                     'Sibling_student__Class')
        siblings = [rel.Sibling_student for rel in sibling_relations]
    else:
        parent = None
        siblings = []


    return render(request, 'Admin_StudentInfo.html', {
        'classes': classes,
        'students': students,
        'student': student,
        'parent': parent,
        'siblings': siblings,
        'selected_id': class_id,
        'selected_student_id': student_id
    })



def Admin_AttendanceReport(request):
    # Retrieve query parameters or default to current date values
    today = date.today()
    selected_class_id = request.GET.get('class_id')
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))

    classes = Class_model.objects.all().order_by('Class_no', 'Section', 'Division')

    # Generate list of years (e.g., past 3 years to next year)
    years = range(today.year - 2, today.year + 2)
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    report_data = []
    second_table_data = []
    days_in_month = []
    selected_class = None

    if selected_class_id:
        try:
            selected_class = Class_model.objects.get(id=selected_class_id)
            # Fetch students ordered by roll number
            students = Student_Model.objects.filter(Class=selected_class).order_by('Roll_no')

            # Calculate total days in month
            today = date.today()

            num_days = calendar.monthrange(selected_year, selected_month)[1]

            # Include days only up to today's date
            month_dates = [
                d for day in range(1, num_days + 1)
                if (d := date(selected_year, selected_month, day)) <= today
            ]
            # Pre-fetch school calendar data for non-working days
            calendar_entries = {
                entry.CalenderDate: entry
                for entry in SchoolCalender_model.objects.filter(
                    CalenderDate__year=selected_year,
                    CalenderDate__month=selected_month
                )
            }

            # Map date status: True for working, False/None for Holiday or Weekend
            for d in month_dates:
                cal_entry = calendar_entries.get(d)
                is_weekend = d.weekday() in (5, 6)  # Saturday or Sunday

                if is_weekend or (cal_entry and not cal_entry.Working_day):
                    days_in_month.append({'day': d.day, 'date': d, 'is_holiday': True})
                else:
                    days_in_month.append({'day': d.day, 'date': d, 'is_holiday': False})

            # Pre-fetch attendance and leave records for performance
            attendance_qs = Attendance_model.objects.filter(
                Student__Class=selected_class,
                AbsentDate__year=selected_year,
                AbsentDate__month=selected_month
            )

            leave_qs = LeaveApplication_model.objects.filter(
                Student__Class=selected_class,
                AbsentDate__year=selected_year,
                AbsentDate__month=selected_month
            )

            # Build data maps
            # key: (student_id, date)
            absent_map = {(att.Student_id, att.AbsentDate): att for att in attendance_qs}
            leave_map = {(leave.Student_id, leave.AbsentDate): leave for leave in leave_qs}

            for student in students:
                student_attendance = []
                for day_info in days_in_month:
                    d = day_info['date']
                    if day_info['is_holiday']:
                        student_attendance.append({'status': 'Holiday'})
                    elif (student.id, d) in absent_map:
                        student_attendance.append({'status': 'Absent'})
                    else:
                        student_attendance.append({'status': 'Present'})

                report_data.append({
                    'student': student,
                    'attendance': student_attendance
                })

                # Table 2: Absent detail entries for this student
                student_absents = attendance_qs.filter(Student=student).order_by('AbsentDate')
                for abs_rec in student_absents:
                    leave_app = leave_map.get((student.id, abs_rec.AbsentDate))
                    second_table_data.append({
                        'roll_no': student.Roll_no,
                        'name': student.Name,
                        'absent_date': abs_rec.AbsentDate,
                        'parent_verified': abs_rec.Parent_verification,
                        'has_leave_app': True if leave_app else False,
                        'leave_status': leave_app.Status if leave_app else 'N/A'
                    })

        except Class_model.DoesNotExist:
            pass

    context = {
        'classes': classes,
        'months': months,
        'years': years,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'days_in_month': days_in_month,
        'report_data': report_data,
        'second_table_data': second_table_data,
        'selected_class': selected_class,
    }
    return render(request, 'Admin_AttendanceReport.html', context)


def Admin_Absenties(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section', 'Division')

    selected_class_id = request.GET.get('class_id')
    selected_date_str = request.GET.get('date')

    selected_class = None
    selected_date = None
    is_holiday = False
    holiday_reason = ""
    absentees = []

    if selected_class_id and selected_date_str:
        try:
            selected_class = Class_model.objects.get(id=selected_class_id)
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

            # Check if weekend (Saturday = 5, Sunday = 6)
            weekday = selected_date.weekday()
            if weekday == 5:
                is_holiday = True
                holiday_reason = "Holiday (Saturday)"
            elif weekday == 6:
                is_holiday = True
                holiday_reason = "Holiday (Sunday)"
            else:
                # Check SchoolCalender_model for non-working day
                cal_entry = SchoolCalender_model.objects.filter(CalenderDate=selected_date).first()
                if cal_entry and not cal_entry.Working_day:
                    is_holiday = True
                    holiday_reason = cal_entry.Description if cal_entry.Description else "Holiday"

            # If it's a working day, retrieve the list of absent students
            if not is_holiday:
                absent_records = Attendance_model.objects.filter(
                    Student__Class=selected_class,
                    AbsentDate=selected_date
                ).select_related('Student').order_by('Student__Roll_no')

                for record in absent_records:
                    absentees.append({
                        'roll_no': record.Student.Roll_no,
                        'name': record.Student.Name,
                        'parent_verified': record.Parent_verification,
                    })

        except (Class_model.DoesNotExist, ValueError):
            pass

    context = {
        'classes': classes,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'selected_date_str': selected_date_str,
        'selected_class': selected_class,
        'selected_date': selected_date,
        'is_holiday': is_holiday,
        'holiday_reason': holiday_reason,
        'absentees': absentees,
    }

    return render(request, 'Admin_Absenties.html', context)



def Admin_LateArrivals(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section', 'Division')

    selected_class_id = request.GET.get('class_id')
    selected_date_str = request.GET.get('date')

    selected_class = None
    selected_date = None
    is_holiday = False
    holiday_reason = ""
    late_arrivals = []

    if selected_class_id and selected_date_str:
        try:
            selected_class = Class_model.objects.get(id=selected_class_id)
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

            # Check if weekend (Saturday = 5, Sunday = 6)
            weekday = selected_date.weekday()
            if weekday == 5:
                is_holiday = True
                holiday_reason = "Holiday (Saturday)"
            elif weekday == 6:
                is_holiday = True
                holiday_reason = "Holiday (Sunday)"
            else:
                # Check SchoolCalender_model for non-working day
                cal_entry = SchoolCalender_model.objects.filter(CalenderDate=selected_date).first()
                if cal_entry and not cal_entry.Working_day:
                    is_holiday = True
                    holiday_reason = cal_entry.Description if cal_entry.Description else "Holiday"

            # If it's a working day, fetch records from LateComing_model
            if not is_holiday:
                late_records = LateComing_model.objects.filter(
                    Student__Class=selected_class,
                    Date=selected_date
                ).select_related('Student').order_by('Student__Roll_no')

                for record in late_records:
                    late_arrivals.append({
                        'roll_no': record.Student.Roll_no,
                        'name': record.Student.Name,
                        'arrival_time': record.Time,
                        'parent_verified': record.Parent_verification,
                    })

        except (Class_model.DoesNotExist, ValueError):
            pass

    context = {
        'classes': classes,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'selected_date_str': selected_date_str,
        'selected_class': selected_class,
        'selected_date': selected_date,
        'is_holiday': is_holiday,
        'holiday_reason': holiday_reason,
        'late_arrivals': late_arrivals,
    }

    return render(request, 'Admin_LateArrivals.html', context)





def Admin_MarkSheet(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section', 'Division')

    # Extract unique examination names available in the schedule
    exam_names = Exam_model.objects.values_list('Name', flat=True).distinct().order_by('Name')

    selected_class_id = request.GET.get('class_id')
    selected_exam_name = request.GET.get('exam_name')

    selected_class = None
    subjects = []
    mark_sheet_data = []

    if selected_class_id and selected_exam_name:
        try:
            selected_class = Class_model.objects.get(id=selected_class_id)
            students = Student_Model.objects.filter(Class=selected_class).order_by('Roll_no')

            # Get subjects associated with the class that have an exam schedule with this exam name
            exams = Exam_model.objects.filter(
                Name=selected_exam_name,
                Subject__Class=selected_class
            ).select_related('Subject')

            # Distinct subject list for table headers
            subjects = [exam.Subject for exam in exams]

            # Map exam by subject id
            exam_by_subject = {exam.Subject.id: exam for exam in exams}

            # Fetch marks for students in selected class & selected exam
            marks_qs = Marks_model.objects.filter(
                Student__Class=selected_class,
                Exam__Name=selected_exam_name
            ).select_related('Student', 'Exam', 'Exam__Subject')

            # Map marks: key = (student_id, subject_id)
            marks_map = {
                (m.Student.id, m.Exam.Subject.id): m for m in marks_qs
            }

            for student in students:
                student_marks = []
                total_obtained = 0
                total_max = 0

                for subject in subjects:
                    exam = exam_by_subject.get(subject.id)
                    mark_obj = marks_map.get((student.id, subject.id))

                    if mark_obj:
                        score = mark_obj.Score
                        max_mark = exam.Max_mark if exam else 0
                        total_obtained += score
                        total_max += max_mark
                        student_marks.append({
                            'score': score,
                            'max_mark': max_mark,
                            'verified': mark_obj.Principal_verification
                        })
                    else:
                        student_marks.append({
                            'score': 'N/A',
                            'max_mark': exam.Max_mark if exam else '-',
                            'verified': False
                        })

                # Calculate overall percentage
                percentage = round((total_obtained / total_max * 100), 2) if total_max > 0 else 0

                mark_sheet_data.append({
                    'roll_no': student.Roll_no,
                    'name': student.Name,
                    'marks': student_marks,
                    'total_obtained': total_obtained,
                    'total_max': total_max,
                    'percentage': percentage,
                })

        except Class_model.DoesNotExist:
            pass

    context = {
        'classes': classes,
        'exam_names': exam_names,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'selected_exam_name': selected_exam_name,
        'selected_class': selected_class,
        'subjects': subjects,
        'mark_sheet_data': mark_sheet_data,
    }

    return render(request, 'Admin_MarkSheet.html', context)



def Admin_ExamScheduleReport(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section', 'Division')

    selected_class_id = request.GET.get('class_id')
    selected_class = None
    exam_schedules = []

    if selected_class_id:
        try:
            selected_class = Class_model.objects.get(id=selected_class_id)

            # Fetch exams for subjects belonging to the selected class in descending order of date
            exam_schedules = Exam_model.objects.filter(
                Subject__Class=selected_class
            ).select_related('Subject', 'Subject__Subject_teacher').order_by('-Date', 'TimeFrom')

        except Class_model.DoesNotExist:
            pass

    context = {
        'classes': classes,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'selected_class': selected_class,
        'exam_schedules': exam_schedules,
    }

    return render(request, 'Admin_ExamScheduleReport.html', context)



def Admin_AcademicCalendarEntry(request):
    # Fetch date from GET or POST query
    raw_date = request.GET.get('CalenderDate') or request.POST.get('CalenderDate') or request.GET.get('date')
    selected_date = None
    calendar_entry = None

    if raw_date:
        # Standardize date format to YYYY-MM-DD for standard HTML date input
        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            selected_date = parsed_date.strftime("%Y-%m-%d")
            calendar_entry = SchoolCalender_model.objects.filter(CalenderDate=parsed_date).first()
        except ValueError:
            selected_date = raw_date

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'cancel':
            return redirect('SchoolDiaryHeaderView')

        cal_date = request.POST.get('CalenderDate')
        if not cal_date:
            messages.error(request, "Please select a date.")
            return render(request, 'Admin_AcademicCalendarEntry.html', {
                'calendar_entry': calendar_entry,
                'selected_date': selected_date
            })

        if action == 'update':
            is_working = request.POST.get('Working_day') == 'on'
            description = request.POST.get('Description', '').strip()

            SchoolCalender_model.objects.update_or_create(
                CalenderDate=cal_date,
                defaults={
                    'Working_day': is_working,
                    'Description': description,
                }
            )
            messages.success(request, f"Calendar entry for {cal_date} updated successfully.")
            return redirect(f"{request.path}?CalenderDate={cal_date}")

        elif action == 'delete':
            if calendar_entry:
                calendar_entry.delete()
                messages.success(request, f"Entry for {cal_date} removed successfully.")
                return redirect(request.path)
            else:
                messages.warning(request, f"No entry found for date {cal_date} to delete.")

    return render(request, 'Admin_AcademicCalendarEntry.html', {
        'calendar_entry': calendar_entry,
        'selected_date': selected_date
    })





def Admin_Acknowledgements(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        # Handle inline Principal Verification
        if action == 'verify_principal':
            ack_id = request.POST.get('ack_id')
            acknowledgement = get_object_or_404(
                Acknowledgement_model, id=ack_id)
            acknowledgement.Principal_verification = True
            acknowledgement.save()
            messages.success(request, f"Acknowledgement for {acknowledgement.Student.Name} verified successfully.")
            return redirect('Admin_Acknowledgements')

    # Query all acknowledgements, latest date first
    # Using select_related to efficiently load student and class details
    acknowledgements = Acknowledgement_model.objects.select_related(
        'Student', 'Student__Class'
    ).order_by('-Date')

    context = {
        'acknowledgements': acknowledgements
    }
    return render(request, 'Admin_Acknowledgements.html', context)

def admin_home(request):
    context = {
        'total_students': 1250,
        'total_teachers': 85,
        'total_classes': 24,
        'today_absentees': 14,
        'role': Role_Model.objects.filter(Login=request.user).first()
    }
    return render(request, 'AdminHome.html', context)



@login_required
def change_password(request):
    """View to handle password changes for logged-in users."""

    # 1. Check if the user is a Superuser, Staff, or has an Admin/Principal role
    role = Role_Model.objects.filter(Login=request.user).first()

    if request.user.is_superuser or request.user.is_staff :
        print('admin')
        base_template = 'AdminPrincipalFrame.html'
    elif role and role.user_type == 'Student':
        base_template = 'StudentFrame.html'
    elif role and role.user_type == 'Parent':
        base_template = 'ParentFrame.html'
    elif role and role.user_type == 'Teacher':
        base_template = 'TeacherFrame.html'
    else:
        # Fallback checks if Role_Model is missing or empty
        if hasattr(request.user, 'student_model'):
            base_template = 'StudentFrame.html'
        elif hasattr(request.user, 'parent_model'):
            base_template = 'ParentFrame.html'
        elif hasattr(request.user, 'teacher_model'):
            base_template = 'TeacherFrame.html'
        else:
            base_template = 'AdminPrincipalFrame.html'  # Safe default fallback for admins

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')

            # 2. Redirect back to their respective home/dashboard views
            if base_template == 'StudentFrame.html':
                return redirect('StudentHome')
            elif base_template == 'ParentFrame.html':
                return redirect('ParentHome')
            elif base_template == 'TeacherFrame.html':
                return redirect('TeacherHome')
            else:
                return redirect('AdminHome')
        else:
            messages.error(request, 'Please correct the error(s) below.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'change_password.html', {
        'form': form,
        'base_template': base_template,
    })
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
import datetime
import calendar
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
from Admin_Principal.models import  Student_Model, Exam_model, \
    LibraryBook_model, Parent_Model, Sibling_model, TimeTable_model, SchoolCalender_model, Notice_model, Role_Model
from Parent.models import LeaveApplication_model
from .models import Attendance_model, ParentTeacherCommunication_model, LateComing_model, Acknowledgement_model, \
    Homework_model, Marks_model, Library_issue_model, HomeworkDone_model
from .models import Teacher_Model, Class_model, Subject_model


def TeacherHome(request):
    # Fetch logged-in teacher profile
    teacher = Teacher_Model.objects.filter(Login=request.user).first()

    # Fetch assigned class where teacher is Class Teacher
    selected_class = Class_model.objects.filter(Class_teacher=teacher).first() if teacher else None

    # Fetch all subjects taught by this teacher
    assigned_subjects = Subject_model.objects.filter(Subject_teacher=teacher) if teacher else []

    context = {
        'Selected_Teacher': teacher,
        'Selected_class': selected_class,
        'assigned_subjects': assigned_subjects,
    }
    return render(request, 'TeacherHome.html', context)

def students_by_class(request):
    """Display students filtered by selected class (via GET param 'class_id').
    If class_id is a primary key, filters by Class_id; if it's a Class_no value,
    falls back to filtering by Class__Class_no.
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

    return render(request, "teacher_students.html", {
        "classes": classes,
        "students": students,
        "selected_id": class_id,
        "selected_class": selected_class,
        "subjects": subjects
    })

def teacher_attendance(request):
    """Manage attendance for the teacher's assigned class.
    GET: show date picker and attendance list (or Holiday message).
    POST: save absent records into Attendance_model for selected date.
    """
    if not request.user.is_authenticated:
        return redirect('login')

    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()

    if not Selected_class:
        return render(request, 'Teacher_Attendance.html', { 'error': 'No class assigned', 'Selected_Teacher': Selected_Teacher })

    # date handling
    date_str = request.POST.get('attendance_date') if request.method == 'POST' else request.GET.get('date')
    if not date_str:
        selected_date = timezone.localdate()
    else:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            selected_date = timezone.localdate()

    # determine if school working day using Admin_Principal's calendar model if available
    is_working_day = True
    try:
        from Admin_Principal.models import SchoolCalender_model
        cal = SchoolCalender_model.objects.filter(CalenderDate=selected_date).first()
        is_working_day = cal.Working_day

    except Exception:
        # If calendar model not present or lookup failed, assume working day
        is_working_day = True

    students = Student_Model.objects.filter(Class_id=Selected_class.id).order_by('Roll_no')

    if request.method == 'POST':
        # process attendance save
        absent_ids = request.POST.getlist('absent')  # list of student ids marked absent
        absent_ids = set(int(x) for x in absent_ids) if absent_ids else set()

        for student in students:
            exists = Attendance_model.objects.filter(Student=student, AbsentDate=selected_date).first()
            if student.id in absent_ids:
                if not exists:
                    Attendance_model.objects.create(Student=student, AbsentDate=selected_date)
            else:
                if exists:
                    exists.delete()

        # redirect back to same page with selected date preserved
        return redirect('TeacherHome')
    # prepare attendance dict: student_id -> absent bool
    attendance = {}
    for student in students:
        exists = Attendance_model.objects.filter(Student=student, AbsentDate=selected_date).exists()
        attendance[student.id] = exists

    absent_ids = [sid for sid, val in attendance.items() if val]

    return render(request, 'Teacher_Attendance.html', {
        'Selected_Teacher': Selected_Teacher,
        'Selected_class': Selected_class,
        'students': students,
        'attendance': attendance,
        'absent_ids': absent_ids,
        'selected_date': selected_date,
        'is_working_day': is_working_day,
    })

def Teacher_Communication(request):
    """Manage parent-teacher communications for the teacher's class.
    - Show student selector (students in the class)
    - When a student selected, show prior communications
    - Allow replying only if Communicator is Parent and no reply exists yet
    - Allow sending message to an individual student or broadcast to all students
    """
    if not request.user.is_authenticated:
        return redirect('login')

    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()

    if not Selected_class:
        return render(request, 'Teacher_Communication.html',
                      {'error': 'No class assigned', 'Selected_Teacher': Selected_Teacher})

    students = Student_Model.objects.filter(Class_id=Selected_class.id).order_by('Roll_no')
    student_id = request.GET.get('student') or request.POST.get('student')
    selected_student = None
    communications = []

    if student_id:
        try:
            selected_student = Student_Model.objects.filter(id=student_id).first()
        except Exception:
            selected_student = None

    # Handle POST - new communication, reply, or broadcast
    if request.method == 'POST':
        action = request.POST.get('action')
        text = request.POST.get('matter', '').strip()

        # BROADCAST to all students in the class
        if action == 'broadcast' and text:
            for s in students:
                ParentTeacherCommunication_model.objects.create(
                    Date=timezone.localdate(),
                    Student=s,
                    Matter=text,
                    Communicator='Teacher'
                )
            redirect_url = reverse('Teacher_Communication')
            if selected_student:
                redirect_url += f'?student={selected_student.id}'
            return HttpResponseRedirect(redirect_url)

        # Individual Student Actions
        elif selected_student and text:
            if action == 'reply':
                response_to_id = request.POST.get('response_to')
                response_to = None
                if response_to_id:
                    # Check if the target communication is from Parent and has not been replied to yet
                    response_to = ParentTeacherCommunication_model.objects.filter(
                        id=response_to_id,
                        Student=selected_student,
                        Communicator='Parent'
                    ).first()

                    # Verify no reply already references this response_to
                    already_replied = ParentTeacherCommunication_model.objects.filter(ResponseTo=response_to).exists()

                    if response_to and not already_replied:
                        ParentTeacherCommunication_model.objects.create(
                            Date=timezone.localdate(),
                            Student=selected_student,
                            Matter=text,
                            ResponseTo=response_to,
                            Communicator='Teacher'
                        )
            else:
                # New individual communication
                ParentTeacherCommunication_model.objects.create(
                    Date=timezone.localdate(),
                    Student=selected_student,
                    Matter=text,
                    Communicator='Teacher'
                )
            return HttpResponseRedirect(reverse('Teacher_Communication') + f'?student={selected_student.id}')

    # Fetch communications & check reply statuses
    if selected_student:
        communications = ParentTeacherCommunication_model.objects.filter(Student=selected_student).order_by('-Date',
                                                                                                            '-id')

        # Get IDs of all messages that have already been replied to
        replied_ids = set(
            ParentTeacherCommunication_model.objects.filter(
                Student=selected_student,
                ResponseTo__isnull=False
            ).values_list('ResponseTo_id', flat=True)
        )

        for c in communications:
            # Can only reply if Communicator is 'Parent' and ID is not in replied_ids
            c.can_reply = (c.Communicator == 'Parent') and (c.id not in replied_ids)

    return render(request, 'Teacher_Communication.html', {
        'Selected_Teacher': Selected_Teacher,
        'Selected_class': Selected_class,
        'students': students,
        'selected_student': selected_student,
        'communications': communications,
    })


def teacher_late_arrival(request):
    """Manage late arrivals for the teacher's assigned class.
    GET: show date picker and late arrivals list (or Holiday message).
    POST: save late arrival records and time into LateComing_model for selected date.
    """
    if not request.user.is_authenticated:
        return redirect('login')

    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()

    if not Selected_class:
        return render(request, 'teacher_late_arrival.html',
                      {'error': 'No class assigned', 'Selected_Teacher': Selected_Teacher})

    # Date handling
    date_str = request.POST.get('late_arrival_date') if request.method == 'POST' else request.GET.get('date')
    if not date_str:
        selected_date = timezone.localdate()
    else:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            selected_date = timezone.localdate()

    # Determine if school working day
    is_working_day = True
    try:
        from Admin_Principal.models import SchoolCalender_model
        cal = SchoolCalender_model.objects.filter(CalenderDate=selected_date).first()
        if cal:
            is_working_day = cal.Working_day
    except Exception:
        is_working_day = True

    students = Student_Model.objects.filter(Class_id=Selected_class.id).order_by('Roll_no')

    if request.method == 'POST':
        late_arrival_ids = request.POST.getlist('late_arrival')  # Student IDs marked as late
        late_arrival_ids = set(int(x) for x in late_arrival_ids) if late_arrival_ids else set()

        for student in students:
            # Check if student checkbox was checked
            if student.id in late_arrival_ids:
                # Get specific time entered for this student
                time_val = request.POST.get(f'late_arrival_time_{student.id}')

                # Format or set default time if left empty
                arrival_time = datetime.strptime(time_val, '%H:%M').time() if time_val else None

                # Create or update LateComing record
                LateComing_model.objects.update_or_create(
                    Student=student,
                    Date=selected_date,
                    defaults={'Time': arrival_time}  # Replace 'Time' with your model's field name
                )
            else:
                # If checkbox is unchecked, remove existing late record for that date
                LateComing_model.objects.filter(Student=student, Date=selected_date).delete()

        return redirect('TeacherHome')

    # Fetch existing records for GET rendering
    late_records = LateComing_model.objects.filter(Student__in=students, Date=selected_date)
    late_arrival_ids = [rec.Student.id for rec in late_records]

    # Store existing arrival times by student ID
    late_arrival_times = {rec.Student.id: rec.Time for rec in late_records}

    return render(request, 'teacher_late_arrival.html', {
        'Selected_Teacher': Selected_Teacher,
        'Selected_class': Selected_class,
        'students': students,
        'late_arrival_ids': late_arrival_ids,
        'late_arrival_times': late_arrival_times,
        'selected_date': selected_date,
        'is_working_day': is_working_day,
    })

def Teacher_Acknowledgement(request):
    """Manage parent-teacher Acknowledgement for the teacher's class.
    - Show student selector (students in the class)
    - When a student selected, show prior communications (read-only)
    - Allow adding a new Acknowledgement
    """
    if not request.user.is_authenticated:
        return redirect('login')

    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()

    if not Selected_class:
        return render(request, 'Teacher_Acknowledgement.html', { 'error': 'No class assigned', 'Selected_Teacher': Selected_Teacher })

    students = Student_Model.objects.filter(Class_id=Selected_class.id).order_by('Roll_no')
    student_id = request.GET.get('student') or request.POST.get('student')
    selected_student = None
    Acknowledgements = []

    if student_id:
        try:
            selected_student = Student_Model.objects.filter(id=student_id).first()
        except Exception:
            selected_student = None

    # Handle POST - new Acknowledgement
    if request.method == 'POST' and selected_student:
        type =request.POST.get('Mode', '').strip()
        text = request.POST.get('Description', '').strip()
        point = request.POST.get('Credit', '').strip()

        if text:
                # new Acknowledgement
                Acknowledgement_model.objects.create(Date=timezone.localdate(),Mode=type, Student=selected_student, Description=text, Credit=point)
        # redirect to GET to avoid resubmission
        return HttpResponseRedirect(reverse('Teacher_Acknowledgement') + f'?student={selected_student.id}')

    if selected_student:
        Acknowledgements = Acknowledgement_model.objects.filter(Student=selected_student)

    return render(request, 'Teacher_Acknowledgement.html', {
        'Selected_Teacher': Selected_Teacher,
        'Selected_class': Selected_class,
        'students': students,
        'selected_student': selected_student,
        'Acknowledgements': Acknowledgements,
    })

def Teacher_Homeworks(request):
    """Manage homework entry and verification for the teacher's class."""
    if not request.user.is_authenticated:
        return redirect('login')

    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()

    today_date = timezone.localdate()

    subjects = Subject_model.objects.filter(Subject_teacher=Selected_Teacher)
    subject_id = request.GET.get('subject') or request.POST.get('subject')
    verify_hw_id = request.GET.get('verify_hw')

    selected_subject = None
    homeworks = []
    students = []
    selected_homework = None
    homework_done_map = {}

    if subject_id:
        try:
            selected_subject = Subject_model.objects.filter(id=subject_id).first()
        except Exception:
            selected_subject = None

    # Handle POST requests
    if request.method == 'POST' and selected_subject:
        action = request.POST.get('action')

        # 1. Update Homework Submissions
        if action == 'update_submissions':
            hw_id = request.POST.get('homework_id')
            homework_obj = Homework_model.objects.filter(id=hw_id).first()
            if homework_obj:
                # Fetch all students belonging to the class of this subject
                class_students = Student_Model.objects.filter(Class=selected_subject.Class)
                for student in class_students:
                    is_submitted = request.POST.get(f'submitted_{student.id}')
                    submitted_date = request.POST.get(f'submitted_date_{student.id}')

                    done_record = HomeworkDone_model.objects.filter(Homework=homework_obj, Student=student).first()

                    if is_submitted:
                        date_val = submitted_date if submitted_date else today_date
                        if done_record:
                            done_record.Submitted_date = date_val
                            done_record.save()
                        else:
                            HomeworkDone_model.objects.create(
                                Student=student,
                                Homework=homework_obj,
                                Submitted_date=date_val
                            )
                    else:
                        if done_record:
                            done_record.delete()

                # Redirect ONLY with subject parameter so selected_homework becomes None
                return HttpResponseRedirect(reverse('Teacher_Homeworks') + f'?subject={selected_subject.id}')
        # 2. Add New Homework
        elif action == 'add_homework':
            text = request.POST.get('Description', '').strip()
            s_date = request.POST.get('Submission_date', '').strip()
            if text:
                Homework_model.objects.create(
                    DateOfIssue=timezone.localdate(),
                    Subject=selected_subject,
                    Description=text,
                    Submission_date=s_date
                )
            return HttpResponseRedirect(reverse('Teacher_Homeworks') + f'?subject={selected_subject.id}')

    if selected_subject:
        homeworks = Homework_model.objects.filter(Subject=selected_subject)

        # Load students and existing submission records if a homework issue is selected to verify
        if verify_hw_id:
            selected_homework = Homework_model.objects.filter(id=verify_hw_id, Subject=selected_subject).first()
            if selected_homework:
                students = Student_Model.objects.filter(Class=selected_subject.Class).order_by('Roll_no')
                done_records = HomeworkDone_model.objects.filter(Homework=selected_homework)

                # Create a dictionary mapping student_id -> Submitted_date
                homework_done_map = {done.Student_id: done.Submitted_date for done in done_records}

                # Attach done_date directly to each student instance
                for student in students:
                    student.done_date = homework_done_map.get(student.id)
                    student.is_submitted = student.id in homework_done_map

    return render(request, 'Teacher_Homeworks.html', {
        'Selected_Teacher': Selected_Teacher,
        'subjects': subjects,
        'selected_subject': selected_subject,
        'homeworks': homeworks,
        'today_date': today_date,
        'selected_homework': selected_homework,
        'students': students,
        'homework_done_map': homework_done_map,
        'Selected_class': Selected_class
    })

def Teacher_Exam_Mark(request):
    """Manage entering and updating exam marks for subjects assigned to the logged-in teacher."""
    if not request.user.is_authenticated:
        return redirect('login')

    # Retrieve logged-in teacher
    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    if not Selected_Teacher:
        return render(request, 'Teacher_Exam_Mark.html', {'error': 'Teacher record not found.'})
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()

    # Fetch exams for subjects taught by this teacher
    Teacher_subject_exams = Exam_model.objects.filter(
        Subject__Subject_teacher=Selected_Teacher
    ).select_related('Subject', 'Subject__Class').order_by('Subject__Class__Class_no', 'Name')

    selected_exam = None
    student_marks = []

    exam_id = request.GET.get('exam_id') or request.POST.get('exam_id')

    if exam_id:
        selected_exam = Exam_model.objects.filter(
            id=exam_id,
            Subject__Subject_teacher=Selected_Teacher
        ).first()

    if selected_exam:
        # Fetch students belonging to the class of the selected exam's subject
        students = Student_Model.objects.filter(
            Class=selected_exam.Subject.Class
        ).order_by('Roll_no')

        if request.method == 'POST':
            today = timezone.localdate()
            for student in students:
                score_val = request.POST.get(f'mark_{student.id}', '0')
                try:
                    score = int(score_val)
                except ValueError:
                    score = 0

                # Create or update mark record for the student and exam
                Marks_model.objects.update_or_create(
                    Student=student,
                    Exam=selected_exam,
                    defaults={
                        'Score': score,
                        'Parent_verification_date': None,
                    }
                )

            return HttpResponseRedirect(reverse('Teacher_Exam_Mark') + f'?exam_id={selected_exam.id}')

        # Fetch existing marks map: student_id -> Score
        existing_marks = {
            m.Student_id: m.Score
            for m in Marks_model.objects.filter(Exam=selected_exam, Student__in=students)
        }

        # Build list of student data with current score (default to 0 if not entered)
        for student in students:
            score = existing_marks.get(student.id, 0)
            student_marks.append({
                'student': student,
                'score': score
            })

    return render(request, 'Teacher_Exam_Mark.html', {
        'Selected_Teacher': Selected_Teacher,
        'Teacher_subject_exams': Teacher_subject_exams,
        'selected_exam': selected_exam,
        'student_marks': student_marks,
        'Selected_class': Selected_class
    })

@login_required
def Teacher_Library_Books(request):
    # Fetch current logged-in teacher profile
    teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=teacher.id).first()

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- ACTION 1: ISSUE BOOK ---
        if action == 'issue':
            book_id = request.POST.get('book_id')
            student_id = request.POST.get('student_id')

            if not book_id or not student_id:
                messages.error(request, "Please select both a book and a student.")
                return redirect('Teacher_Library_Books')

            book = get_object_or_404(LibraryBook_model, id=book_id)
            student = get_object_or_404(Student_Model, id=student_id)

            # Ensure the book isn't already currently issued
            already_issued = Library_issue_model.objects.filter(
                Book=book,
                DateOfReturn__isnull=True
            ).exists()

            if already_issued:
                messages.error(request, f'The book "{book.BookName}" is currently already issued.')
            else:
                # Create the issue entry
                Library_issue_model.objects.create(
                    Book=book,
                    Student=student,
                    DateOfIssue=date.today(),
                    DateOfReturn=None,  # Null until returned
                    Teacher=teacher
                )
                messages.success(request, f'Book "{book.BookName}" issued successfully to {student.Name}.')

            return redirect('Teacher_Library_Books')

        # --- ACTION 2: RETURN BOOK ---
        elif action == 'return':
            issue_id = request.POST.get('issue_id')

            if issue_id:
                issue_record = get_object_or_404(Library_issue_model, id=issue_id)

                # Update return date to current date
                issue_record.DateOfReturn = date.today()
                issue_record.save()

                messages.success(request, f'Book "{issue_record.Book.BookName}" returned successfully!')
            else:
                messages.error(request, "Invalid book issue record selected for return.")

            return redirect('Teacher_Library_Books')

    # --- GET REQUEST DATA PREPARATION ---

    # Get IDs of books currently issued and NOT returned yet
    currently_issued_book_ids = Library_issue_model.objects.filter(
        DateOfReturn__isnull=True
    ).values_list('Book_id', flat=True)

    # Available books = All books excluding currently issued ones
    available_books = LibraryBook_model.objects.exclude(id__in=currently_issued_book_ids)

    # Currently active/issued books for the return list
    issued_books_list = Library_issue_model.objects.filter(
        DateOfReturn__isnull=True
    ).select_related('Book', 'Student', 'Teacher', 'Student__Class').order_by('-DateOfIssue')

    # Classes for dropdown filter
    classes = Class_model.objects.all()

    # Pass all students serialized for JS filtering by Class ID
    students = Student_Model.objects.all().select_related('Class')

    context = {
        'available_books': available_books,
        'issued_books_list': issued_books_list,
        'classes': classes,
        'students': students,
        'teacher': teacher,
        'today': date.today(),
        'Selected_class': Selected_class
    }

    return render(request, 'Teacher_Library_Books.html', context)


def teacher_student_info(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section')
    class_id = request.GET.get('class_id') or request.POST.get('class_id')
    student_id = request.GET.get('student_id') or request.POST.get('student_id')
    students = Student_Model.objects.none()
    student = None

    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()

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


    return render(request, 'Teacher_StudentInfo.html', {
        'classes': classes,
        'students': students,
        'student': student,
        'parent': parent,
        'siblings': siblings,
        'selected_id': class_id,
        'selected_student_id': student_id,
        'Selected_class': Selected_class
    })

@login_required
def Teacher_TimeTables(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section')
    class_id = request.GET.get('class_id')
    selected_class = Class_model.objects.none()
    periods=[]
    timetable_rows=[]

    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()

    if class_id:
        try:
            selected_class = Class_model.objects.filter(id=class_id).first()
        except Exception:
            selected_class = None


    if selected_class:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        periods = list(range(1, 9))

        # Fetch timetable entries for student's class
        timetable_entries = TimeTable_model.objects.filter(Class=selected_class).select_related('Subject')

        # Populate lookup mapping: (Day, Period) -> Subject
        saved_grid = {}
        for entry in timetable_entries:
            saved_grid[(entry.Day, int(entry.Period))] = entry.Subject

        # Build matrix structure for the template
        timetable_rows = []
        for day in days:
            slots = []
            for p in periods:
                subject = saved_grid.get((day, p), None)
                slots.append({
                    'period': p,
                    'subject': subject
                })
            timetable_rows.append({
                'day': day,
                'slots': slots
            })

    context = {
            'selected_class': selected_class,
            'periods': periods,
            'timetable_rows': timetable_rows,
            'classes': classes,
            'Selected_class': Selected_class
        }
    return render(request, 'Teacher_Timetables.html', context)


def teacher_academic_calendar(request):

    # Get selected year/month from GET parameters or default to current date
    selected_year = int(request.GET.get('year', datetime.now().year))
    selected_month = int(request.GET.get('month', datetime.now().month))
    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()

    # Fetch calendar entries for the selected month/year
    calendar_records = {
        c.CalenderDate: c
        for c in SchoolCalender_model.objects.filter(
            CalenderDate__year=selected_year,
            CalenderDate__month=selected_month
        )
    }

    # Fetch exams scheduled  during the selected month/year
    exams = Exam_model.objects.filter(
        Date__year=selected_year,
        Date__month=selected_month
    ).select_related('Subject')

    # Group exams by date
    exam_dict = {}
    for exam in exams:
        exam_dict.setdefault(exam.Date, []).append(exam)

    # Build the daily calendar list
    _, num_days = calendar.monthrange(selected_year, selected_month)
    calendar_days = []

    for day in range(1, num_days + 1):
        date_obj = datetime(selected_year, selected_month, day).date()
        is_weekend = date_obj.weekday() in (5, 6)  # 5: Saturday, 6: Sunday
        cal_record = calendar_records.get(date_obj)

        # A day is non-working if it's Saturday/Sunday or explicitly set in model
        is_working = not is_weekend
        if cal_record:
            is_working = cal_record.Working_day and not is_weekend

        calendar_days.append({
            'date': date_obj,
            'day_name': date_obj.strftime('%A'),
            'is_weekend': is_weekend,
            'is_working': is_working,
            'description': cal_record.Description if cal_record else '',
            'exams': exam_dict.get(date_obj, [])
        })

    context = {
        'selected_year': selected_year,
        'selected_month': selected_month,
        'month_name': calendar.month_name[selected_month],
        'months': range(1, 13),
        'years': range(datetime.now().year - 1, datetime.now().year + 3),
        'calendar_days': calendar_days,
        'Selected_class': Selected_class
    }
    return render(request, 'Teacher_AcademicCalendar.html', context)

def Teacher_Notice(request):
    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()
    # Retrieve all notices ordered by IssueDate descending (latest on top)
    notices = Notice_model.objects.all().order_by('-IssueDate', '-id')
    return render(request, 'Teacher_Notice.html', {'notices': notices,'Selected_class': Selected_class})

def Teacher_AttendanceReport(request):
    # Retrieve query parameters or default to current date values
    today = date.today()
    selected_class_id = request.GET.get('class_id')
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))
    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()

    classes = Class_model.objects.all().order_by('Class_no', 'Section', 'Division')

    # Generate list of years (e.g., past 3 years to next year)
    years = range(today.year - 2, today.year + 2)
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    report_data = []
    days_in_month = []
    selected_class = None

    if selected_class_id:
        try:
            selected_class = Class_model.objects.get(id=selected_class_id)
            # Fetch students ordered by roll number
            students = Student_Model.objects.filter(Class=selected_class).order_by('Roll_no')

            # Calculate total days in month
            num_days = calendar.monthrange(selected_year, selected_month)[1]
            month_dates = [date(selected_year, selected_month, day) for day in range(1, num_days + 1)]

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

            # Build data maps
            # key: (student_id, date)
            absent_map = {(att.Student_id, att.AbsentDate): att for att in attendance_qs}

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
        'selected_class': selected_class,
        'Selected_class': Selected_class
    }
    return render(request, 'Teacher_AttendanceReport.html', context)


def Teacher_MarkSheet(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section', 'Division')
    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()
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
        'Selected_class': Selected_class,
    }

    return render(request, 'Teacher_MarkSheet.html', context)

def Teacher_ExamScheduleReport(request):
    classes = Class_model.objects.all().order_by('Class_no', 'Section', 'Division')
    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    Selected_class = None
    if Selected_Teacher:
        Selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()
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
        'Selected_class': Selected_class
    }

    return render(request, 'Teacher_ExamScheduleReport.html', context)


def Teacher_LeaveApplication(request):
    if not request.user.is_authenticated:
        return redirect('login')

    Selected_Teacher = Teacher_Model.objects.filter(Login=request.user).first()
    selected_class = None
    if Selected_Teacher:
        selected_class = Class_model.objects.filter(Class_teacher_id=Selected_Teacher.id).first()

    if not selected_class:
        return render(request, 'Teacher_LeaveApplication.html',
                      {'error': 'No class assigned', 'Selected_Teacher': Selected_Teacher})

    # --- Handle POST requests for Approve / Reject actions ---
    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')  # Expected 'approve' or 'reject'
        remark = request.POST.get('remark', '').strip()

        if leave_id and action:
            leave_app = LeaveApplication_model.objects.filter(
                id=leave_id,
                Student__Class=selected_class
            ).first()

            if leave_app:
                if action == 'approve':
                    leave_app.Status = 'Approved'
                    messages.success(request, f"Leave application for {leave_app.Student.Name} approved successfully.")
                elif action == 'reject':
                    leave_app.Status = 'Rejected'
                    messages.warning(request, f"Leave application for {leave_app.Student.Name} rejected.")

                if remark:
                    leave_app.Remark = remark
                leave_app.save()

        # Preserve selected month & year parameters across redirect
        current_month = request.GET.get('month', '')
        current_year = request.GET.get('year', '')
        redirect_url = reverse('Teacher_LeaveApplication')
        if current_month or current_year:
            redirect_url += f"?month={current_month}&year={current_year}"
        return HttpResponseRedirect(redirect_url)

    # Retrieve query parameters or default to current date values
    today = date.today()
    selected_class_id = selected_class.id
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
    pending_leaves = []

    if selected_class_id:
        try:
            selected_class = Class_model.objects.get(id=selected_class_id)

            # Fetch pending leave applications for this class
            pending_leaves = LeaveApplication_model.objects.filter(
                Student__Class=selected_class,
                Status='Pending'
            ).select_related('Student').order_by('ApplicationDate', 'Student__Roll_no')

            # Fetch students ordered by roll number
            students = Student_Model.objects.filter(Class=selected_class).order_by('Roll_no')

            # Calculate total days in month
            num_days = calendar.monthrange(selected_year, selected_month)[1]
            month_dates = [date(selected_year, selected_month, day) for day in range(1, num_days + 1)]

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
        'pending_leaves': pending_leaves,
        'Selected_class': selected_class,

    }
    return render(request, 'Teacher_LeaveApplication.html', context)

@login_required
def change_password(request):
    """View to handle password changes for logged-in users."""

    # 1. Superuser / Staff check FIRST so admins don't get trapped by teacher/student roles
    if request.user.is_superuser or request.user.is_staff:
        base_template = 'AdminPrincipalFrame.html'
    else:
        # Determine base template based on user role
        role = Role_Model.objects.filter(Login=request.user).first()

        if role and role.user_type == 'Student':
            base_template = 'StudentFrame.html'
        elif role and role.user_type == 'Parent':
            base_template = 'ParentFrame.html'
        elif role and role.user_type == 'Teacher':
            base_template = 'TeacherFrame.html'
        else:
            # Fallback checks
            if hasattr(request.user, 'student_model'):
                base_template = 'StudentFrame.html'
            elif hasattr(request.user, 'parent_model'):
                base_template = 'ParentFrame.html'
            elif hasattr(request.user, 'teacher_model'):
                base_template = 'TeacherFrame.html'
            else:
                base_template = 'AdminPrincipalFrame.html'  # Default fallback

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')

            # 2. Redirect properly according to the base template type
            if base_template == 'StudentFrame.html':
                return redirect('StudentHome')
            elif base_template == 'ParentFrame.html':
                return redirect('ParentHome')
            elif base_template == 'TeacherFrame.html':
                return redirect('TeacherHome')
            else:
                # Redirect to your admin/principal home view URL name
                return redirect('AdminPrincipalFrame') # Or whatever your admin dashboard url name is
        else:
            messages.error(request, 'Please correct the error(s) below.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'change_password.html', {
        'form': form,
        'base_template': base_template
    })
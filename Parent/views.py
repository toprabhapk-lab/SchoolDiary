
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import  HttpResponseRedirect
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum
from datetime import date
import datetime
from calendar import month_name
from datetime import datetime
import calendar
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Admin_Principal.models import Notice_model, Student_Model, TimeTable_model, Sibling_model, Parent_Model, \
    Class_model, Exam_model, Subject_model, SchoolCalender_model, Role_Model
from Parent.models import LeaveApplication_model
from Teacher.models import Marks_model, HomeworkDone_model, Homework_model, LateComing_model, Attendance_model, \
    Acknowledgement_model, ParentTeacherCommunication_model
from django.shortcuts import render
from Admin_Principal.models import Student_Model

def ParentHome(request):
    parent = Parent_Model.objects.filter(Login=request.user).first()

    pending_ack_count = 0
    unverified_attendance_count = 0
    unreplied_communication_count = 0
    unverified_marks_count = 0

    if parent and parent.Student:
        student = parent.Student

        # 1. Acknowledgements unverified by parent
        pending_ack_count = Acknowledgement_model.objects.filter(
            Student=student,
            Principal_verification=True,
            Parent_verification=False
        ).count()

        # 2. Attendance leaves unverified by parent
        unverified_attendance_count = Attendance_model.objects.filter(
            Student=student,
            Parent_verification=False
        ).count()

        # 3. Marks verified by Principal but not yet verified by Parent
        unverified_marks_count = Marks_model.objects.filter(
            Student=student,
            Principal_verification=True,
            Parent_verification_date__isnull=True
        ).count()

        # 4. Teacher communications with no parent reply yet
        # Get IDs of all communications that have been replied to
        replied_comm_ids = ParentTeacherCommunication_model.objects.filter(
            Student=student,
            ResponseTo__isnull=False
        ).values_list('ResponseTo_id', flat=True)

        # Count messages from Teacher that are not referenced by any reply
        unreplied_communication_count = ParentTeacherCommunication_model.objects.filter(
            Student=student,
            Communicator='Teacher'
        ).exclude(id__in=replied_comm_ids).count()

    context = {
        'parent': parent,
        'pending_acknowledgements_count': pending_ack_count,
        'unverified_attendance_count': unverified_attendance_count,
        'unreplied_communication_count': unreplied_communication_count,
        'unverified_marks_count': unverified_marks_count,
    }
    return render(request, 'ParentHome.html', context)
def ParentFrame(request):
    return render(request, "ParentFrame.html")

@login_required
def Parent_TimeTable(request):
    try:
        # Fetch logged-in student profile
        parent = Parent_Model.objects.get(Login=request.user)
        student = Student_Model.objects.get(id=parent.Student.id)
        student_class = student.Class
    except (Parent_Model.DoesNotExist, Student_Model.DoesNotExist):
        messages.error(request, "Student profile not found.")
        return redirect('SchoolDiaryHeaderView')

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = list(range(1, 9))

    # Fetch timetable entries for student's class
    timetable_entries = TimeTable_model.objects.filter(Class=student_class).select_related('Subject')

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
        'parent': parent,
        'student': student,
        'student_class': student_class,
        'periods': periods,
        'timetable_rows': timetable_rows,
    }
    return render(request, 'Parent_TimeTable.html', context)

def Parent_Notice(request):
    parent = Parent_Model.objects.get(Login=request.user)
    student = Student_Model.objects.get(id=parent.Student.id)
    # Retrieve all notices ordered by IssueDate descending (latest on top)
    notices = Notice_model.objects.all().order_by('-IssueDate', '-id')
    return render(request, 'Parent_Notice.html', {'notices': notices, 'student': student})

def Parent_PersonalData(request):
    # Fetch the logged-in Parent's record and associated Student via the OneToOne relationship
    parent = get_object_or_404(Parent_Model, Login=request.user)
    student = get_object_or_404(Student_Model, id=parent.Student.id)

    # Retrieve sibling details
    sibling_relations = Sibling_model.objects.filter(Student=student).select_related('Sibling_student',
                                                                                     'Sibling_student__Class')
    siblings = [rel.Sibling_student for rel in sibling_relations]

    context = {
        'student': student,
        'parent': parent,
        'siblings': siblings,
    }
    return render(request, 'Parent_PersonalData.html', context)

@login_required
def Parent_Progress(request):
    # Retrieve the logged-in student's record
    parent = get_object_or_404(Parent_Model, Login=request.user)
    student = get_object_or_404(Student_Model, id=parent.Student.id)

    # Get all subjects for the student's class
    subjects = Subject_model.objects.filter(Class=student.Class)

    progress_data = []

    for subject in subjects:
        # Fetch exams for this subject ordered chronologically from left to right
        exams = Exam_model.objects.filter(Subject=subject).order_by('Date')

        exam_marks_list = []
        for exam in exams:
            # Get the mark for this student and exam if available
            mark_entry = Marks_model.objects.filter(Student=student, Exam=exam, Principal_verification=True).first()
            exam_marks_list.append({
                'mark_id': mark_entry.id if mark_entry else None,
                'exam_name': exam.Name,
                'exam_date': exam.Date,
                'max_mark': exam.Max_mark,
                'score': mark_entry.Score if mark_entry else '-',
                'verification_date': mark_entry.Parent_verification_date if mark_entry else None
            })

        progress_data.append({
            'subject': subject,
            'exam_marks': exam_marks_list
        })

    context = {
        'student': student,
        'progress_data': progress_data,
    }
    return render(request, 'Parent_Progress.html', context)


@login_required
def verify_mark(request):
    """View to record system current date into Parent_verification_date when clicked."""
    if request.method == 'POST':
        mark_id = request.POST.get('mark_id')
        if mark_id:
            mark = get_object_or_404(Marks_model, id=mark_id)
            mark.Parent_verification_date = date.today()
            mark.save()
    return redirect(request.META.get('HTTP_REFERER', 'Parent_Progress'))

def Parent_AcademicCalendar(request):
    parent = get_object_or_404(Parent_Model, Login=request.user)
    student = get_object_or_404(Student_Model, id=parent.Student.id)

    # Get selected year/month from GET parameters or default to current date
    selected_year = int(request.GET.get('year', datetime.now().year))
    selected_month = int(request.GET.get('month', datetime.now().month))

    # Fetch calendar entries for the selected month/year
    calendar_records = {
        c.CalenderDate: c
        for c in SchoolCalender_model.objects.filter(
            CalenderDate__year=selected_year,
            CalenderDate__month=selected_month
        )
    }

    # Fetch exams scheduled for this student's class during the selected month/year
    exams = Exam_model.objects.filter(
        Subject__Class=student.Class,
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
        'student': student,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'month_name': calendar.month_name[selected_month],
        'months': range(1, 13),
        'years': range(datetime.now().year - 1, datetime.now().year + 3),
        'calendar_days': calendar_days,
    }
    return render(request, 'Parent_AcademicCalendar.html', context)

@login_required
def Parent_Homework(request):
    # Retrieve the logged-in student's profile
    parent = get_object_or_404(Parent_Model, Login=request.user)
    student = get_object_or_404(Student_Model, id=parent.Student.id)

    # Get all subjects registered for the student's class
    subjects = Subject_model.objects.filter(Class=student.Class).order_by('Name')

    # Selected subject from GET parameter (optional)
    selected_subject_id = request.GET.get('subject')
    selected_subject = None

    # Fetch homeworks for the student's class
    homework_queryset = Homework_model.objects.filter(Subject__Class=student.Class)

    # Filter by subject if chosen
    if selected_subject_id:
        homework_queryset = homework_queryset.filter(Subject_id=selected_subject_id)
        selected_subject = subjects.filter(id=selected_subject_id).first()

    # Order homeworks by Issue Date descending (latest/newest first)
    homeworks_list = homework_queryset.order_by('-DateOfIssue')

    # Fetch submitted homework records for this student
    submitted_records = HomeworkDone_model.objects.filter(Student=student).select_related('Homework')

    # Map submitted homework ID to submission date for quick lookup
    submission_dict = {
        record.Homework_id: record.Submitted_date
        for record in submitted_records
    }

    # Attach submission status and submitted date to each homework object
    homework_data = []
    for hw in homeworks_list:
        is_submitted = hw.id in submission_dict
        homework_data.append({
            'homework': hw,
            'is_submitted': is_submitted,
            'submitted_date': submission_dict.get(hw.id) if is_submitted else None
        })

    context = {
        'student': student,
        'subjects': subjects,
        'selected_subject_id': selected_subject_id,
        'selected_subject': selected_subject,
        'homework_data': homework_data,
    }
    return render(request, 'Parent_Homework.html', context)


@login_required
def parent_attendance(request):
    parent = get_object_or_404(Parent_Model, Login=request.user)
    student = get_object_or_404(Student_Model, id=parent.Student.id)

    today = date.today()
    selected_year = int(request.GET.get('year', today.year))
    selected_month = int(request.GET.get('month', today.month))

    months_list = [(i, month_name[i]) for i in range(1, 13)]
    years_list = range(today.year - 3, today.year + 1)

    absences = Attendance_model.objects.filter(
        Student=student,
        AbsentDate__year=selected_year,
        AbsentDate__month=selected_month
    ).order_by('-AbsentDate')

    leave_applications = LeaveApplication_model.objects.filter(
        Student=student,
        AbsentDate__year=selected_year,
        AbsentDate__month=selected_month
    )

    leave_map = {leave.AbsentDate: leave for leave in leave_applications}

    attendance_report = []
    for abs_record in absences:
        leave_app = leave_map.get(abs_record.AbsentDate)
        attendance_report.append({
            'id': abs_record.id,
            'absent_date': abs_record.AbsentDate,
            'parent_verified': abs_record.Parent_verification,
            'has_leave_app': leave_app is not None,
            'leave_status': leave_app.Status if leave_app else None,
            'leave_reason': leave_app.Reason if leave_app else None,
            'leave_remark': leave_app.Remark if leave_app else None,
        })

    late_arrivals = LateComing_model.objects.filter(
        Student=student,
        Date__year=selected_year,
        Date__month=selected_month
    ).order_by('-Date', '-Time')

    context = {
        'student': student,
        'months_list': months_list,
        'years_list': years_list,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_month_name': month_name[selected_month],
        'attendance_report': attendance_report,
        'late_arrivals': late_arrivals,
        'total_absent_days': len(attendance_report),
        'total_late_arrivals': late_arrivals.count(),
    }

    return render(request, 'Parent_attendance.html', context)

@login_required
def verify_attendance(request, record_type, record_id):
    parent = get_object_or_404(Parent_Model, Login=request.user)
    student = parent.Student

    selected_year = request.GET.get('year', '')
    selected_month = request.GET.get('month', '')

    if record_type == 'absent':
        record = get_object_or_404(Attendance_model, id=record_id, Student=student)
        record.Parent_verification = True
        record.save()
    elif record_type == 'late':
        record = get_object_or_404(LateComing_model, id=record_id, Student=student)
        record.Parent_verification = True
        record.save()

    base_url = reverse('Parent_Attendance')  # Matches line 17 in your URLconf
    return redirect(f"{base_url}?year={selected_year}&month={selected_month}")



@login_required
def parent_acknowledgement(request):
    # Fetch the logged-in student's profile
    parent = get_object_or_404(Parent_Model, Login=request.user)
    student = get_object_or_404(Student_Model, id=parent.Student.id)

    # Optional mode filter (Gain / Lesson / All)
    selected_mode = request.GET.get('mode', '')

    # Fetch acknowledgements for the student
    acknowledgements_qs = Acknowledgement_model.objects.filter(Student=student, Principal_verification=True)

    if selected_mode in ['Gain', 'Lesson']:
        acknowledgements_qs = acknowledgements_qs.filter(Mode=selected_mode)

    # Order by Date descending (latest first)
    acknowledgements = acknowledgements_qs.order_by('-Date')

    # Total calculated credits (only counting non-null credits)
    total_credits = Acknowledgement_model.objects.filter(
        Student=student, Principal_verification=True
    ).aggregate(total=Sum('Credit'))['total'] or 0

    # Counts for summary statistics
    gain_count = Acknowledgement_model.objects.filter(Student=student, Mode='Gain', Principal_verification=True).count()
    lesson_count = Acknowledgement_model.objects.filter(Student=student, Mode='Lesson', Principal_verification=True).count()

    context = {
        'student': student,
        'acknowledgements': acknowledgements,
        'selected_mode': selected_mode,
        'total_credits': total_credits,
        'gain_count': gain_count,
        'lesson_count': lesson_count,
        'total_records': acknowledgements.count(),
    }

    return render(request, 'Parent_Acknowledgement.html', context)

@login_required
def verify_acknowledgement(request, ack_id):
    parent = get_object_or_404(Parent_Model, Login=request.user)
    student = parent.Student

    ack_record = get_object_or_404(Acknowledgement_model, id=ack_id, Student=student, Principal_verification=True)
    ack_record.Parent_verification = True
    ack_record.save()

    selected_mode = request.GET.get('mode', '')

    # Redirect using the URL pattern name 'parent_acknowledgement'
    base_url = reverse('parent_acknowledgement')
    if selected_mode:
        return redirect(f"{base_url}?mode={selected_mode}")
    return redirect(base_url)


@login_required
def Parent_LeaveApplication(request):
    # Retrieve the Parent object associated with the currently logged-in user
    try:
        parent = Parent_Model.objects.get(Login=request.user)
    except Parent_Model.DoesNotExist:
        messages.error(request, "Parent profile not found.")
        return redirect('login')

    student = parent.Student

    if request.method == 'POST':
        absent_date_str = request.POST.get('absent_date')
        reason = request.POST.get('reason')

        if not absent_date_str or not reason:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'Parent_LeaveApplication.html', {'student': student})

        absent_date = date.fromisoformat(absent_date_str)

        # 1. Check for Weekend (Saturday = 5, Sunday = 6 in Python's weekday())
        if absent_date.weekday() in [5, 6]:
            messages.error(request, "Leave applications cannot be submitted for Saturdays or Sundays.")
            return render(request, 'Parent_LeaveApplication.html', {'student': student, 'reason': reason, 'absent_date': absent_date_str})

        # 2. Check School Calendar for Non-Working Days
        calender_entry = SchoolCalender_model.objects.filter(CalenderDate=absent_date).first()
        if calender_entry and not calender_entry.Working_day:
            description = calender_entry.Description or "a non-working day"
            messages.error(request, f"Selected date ({absent_date}) is not a working day according to the school calendar ({description}).")
            return render(request, 'Parent_LeaveApplication.html', {'student': student, 'reason': reason, 'absent_date': absent_date_str})

        # Save Leave Application
        LeaveApplication_model.objects.create(
            Student=student,
            AbsentDate=absent_date,
            ApplicationDate=date.today(),
            Reason=reason,
            Status='Pending'
        )

        messages.success(request, "Leave application submitted successfully!")
        return redirect('Parent_LeaveApplication')

    return render(request, 'Parent_LeaveApplication.html', {'student': student})



def Parent_Communication(request):
    """Manage parent-teacher communications for the logged-in parent.
    - Fetch parent and associated student
    - Display communication history
    - Allow sending new communications to the Class Teacher
    - Allow replying ONLY if Communicator is 'Teacher' and not yet replied to
    """
    if not request.user.is_authenticated:
        return redirect('login')

    # Fetch logged-in parent
    parent = Parent_Model.objects.filter(Login=request.user).first()
    if not parent or not parent.Student:
        return render(request, 'Parent_Communication.html', {
            'error': 'No student details found for this parent user account.'
        })

    student = parent.Student

    # Handle POST - New Communication or Reply
    if request.method == 'POST':
        action = request.POST.get('action')
        text = request.POST.get('matter', '').strip()

        if text:
            if action == 'reply':
                response_to_id = request.POST.get('response_to')
                response_to = None
                if response_to_id:
                    # Check if target communication was sent by Teacher for this student
                    response_to = ParentTeacherCommunication_model.objects.filter(
                        id=response_to_id,
                        Student=student,
                        Communicator='Teacher'
                    ).first()

                    # Verify no reply already references this message
                    already_replied = ParentTeacherCommunication_model.objects.filter(
                        ResponseTo=response_to
                    ).exists()

                    if response_to and not already_replied:
                        ParentTeacherCommunication_model.objects.create(
                            Date=timezone.localdate(),
                            Student=student,
                            Matter=text,
                            ResponseTo=response_to,
                            Communicator='Parent'
                        )
            else:
                # New communication sent by Parent
                ParentTeacherCommunication_model.objects.create(
                    Date=timezone.localdate(),
                    Student=student,
                    Matter=text,
                    Communicator='Parent'
                )

        return HttpResponseRedirect(reverse('Parent_Communication'))

    # Fetch all communications for the student
    communications = ParentTeacherCommunication_model.objects.filter(Student=student).order_by('-Date', '-id')

    # Identify message IDs that have already been replied to
    replied_ids = set(
        ParentTeacherCommunication_model.objects.filter(
            Student=student,
            ResponseTo__isnull=False
        ).values_list('ResponseTo_id', flat=True)
    )

    for c in communications:
        # Parent can reply ONLY if the message was sent by 'Teacher' and hasn't been replied to yet
        c.can_reply = (c.Communicator == 'Teacher') and (c.id not in replied_ids)

    return render(request, 'Parent_Communication.html', {
        'parent': parent,
        'student': student,
        'communications': communications,
    })




@login_required
def change_password(request):
    """View to handle password changes for logged-in users."""

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
        else:
            base_template = 'TeacherFrame.html'

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')

            if base_template == 'StudentFrame.html':
                return redirect('StudentHome')
            elif base_template == 'ParentFrame.html':
                return redirect('ParentHome')
            else:
                return redirect('TeacherHome')
        else:
            messages.error(request, 'Please correct the error(s) below.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'change_password.html', {
        'form': form,
        'base_template': base_template
    })
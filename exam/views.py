from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.contrib import messages
from .models import Student, Subject, Question, Result
import random
import time
from django.core.files.storage import FileSystemStorage


# =========================
# HOME & DASHBOARD
# =========================

def home(request):
    return render(request, 'home.html')


@login_required(login_url='login')
def index(request):
    return render(request, 'index.html')


# =========================
# REGISTER WITH OTP
# =========================

import base64
import random
import time
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.core.mail import send_mail


def student_register(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        roll_no = request.POST['roll_no']
        mobile = request.POST['mobile']
        email = request.POST['email']
        image = request.FILES.get('profile_image')

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'error': 'Username already exists!'
            })

        if password != confirm_password:
            return render(request, 'register.html', {
                'error': 'Passwords do not match!'
            })

        # Save image temporarily in MEDIA folder
        if image:
            fs = FileSystemStorage()
            filename = fs.save(image.name, image)
            request.session['temp_image_name'] = filename
        else:
            request.session['temp_image_name'] = None

        otp = random.randint(100000, 999999)

        request.session['otp'] = otp
        request.session['otp_time'] = time.time()
        request.session['otp_attempts'] = 0
        request.session['temp_user'] = {
            'username': username,
            'password': password,
            'roll_no': roll_no,
            'mobile': mobile,
            'email': email
        }

        send_mail(
            'Your OTP Code',
            f'Your OTP is {otp}',
            'your_email@gmail.com',
            [email],
            fail_silently=False,
        )

        return redirect('verify_otp')

    return render(request, 'register.html')

def verify_otp(request):

    if request.session.get('otp_attempts', 0) >= 3:
        return render(request, 'otp.html', {
            'error': 'Too many wrong attempts! Please resend OTP.'
        })

    if request.method == "POST":
        user_otp = request.POST.get('otp')
        session_otp = str(request.session.get('otp'))
        otp_time = request.session.get('otp_time')

        if otp_time and time.time() - otp_time > 60:
            return render(request, 'otp.html', {
                'error': 'OTP Expired! Please resend OTP.'
            })

        if user_otp == session_otp:

            data = request.session.get('temp_user')
            image_name = request.session.get('temp_image_name')

            user = User.objects.create_user(
                username=data['username'],
                password=data['password'],
                email=data['email']
            )

            Student.objects.create(
                user=user,
                roll_no=data['roll_no'],
                mobile=data['mobile'],
                profile_image=image_name
            )

            request.session.flush()
            return redirect('login')

        else:
            request.session['otp_attempts'] += 1
            remaining = 3 - request.session['otp_attempts']

            return render(request, 'otp.html', {
                'error': f'Invalid OTP! Attempts left: {remaining}'
            })

    return render(request, 'otp.html')


def resend_otp(request):

    data = request.session.get('temp_user')
    if not data:
        return redirect('register')

    otp = random.randint(100000, 999999)

    request.session['otp'] = otp
    request.session['otp_time'] = time.time()
    request.session['otp_attempts'] = 0

    send_mail(
        'Your New OTP Code',
        f'Your new OTP is {otp}',
        'your_email@gmail.com',
        [data['email']],
        fail_silently=False,
    )

    return render(request, 'otp.html', {
        'success': 'New OTP sent to your email!'
    })


# =========================
# LOGIN / LOGOUT
# =========================

def student_login(request):

    if 'attempts' not in request.session:
        request.session['attempts'] = 0

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            request.session['attempts'] = 0
            login(request, user)
            return redirect('index')
        else:
            request.session['attempts'] += 1

            if request.session['attempts'] >= 3:
                return render(request, 'login.html', {
                    'error': 'Too many failed attempts! Try later.'
                })

            return render(request, 'login.html', {
                'error': f'Invalid credentials! Attempts left: {3 - request.session["attempts"]}'
            })

    return render(request, 'login.html')


def student_logout(request):
    logout(request)
    return redirect('login')


# =========================
# SUBJECTS & EXAM
# =========================

@login_required(login_url='login')
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'subjects.html', {'subjects': subjects})


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subject, Question, Result


@login_required(login_url='login')
def start_exam(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    questions = Question.objects.filter(subject=subject)

    if request.method == "POST":

        score = 0
        result_data = []

        for q in questions:
            selected = request.POST.get(str(q.id))
            correct = q.correct_answer.strip().lower()

            if selected:
                selected_clean = selected.strip().lower()
            else:
                selected_clean = ""

            is_correct = selected_clean == correct

            if is_correct:
                score += 1

            result_data.append({
                "question": q.question,
                "selected": selected,
                "correct": q.correct_answer,
                "is_correct": is_correct
            })

        total = questions.count()
        percentage = (score / total) * 100 if total > 0 else 0

        # Save result in database
        Result.objects.create(
            student=request.user,
            subject=subject,
            score=score,
            total=total,
            percentage=percentage
        )

        return render(request, 'result.html', {
            'score': score,
            'total': total,
            'percentage': percentage,
            'result_data': result_data
        })

    return render(request, 'exam.html', {
        'subject': subject,
        'questions': questions
    })


# =========================
# RANKING
# =========================

@login_required(login_url='login')
def ranking(request):
    results = Result.objects.order_by('-percentage')
    return render(request, 'ranking.html', {'results': results})


# =========================
# PROFILE
# =========================

@login_required(login_url='login')
def profile(request):
    student = Student.objects.filter(user=request.user).first()
    results = Result.objects.filter(student=request.user).order_by('-date')

    return render(request, 'profile.html', {
        'student': student,
        'results': results
    })


# =========================
# FORGOT PASSWORD
# =========================

def forgot_password(request):

    if request.method == "POST":
        email = request.POST['email']
        user = User.objects.filter(email=email).first()

        if not user:
            return render(request, 'forgot.html', {
                'error': 'Email not found'
            })

        otp = random.randint(100000, 999999)

        request.session['reset_otp'] = otp
        request.session['reset_user'] = user.id

        send_mail(
            'Password Reset OTP',
            f'Your OTP is {otp}',
            'your_email@gmail.com',
            [email],
            fail_silently=False,
        )

        return redirect('reset_password')

    return render(request, 'forgot.html')


def reset_password(request):

    if request.method == "POST":
        otp = request.POST['otp']
        new_password = request.POST['password']

        if str(otp) == str(request.session.get('reset_otp')):
            user_id = request.session.get('reset_user')
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()

            request.session.flush()
            return redirect('login')

        return render(request, 'reset.html', {'error': 'Invalid OTP'})

    return render(request, 'reset.html')
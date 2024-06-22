from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import IntegrityError
from django.contrib import messages
from management.models import Student
import re
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login


# Create your views here.


def home(request):
    return render(request, 'mainpage/home.html')


def login_view(request):
    if request.user.is_authenticated:  # 避免重复登录
        return redirect('dashboard')
    else:
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, '账号或密码错误')
                return render(request, 'mainpage/login.html')
        else:
            return render(request, 'mainpage/login.html')


def register_view(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        name = request.POST.get('name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        print(student_id, name, age, gender, phone, password)

        if not re.match(r'PB\d{8}', student_id):
            messages.error(request, '学号格式不正确，必须以PB开头，后跟8位数字。')
            return render(request, 'mainpage/register.html')

        if Student.objects.filter(student_id=student_id).exists():
            messages.error(request, '该学号已经注册，请尝试登录或使用其他学号。')
            return render(request, 'mainpage/register.html')

        # 创建学生实例，添加到数据库，保存学生ID和密码到Django内置用户模型中，设置组别
        student = Student(student_id=student_id, name=name, age=age, gender=gender, phone=phone)
        user = User.objects.create_user(username=student_id, password=password)
        user.groups.add(Group.objects.get(name='Student'))
        user.save()
        student.save()
        messages.success(request, '注册成功，请登录！')
        return redirect('login')
    else:
        return render(request, 'mainpage/register.html')



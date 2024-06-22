from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Repair, DormBuilding, ImgUpload, Visitor, DormApply, Dorm, DormManager
from datetime import datetime
from .forms import ImageForm
from datetime import date
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
import json
import re
from django.contrib.auth.models import User, Group
from django.db import transaction


# 针对三个不同组别的用户对应不同的渲染结果
def dashboard(request):
    if request.user.is_authenticated:
        print(request.user)
        if request.user.groups.filter(name='Student').exists():  # 学生登录
            stu = Student.objects.get(pk=request.user.username)
            icon = stu.icon
            context = {'student': stu, 'icon': icon}
            return render(request, 'management/dashboard_stu.html', context)
        elif request.user.groups.filter(name='DormManager').exists():
            dm_id = request.user.username
            dm = DormManager.objects.get(pk=dm_id)
            try:
                build = dm.building
                dorm_count = Dorm.objects.filter(building=build.pk).count()
            except DormBuilding.DoesNotExist:
                dorm_count = 0

            try:
                build = dm.building
                stu_count = Student.objects.filter(dorm__building=build.pk).count()
            except DormBuilding.DoesNotExist:
                stu_count = 0
            except Dorm.DoesNotExist:
                stu_count = 0
            context = {'dorm_count': dorm_count, 'dm': dm, 'stu_count': stu_count}
            return render(request, 'management/dashboard_dm.html', context)
        elif request.user.groups.filter(name='SuperUser').exists():
            building_count = DormBuilding.objects.all().count()
            dorm_count = Dorm.objects.all().count()
            student_count = Student.objects.all().count()
            dormmanager_count = DormManager.objects.all().count()
            context = {'building_count': building_count, 'dorm_count': dorm_count, 'student_count': student_count,
                       'dormmanager_count': dormmanager_count}
            return render(request, 'management/dashboard_su.html', context)
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def editprofile(request):
    return 0


def repair(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Student').exists():
            if request.method == 'POST':
                repair_date = datetime.today().date()
                building = DormBuilding.objects.get(name=request.POST.get('building'))
                description = request.POST.get('description')
                reporter = Student.objects.get(pk=request.user.username)
                repair_report = Repair(repair_date=repair_date, building=building, description=description,
                                       reporter=reporter)
                repair_report.save()
                return redirect('repair')
            else:
                building = DormBuilding.objects.all().values('name')
                repairs = Repair.objects.filter(reporter=request.user.username)
                repairs_data = []
                for repair in repairs:
                    repairs_data.append({
                        'repair_id': repair.pk,
                        'repair_date': str(repair.repair_date),
                        'building': repair.building.name,
                        'description': repair.description,
                        'reporter': repair.reporter,
                        'completed': repair.completed,
                    })
                context = {'building': building, 'repair': repairs_data}

                print(context)
                return render(request, 'management/repair_stu.html', context)
        if request.user.groups.filter(name='DormManager').exists():
            dm = DormManager.objects.get(pk=request.user.username)
            sort_by = request.GET.get('sort', 'repair_date')
            reverse = '-' if 'reverse' in request.GET else ''
            if dm.building:
                repairs = Repair.objects.filter(building=dm.building).order_by(reverse + sort_by)
            else:
                repairs = Repair.objects.none()
            context = {'repairs': repairs, 'current_sort': reverse + sort_by}
            return render(request, 'management/repair_dm.html', context)

    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def repair_complete(request, repair_id):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='DormManager').exists():
            repair = Repair.objects.get(pk=repair_id)
            if repair:
                if repair.completed == 0:
                    repair.completed = 1
                else:
                    messages.error(request, "此报修已解决，请勿重复处理")
                    return redirect('repair')
                repair.save()
                return redirect('repair')
            else:
                messages.error(request, "不存在此报修")
                return redirect('repair')
        else:
            messages.error(request, "用户身份错误")
            return redirect('dashboard')
    else:
        messages.error(request, "用户未登录")
        return redirect('login')


def visit(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Student').exists():
            if request.method == 'POST':
                phone = request.POST.get('phone')
                reason = request.POST.get('reason')
                applicant = Student.objects.get(pk=request.user.username)
                visit_date = datetime.strptime(request.POST.get('visit_date'), '%Y-%m-%d').date()
                applicant_date = datetime.today().date()
                print(request.user.username, applicant_date)
                application_count = Visitor.objects.filter(applicant=request.user.username,
                                                           applicant_date=applicant_date).count()
                visitors = Visitor(applicant=applicant, visit_date=visit_date, phone=phone, reason=reason,
                                   applicant_date=applicant_date)

                print(application_count)
                if application_count >= 3:
                    messages.error(request, '今日已申请三次访问')
                    return redirect('visit')
                elif applicant_date > visit_date:
                    messages.error(request, '不可申请今天之前的访问')
                    return redirect('visit')
                else:
                    visitors.save()
                    return redirect('visit')
            else:
                visitors = Visitor.objects.filter(applicant=request.user.username).order_by('applicant_date')
                visitors_data = []
                for visitor in visitors:
                    visitors_data.append({
                        'visitor_id': visitor.pk,
                        'visit_date': str(visitor.visit_date),
                        'visitor_phone': visitor.phone,
                        'visitor_reason': visitor.reason,
                        'visitor_applicant': visitor.applicant,
                        'applicant_date': str(visitor.applicant_date),
                        'state': visitor.state,
                        'reason': visitor.reason,
                    })
                context = {'visitors': visitors_data}

                return render(request, 'management/visitor_stu.html', context)
        if request.user.groups.filter(name='DormManager').exists():
            sort_by = request.GET.get('sort', 'applicant_date')
            reverse = '-' if 'reverse' in request.GET else ''
            visitors = Visitor.objects.all().order_by(reverse + sort_by)
            context = {'visitors': visitors, 'current_sort': reverse + sort_by}
            return render(request, 'management/visitor_dm.html', context)
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def visit_ac(request, id):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='DormManager').exists():
            if request.method == 'POST':
                vs = Visitor.objects.get(pk=id)
                if vs:
                    if vs.state == 0:
                        vs.state = 1
                        vs.save()
                        return redirect('visit')
                    else:
                        messages.error(request, "不可更改已处理后的申请")
                        return redirect('visit')
                else:
                    messages.error(request, "不存在该申请")
                    return redirect('visit')
        else:
            messages.error(request, "用户身份错误")
            return redirect('dashboard')
    else:
        messages.error(request, "用户未登录")
        return redirect('login')


def visit_dn(request, id):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='DormManager').exists():
            if request.method == 'POST':
                vs = Visitor.objects.get(pk=id)
                if vs:
                    if vs.state == 0:
                        vs.state = 2
                        vs.save()
                        return redirect('visit')
                    else:
                        messages.error(request, "不可更改已处理后的申请")
                        return redirect('visit')
                else:
                    messages.error(request, "不存在该申请")
                    return redirect('visit')
        else:
            messages.error(request, "用户身份错误")
            return redirect('dashboard')
    else:
        messages.error(request, "用户未登录")
        return redirect('login')


def inoutdorm(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Student').exists():
            if request.method == 'POST':
                applicant = Student.objects.get(pk=request.user.username)
                status = Student.objects.get(pk=request.user.username).status
                apply_type = 0
                if status == 1 or status == 3:
                    messages.error(request, '您有未处理的申请，不能再申请')
                    return redirect('inoutdorm')
                elif status == 0:
                    apply_type = 0
                elif status == 2:
                    apply_type = 1

                apply = DormApply(applicant=applicant, apply_type=apply_type)
                apply.save()
                return redirect('inoutdorm')
            else:
                applications = DormApply.objects.filter(applicant=request.user.username).order_by('applicant_date')
                applications_data = []
                for apply in applications:
                    applications_data.append({
                        'applicant': apply.applicant,
                        'applicant_date': str(apply.applicant_date),
                        'apply_type': apply.apply_type,
                        'status': apply.status,
                    })
                student_id = request.user.username
                student = Student.objects.get(pk=student_id)
                context = {'applications': applications_data, 'student': student}

                return render(request, 'management/inoutdorm_stu.html', context)
        if request.user.groups.filter(name='DormManager').exists():
            apply_in = DormApply.objects.filter(apply_type=0, status=0)
            dm = DormManager.objects.get(pk=request.user.username)

            if dm.building:
                dorm = Dorm.objects.filter(building=dm.building.id)
                apply_out = DormApply.objects.filter(applicant__dorm__building=dm.building.id, status=0)
                print(dm.building.id)
                print(dorm)
            else:
                apply_out = DormApply.objects.none()
                dorm = Dorm.objects.none()

            sort_by = request.GET.get('sort', 'applicant_date')
            reverse = '-' if 'reverse' in request.GET else ''
            apply = (apply_in | apply_out).distinct().order_by(reverse + sort_by)
            context = {'apply': apply, 'current_sort': reverse + sort_by, 'dorm': dorm}

            return render(request, 'management/inoutdorm_dm.html', context)

    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def image_upload(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Student').exists():
            if request.method == 'POST':
                form = ImageForm(request.POST, request.FILES)
                if form.is_valid():
                    new_img = form.save(commit=False)
                    new_img.uploader = Student.objects.get(pk=request.user.username)
                    new_img.save()
                    messages.success(request, "上传图片成功")
                    return redirect('editprofile')
            else:
                form = ImageForm()
            return render(request, "management/image_upload.html", {'form': form})
        else:
            messages.error(request, "用户身份错误")
            return redirect('dashboard')
    else:
        messages.error(request, "用户未登录")
        return redirect('login')


@login_required
def delete_repair(request, repair_id):
    if request.method == "POST":
        try:
            repair = Repair.objects.get(pk=repair_id)
            repair.delete()
        except Repair.DoesNotExist:
            pass
        return redirect('repair')


def dormbuilding(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='SuperUser').exists():
            if request.method == 'POST':
                bd_name = request.POST.get('bd_name')

                if DormBuilding.objects.filter(name=bd_name).exists():
                    messages.error(request, '该楼宇已经存在，请不要重复添加')
                    return redirect('dormbuilding')

                with transaction.atomic():
                    try:
                        bd = DormBuilding(name=bd_name)
                        bd.save()
                        messages.success(request, "添加楼宇成功！")
                    except Exception as e:
                        messages.error(request, e)
                        print(e)
                return redirect('dormbuilding')
            else:
                bds = DormBuilding.objects.all()
                if bds.exists():
                    default_filter = bds.first().id
                else:
                    default_filter = None
                bds_data = []
                filter_by = request.GET.get('filter', default_filter)
                dorms = Dorm.objects.filter(building=filter_by)
                print(filter_by)
                dorms_data = []
                for dorm in dorms:
                    dorms_data.append({
                        'dorm_id': dorm.pk,
                        'dorm_bd': DormBuilding.objects.get(pk=filter_by).name,
                        'count': Student.objects.filter(dorm=dorm.Dorm_id).count(),
                    })
                for bd in bds:
                    bds_data.append({
                        'bd_id': bd.pk,
                        'bd_name': bd.name,
                        'dm_count': Dorm.objects.filter(building=bd.id).count(),
                        # 'stu_count':Student.objects.filter(dorm = ).count(),
                    })
                context = {'bds_data': bds_data, 'dorms_data': dorms_data}
                return render(request, 'management/dormbuilding_su.html', context)
        elif request.user.groups.filter(name='DormManager').exists():
            if request.method != 'Post':
                dormmanager = DormManager.objects.get(pk=request.user.username)
                bd = DormBuilding.objects.get(Dorm_id=dormmanager.building)
            else:
                messages.error(request, '您不是管理用户，禁止访问')
                return redirect('dashboard')
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def apply_denied(request, apply_id):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='DormManager').exists():
            apply = DormApply.objects.get(pk=apply_id)
            apply.status = 2
            apply.save()
            return redirect('inoutdorm')
        else:
            messages.error(request, "用户身份错误")
            return redirect('dashboard')
    else:
        messages.error(request, "用户未登录")
        return redirect('login')


def apply_in(request, applicant_id):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='DormManager').exists():
            stu = Student.objects.get(pk=applicant_id)
            dorm = Dorm.objects.get(pk=request.POST.get('dorm'))
            stu.dorm = dorm
            apply = DormApply.objects.get(applicant=applicant_id, status=0)
            if apply:
                apply.status = 1
            else:
                messages.error(request, "不存在此类申请，请重试")
                return redirect('inoutdorm')
            apply.status = 1
            stu_dorm_count = Student.objects.filter(dorm=dorm).count()
            if stu_dorm_count >= 4:
                messages.error(request, "目标宿舍已经有4名学生，不能继续添加")
                return redirect('inoutdorm')

            stu.save()
            apply.save()
            messages.success(request, "入宿成功")
            return redirect('inoutdorm')
        else:
            messages.error(request, "用户身份错误")
            return redirect('dashboard')
    else:
        messages.error(request, "用户未登录")
        return redirect('login')


def apply_out(request, applicant_id_out):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='DormManager').exists():
            stu = Student.objects.get(pk=applicant_id_out)
            apply = DormApply.objects.get(applicant=applicant_id_out, status=0)
            if apply:
                apply.status = 1
            else:
                messages.error(request, "不存在此类申请，请重试")
                return redirect('inoutdorm')
            apply.save()
            messages.success(request, "退宿成功")
            return redirect('inoutdorm')
        else:
            messages.error(request, "用户身份错误")
            return redirect('dashboard')
    else:
        messages.error(request, "用户未登录")
        return redirect('login')


def student(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='SuperUser').exists():
            if request.method == 'POST':
                return redirect('student')
            else:
                sort_by = request.GET.get('sort', 'student_id')
                reverse = '-' if 'reverse' in request.GET else ''

                student_all = Student.objects.all().order_by(reverse + sort_by)
                student_all_data = []
                print(sort_by)
                for stu in student_all:
                    student_all_data.append({
                        'stu_id': stu.student_id,
                        'stu_name': stu.name,
                        'stu_age': stu.age,
                        'stu_gender': stu.gender,
                        'stu_phone': stu.phone,
                        'stu_dorm': stu.dorm,
                        'stu_status': stu.status,
                    })

                building = DormBuilding.objects.all()
                context = {'student_all_data': student_all_data,
                           'building': building,
                           'current_sort': reverse + sort_by}
                return render(request, 'management/student_su.html', context)
        elif request.user.groups.filter(name='DormManager').exists():
            if request.method == 'POST':
                return redirect('student')
            else:
                sort_by = request.GET.get('sort', 'student_id')
                reverse = '-' if 'reverse' in request.GET else ''

                dm = DormManager.objects.get(pk=request.user.username)
                student_all_data = []

                if dm.building:
                    building = DormBuilding.objects.get(pk=dm.building.id)
                    dorm = Dorm.objects.filter(building=dm.building.id)
                    if (dorm.count() == 0):
                        stu_all = Student.objects.none()
                    else:
                        stu_all = Student.objects.filter(dorm__building=building).order_by(reverse + sort_by)
                else:
                    stu_all = Student.objects.none()
                    dorm = Dorm.objects.none()

                for stu in stu_all:
                    student_all_data.append({
                        'stu_id': stu.student_id,
                        'stu_name': stu.name,
                        'stu_age': stu.age,
                        'stu_gender': stu.gender,
                        'stu_phone': stu.phone,
                        'stu_dorm': stu.dorm.Dorm_id,
                        'stu_status': stu.status,
                    })

                building = DormBuilding.objects.all()
                context = {'student_all_data': student_all_data,
                           'building': building,
                           'current_sort': reverse + sort_by,
                           'dorm': dorm}
                return render(request, 'management/student_dm.html', context)
        else:
            messages.error(request, '您不是管理员用户，禁止访问')
            return redirect('dashboard')
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def edit_student(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Student').exists():
            if request.method == 'POST':
                stu = Student.objects.get(pk=request.user.username)
                name = request.POST.get('name')
                age = request.POST.get('age')
                gender = request.POST.get('gender')
                phone = request.POST.get('phone')
                password = request.POST.get('password')
                icon = request.POST.get('icon')
                stu.icon = ImgUpload.objects.get(pk=icon)
                stu.name = name
                stu.age = age
                stu.gender = gender
                stu.phone = phone
                user = request.user
                user.set_password(password)
                user.save()
                stu.save()
                messages.success(request, "更改信息成功")
                return redirect('dashboard')
            else:
                img = ImgUpload.objects.filter(uploader=request.user.username)
                context = {'img': img}
                return render(request, 'management/edit_student_stu.html', context)
        else:
            messages.error(request, "用户身份错误")
            return redirect('dashboard')
    else:
        messages.error(request, "用户未登录")
        return redirect('login')


def delete_student(request, stu_id):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='SuperUser').exists():
            if request.method == 'POST':
                stu = Student.objects.get(pk=stu_id)
                user = User.objects.get(username=stu_id)
                with transaction.atomic():
                    try:
                        user.delete()
                        stu.delete()
                        messages.success(request, "删除学生成功")
                    except Exception as e:
                        messages.error(request, e)
                        print(e)
                return redirect('student')

        else:
            messages.error(request, '您不是管理员用户，禁止访问')
            return redirect('dashboard')
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def deletebuilding(request, id):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='SuperUser').exists():
            if request.method == 'POST':
                dm = DormBuilding.objects.get(pk=id)
                with transaction.atomic():
                    try:
                        dm.delete()
                        messages.success(request, "删除楼宇成功")
                    except Exception as e:
                        messages.error(request, e)
                        print(e)
                return redirect('dormbuilding')
        else:
            messages.error(request, '您不是管理员用户，禁止访问')
            return redirect('dashboard')
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def deletedorm(request, id):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='SuperUser').exists():
            if request.method == 'POST':
                dm = Dorm.objects.get(pk=id)
                with transaction.atomic():
                    try:
                        dm.delete()
                        messages.success(request, "删除宿舍成功")
                    except Exception as e:
                        messages.error(request, e)
                        print(e)
                return redirect('dormbuilding')
        else:
            messages.error(request, '您不是管理员用户，禁止访问')
            return redirect('dashboard')
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def dorm(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='SuperUser').exists():
            if request.method == 'POST':
                dorm_id = request.POST.get('dorm_id')
                building = DormBuilding.objects.get(name=request.POST.get('building'))
                dorm = Dorm(building=building, Dorm_id=dorm_id)

                if Dorm.objects.filter(Dorm_id=dorm_id).exists():
                    messages.error(request, '该宿舍已经存在，请不要重复添加')
                    return redirect('dormbuilding')
                with transaction.atomic():
                    try:
                        dorm.save()
                        messages.success(request, "添加宿舍成功！")
                    except Exception as e:
                        messages.error(request, e)
                        print(e)
                return redirect('dormbuilding')
            else:
                bds = DormBuilding.objects.all()
                if bds.exists():
                    default_filter = bds.first().id
                else:
                    default_filter = None
                bds_data = []
                filter_by = request.GET.get('filter', default_filter)
                dorms = Dorm.objects.filter(building=filter_by)
                dorms_data = []
                for dorm in dorms:
                    dorms_data.append({
                        'dorm_id': dorm.pk,
                        'dorm_bd': DormBuilding.objects.get(pk=filter_by).name,
                        'count': Student.objects.filter(dorm=dorm.Dorm_id).count(),
                    })
                for bd in bds:
                    bds_data.append({
                        'bd_id': bd.pk,
                        'bd_name': bd.name,
                        'dm_count': Dorm.objects.filter(building=bd.id).count(),
                        # 'stu_count':Student.objects.filter(dorm = ).count(),
                    })
                context = {'bds_data': bds_data, 'dorms_data': dorms_data}
                return render(request, 'management/dormbuilding_su.html', context)
        elif request.user.groups.filter(name='DormManager').exists():
            if request.method != 'Post':
                dormmanager = DormManager.objects.get(pk=request.user.username)
                bd = DormBuilding.objects.get(Dorm_id=dormmanager.building)
        else:
            messages.error(request, '您不是管理用户，禁止访问')
            return redirect('dashboard')
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def dorm_change(request, id):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='DormManager').exists():
            if request.method == 'POST':
                stu = Student.objects.get(pk=id)
                dorm_id = request.POST.get('dorm_change')
                dorm = Dorm.objects.get(pk=dorm_id)
                print(dorm)
                stu_dorm_count = Student.objects.filter(dorm=dorm).count()
                if stu.dorm is None:
                    messages.error(request, "只允许更换宿舍，入宿需学生自行申请")
                    return redirect('student')
                if stu_dorm_count >= 4:
                    messages.error(request, "目标宿舍已经有4名学生，不能继续添加")
                    return redirect('student')

                stu.dorm = dorm
                stu.save()
                messages.success(request, "更换宿舍成功")
                return redirect('student')
            else:
                return redirect('student')
        else:
            messages.error(request, '您不是管理员用户，禁止访问')
            return redirect('dashboard')
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def dormmanager(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='SuperUser').exists():
            if request.method == 'POST':
                dormmanager_id = request.POST.get('dormmanager_id')
                name = request.POST.get('name')
                age = request.POST.get('age')
                gender = request.POST.get('gender')
                phone = request.POST.get('phone')
                building_id = request.POST.get('building')

                # 如果不能获得楼宇数据则不填写宿管管理的楼宇
                try:
                    building = DormBuilding.objects.get(id=building_id)
                except DormBuilding.DoesNotExist:
                    building = None
                password = request.POST.get('password')

                if not re.match(r'DM\d{8}', dormmanager_id):
                    messages.error(request, '宿管ID格式不正确，必须以DM开头，后跟8位数字。')
                    return redirect('dormmanager')

                if DormManager.objects.filter(dormmanager_id=dormmanager_id).exists():
                    messages.error(request, '该宿管ID已存在，请添加新的宿管ID')
                    return redirect('dormmanager')

                with transaction.atomic():
                    try:
                        dm = DormManager(name=name, age=age, gender=gender, phone=phone, dormmanager_id=dormmanager_id,
                                         building=building)
                        user = User.objects.create_user(username=dormmanager_id, password=password)
                        user.groups.add(Group.objects.get(name='DormManager'))
                        user.save()
                        dm.save()
                        messages.success(request, "添加宿管成功！")
                    except Exception as e:
                        messages.success(request, e)
                        print(e)

                return redirect('dormmanager')
            else:
                # 默认按照ID排序，实现排序功能
                sort_by = request.GET.get('sort', 'dormmanager_id')
                reverse = '-' if 'reverse' in request.GET else ''

                dormmanagers_all = DormManager.objects.all().order_by(reverse + sort_by)
                dormmanagers_all_data = []
                print(sort_by)
                for dm in dormmanagers_all:
                    building_name = dm.building.name if dm.building else "暂无管理楼宇"
                    dormmanagers_all_data.append({
                        'dm_id': dm.dormmanager_id,
                        'dm_name': dm.name,
                        'dm_age': dm.age,
                        'dm_gender': dm.gender,
                        'dm_phone': dm.phone,
                        'dm_building_id': dm.building,
                        'dm_building': building_name,
                    })

                building = DormBuilding.objects.all()
                context = {'dormmanagers_all_data': dormmanagers_all_data,
                           'building': building,
                           'current_sort': reverse + sort_by}
                return render(request, 'management/dormmanager.html', context)
        else:
            messages.error(request, '您不是管理员用户，禁止访问')
            return redirect('dashboard')
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def edit_dormmanager(request, dormmanager_id):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='SuperUser').exists():
            if request.method == 'POST':
                dm = DormManager.objects.get(pk=dormmanager_id)
                name = request.POST.get('name')
                age = request.POST.get('age')
                gender = request.POST.get('gender')
                phone = request.POST.get('phone')
                building_id = request.POST.get('building')

                try:
                    building = DormBuilding.objects.get(id=building_id)
                except DormBuilding.DoesNotExist:
                    building = None

                with transaction.atomic():
                    try:
                        dm.name = name
                        dm.age = age
                        dm.gender = gender
                        dm.phone = phone
                        dm.building = building
                        dm.save()
                        messages.success(request, "更新宿管信息成功！")
                    except Exception as e:
                        messages.error(request, e)
                        print(e)
                return redirect('dormmanager')
            else:
                dm = DormManager.objects.get(pk=dormmanager_id)
                building = DormBuilding.objects.all()
                context = {'dm': dm, 'building': building}
                return render(request, 'management/edit_dormmanager.html', context)
        else:
            messages.error(request, '您不是管理员用户，禁止访问')
            return redirect('dashboard')
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')


def delete_dormmanager(request, dormmanager_id):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='SuperUser').exists():
            if request.method == 'POST':
                dm = DormManager.objects.get(pk=dormmanager_id)
                user = User.objects.get(username=dormmanager_id)
                with transaction.atomic():
                    try:
                        user.delete()
                        dm.delete()
                        messages.success(request, "删除宿管成功")
                    except Exception as e:
                        messages.error(request, e)
                        print(e)
                return redirect('dormmanager')

        else:
            messages.error(request, '您不是管理员用户，禁止访问')
            return redirect('dashboard')
    else:
        messages.error(request, '用户未登录！')
        return redirect('login')

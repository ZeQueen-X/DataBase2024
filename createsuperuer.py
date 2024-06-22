import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DataBase_Django.settings')
django.setup()

from django.contrib.auth.models import User, Group

su_user = User.objects.create_superuser(username='admin', password='adminadmin')
su_user.groups.add(Group.objects.get(name='superuser'))
su_user.save()

print("已成功创建超级管理员用户")

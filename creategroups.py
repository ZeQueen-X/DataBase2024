import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DataBase_Django.settings')
django.setup()

from django.contrib.auth.models import Group

#创建三个用户组
def create_groups():
    groups = ['DormManager', 'Student', 'SuperUser']
    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"Group '{group_name}' created successfully.")
        else:
            print(f"Group '{group_name}' already exists.")


if __name__ == "__main__":
    create_groups()

from django import forms
from .models import ImgUpload


class ImageForm(forms.ModelForm):
    class Meta:
        model = ImgUpload
        fields = ['image','title']

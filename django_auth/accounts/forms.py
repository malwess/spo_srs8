from django import forms

from .models import AcademicGroup, Course, Department


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']
        labels = {'name': 'Название факультета'}
        help_texts = {'name': 'Например: Информационные технологии'}
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название'}),
        }


class AcademicGroupForm(forms.ModelForm):
    class Meta:
        model = AcademicGroup
        fields = ['name', 'department']
        labels = {
            'name': 'Название группы',
            'department': 'Факультет',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'М3О-236БВ-25'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].empty_label = 'Выберите факультет'


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'department']
        labels = {
            'title': 'Название курса',
            'description': 'Описание',
            'department': 'Факультет',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название курса'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                                 'placeholder': 'Кратко опишите, чему посвящён курс'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].empty_label = 'Выберите факультет'

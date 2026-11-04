from datetime import date

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Assessment, StudentProfile
from .survey import SECTIONS, SURVEY_FIELDS, YES_NO

User = get_user_model()


def _style(form):
    """Give every normal input the shared CSS class (radios are styled separately)."""
    for field in form.fields.values():
        if not isinstance(field.widget, (forms.RadioSelect, forms.CheckboxInput)):
            field.widget.attrs.setdefault('class', 'field-input')


# ---------------------------------------------------------------- welcome page

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'name-input', 'autocomplete': 'username', 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update(
            {'class': 'name-input', 'autocomplete': 'current-password', 'placeholder': 'Password'})


class SignUpForm(forms.Form):
    name = forms.CharField(
        max_length=100, label='Your name',
        widget=forms.TextInput(attrs={'class': 'name-input', 'autocomplete': 'name', 'placeholder': 'Enter your name'}))
    username = forms.CharField(
        max_length=150, label='Username', validators=[User.username_validator],
        widget=forms.TextInput(attrs={'class': 'name-input', 'autocomplete': 'username', 'placeholder': 'Choose a username'}))
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'name-input', 'autocomplete': 'new-password', 'placeholder': 'Choose a password',
                'aria-describedby': 'signup-password-hint'}))

    def clean_name(self):
        return self.cleaned_data['name'].strip()

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('That username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        if password:
            try:
                validate_password(password, user=User(username=cleaned.get('username') or ''))
            except ValidationError as error:
                self.add_error('password', error)
        return cleaned

    def save(self):
        user = User.objects.create_user(username=self.cleaned_data['username'],
                                        password=self.cleaned_data['password'])
        StudentProfile.objects.create(user=user, name=self.cleaned_data['name'])
        return user


# ---------------------------------------------------------- primary attributes

class ProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['name', 'date_of_birth', 'major', 'year_of_enrollment', 'gender',
                  'courses_taken', 'avg_daily_study_hours', 'height_cm', 'weight_kg', 'chronic_illnesses',
                  'ai_opt_in']
        labels = {
            'name': 'Name',
            'date_of_birth': 'Date of birth',
            'major': 'Major',
            'year_of_enrollment': 'Year of enrollment',
            'gender': 'Gender',
            'courses_taken': 'Courses taken this semester',
            'avg_daily_study_hours': 'Average daily study hours',
            'height_cm': 'Height (cm)',
            'weight_kg': 'Weight (kg)',
            'chronic_illnesses': 'Chronic illnesses',
            'ai_opt_in': 'Use AI to write my Note of the Day',
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'year_of_enrollment': forms.NumberInput(attrs={'min': 2000, 'max': date.today().year}),
            'courses_taken': forms.NumberInput(attrs={'min': 1, 'max': 15, 'placeholder': 'e.g. 5'}),
            'height_cm': forms.NumberInput(attrs={'step': '0.1', 'placeholder': 'e.g. 165'}),
            'weight_kg': forms.NumberInput(attrs={'step': '0.1', 'placeholder': 'e.g. 60'}),
            'chronic_illnesses': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Leave empty if none'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('name', 'date_of_birth', 'major', 'year_of_enrollment', 'gender',
                     'courses_taken', 'avg_daily_study_hours'):   # primary = must
            self.fields[name].required = True
        _style(self)

    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        if dob and (dob >= date.today() or dob.year < 1940):
            raise ValidationError('Please enter a valid date of birth.')
        return dob

    def clean_year_of_enrollment(self):
        year = self.cleaned_data['year_of_enrollment']
        if year and not (2000 <= year <= date.today().year):
            raise ValidationError(f'Please enter a year between 2000 and {date.today().year}.')
        return year


# ------------------------------------------------------------------ account (profile page)

class UsernameChangeForm(forms.Form):
    username = forms.CharField(
        max_length=150, label='New username', validators=[User.username_validator],
        widget=forms.TextInput(attrs={'class': 'field-input', 'autocomplete': 'username'}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        if username == self.user.get_username():
            raise ValidationError('That is already your username.')
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise ValidationError('That username is already taken.')
        return username

    def save(self):
        self.user.username = self.cleaned_data['username']
        self.user.save(update_fields=['username'])
        return self.user


class StyledPasswordChangeForm(PasswordChangeForm):
    """Django's own password change form (checks the current password and the same password rules as sign up)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {'old_password': 'Current password', 'new_password1': 'New password',
                  'new_password2': 'Confirm new password'}
        for name, label in labels.items():
            self.fields[name].label = label
            self.fields[name].widget.attrs['class'] = 'field-input'
        self.fields['old_password'].widget.attrs.pop('autofocus', None)   # do not grab focus on page load
        self.fields['new_password1'].help_text = ''                        # the rules are listed in the template


# ------------------------------------------------------------------ survey

class AssessmentForm(forms.ModelForm):
    # Not a database column of the answers: it is the same setting as the profile's AI choice,
    # shown again right before the answers are sent (the view keeps the two in step).
    use_ai = forms.BooleanField(required=False, label='Use AI to write my Note of the Day')

    class Meta:
        model = Assessment
        # the survey fields must be listed here so ModelForm.save() stores them
        fields = SURVEY_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Survey questions: 1-5 radios that start on 3 (Neutral); yes/no start on "No"
        for section in SECTIONS:
            for name, text, choices in section['questions']:
                if choices is YES_NO:
                    self.fields[name] = forms.TypedChoiceField(
                        label=text, choices=choices, initial='False',
                        coerce=lambda value: value == 'True', widget=forms.RadioSelect)
                else:
                    self.fields[name] = forms.TypedChoiceField(
                        label=text, choices=choices, initial=3,
                        coerce=int, widget=forms.RadioSelect)
        _style(self)

    @property
    def sections(self):
        return [
            {'title': s['title'], 'intro': s['intro'], 'fields': [self[q[0]] for q in s['questions']]}
            for s in SECTIONS
        ]

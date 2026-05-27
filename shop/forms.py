from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Review, Newsletter, Profile

# --- ФОРМА ВІДГУКУ ---
class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        widget=forms.RadioSelect(),
        label='Оцінка'
    )

    class Meta:
        model = Review
        # 'author' видалено, бо тепер ми прив'язуємо відгук до user у views.py
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Напишіть ваш відгук...', 'rows': 4}),
        }

# --- ФОРМА ПІДПИСКИ ---
class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Ваш email...',
                'required': True,
                'style': 'padding: 8px; border-radius: 4px; border: none; width: 250px;'
            }),
        }

# --- ФОРМА РЕЄСТРАЦІЇ ---
class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50, required=True, label="Ім'я",
        widget=forms.TextInput(attrs={'placeholder': "Ваше ім'я", 'class': 'form-input'})
    )
    email = forms.EmailField(
        required=True, label="Email",
        widget=forms.EmailInput(attrs={'placeholder': 'email@example.com', 'class': 'form-input'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']
        labels = {'username': 'Логін'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-input')
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Підтвердження"
        self.fields['password1'].help_text = "Мінімум 8 символів."

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Profile.objects.get_or_create(user=user)
        return user

# --- ФОРМА ЗАМОВЛЕННЯ ---
class OrderForm(forms.Form):
    last_name = forms.CharField(label="Прізвище", widget=forms.TextInput(attrs={'placeholder': 'Ваше прізвище', 'class': 'velo-input'}))
    first_name = forms.CharField(label="Ім'я", widget=forms.TextInput(attrs={'placeholder': "Ваше ім'я", 'class': 'velo-input'}))
    middle_name = forms.CharField(label="По батькові", required=False, widget=forms.TextInput(attrs={'placeholder': 'По батькові', 'class': 'velo-input'}))
    phone = forms.CharField(label="Телефон", widget=forms.TextInput(attrs={'placeholder': '+380...', 'class': 'velo-input'}))
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'id': 'city-input', 'autocomplete': 'off', 'class': 'velo-input'}))
    warehouse = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'id': 'warehouse-final'}))
    use_bonuses = forms.BooleanField(required=False, label="Списати бонуси для знижки")

# --- ФОРМА ПРОФІЛЮ ---
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['last_name', 'first_name', 'middle_name', 'phone', 'city', 'warehouse']
        widgets = {
            'last_name': forms.TextInput(attrs={'placeholder': 'Прізвище', 'class': 'velo-input'}),
            'first_name': forms.TextInput(attrs={'placeholder': "Ім'я", 'class': 'velo-input'}),
            'middle_name': forms.TextInput(attrs={'placeholder': 'По батькові', 'class': 'velo-input'}),
            'phone': forms.TextInput(attrs={'placeholder': '+380...', 'class': 'velo-input'}),
            'city': forms.TextInput(attrs={'placeholder': 'Місто...', 'class': 'velo-input'}),
            'warehouse': forms.HiddenInput(),
        }
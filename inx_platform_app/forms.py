from django import forms
from django.utils.formats import number_format
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, AuthenticationForm, UsernameField, PasswordResetForm, SetPasswordForm
# from .models import *
from .models import (
    Brand,
    MajorLabel,
    Division,
    InkTechnology,
    NSFDivision,
    MarketSegment,
    Customer,
    MaterialGroup,
    User,
    CustomerType,
    Currency,
    Industry,Product, Color, MadeIn, Packaging, ProductLine, ProductStatus, BudgetForecastDetail)


class EditMajorLabelForm(forms.ModelForm):
    class Meta:
        model = MajorLabel
        fields =(
            'name',
            'sap_id',
            'sap_name',
            'sqlapp_id',
            'svg_logo'
        )
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sap_id': forms.TextInput(attrs={'class': 'form-control'}),
            'sap_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sqlapp_id': forms.TextInput(attrs={'class': 'form-control'}),
            'svg_logo': forms.Textarea(attrs={'class': 'form-control'}),
        }


class EditBrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = (
            'name',
            'no_budget',
            'division',
            'major_label',
            'ink_technology',
            'nsf_division',
            'market_segment',
            'material_group',
            'sap_id',
            'sap_name'
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'no_budget': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sap_id': forms.TextInput(attrs={'class': 'form-control'}),
            'sap_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        division = forms.ModelChoiceField(queryset=Division.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        major_label = forms.ModelChoiceField(queryset=MajorLabel.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        ink_technology = forms.ModelChoiceField(queryset=InkTechnology.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        nsf_division = forms.ModelChoiceField(queryset=NSFDivision.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        market_segment = forms.ModelChoiceField(queryset=MarketSegment.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        materal_group = forms.ModelChoiceField(queryset=MaterialGroup.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))


class EditCustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields=(
            'number',
            'name',
            'currency',
            'sales_employee',
            'customer_type',
            'active',
            'insurance',
            'insurance_value',
            'credit_limit',
            'vat',
            'email',
            'approved_by',
            # 'approved_on',
            'import_note',
            'import_status',
            'sqlapp_id'
        )
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'insurance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'insurance_value': forms.TextInput(attrs={'class': 'form-control'}),
            'credit_limit': forms.TextInput(attrs={'class': 'form-control'}),
            'vat': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            # 'approved_on': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'import_note': forms.TextInput(attrs={'class': 'form-control'}),
            'import_status': forms.TextInput(attrs={'class': 'form-control'}),
            'sqlapp_id': forms.TextInput(attrs={'class': 'form-control'})
        }
        sales_employee = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        customer_type = forms.ModelChoiceField(queryset=CustomerType.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        industry = forms.ModelChoiceField(queryset=Industry.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        currency = forms.ModelChoiceField(queryset=Currency.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    
    # this below replaces the email of the user with teh full name
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sales_employee'].label_from_instance = lambda obj: obj.get_full_name()


class EditProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields=(
            'number',
            'name',
            'is_ink',
            'import_note',
            'import_status',
            'color',
            'made_in',
            'brand',
            'packaging',
            'product_line',
            'product_status',
            'sqlapp_id'
        )
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_ink': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'import_note': forms.TextInput(attrs={'class': 'form-control'}),
            'import_status': forms.TextInput(attrs={'class': 'form-control'}),
            'sqlapp_id': forms.TextInput(attrs={'class': 'form-control'})
        }
        color = forms.ModelChoiceField(queryset=Color.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        made_in = forms.ModelChoiceField(queryset=MadeIn.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        brand = forms.ModelChoiceField(queryset=Brand.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        packaging = forms.ModelChoiceField(queryset=Packaging.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        product_line = forms.ModelChoiceField(queryset=ProductLine.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
        product_status = forms.ModelChoiceField(queryset=ProductStatus.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2',
            'sqlapp_id',
            'is_active',
            'is_staff',
            'is_superuser'
            )
        widgets={
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            'sqlapp_id': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        "placeholder": "Current Password"
    }), label='Current Password')
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        "placeholder": "New Password"
    }), label="New Password")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        "placeholder": "Confirm New Password"
    }), label="Confirm New Password")


class RegistrationForm(UserCreationForm):
  password1 = forms.CharField(
      label="Password",
      widget=forms.PasswordInput(attrs={'class': 'form-control', "placeholder": "Password"}),
  )
  password2 = forms.CharField(
      label="Password Confirmation",
      widget=forms.PasswordInput(attrs={'class': 'form-control', "placeholder": "Confirm Password"}),
  )

  class Meta:
    model = User
    fields = ('email', )

    widgets = {
      'username': forms.TextInput(attrs={
          'class': 'form-control',
          "placeholder": "Username",
      }),
      'email': forms.EmailInput(attrs={
          'class': 'form-control',
          "placeholder": "Email address"
      })
    }


class LoginForm(AuthenticationForm):
  username = UsernameField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Your email"}))
  password = forms.CharField(
      label="Password",
      strip=False,
      widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Your password"}),
  )


class UserPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        "placeholder": "Email address",
    }))


class UserSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        "placeholder": "New Password",
    }), label="New Password")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        "placeholder": "Confirm New Password"
    }), label="Confirm New Password")


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'vat': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'approved_by_old': forms.TextInput(attrs={'class': 'form-control'}),
            'import_note': forms.TextInput(attrs={'class': 'form-control'}),
            'import_status': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'insurance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sales_employee': forms.Select(attrs={'class': 'form-select'}),
            'customer_type': forms.Select(attrs={'class': 'form-select'}),
            'industry': forms.Select(attrs={'class': 'form-select'}),
            'country': forms.Select(attrs={'class': 'form-select'}),
            'approved_on': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'approved_by': forms.Select(attrs={'class': 'form-select'}),
            'customer_service_rep': forms.Select(attrs={'class': 'form-select'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control number-input'}),
            'name': forms.TextInput(attrs={'class': 'form-control name-input'}),
            'is_ink': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'import_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'import_status': forms.TextInput(attrs={'class': 'form-control'}),
            
            'color': forms.Select(attrs={'class': 'form-select'}),
            'made_in': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'packaging': forms.Select(attrs={'class': 'form-select'}),
            'product_line': forms.Select(attrs={'class': 'form-select'}),
            'product_status': forms.Select(attrs={'class': 'form-select'}),
            'sqlapp_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_new': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_fert': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'approved_on': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'approved_by': forms.Select(attrs={'class': 'form-select'}),
        }


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sap_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sap_id': forms.TextInput(attrs={'class': 'form-control'}),
            'has_colors': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'no_budget': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'major_label': forms.Select(attrs={'class': 'form-select'}),
            'division': forms.Select(attrs={'class': 'form-select'}),
            'ink_technology': forms.Select(attrs={'class': 'form-select'}),
            'nsf_division': forms.Select(attrs={'class': 'form-select'}),
            'material_group': forms.Select(attrs={'class': 'form-select'}),
            'market_segment': forms.Select(attrs={'class': 'form-select'})
        }


class NumberInputWithThousandsSeparator(forms.TextInput):
    input_type = 'text'

    def format_value(self, value):
        if value is None:
            return ''
        return number_format(value, use_l10n=True, force_grouping=True)


class ForecastForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput(), required=True)
    budforline_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = BudgetForecastDetail
        fields = ['id', 'budforline_id', 'month', 'volume', 'price', 'value']
        widgets = {
            'id': forms.HiddenInput(),
            'budforline_id': forms.HiddenInput(),
            # 'budforline_id': forms.TextInput(attrs={'class': 'form-control p-1', 'readonly': 'readonly'}),
            'month': forms.TextInput(attrs={'class': 'form-control p-1 text-center', 'readonly': 'readonly', 'disabled': 'disabled'}),
            'volume': forms.NumberInput(attrs={'class': 'form-control p-1'}),
            # 'volume': NumberInputWithThousandsSeparator(attrs={'class': 'form-control p-1'}),
            'price': forms.NumberInput(attrs={'class': 'form-control p-1'}),
            # 'value': forms.NumberInput(attrs={'class': 'form-control p-0', 'readonly': 'readonly', 'disabled':'disabled'}),
            'value': NumberInputWithThousandsSeparator(attrs={'class': 'form-control ps-1 pe-0', 'readonly': 'readonly', 'disabled':'disabled'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(ForecastForm, self).__init__(*args, **kwargs)
        self.fields['value'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.value = instance.volume * instance.price
        if commit:
            instance.save()
        return instance

class FlatBudgetForm(forms.Form):
    volume = forms.FloatField(
        label='Volume',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control p-1', 'placeholder': 'Enter full year volume'})
        )
    
    price = forms.DecimalField(
        label='Price',
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control p-1', 'placeholder': 'Enter a valid price through the year'})
        )
    
class SalesForecastBudgetFilterForm(forms.Form):

    user = forms.ChoiceField(
        choices=[('all', 'All')] + [(user.id, user.email) for user in User.objects.all()],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    customer = forms.ChoiceField(
        choices = [('all', 'All')] + [(c.id, c.name) for c in Customer.objects.all()],
        required = False,
        widget = forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super(SalesForecastBudgetFilterForm, self).__init__(*args, **kwargs)
        # Initialize user choices
        self.fields['user'].choices = [('all', 'All')] + [(user.id, user.email) for user in User.objects.all()]

        if 'user' in self.data:
            user_id = self.data.get('user')
            if user_id and user_id != 'all':
                self.fields['customer'].choices = [('all', 'All')] + [(c.id, c.name) for c in Customer.objects.filter(sales_employee__id=user_id, active=True)]
            else:
                self.fields['customer'].choices = [('all', 'All')] + [(c.id, c.name) for c in Customer.objects.filter(active=True)]
        else:
            self.fields['customer'].choices = [('all', 'All')] + [(c.id, c.name) for c in Customer.objects.all()]


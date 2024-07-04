import django_filters
from django import forms
from .models import *


class ProductFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, forms.ModelChoiceField):
                field.widget.attrs.update({'class': 'form-select'})
            elif field_name == 'is_ink' or field_name == 'is_new':
                field.widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

class ProductFilter(django_filters.FilterSet):
    number = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Product Number"
        )
    name = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Product Name"
        )
    brand_name = django_filters.ModelChoiceFilter(
        field_name='brand',
        queryset=Brand.objects.all().order_by('name'),
        empty_label='All',
        label='Brand'
    )
    products_status = django_filters.ModelChoiceFilter(
        field_name='product_status',
        queryset=ProductStatus.objects.all().order_by('name'),
        empty_label='All',
        label='Product Status'
    )
    major_label = django_filters.ModelChoiceFilter(
        field_name='brand__major_label',
        queryset=MajorLabel.objects.all().order_by('name'),
        empty_label="All",
        label="Major Label"
    )
    packaging = django_filters.ModelChoiceFilter(
        field_name="packaging",
        queryset=Packaging.objects.all().order_by('name'),
        empty_label="All",
        label="Packaging"
    )
    is_ink=django_filters.BooleanFilter(
        lookup_expr="iexact"
        )
    is_new=django_filters.BooleanFilter(
        lookup_expr="iexact"
    )

    class Meta:
        model = Product
        fields = ['is_new', 'is_ink', 'name', 'number', 'brand_name', 'products_status', 'major_label', 'packaging']
        form = ProductFilterForm
    
    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        is_ink_value = self.form.cleaned_data.get('is_ink')

        if is_ink_value is not None:
            queryset = queryset.filter(is_ink=is_ink_value)

        return queryset


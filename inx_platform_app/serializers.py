from rest_framework import serializers
from .models import *

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ColorGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorGroup
        fields = '__all__'

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'


class MarketSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSegment
        fields = '__all__'


class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = '__all__'


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = '__all__'


class ProductLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLine
        fields = '__all__'


class MajorLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MajorLabel
        fields = '__all__'


class InkTechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = InkTechnology
        fields = '__all__'


class NSFDivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NSFDivision
        fields = '__all__'


class MaterialGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialGroup
        fields = '__all__'


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = '__all__'


class PackagingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Packaging
        fields = '__all__'


class PackagingRateToLiterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingRateToLiter
        fields = '__all__'


class ProductStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStatus
        fields = '__all__'


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = '__all__'


class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = '__all__'


class CountryCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryCode
        fields = '__all__'


class CustomerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerType
        fields = '__all__'


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = '__all__'


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'


class RateToLTSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateToLT
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class Ke30Serializer(serializers.ModelSerializer):
    class Meta:
        model = Ke30Line
        fields = '__all__'

class ZaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZAQCODMI9_line
        fields = '__all__'

class BudForLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudForLine
        fields = '__all__'

class BudgetForecastDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetForecastDetail
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
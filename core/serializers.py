from rest_framework import serializers
from .models import User, PatientProfile

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'full_name', 'age', 'gender')

    def create(self, validated_data):
        # пользователь с хешированным паролем
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name'),
            age=validated_data.get('age'),
            gender=validated_data.get('gender')
        )
        # пустой профиль пациента, связанный с этим юзером
        PatientProfile.objects.create(user=user)
        return user

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = (
                'diagnosis', 'diagnosis_detail', 'limitation_type',
                'baseline_value', 'baseline_unit', 'baseline_condition'
        )
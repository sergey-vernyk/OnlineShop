from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import serializers
from rest_framework.validators import ValidationError

from account.models import Profile
from goods.models import Favorite


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer with user's profile information
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    coupons = serializers.StringRelatedField(read_only=True, many=True)
    username = serializers.CharField(source='user.username', max_length=150)
    email = serializers.EmailField(source='user.email', max_length=254)
    first_name = serializers.CharField(source='user.first_name', max_length=150)
    last_name = serializers.CharField(source='user.last_name', max_length=150)
    password1 = serializers.CharField(source='user.password1', write_only=True)
    password2 = serializers.CharField(source='user.password2', write_only=True)

    class Meta:
        model = Profile
        fields = '__all__'

    def create(self, validated_data):
        """
        Create profile instance
        """
        user_data = validated_data.pop('user')
        username = user_data.get('username')
        password1 = user_data.get('password1')
        password2 = user_data.get('password2')
        email = user_data.get('email')

        # check whether user with passed username or email doesn't exist
        if User.objects.filter(Q(username=username) | Q(email=email)).exists():
            raise ValidationError(f"User with username '{username}' or email '{email}' exists", code='exists_user')

        # check passed passwords
        if password1 == password2:
            try:
                validate_password(password1)
                user_data['password'] = user_data.pop('password2')
                user_data.pop('password1')
            except DjangoValidationError as e:
                raise ValidationError(e)  # replacing django ValidationError to DRF ValidationError
        else:
            raise ValidationError('Passwords are mismatch', code='mismatch_password')

        user = User.objects.create_user(**user_data)
        validated_data['user'] = user

        profile = Profile.objects.create(**validated_data)

        Favorite.objects.create(profile=profile)

        return profile

    def update(self, instance, validated_data):
        """
        Update profile's info or built-in user's info, which relates with profile
        """
        user_data = validated_data.pop('user')
        if user_data:
            for field, value in user_data.items():
                setattr(instance.user, field, value)

            instance.user.save()

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save(update_fields=[*validated_data.keys()])

        return instance

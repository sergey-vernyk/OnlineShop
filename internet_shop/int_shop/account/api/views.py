import coreapi
import coreschema
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import viewsets, permissions, status, views, parsers
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes, action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from rest_framework.validators import ValidationError

from account.models import Profile
from common.moduls_init import redis
from goods.api.serializers import ProductSerializer
from goods.models import Product
from . import serializers
from .permissions import IsTheSameUserThatMakesAction
from .schemas import FavoriteActionsSchema
from .tasks import send_email_for_set_new_account_password


class AccountViewSet(viewsets.ModelViewSet):
    """
    View allows obtaining all profiles, create, delete, update profile
    """
    queryset = Profile.objects.prefetch_related('coupons').select_related('user')
    serializer_class = serializers.ProfileSerializer
    permission_classes = [IsTheSameUserThatMakesAction]
    authentication_classes = [TokenAuthentication, BasicAuthentication]

    @action(methods=['GET'],
            detail=False,
            url_path=r'favorite/me',
            url_name='favorite_products_list',
            name='Favorites list')
    def list_favorites(self, request):
        """
        Displaying profile's favorite list
        """
        current_profile = get_object_or_404(Profile, user_id=request.user.pk)
        products = current_profile.profile_favorite.product.prefetch_related('comments')
        serializer = ProductSerializer(instance=[product for product in products], many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    @action(methods=['GET'],
            detail=False,
            url_path=r'watched/me',
            url_name='watched_products_list',
            name='Watched list')
    def list_watched_products(self, request):
        """
        Displaying products which profile has watched
        """
        current_profile = get_object_or_404(Profile, user_id=request.user.pk)
        products_ids = (int(pk) for pk in redis.smembers(f'profile_id:{current_profile.pk}'))
        products = Product.available_objects.prefetch_related('comments').filter(id__in=products_ids)
        serializer = ProductSerializer(instance=[product for product in products], many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    @action(methods=['POST'],
            detail=False,
            url_path=r'favorite/me/(?P<product_pk>[0-9]+)?/(?P<act>[a-zA-Z]+)/?',
            url_name='favorite_actions',
            name='Add Or Remove Favorite Item',
            schema=FavoriteActionsSchema())
    def actions_with_favorite_products(self, request, product_pk: int, act: str):
        """
        Add or remove product with `product_id` into/from own favorites list
        """
        current_profile = Profile.objects.get(user=request.user)
        product = get_object_or_404(Product, pk=product_pk)
        if act == 'add':
            current_profile.profile_favorite.product.add(product)
        elif act == 'remove':
            current_profile.profile_favorite.product.remove(product)

        return Response({'success': f"Product '{product.name}' has been successfully {act}"})


class ResetUserAccountPasswordView(views.APIView):
    """
    API view allows to reset forgot user password and set new password
    """
    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            name='email',
            required=False,
            type='string',
            location='form',
            schema=coreschema.String(description='Field for email address in order to reset password. '
                                                 'Type only for the first time and either without password, uid or token', )
        ),
        coreapi.Field(
            name='password',
            required=False,
            type='string',
            location='form',
            schema=coreschema.String(description='Field for new password after old password has been reset'
                                                 ' Typed along with token and uid.'),
        ),
        coreapi.Field(
            name='token',
            required=False,
            type='string',
            location='form',
            schema=coreschema.String(
                description='Field for enter received token for set new password. Type along with password and uid.'),
        ),
        coreapi.Field(
            name='uid',
            required=False,
            type='string',
            location='form',
            schema=coreschema.String(
                description='Field for enter received uid for set new password. Type along with token and password.'),
        ),
    ])

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        token = request.data.get('token')
        uidb64 = request.data.get('uid')
        new_password = request.data.get('password')

        if all([token, uidb64, new_password]):
            uidb64_decode = force_str(urlsafe_base64_decode(uidb64))  # decode uidb64 to get username
            user = User.objects.get(username=uidb64_decode)
            # check token, set new password and save user, otherwise raise error
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({'success': 'Password has been successfully changed'})
            else:
                raise ValidationError('Token has expired or has been already used', code='wrong_token')
        else:
            is_exist = User.objects.filter(email=email).exists()
            if is_exist:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uidb64 = urlsafe_base64_encode(force_bytes(user.username))
                # send email with instructions about set new password
                send_email_for_set_new_account_password.delay(token=token,
                                                              uidb64=uidb64,
                                                              email=email,
                                                              username=user.username,
                                                              is_secure=request.stream.scheme,
                                                              domain=request.stream.site.domain)
                return Response({'message': 'Please, check your email. '
                                            'You have to receive email with instruction for reset password'},
                                status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, BasicAuthentication])
def auth_user(request):
    """
    API view attempts to authenticate user using passed token or username with password
    """
    content = {'success': f"User '{request.user.username}' was successfully authenticated"}
    if not isinstance(request.user, AnonymousUser):
        return Response(content, status=status.HTTP_202_ACCEPTED)
    else:
        raise ValidationError({'error': 'Credentials are wrong'}, code='authentication')


class PhotoUploadView(views.APIView):
    """
    View allows upload profile's photo
    """
    parser_classes = [parsers.FileUploadParser]
    permission_classes = [permissions.IsAuthenticated, IsTheSameUserThatMakesAction]

    def put(self, request, filename, instance_pk, format=None):
        file_obj = request.data['file']
        try:
            instance = get_object_or_404(Profile, pk=instance_pk)
            self.check_object_permissions(request, instance)
        except Http404:
            raise NotFound(f'Object with id {instance_pk} was not found')
        else:
            instance.photo.save(filename, file_obj)  # save photo to DB
            return Response(status=status.HTTP_200_OK)

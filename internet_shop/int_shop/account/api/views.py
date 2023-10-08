import coreapi
import coreschema
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status, views, parsers
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from rest_framework.validators import ValidationError

from account.models import Profile
from common.moduls_init import redis
from goods.api.serializers import ProductSerializer
from goods.models import Product
from . import serializers
from .permissions import ActionsWithOwnProfilePermission, IsNotAuthenticated
from .schemas import FavoriteActionsSchema
from .serializers import PhotoUploadSerializer, ResetPasswordSerializer
from .tasks import send_email_for_set_new_account_password


class AccountViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` actions.

    * get - obtain all profiles
    * post - create new profile
    * get/{id} - retrieve profile with `id`
    * patch/{id} - update one or several fields of profile with `id`
    * put/{id} - update all fields of profile with id
    * delete/{id} - delete profile with id

    """
    queryset = Profile.objects.prefetch_related('coupons').select_related('user')
    serializer_class = serializers.ProfileSerializer
    permission_classes = [ActionsWithOwnProfilePermission]

    @action(methods=['GET'],
            detail=False,
            url_path=r'me',
            url_name='profile_detail',
            name='Profile detail',
            permission_classes=[permissions.IsAuthenticated])
    def get_profile_info(self, request):
        """
        Get all info about current profile
        """
        current_profile = Profile.objects.get(user=request.user)
        serializer = self.get_serializer(instance=current_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'],
            detail=False,
            url_path=r'me/favorite',
            url_name='favorite_products_list',
            name='Favorites list',
            permission_classes=[permissions.IsAuthenticated])
    def get_list_favorites(self, request):
        """
        Obtain profile's favorite list
        """
        current_profile = get_object_or_404(Profile, user_id=request.user.pk)
        products = current_profile.profile_favorite.product.prefetch_related('comments')
        serializer = ProductSerializer(instance=[product for product in products], many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    @action(methods=['GET'],
            detail=False,
            url_path=r'me/watched_products',
            url_name='watched_products_list',
            name='Watched list',
            permission_classes=[permissions.IsAuthenticated])
    def get_list_watched_products(self, request):
        """
        Obtain products which profile has watched
        """
        current_profile = get_object_or_404(Profile, user_id=request.user.pk)
        products_ids = (int(pk) for pk in redis.smembers(f'profile_id:{current_profile.pk}'))
        products = Product.available_objects.prefetch_related('comments').filter(id__in=products_ids)
        serializer = ProductSerializer(instance=[product for product in products], many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    @action(methods=['POST'],
            detail=False,
            url_path=r'favorite/me/(?P<product_pk>[0-9]+)?/(?P<act>(add|remove))?',
            url_name='add_remove_product_favorite',
            name='Add Or Remove Favorite Product',
            schema=FavoriteActionsSchema(),
            permission_classes=[permissions.IsAuthenticated])
    def add_or_remove_favorite_product(self, request, product_pk: int, act: str):
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

    @action(methods=['DELETE'],
            detail=False,
            url_path='me/delete',
            url_name='delete_own_profile',
            name='Delete Own Profile',
            permission_classes=[ActionsWithOwnProfilePermission])
    def delete_own_profile(self, request):
        """
        Delete own profile with build-in user from the system
        """
        current_profile = Profile.objects.get(user=request.user)
        current_profile.delete()
        return Response({'success': 'Your profile was successfully removed from the system'},
                        status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        """
        User can update only own profile
        """
        profile_to_update = Profile.objects.get(pk=kwargs['pk'])
        self.check_object_permissions(request, profile_to_update)
        return super().update(request, *args, **kwargs)


class ResetUserAccountPasswordView(views.APIView):
    """
    Reset forgot user's password and set new password using `post` method.
    At the beginning must send only `email`, then after response must send only new `password`, `token` and `uid`
    """
    permission_classes = [IsNotAuthenticated]
    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            name='email',
            required=False,
            type='string',
            location='form',
            schema=coreschema.String(
                description='Field for email address in order to reset password. '
                            'Type only for the first time and either without password, uid or token',
            )
        ),
        coreapi.Field(
            name='password',
            required=False,
            type='string',
            location='form',
            schema=coreschema.String(
                description='Field for new password after old password has been reset'
                            ' Typed along with token and uid.'
            ),
        ),
        coreapi.Field(
            name='token',
            required=False,
            type='string',
            location='form',
            schema=coreschema.String(
                description='Field for enter received token for set new password. Type along with password and uid.'
            ),
        ),
        coreapi.Field(
            name='uid',
            required=False,
            type='string',
            location='form',
            schema=coreschema.String(
                description='Field for enter received uid for set new password. Type along with token and password.'
            ),
        ),
    ])

    @swagger_auto_schema(method='post', request_body=ResetPasswordSerializer)
    @action(detail=False, methods=['POST'])
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
def check_user_is_authenticate(request):
    """
    Checking whether user can be authenticated with passed in headers `token` or `username` with `password`
    """
    content = {'success': 'Credentials are correct'}
    if not isinstance(request.user, AnonymousUser):
        return Response(content, status=status.HTTP_202_ACCEPTED)
    else:
        return Response({'error': 'Credentials are wrong'}, status=status.HTTP_401_UNAUTHORIZED)


class PhotoUploadView(views.APIView):
    """
    Upload profile's photo
    """
    parser_classes = [parsers.MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(method='put', request_body=PhotoUploadSerializer)
    @action(detail=False, methods=['put'])
    def put(self, request, photo_name: str):
        photo_obj = request.data['photo']
        profile = Profile.objects.get(user=request.user)
        profile.photo.save(photo_name, photo_obj)  # save photo to DB
        return Response(status=status.HTTP_200_OK)

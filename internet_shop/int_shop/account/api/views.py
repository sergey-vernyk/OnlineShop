from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import viewsets, permissions, status, views, parsers
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from account.models import Profile
from . import serializers
from .permissions import IsTheSameUserThatMakeAction
from .tasks import send_email_for_set_new_account_password


class AccountSet(viewsets.ModelViewSet):
    """
    View allows obtaining all profiles, create, delete, update profile
    """
    queryset = Profile.objects.all()
    serializer_class = serializers.ProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [TokenAuthentication, BasicAuthentication]


class ResetUserAccountPasswordView(views.APIView):
    """
    API view allows to reset forgot user password and set new password
    """

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
        raise ValidationError('Credentials are wrong', code='authentication')


class FileUploadView(views.APIView):
    """
    View allows upload profile's photo
    """
    parser_classes = [parsers.FileUploadParser]
    permission_classes = [permissions.IsAuthenticated, IsTheSameUserThatMakeAction]

    def put(self, request, filename, instance_pk, format=None):
        file_obj = request.data['file']
        try:
            instance = get_object_or_404(Profile, pk=instance_pk)
            self.check_object_permissions(request, instance)
        except Http404:
            raise NotFound(f'Object with id {instance_pk} was not found')
        else:
            instance.photo.save(filename, file_obj)  # save photo to DB
            return Response(status=200)

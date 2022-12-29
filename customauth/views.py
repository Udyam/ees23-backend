
from rest_framework import serializers, generics, status
# from rest_framework.views import APIView
from rest_framework.response import Response
from .models import UserAcount
from rest_framework import permissions
# from django.conf import settings
# from django.http import HttpResponse
from django.http import HttpResponse
from django.http import Http404
from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError
from typing import Tuple
from udyamBackend.settings import CLIENT_ID
import requests
from django.core.mail import send_mail,EmailMultiAlternatives
from .models import BroadCast_Email
from django.shortcuts import render
from.models import BroadCast_Email
from.forms import PostForm
from django.http import HttpResponseRedirect
from django.contrib.auth import login, logout
from rest_framework.authtoken.models import Token

# from models import UserAccount
# from django.contrib.auth import login, logout
# from rest_framework.authtoken.models import Token


GOOGLE_ID_TOKEN_INFO_URL = 'https://oauth2.googleapis.com/tokeninfo'

def google_validate(*, id_token: str, email:str) -> bool:

    response = requests.get(
        GOOGLE_ID_TOKEN_INFO_URL,
        params={'id_token': id_token}
    )

    if not response.ok:
        raise ValidationError('Id token is invalid')

    audience = response.json()['aud']
    if audience != CLIENT_ID:
        raise ValidationError("Invalid Audience")

    if (response.json())["email"]!=email:
        raise ValidationError('Email mismatch')

    return True


def user_create(email, **extra_field) -> UserAcount:
    permission_classes = (permissions.IsAuthenticated,)
    extra_fields = {
        'is_staff': False,
        'is_active': True,
        **extra_field
    }

    print(extra_fields)

    user = UserAcount(email=email, **extra_fields)
    user.save()
    return user


def user_get_or_create(*, email: str, **extra_data) -> Tuple[UserAcount, bool]:
    # print(email)
    user = UserAcount.objects.filter(email=email).first()

    if user:
        return user, False
    # print(extra_data)
    return user_create(email=email, **extra_data), True

def user_get_me(*, user: UserAcount):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'message': "You have registeration is complete",
    }

# Custom
def broadcast_mail(request,subject,created):


    if request.method == "GET" and request.user.has_perm("view_broadcast_email"):
        message = BroadCast_Email.objects.get(subject=subject,created=created).message
        users = UserAcount.objects.all()
        list_email_user = [user.email for user in users]
        n = 100
        list_group = [
            list_email_user[i: i + n] for i in range(0, len(list_email_user), n)
        ]
        for group in list_group:
            email = EmailMessage(subject, message, bcc=group)
            email.content_subtype = "html"
            email.send()

        return HttpResponse("Mail sent successfully")
    return HttpResponse("Invalid request")


def index(request):
    
    subject = None
    created = None
    form = None
    if request.method == "POST" and request.user.has_perm("view_broadcast_email"):
        form = PostForm(request.POST)
        if form.is_valid():
            print(subject)
            form.save()
            subject=request.POST['subject']
            created=request.POST['created']
            # return HttpResponseRedirect('/thanks/')
    elif request.user.has_perm("view_broadcast_email"):

        form = PostForm()
    
    else :
        return HttpResponse("Invalid request")

    return render(request, 'index.html',{'form':form,'subject':subject,'created':created})


class UserInitApi(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        name = serializers.CharField(required=True)
        college_name = serializers.CharField(required=True)
        year = serializers.CharField(required=True)
        phone_number = serializers.CharField(required=True)
        serializer_class=InputSerializer

    def post(self, request, *args, **kwargs):
        # print(request.data)
        id_token = request.headers.get('Authorization')
        email = request.data.get("email")
        google_validate(id_token=id_token,email=email)

        if UserAcount.objects.filter(email=email).count()==0:
            serializer = self.InputSerializer(data=request.data)
            if not serializer.is_valid():
                error = {}
                for err in serializer.errors:
                    error[err] = serializer.errors[err][0]
                return Response(error, status=status.HTTP_409_CONFLICT)
            user, bool = user_get_or_create(**serializer.validated_data)
        
        token,_ = Token.objects.get_or_create(user = user)
        response = Response({"token" : token.key},data=user_get_me(user=UserAcount.objects.get(email=email)))
        
        return response
      
class LogoutView(generics.GenericAPIView):

    permission_classes = (permissions.IsAuthenticated)

    def get(self, request):
        request.user.auth_token.delete()
        logout(request)
        return Response(status=status.HTTP_200_OK)      
            


from django.urls import path
from .views import UserInitApi,broadcast_mail,index
from .admin import BroadCast_Email_Admin
urlpatterns = [
    path('google-login/', UserInitApi.as_view(), name='google-login'),
    path("broadcast/<subject>/<created>/", broadcast_mail, name="broadcast_mail"),
    path("broadcaster", index),
]

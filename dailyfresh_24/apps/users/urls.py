from django.conf.urls import url
from users import views

urlpatterns = [

    # url(r'^register$', views.register),
    url(r'^register$', views.RegisterView.as_view(), name='register'),

    url(r'^active/(?P<token>.+)$', views.ActiveView.as_view(), name='active'),

    url(r'^login', views.LoginView.as_view(), name='login'),
]
from django.conf.urls import url
from order import views


urlpatterns = [

    url(r'^place$', views.PlaceOrderView.as_view(), name='place'),

    url(r'^commit$', views.CommitOrderView.as_view(), name='commit'),
]
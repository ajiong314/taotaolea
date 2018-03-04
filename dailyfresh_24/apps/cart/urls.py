from django.conf.urls import url
from cart import views


urlpatterns = [

    url(r'^add$',views.AddCartViews.as_view(), name='add'),

    url(r'^$',views.AddCartViews.as_view(), name='info')
]

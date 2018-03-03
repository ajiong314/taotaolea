from django.conf.urls import url
from goods import views

urlpatterns = [

    url(r'^$',views.IndexView.as_view(), name='index'),

    url(r'^detail/(?P<sku_id>\d+)$',views.DetailView.as_view(), name='detail')

]
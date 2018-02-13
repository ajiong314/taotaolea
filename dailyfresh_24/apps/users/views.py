from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import View
from django.core.urlresolvers import reverse
import re
from users.models import User
from django import db
# Create your views here.


class RegisterView(View):

    def get(self,request):

        return render(request, 'register.html')

    def post(self,request):



        name = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')


        if  not all([name, pwd, email, allow]):

            return redirect(reversed('users:register'))


        if re.match(r'/^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$/', email):

            return render(request, 'register.html', {'errmsg': '邮箱格式错误'})

        if allow != 'on':

            return render(request, 'register.html', {'errmsg': '请勾选用户协议'})


        try:

            user = User.objects.create_user(name, email, pwd)

        except db.IntegrityError:

            return render(request, 'register.html', {'errmsg': '用户名已经注册'})


        user.is_active = False

        user.save()


        return HttpResponse('ceshi')

# def register(request):
#
#     # return HttpResponse('cs')
#
#     if request.method == 'GET':
#         return render(request, 'register.html')
#
#     if request.method == 'POST':
#
#         return HttpResponse('chuliqingqiu')

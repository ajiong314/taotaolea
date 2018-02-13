from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import View
from django.core.urlresolvers import reverse
import re
# Create your views here.


class RegisterView(View):

    def get(self,request):

        return render(request, 'register.html')

    def post(self,request):

        name = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        if all([name, pwd, email, allow]):

            return redirect(reversed('users:register'))

        if re.match(r'/^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$/', email):

            return render(request, 'register.html', {'errmsg': '邮箱格式错误'})

        if allow != 'on':

            return render(request, 'register.html', {'errmsg': '请勾选用户协议'})



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

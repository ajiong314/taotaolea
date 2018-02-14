from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import View
from django.core.urlresolvers import reverse
import re
from users.models import User
from django import db
from django.conf import settings
from celery_tasks.tasks import send_active_email
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
# Create your views here.

class LoginView(View):

    def get(self,request):
        return render(request, 'login.html')

    def post(self,request):

        pass


class ActiveView(View):

    def get(self, request, token):

        serializer = Serializer(settings.SECRET_KEY, 3600)

        try:

            result = serializer.load(token)

        except SignatureExpired:

            return HttpResponse('邮箱验证已经过期')

        user_id = result.get('confirm')

        try:

            user = User.objects.get(id = user_id)

        except User.DoesnotExit:

            return HttpResponse('用户不存在')

        user.is_active = True

        user.save()

        return HttpResponse('chenggong')


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

            # 新创建的用户名存到数据库 create-user就是专门用数据库新创建的

            user = User.objects.create_user(name, email, pwd)

        except db.IntegrityError:

            return render(request, 'register.html', {'errmsg': '用户名已经注册'})


        user.is_active = False

        user.save()

        token = user.generate_active_token()

        send_active_email.delay(email, name, token)



        # send_mail()
        # user 是通过models中的user类来创建的的对象，调用生成token的方法


        # # def send_active_email(email, name, token):
        # #     """封装发送邮件方法"""
        #
        #
        # from django.core.mail import send_mail
        # subject = "淘淘乐用户激活"  # 标题
        # body = ""  # 文本邮件体
        # sender = settings.EMAIL_FROM  # 发件人
        # receiver = [email]  # 接收人
        # html_body = '<h1>尊敬的用户 %s, 感谢您注册淘淘乐！</h1>' \
        #             '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
        #             'http://127.0.0.1:8000/users/active/%s</a></p>' % (name, token, token)
        # send_mail(subject, body, sender, receiver, html_message=html_body)


        # return HttpResponse('ceshi')
        return redirect(reverse('users:login'))

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

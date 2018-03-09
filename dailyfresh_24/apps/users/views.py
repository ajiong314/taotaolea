from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import View
from django.core.urlresolvers import reverse
import re
from users.models import User, Address
from django import db
from django.conf import settings
from celery_tasks.tasks import send_active_email
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.contrib.auth import authenticate,login,logout
from utils.view import LoginRequiredMixin
from django_redis import get_redis_connection
from goods.models import GoodsSKU

# Create your views here.


class UserInfoView(LoginRequiredMixin,View):

    def get(self, request):
        # 拿到用户
        user = request.user
        # 查找地址信息,如果为空会出现异常
        try:

            address = Address.objects.filter(user=user).order_by("-create_time")[0]

        except Address.DoesNotExist:

            address = None

        # 查询最近浏览的商品
        redis_conn = get_redis_connection('default')

        sku_ids = redis_conn.lrange('history_%s' % user.id, 0, 4)
        sku_list = []
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            sku_list.append(sku)
        # 构造上下文
        context ={
            'address':address,
            'sku_list': sku_list
        }
        # 渲染模板

        return render(request, 'user_center_info.html', context)


class AddressView(LoginRequiredMixin, View):

    def get(self,request):
        # 获取登陆的用户名
        user = request.user
        # 查找相应的地址信息
        # address = Address.objects.filter(user=user).order_by('-create_time')[0]
        # address = user.address_set.order_by('-create_time')[0]
        # latest默认倒序排列
        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None

        # 构造上下文
        context = {

            'user':user,
            'address': address
        }
        # 渲染模板

        # if not request.user.is_authenticated():
        #     return redirect(reverse("users:login"))
        # else:
        return render(request, 'user_center_site.html',context)

    def post(self,request):

        # 接收数据
        recv_name = request.POST.get('recv_name')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        recv_mobile = request.POST.get('recv_mobile')

        # 分析数据
        if all([recv_name, addr, zip_code, recv_mobile]):
            Address.objects.create(
                user=request.user,
                receiver_name = recv_name,
                receiver_mobile = recv_mobile,
                detail_addr = addr,
                zip_code = zip_code
            )
        # 保存数据

        return redirect(reverse('users:address'))



class LogoutView(View):

    def get(self,request):

        logout(request)

        return redirect(reverse('users:login'))
        # return redirect(reverse('goods:index'))


class LoginView(View):


    def get(self,request):

        return render(request, 'login.html')


    def post(self,request):


        name = request.POST.get('username')

        pwd = request.POST.get('pwd')

        if not all([name, pwd]):

            return render(request, 'login.html')

        user = authenticate(username = name, password = pwd)

        if user is None:

            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})

        if user.is_active == False:


            return render(request, 'login.html', {'errmsg': '用户未激活'})

        login(request, user)

        remembered = request.POST.get('remembered')

        if remembered != 'on':

            request.session.set_expiry(0)

        else:

            request.session.set_expiry(60*60*24*10)

            # 在界面跳转之前,将cookie中的购物车信息合并到redis
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                # 从cookie中得到的购物车字典,key是string,value是int
                cart_dict_cookie = json.loads(cart_json)
            else:
                cart_dict_cookie = {}

            # 查询redis中的购物车信息
            redis_conn = get_redis_connection('default')
            # 通过django_redis从redis中读取的购物车字典,key和value都是bytes类型的
            cart_dict_redis = redis_conn.hgetall('cart_%s' % user.id)

            # 遍历cart_dict_cookie,取出其中的sku_id和count信息,存储到redis
            for sku_id, count in cart_dict_cookie.items():

                # 将string转bytes
                # 提醒 : 在做计算和比较时,需要记住类型统一
                sku_id = sku_id.encode()
                if sku_id in cart_dict_redis:
                    origin_count = cart_dict_redis[sku_id]
                    count += int(origin_count)

                    # 在这里合并有可能造成库存不足
                    # sku = GoodsSKU.objects.get(id=sku_id)
                    # if count > sku.stock:
                    # pass # 具体如何处理,只要不影响登录的正常流程即可

                # 保存合并的数据到redis
                cart_dict_redis[sku_id] = count

            # 一次性向redis中新增多条记录
            if cart_dict_redis:
                redis_conn.hmset('cart_%s' % user.id, cart_dict_redis)


                # 在界面跳转以前,需要判断登录之后跳转的地方.如果有next就跳转到next指向的地方,反之,跳转到主页
                # http://127.0.0.1:8000/users/login?next=/users/info

        next = request.GET.get('next')
        # print(next)

        if next is None:

            response = redirect(reverse('goods:index'))
        else:
            if next == '/order/place':
                response = redirect(reverse('cart:info'))
            else:
                response = redirect(next)

        response.delete_cookie('cart')
        return response



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

        return redirect(reversed('goods:index'))


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
        return redirect(reverse('goods:index'))

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

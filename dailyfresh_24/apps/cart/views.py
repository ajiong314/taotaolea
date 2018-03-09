from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from goods.models import GoodsSKU
from django_redis import get_redis_connection
import json
# Create your views here.
class DeleteCartView(View):

    def post(self,request):
        """删除购物车记录:一次删除一条"""

        def post(self, request):

            # 接收参数：sku_id

            sku_id = request.POST.get('sku_id')
            # 校验参数：not，判断是否为空

            if not sku_id:
                return JsonResponse({'code':1, 'message':'sku_id为空'})

            # 判断sku_id是否合法
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesnotExit:
                return JsonResponse({'code':2 , 'message': '商品不存在'})

            # 判断用户是否登录
            if request.user.is_authenticated():

                # 如果用户登陆，删除redis中购物车数据
                redis_conn = get_redis_connection('default')
                user_id = request.user.id
                redis_conn.hdel('cart_%s' % user_id, sku_id)


            # 如果用户未登陆，删除cookie中购物车数据
            else:
                    # 删除字典中某个key及对应的内容
                cart_json = request.COOKIES.get('cart')
                if cart_json is not None:
                    cart_dict = json.load(cart_json)
                    del cart_dict[sku_id]
                    new_cart_json = json.dump(cart_dict)
                # else:
                #     cart_dict = {}
                response = JsonResponse({'code': 0, 'message': '删除成功'})
                    # 删除结果写入cookie
                response.set_cookie('cart',new_cart_json)

                return response
            return JsonResponse({'code': 0, 'message': '删除成功'})


class UpdateCartView(View):

    def post(self, request):

        """+ - 手动输入"""

        # 获取参数：sku_id, count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验参数all()
        if not all([sku_id,count]):

            return JsonResponse({'code':1 , 'message':'参数不对'})

        # 判断商品是否存在
        try:

            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesnotExit:
            return JsonResponse({'code':2, 'message':'商品不存在'})


        # 判断count是否是整数
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code':3, 'message':'商品数量不对'})


        # 判断库存
        if count > sku.stock:
            return JsonResponse({'code':4, 'message':'商品库存不足'})

        # 判断用户是否登陆
        if request.user.is_authenticated():

            # 如果用户登陆，将修改的购物车数据存储到redis中
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            # 因为我们设计的接口是幂等的风格.传入的count就是用户最后要记录的商品的数量
            redis_conn.hset('cart_%s' % user_id, sku_id, count)
            return JsonResponse({'code': 3, 'message': '商品数量不对'})



        else:
            # 如果用户未登陆，将修改的购物车数据存储到cookie中
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                cart_dict = json.load(cart_json)
            else:
                cart_dict = {}
            # 因为我们设计的接口是幂等的风格.传入的count就是用户最后要记录的商品的数量
            cart_dict[sku_id] = count

            # 把cart_dict转成最新的json字符串
            new_cart_json = json.dump(cart_dict)

            # 更新cookie中的购物车信息

            response = JsonResponse({'code': 0, 'message': '更新购物车成功'})
            response.set_cookie('cart', new_cart_json)
            return response


class CartInfoView(View):

    def get(self,request):

        if request.user.is_authenticated():

            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            cart_dict = redis_conn.hgetall('cart_%s' % user_id)

        else:

            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                cart_dict = json.load(cart_json)
            else:
                cart_dict = {}
        skus = []
        total_sku_amount = 0
        total_count = 0
        for sku_id,count in cart_dict.items():

            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except Exception:
                continue

            count = int(count)

            amount = count * sku.price

            sku.count = count
            sku.amount = amount

            skus.append(sku)

            total_sku_amount += amount
            total_count += count

        context = {
            'skus':skus,
            'total_sku_amount': total_sku_amount,
            'total_count':total_count
        }

        return render(request, 'cart.html', context)




class AddCartView(View):


    def post(self,request):

# 接受购物车参数, 校验购物车参数, 保存购物车参数

        # 判断用户是否登录
        # if not request.user.is_authenticated():
        #
        #     return JsonResponse({'code':1, 'message':'用户未登录'})


        # 接受购物车参数 : sku_id, count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验参数 : all()
        if not all([sku_id, count]):
            return JsonResponse({'code':2, 'message':'缺少参数'})


        # 判断sku_id是否合法
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesnotExit:
            return JsonResponse({'code':3, 'message':'商品不存在'})


        # 判断count是否合法
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code': 4, 'message': '商品数量不对'})

        # 判断库存是否超出
        if count > sku.stock:
            return JsonResponse({'code':5, 'message':'商品库存不足'})
        # 获取user_id

        if request.user.is_authenticated():

            user_id = request.user.id

            # 保存购物车数据到Redis
            redis_conn = get_redis_connection('default')
            # 需要查询要保存到购物车的商品数据是否存在,如果存在,需要累加,反之,赋新值
            origin_count = redis_conn.hget('cart_%s' % user_id, sku_id )
            if origin_count is not None:
                count += int(origin_count)

            # 再次:判断库存是否超出,拿着最终的结果和库存比较
            if count > sku.stock:

                return JsonResponse({'code': 5, 'message': '商品库存不足'})

            redis_conn.hset('cart_%s' % user_id,sku_id,count)

            # 查询购物车中的商品数量,响应给前端
            cart_num = 0
            cart_dict = redis_conn.hgetall('cart_%s' % user_id)
            for val in cart_dict.values():
                cart_num += int(val)

            return JsonResponse({'code':1, 'message':'添加购物车成功', 'cart_num': cart_num})


        # 响应结果

        else:
            # 用户未登录,保存购物车数据到cookie {sku_id:count}
            # 读取cookie中的购物车数据
            cart_json = request.COOKIES.get('cart')
                # 把cart_json转成字典 : loads 将json字符串转成json字典
            if cart_json is not None:
                cart_dict = json.load(cart_json)
            else:
                cart_dict ={}

                 # 为了后面继续很方便的操作购物车数据,这里定义空的字典对象

            # 判断要存储的商品信息,是否已经存在.如果已经存在就累加.反之,赋新值
            # 提醒 : 需要保证 sku_id和cart_dict里面的key的类型一致;此处的正好一致
            if sku_id in cart_dict:

                origin_count = cart_dict[sku_id]
                count += origin_count

                 # origin_count : 在json模块中,数据类型不变


            # 再再次:判断库存是否超出,拿着最终的结果和库存比较
            if count > sku.stock:
                return JsonResponse({'code':1, 'message':'超出库存'})


            # 把最新的商品的数量,赋值保存到购物车字典
            cart_dict[sku_id] = count


            # 在写入cookie之前,将cart_dict转成json字符串

            new_cart_json = json.dump(cart_dict)
            # 为了方便前端展示最新的购物车数量,后端添加购物车成功后,需要查询购物车
            cart_num = 0
            for val in new_cart_json.values():
                cart_num += val
               # val 是json模块运作的,存储的市数字,读取的也是数字

            # 创建response
            response = JsonResponse({'code':1, 'message':'添加成功', 'cart_num':cart_num})


            # 写入cookie
            response.set_cookie('cart', new_cart_json)
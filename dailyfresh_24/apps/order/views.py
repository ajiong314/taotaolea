from django.shortcuts import render,redirect
from django.views.generic import View
from utils.view import LoginRequiredMixin
import json
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from users.models import Address
from django.core.urlresolvers import reverse
# Create your views here.


class PlaceOrderView(LoginRequiredMixin,View):

    def post(self,request):
        """订单确认"""

        def post(self, request):
            """购物车去结算和详情页立即购买进入订单确认页main"""
            # 判断用户是否登陆：LoginRequiredMixin

            # 获取参数：sku_ids, count
            sku_ids = request.POST.getlist('sku_ids')
            count = request.POST.get('count')
            # 校验sku_ids参数：not
            if not sku_ids:
                return redirect(reverse('cart:info'))

            # 定义临时变量
            total_count = 0
            total_sku_amount = 0
            skus = []
            trans_cost = 10# 邮费
            if count is None:
            # 校验count参数：用于区分用户从哪儿进入订单确认页面

                # 如果是从购物车页面的去结算过来

                # 商品的数量从redis中获取
                redis_conn = get_redis_connection('default')
                user_id = request.user.id

                # cart_dict 里面的key和value是bytes
                cart_dict = redis_conn.hgetall('cart_%s' % user_id)

                # 查询商品数据 sku <- sku_id <- sku_ids
                # 提醒 : sku_id 是 string 字符串
                for sku_id in sku_ids:



                    # 查询商品信息
                    try:
                        sku = GoodSKU.objects.get(id=sku_id)
                    except GoodSKU.DoesnotExit:
                        return redirect(reverse('cart:info'))


                # 得到商品数量 : sku_count 默认是bytes
                    sku_count = cart_dict[sku_id.encode()]
                    sku_count = int(sku_count)
                    # 计算小计
                    sku_amount = sku_count*sku.price

                    # 动态的给sku对象绑定count 和 amount
                    sku.count = sku_count
                    sku.amount = sku_amount

                    # 记录sku
                    skus.append(sku)

                    # 累加总数量和总金额
                    total_count += sku_count
                    total_sku_amount += sku_amount

            else:
                # 如果是从详情页面的立即购买过来

                # 查询商品数据

                # 商品的数量从request中获取,并try校验

                # 判断库存：立即购买没有判断库存
                pass

            # 计算实付款 = 总金额 + 邮费
            total_amount = total_sku_amount + trans_cost
            # 查询用户地址信息
            try:
                address = Address.objects.filter(user=request.user).latest('create_time')
            except Address.DoesnotExit:
                address = None

            # 构造上下文
            context = {
                'skus': skus,
                'total_count': total_count,
                'total_sku_amount': total_sku_amount,
                'trans_cost': trans_cost,
                'total_amount': total_amount,
                'address': address


            }

            # 响应结果:html页面
            return render(request, 'place_order.html', context)

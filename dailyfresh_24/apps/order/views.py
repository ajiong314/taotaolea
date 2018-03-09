from django.shortcuts import render,redirect
from django.views.generic import View
from utils.view import LoginRequiredMixin,LoginRequiredJSONMixin
import json
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from users.models import Address
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from order.models import OrderInfo, OrderGoods

# Create your views here.
# class CommitOrderView():
#
#     def post(self,request):
#         # 获取参数：user,address_id,pay_method,sku_ids,
#         user = request.user
#         address_id = request.POST.get('address_id')
#         pay_method = request.POST.get('pay_method')
#         sku_ids = request.POST.get('sku_ids')
#
#
#         # 校验参数：all([address_id, pay_method, sku_ids])
#         if not all([address_id,pay_method,sku_ids]):
#             return JsonResponse({'code':2, 'message':'缺少参数'})
#
#         # 判断地址
#         try:
#             address = Address.objects.filter(id=address_id)
#         except Address.DoesnotExit:
#             return JsonResponse({{'code': 3, 'message': '地址错误'}})
#
#         # 判断支付方式
#         if pay_method not in OrderInfo.PAY_METHODS
#             return JsonResponse({'code': 4, 'message': '支付方式错误'})
#         # 截取出sku_ids列表
#         sku_ids = sku_ids.split(',')
#
#         redis_conn = get_redis_connection('default')
#         # 遍历sku_ids
#         for sku_id in sku_ids:
#
#         # 循环取出sku，判断商品是否存在
#             try:
#                 sku = GoodsSKU.objects.get(id=sku_id)
#             except GoodsSKU.DoesNotExist:
#                 # 异常,回滚
#                 return JsonResponse({'code': 5, 'message': '商品不存在'})
#         # 获取商品数量，判断库存 (redis)
#         sku_count = redis_conn.hget('cart_%s' % user.id, sku_id)
#         sku_count = int(sku_count)
#         if sku_count > sku.stock:
#             return JsonResponse({'code': 6, 'message': '库存不足'})
#
#         # 计算小计
#         amount = sku_count * sku.price
#         # 减少sku库存
#         sku.stock -= sku_count
#
#         # 增加sku销量
#         sku.sales += sku_count
#         sku.save()
#
#         # 保存订单商品数据OrderGoods(能执行到这里说明无异常)
#         # 先创建商品订单信息
#
#         # 计算总数和总金额
#
#         # 修改订单信息里面的总数和总金额(OrderInfo)
#
#         # 订单生成后删除购物车(hdel)
#
#         # 响应结果
#         pass



class PlaceOrderView(LoginRequiredMixin,View):


    def post(self, request):
        """购物车去结算和详情页立即购买进入订单确认页main"""
        # 判断用户是否登陆：LoginRequiredMixin
        # 获取参数：sku_ids, count
        sku_ids = request.POST.getlist('sku_ids')
        count = request.POST.get('count')
        # 校验sku_ids参数：not
        if not sku_ids:
            return redirect(reverse('cart:info'))
        redis_conn = get_redis_connection('default')
        user_id = request.user.id
        # 定义临时变量
        total_count = 0
        total_sku_amount = 0
        skus = []
        trans_cost = 10# 邮费

        if count is None:
        # 校验count参数：用于区分用户从哪儿进入订单确认页面

            # 如果是从购物车页面的去结算过来

            # 商品的数量从redis中获取



            # cart_dict 里面的key和value是bytes
            cart_dict = redis_conn.hgetall('cart_%s' % user_id)

            # 查询商品数据 sku <- sku_id <- sku_ids
            # 提醒 : sku_id 是 string 字符串
            for sku_id in sku_ids:



                # 查询商品信息
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesnotExit:
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
            for sku_id in sku_ids:
                try:

                    sku = GoodsSKU.objects.get(id = sku_id)
                except GoodsSKU.DoesnotExist:
                    return redirect(reverse('goods:index'))

            # 商品的数量从request中获取,并try校验
            try:
                sku_count = int(count)
            except Exception:
                return redirect(reverse('goods:detail', args=(sku_id,)))

            # 判断库存：立即购买没有判断库存
            if sku_count > sku.stock:
                return redirect(reverse('goods:detail', args=(sku_id,)))
            # 小计
            amount = sku_count * sku.price
            # 动态给sku绑定sku-count和amount
            sku.count = sku_count
            sku.amount = sku.amount
            # 记录sku
            skus.append(sku)
            # 累加总数量和总付款
            total_count += sku_count
            total_sku_amount += amount
        # 将sku_id和count写入到redis购物车,方便提交订单时,直接从redis中读取,而不会再次判断count的来源
            redis_conn.hset('cart_%s' % sku_id, sku_id, sku_count)
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
            'address': address,
            'sku_ids': ','.join(sku_ids)


        }

        # 响应结果:html页面
        return render(request, 'place_order.html', context)

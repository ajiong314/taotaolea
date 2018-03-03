from django.shortcuts import render,redirect
from django.views.generic import View
from goods.models import GoodsCategory, Goods, GoodsSKU, GoodsImage, IndexGoodsBanner, IndexCategoryGoodsBanner, IndexPromotionBanner
from django.core.cache import cache
from django_redis import  get_redis_connection
from django.core.urlresolvers import reverse

# Create your views here.
class DetailView(View):


    def get(self, request, sku_id):

        """查询详情页数据,渲染模板"""

        # 查询商品SKU信息
        try:

            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesnotExit:
            return redirect(reverse('goods:index'))


        # 查询商品分类信息
        categorys = GoodsCategory.objects.all()

        # 查询商品评价信息:从订单中获取评论信息
        sku_orders = sku.ordergoods_set.all().order_by('-create_time')[:30]
        if sku_orders:
            for sku_order in sku_orders:
                sku_order.ctime = sku_order.create_time.strftime('%Y-%m-%d %H:%M:%S')
                sku_order.username = sku_order.order.user.username
        else:
            sku_orders = []

        # 查询最新推荐信息:从数据库中获取最新发布的两件商品
        new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('create_time')

        # 查询其他规格商品信息:exclude()  500g草莓 盒装草莓

        other_skus = sku.goods.goodssku_set.exclude(id=sku_id)
        """
        sku = 500g草莓
        sku.goods = 草莓
        sku.goods.goodssku_set = 500g草莓 盒装草莓 1000g草莓
        sku.goods.goodssku_set.exclude(id=500g草莓_id)
        """

        # 查询购物车信息

        cart_num = 0
        # 如果是登录用户,读取购物车数据
        if request.user.is_authenticated():
            # 创建连接到redis的对象
            redis_conn = get_redis_connection('default')

            # 调用hgetall(), 读取所有的购物车数据
            user_id = request.user.id
            cart_dict = redis_conn.hgetall('cart_%s' % user_id)

            # 遍历cart_dict,取出数量,累加求和
            # 说明:hgetall()返回的字典,里面的key和value是字节类型(bytes)的,所以在计算和比较时需要对类型进行处理
            for val in cart_dict.values():
                cart_num += int(val)



            # 删除重复的sku_id
            redis_conn.lrem('history_%s' % user_id, 0, sku_id)
            # 记录浏览信息
            redis_conn.lpush('history_%s' % user_id, sku_id)
            # 最多保存五条记录
            redis_conn.ltrim('history_%s' % user_id, 0, 4)

        # 构造上下文
        context = {
            'sku': sku,
            'categorys': categorys,
            'sku_orders': sku_orders,
            'new_skus': new_skus,
            'other_skus': other_skus,
            'cart_num': cart_num
        }

        # 渲染模板
        return render(request, 'detail.html', context)



class IndexView(View):

    def get(self, request):

        # 读取缓存数据
        context = cache.get('index_page_data')
        # 对缓存数据进行判断分为两种情况，一种是数据为空的情况，另一种是数据存在的情况,还分为登录用户和文登陆用户，上面这个if是
        # 两种情况的抽离
        if context is None:
       # 查询用户user信息:在request中
                # 查询商品分类信息
            goodscategorys = GoodsCategory.objects.all()

            # 查询图片轮播信息:需求,根据index从小到大排序
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')


            # 查询商品活动信息:需求,根据index从小到大排序
            promotionbanners = IndexPromotionBanner.objects.all().order_by('index')

            # 查询主页分类商品列表信息
            for category in goodscategorys:
                titlebanners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type = 0)
                category.titlebanners = titlebanners

                imagebanners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1)
                category.imagebanners = imagebanners
            # 查询购物车信息

            # 构造上下文
            context = {
                'goodscategorys':goodscategorys,
                'goods_banners':goods_banners,
                'promotionbanners':promotionbanners,
            }

            # 缓存上下文: 缓存的key   要缓存的数据   过期的秒数
            # 说明 : 存储的类型和读取后的类型一致.存进去的是什么,读取的也是什么.但是.存储在redis中时是字符串
            # context_dict  存-->  string   读-->  context_dict
            cache.set('index_page_data', context, 3600)

        cart_num = 0

        if request.user.is_authenticated():
        #     创建redis对象
            redis_conn = get_redis_connection("default")

        #     读取数据,拿出所有数据局
        #     先得到用户的id信息,根据用户的id信息查询出对应的cart——num信息
            user_id = request.user.id
            cart_dict = redis_conn.hgetall('cart_%s' % user_id)

        # 遍历字典，得到数量
            for val in cart_dict.values():

                cart_num += int(val)
        # 更新购物和数据
            context.update(cart_num = cart_num)
        # 渲染模板
        return render(request, 'index.html', context)


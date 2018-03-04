from django.shortcuts import render,redirect
from django.views.generic import View
from goods.models import GoodsCategory, Goods, GoodsSKU, GoodsImage, IndexGoodsBanner, IndexCategoryGoodsBanner, IndexPromotionBanner
from django.core.cache import cache
from django_redis import  get_redis_connection
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator,EmptyPage
import json

# Create your views here.


class BaseCartView(View):

    def get_cart_num(self,request):
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

        else:
            cart_json = request.COOKIES.get('cart')

            if cart_json is not None:
                cart_dict =json.load(cart_json)

            else:
                cart_dict = {}

            for val in cart_dict.values():

                cart_num += val

        return  cart_num



class ListView(BaseCartView):

    def get(self, request, category_id, page_num):

        sort = request.GET.get('sort', 'default')

        # 查询商品分类，category_id对应的
        try:

            category = GoodsCategory.objects.get(id = category_id)
        except Goods.DoesnotException:
            return redirect(reverse('user:index'))
        # 查询所有商品的分类
        categorys = GoodsCategory.objects.all()

        # 查询新品推荐
        new_SKUS = GoodsSKU.objects.filter(category=category).order_by('-create_time')[:2]

        # 查询商品分类category_id对应的SKU信息并且排序
        if sort == 'price':
            skus = GoodsCategory.objects.filter(category=category).order_by('price')

        elif sort == 'hot':
            skus = GoodsCategory.objects.filter(category=category).order_by('-sales')

        else:

            skus = GoodsCategory.objects.filter(category=category)
            sort = 'default'

        # 查询购物车信
        cart_num = self.get_cart_num(request)
        # 如果是登录用户,读取购物车数据

        # 查询分页数据 paginator page
        # paginator = [GoodsSKU, GoodsSKU, GoodsSKU, GoodsSKU, GoodsSKU, ...]
        # paginator 的两个参数分别是 查寻出来的一个列表 ， 每一页展示几条内容
        paginator = paginator(skus, 2)

        # 获取用户要看的那一页 page_skus = [GoodsSKU, GoodsSKU]
        # 根据从网页接受的参数判断用户要看那一夜
        page_num = int(page_num)
        try:
            page_skus = paginator.page(page_num)
        except:
            page_skus = paginator.page(1)    #如果出现错误的话就给默认成第一页

        # 获取页码列表
        page_list = paginator.page_range

        # 构造上下文
        context ={
            'category':category,
            'categorys':categorys,
            'new_SKUS':new_SKUS,
            'skus':skus,
            'page_list':page_list,
            'sort':sort,
            'page_skus': page_skus,
            'cart_num': cart_num
        }

        return render(request,'list.html', context)


class DetailView(BaseCartView):


    def get(self, request, sku_id):
        print(1111)

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

        cart_num = self.get_cart_num(request)
        # 如果是登录用户,读取购物车数据
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
        print(666)

        # 渲染模板
        return render(request, 'detail.html', context)



class IndexView(BaseCartView):

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

        cart_num = self.get_cart_num(request)


        # 更新购物和数据
        context.update(cart_num = cart_num)
        # 渲染模板
        return render(request, 'index.html', context)


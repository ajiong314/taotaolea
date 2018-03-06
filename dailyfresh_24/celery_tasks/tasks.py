import os
os.environ["DJANGO_SETTINGS_MODULE"] = "dailyfresh_24.settings"
# 放到Celery服务器上时添加的代码
import django
django.setup()

from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from goods.models import GoodsCategory, Goods, GoodsSKU, GoodsImage, IndexGoodsBanner, IndexCategoryGoodsBanner, IndexPromotionBanner


# 第一个参数制定路径，第二个参数制定redis数据库

app = Celery('celery_tasks.tasks',broker='redis://192.168.182.129:6379/4')


@app.task
def send_active_email(to_email, name, token):
        #     """封装发送邮件方法"""
        subject = "天天生鲜用户激活"  # 标题
        body = ""  # 文本邮件体
        sender = settings.EMAIL_FROM  # 发件人
        receiver = [to_email]  # 接收人
        html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                    '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                    'http://127.0.0.1:8000/users/active/%s</a></p>' % (name, token, token)
        send_mail(subject, body, sender, receiver, html_message=html_body)


@app.task
def generate_static_index_html():
    # 查询商品分类信息
    goodscategorys = GoodsCategory.objects.all()

    # 查询图片轮播信息:需求,根据index从小到大排序
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 查询商品活动信息:需求,根据index从小到大排序
    promotionbanners = IndexPromotionBanner.objects.all().order_by('index')

    # 查询主页分类商品列表信息
    for category in goodscategorys:
        titlebanners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0)
        category.titlebanners = titlebanners

        imagebanners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1)
        category.imagebanners = imagebanners
    # 查询购物车信息

    cart_num = 0
    # 构造上下文
    context = {
        'goodscategorys': goodscategorys,
        'goods_banners': goods_banners,
        'promotionbanners': promotionbanners,
        'cart_num': cart_num

    }

    template = loader.get_template('static_index.html')

    html_data = template.render(context)

    # 渲染模

    path = os.path.join(settings.STATICFILES_DIRS[0], 'static_index.html')

    with open(path, 'w') as file:

        file.write(html_data)


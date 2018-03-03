from django.contrib import admin
from goods.models import GoodsCategory, Goods, GoodsSKU, GoodsImage, IndexGoodsBanner, IndexCategoryGoodsBanner, IndexPromotionBanner
from celery_tasks.tasks import generate_static_index_html
from django.core.cache import cache

# Register your models here.

class BaseAdmin(admin.ModelAdmin):


    def save_model(self, request, obj, form, change):
        obj.save()
        generate_static_index_html.delay()
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        obj.delete()
        generate_static_index_html.delay()
        cache.delete('index_page_data')




class IndexPromotionBannerAdmin(BaseAdmin):


    pass

class GoodsAdmin(BaseAdmin):


    pass

class GoodsSKUAdmin(BaseAdmin):


    pass



admin.site.register(GoodsCategory)
admin.site.register(Goods, GoodsAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(GoodsImage)
admin.site.register(IndexGoodsBanner, )
admin.site.register(IndexCategoryGoodsBanner)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)

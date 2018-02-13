from django.db import models

class BaseModel(models.Model):

    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True,verbose_name='更新时间')

    class Meta:
        # 当做抽象类不单独迁移
        abstract = True
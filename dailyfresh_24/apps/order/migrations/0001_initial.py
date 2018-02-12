# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrderGoods',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('count', models.IntegerField(verbose_name='数量', default=1)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='单价')),
                ('comment', models.TextField(verbose_name='评价信息', default='')),
            ],
            options={
                'db_table': 'df_order_goods',
            },
        ),
        migrations.CreateModel(
            name='OrderInfo',
            fields=[
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('order_id', models.CharField(primary_key=True, serialize=False, verbose_name='订单号', max_length=64)),
                ('total_count', models.IntegerField(verbose_name='商品总数', default=1)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='商品总金额')),
                ('trans_cost', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='运费')),
                ('pay_method', models.SmallIntegerField(verbose_name='支付方式', choices=[(1, '货到付款'), (2, '支付宝')], default=1)),
                ('status', models.SmallIntegerField(verbose_name='订单状态', choices=[(1, '待支付'), (2, '待发货'), (3, '待收货'), (4, '待评价'), (5, '已完成')], default=1)),
                ('trade_id', models.CharField(null=True, blank=True, unique=True, verbose_name='支付编号', max_length=100)),
            ],
            options={
                'db_table': 'df_order_info',
            },
        ),
    ]

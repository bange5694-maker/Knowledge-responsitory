# LZH: 模块功能：servermanager 的路由配置，把微信公众号机器人的回调地址挂到 Django 路由上。

from django.urls import path
from werobot.contrib.django import make_view

from .robot import robot

# LZH: 应用命名空间：用于 reverse('servermanager:...') 反向解析。
app_name = "servermanager"
urlpatterns = [
    # LZH: 微信公众平台服务器配置中的 URL 指向 /robot；
    # LZH: make_view(robot) 把 WeRoBot 实例包装成 Django 视图，由它完成签名校验与消息分发。
    path(r'robot', make_view(robot)),

]

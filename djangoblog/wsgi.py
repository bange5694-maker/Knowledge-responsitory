# DH: 这个文件是给正式部署用的入口，服务器通过它来启动 Django 网站。

"""
WSGI config for djangoblog project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# DH: 告诉 Django 用哪个配置文件，这里是 djangoblog/settings.py。
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoblog.settings")

# DH: 真正被服务器调用的对象，名字固定叫 application。
application = get_wsgi_application()

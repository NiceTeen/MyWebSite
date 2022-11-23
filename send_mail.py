#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from django.core.mail import send_mail

os.environ["DJANGO_SETTINGS_MODULE"] = "MyWebSite.settings"

if __name__ == '__main__':
    send_mail(
        "来自www.xu.com的注册邮件",
        "欢迎注册www.xu.com，本邮件仅用于测试。",
        "15058455670@163.com",
        ["1549311473@qq.com"]
    )
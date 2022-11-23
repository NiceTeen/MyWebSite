#!/usr/bin/env python
# -*- coding: utf-8 -*-
import hashlib
import datetime
from django.conf import settings

from django.shortcuts import render
from django.shortcuts import redirect

from . import models
from . import forms


def index(request):
    if not request.session.get("is_login", None):
        return redirect("/login/")
    return render(request, 'login/index.html')


def login(request):
    if request.session.get("is_login", None):
        return redirect('/index/')
    if request.method == "POST":
        login_form = forms.UserForm(request.POST)
        message = "请检查填写内容"
        if login_form.is_valid():
            username = login_form.cleaned_data.get("username")
            password = login_form.cleaned_data.get("password")
            if username.strip() and password:
                try:
                    user = models.User.objects.get(name=username)
                except:
                    message = "用户名不存在"
                    return render(request, 'login/login.html', locals())

                if not user.has_confirmed:
                    message = "您还未进行邮件确认，请确认后再登录"
                    return render(request, "login/login.html", locals())

                if user.password == hash_code(password):
                    request.session["is_login"] = True
                    request.session["user_id"] = user.id
                    request.session["user_name"] = user.name
                    return redirect("/index/")
                else:
                    message = "密码错误"
                    return render(request, 'login/login.html', locals())
        else:
            return render(request, 'login/login.html', locals())
    login_form = forms.UserForm()
    return render(request, 'login/login.html', locals())


def register(request):
    if request.session.get("is_login", None):
        return redirect("/index/")
    if request.method == "POST":
        register_form = forms.RegisterForm(request.POST)
        message = "请检查填写内容"
        if register_form.is_valid():
            username = register_form.cleaned_data.get("username")
            password1 = register_form.cleaned_data.get("password1")
            password2 = register_form.cleaned_data.get("password2")
            email = register_form.cleaned_data.get("email")
            sex = register_form.cleaned_data.get("sex")

            if password1 != password2:
                message = "两次输入的密码不一致，请检查"
                return render(request, "login/register.html", locals())
            else:
                same_name_user = models.User.objects.filter(name=username)
                if same_name_user:
                    message = "用户名已经存在"
                    return render(request, "login/register.html", locals())
                same_email = models.User.objects.filter(email=email)
                if same_email:
                    message = "该邮箱已被注册"
                    return render(request, "login/register.html", locals())

                new_user = models.User()
                new_user.name = username
                new_user.password = hash_code(password1)
                new_user.email = email
                new_user.sex = sex
                new_user.save()

                code = make_confirm_string(new_user)
                send_email(email, code)
                return redirect("/login/")
        else:
            return render(request, "login/register.html", locals())
    else:
        register_form = forms.RegisterForm()
    return render(request, 'login/register.html', locals())


def logout(request):
    if not request.session.get("is_login", None):
        return redirect("/login/")
    request.session.flush()
    return redirect("/login/")


def user_confirm(request):
    code = request.GET.get("code", None)
    message = ""
    try:
        confirm = models.ConfirmString.objects.get(code=code)
    except:
        message = "无效的确认事件"
        return render(request, 'login/confirm.html', locals())

    c_time = confirm.c_time
    now = datetime.datetime.now()
    if now > c_time + datetime.timedelta(settings.CONFIRM_DAYS):
        confirm.user.delete()
        message = "您的邮件在%d天内未确认，已过期，请重新注册" %settings.CONFIRM_DAYS
        return render(request, "login/confirm.html", locals())
    else:
        confirm.user.has_confirmed = True
        confirm.user.save()
        confirm.delete()
        message = "邮件已确认，欢迎登录"
        return render(request, "login/confirm.html", locals())


def hash_code(s, salt="mywebsite"):
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())
    return h.hexdigest()


def make_confirm_string(user):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.name, now)
    models.ConfirmString.objects.create(code=code, user=user)
    return code


def send_email(email, code):
    from django.core.mail import EmailMultiAlternatives

    subject = "来自www.XU.com的注册确认邮件"
    text_context = "欢迎注册www.XU.com， 若您看到本条消息，说明您的邮箱服务器不提供HTML链接功能，请联系管理员或更换邮箱注册。"
    html_context = '''
                    <p>欢迎注册<a href="http://{}/confirm/?code={}" target=blank>www.XU.com</a></p>
                    <p>请点击站点链接完成注册确认！</p>
                    <p>此链接有效期为{}天！</p>
                    '''.format("127.0.0.1:8000", code, settings.CONFIRM_DAYS)
    msg = EmailMultiAlternatives(subject, text_context, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_context, "text/html")
    msg.send()


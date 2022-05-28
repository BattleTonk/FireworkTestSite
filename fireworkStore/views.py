from django.shortcuts import render
import smtplib
import hashlib
from django.shortcuts import redirect
import time
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


tokens_for_registration = []


# Create your views here.
def index_page(request):
    context = {}
    return render(request, 'mainPage.html', context)


def register_page(request):
    global tokens_for_registration
    context = {}
    if request.method == 'POST':
        fromaddr = "fireworkclientregistration@mail.ru"
        toaddr = request.POST["your_email"]
        mypass = "TBfxZUzfav0aScPpHEBe"
        server = smtplib.SMTP_SSL('smtp.mail.ru', 465)
        server.login(fromaddr, mypass)
        time_now = int(time.time())
        token = hashlib.sha256((str(time_now) + toaddr).encode('utf-8')).hexdigest()
        server.sendmail(fromaddr, toaddr, f"yep, here is the key {token}")
        tokens_for_registration.append([token, time_now, toaddr])
    return render(request, 'registerStartPage.html', context)


def clear_expired_tokens():
    global tokens_for_registration
    time_now = int(time.time())
    left_tokens = []
    for i in tokens_for_registration:
        if i[1] + 600 > time_now:
            left_tokens.append(i)
    tokens_for_registration = left_tokens


def register_page_finish(request, token):
    global tokens_for_registration

    context = {}

    clear_expired_tokens()

    if request.method == 'POST':
        time_now = int(time.time())
        for i in range(len(tokens_for_registration)):
            if token == tokens_for_registration[i][0] and tokens_for_registration[i][1] + 600 >= time_now:
                name = request.POST["name"]
                password = request.POST["password"]
                email = tokens_for_registration[i][2]
                user = User.objects.create_user(name, email, password)
                del tokens_for_registration[i]
                user.save()
                return redirect('/')
        return redirect('/registration/start')
    else:
        return render(request, 'registerFinishPage.html', context)
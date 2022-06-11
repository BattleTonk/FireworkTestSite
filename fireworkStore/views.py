from django.shortcuts import render
import smtplib
from django.shortcuts import redirect
import time
from .models import CustomUser
from django.contrib.auth import authenticate, login
import hmac
import hashlib
from base64 import b64encode
from .config import config
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
import os


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
                user = CustomUser.objects.create_user(name, email, password)
                del tokens_for_registration[i]
                user.save()
                return redirect('/')
        return redirect('/registration/start')
    else:
        return render(request, 'registerFinishPage.html', context)


def login_page(request):
    context = {}

    clear_expired_tokens()

    if request.method == 'POST':
        name = request.POST["name"]
        password = request.POST["password"]
        user = authenticate(username=name, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('/')
            else:
                context = {
                    "error": True,
                    "type": "invalid login"
                }
                return render(request, 'loginPage.html', context)
        else:
            context = {
                "error": True,
                "type": "invalid login"
            }
            return render(request, 'loginPage.html', context)
    else:
        return render(request, 'loginPage.html', context)


def features_page(request):
    context = {}
    return render(request, 'featuresPage.html', context)


def buy_page(request):
    user = request.user
    url = f"https://oplata.qiwi.com/create?publicKey={config['PUBLIC_QIWI_KEY']}&amount={2000}&successUrl={'https://firework-web-site.herokuapp.com'}&customFields[who_bought]={user.username}&customFields[paySourcesFilter]=qw,card"
    context = {'qiwiLink': url}
    return render(request, 'buyPage.html', context)


def qiwi_oplata(request):
    if request.method == 'POST':
        error = 1
        req = request.POST.json["bill"]
        qSignature = request.headers.get("X-Api-Signature-SHA256")  # предположительно строка в base64
        hSignature = b64encode(hmac.new(config["SECRET_QIWI_KEY"], msg="{}|{}|{}|{}|{}".format(req["amount"]["currency"], req["amount"]["value"], req["billId"], req["siteId"], req["status"]["value"]), digestmod=hashlib.sha256).digest())
        if qSignature == hSignature:
            user = CustomUser.objects.get_by_natural_key(req["customFields"]["who_bought"])
            user.bought_the_client = True
            user.save()
            error = 0
        return {"error": error}
    else:
        pass


@login_required
def download_page(request):
    user = request.user
    if user.bought_the_client:
        return FileResponse(open(os.path.join(os.path.dirname(__file__), 'data/Uranium1.jar'), 'rb'))
    else:
        return redirect('/')
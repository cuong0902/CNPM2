import os
from flask import Flask
from flask_admin import Admin
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from oauthlib.oauth2 import WebApplicationClient
from flask_mail import Mail
from urllib.parse import quote


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%s@localhost/it02?charset=utf8mb4' % quote('Admin@123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.secret_key = "my@clinic.com"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'temporaryleo0512@gmail.com'
app.config['MAIL_PASSWORD'] = 'tuan0512@'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = ('MedAll', 'temporaryleo0512@gmail.com')


app.config["PAYPAL-SANDBOX-CLIENT-ID"] = "Aa6Hn8C93yInGY6oa-St9YgzwOxToXoD_-iqvbmpcn8vl-0qVFqF0Qr6Z5F6DjWVSR4OMuaFNVg7ewEk"
app.config["PAYPAL-SANDBOX-CLIENT-SECRET"] = "EJSfWZBrSsHIkqFwB-jPlgpFQNlaw5BG2TQEarvw6cY9JSg4noNbyERKqvHy21Na-C33CuYX_J8J4Csj"


GOOGLE_CLIENT_ID = "919352421263-e18mqjhotmb6l176kflviroomrbbd5qd.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

BOOKING_MAX = 2

db = SQLAlchemy(app=app)
admin = Admin(app=app, name='CLINIC', template_mode='bootstrap4')
my_login = LoginManager(app)
client = WebApplicationClient(GOOGLE_CLIENT_ID)  # OAuth 2 client setup
mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)


momo = {
    "endpoint": "https://test-payment.momo.vn/gw_payment/transactionProcessor",
    "partnerCode": "MOMO",
    "accessKey": "F8BBA842ECF85",
    "secretKey": "K951B6PE1waDMi640xX08PD3vg6EkVlz",
    "orderInfo": "pay with MoMo",
    "returnUrl": "http://127.0.0.1:5000/momo/payment-result",
    "notifyUrl": "http://127.0.0.1:5000/momo/payment-result",
    "amount": "",
    "orderId": "",
    "requestId": "",
    "requestType": "captureMoMoWallet",
    "extraData": ""
}

import base64
import json
from datetime import datetime as dt, time

import requests
from flask import render_template, jsonify
from flask_login import login_user
from itsdangerous import SignatureExpired

from admin import *
from my_clinic import app, my_login, s, client, \
    GOOGLE_DISCOVERY_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, BOOKING_MAX
from my_clinic.models import Account, AccountPatient, Customer, AccountAssistant
from my_clinic.momo import MoMo
from my_clinic.paypal import CaptureOrder, CreateOrder


@app.route('/')
def index():  # put application's code here
    return render_template('index.html')


@app.route('/about')
def about_us():
    return render_template('about-us.html')


@app.route('/schedule')
def schedule():
    return render_template('schedule.html', booking_max=BOOKING_MAX)


@app.route('/question')
def question():
    return render_template('question.html')


@app.route('/blog')
def blog():
    return render_template('blog.html')


@app.route('/blog/post')
def blog_post():
    return render_template('blog-single.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/user-profile')
def user_profile():
    return render_template("user-profile.html", records=dao.get_records(current_user.patient.id))


@app.route('/payment-online')
def payment_online():
    receipt = dao.get_request_payment(current_user.patient_id)
    return render_template('payment.html',
                           receipt=receipt,
                           receipt_stats=dao.receipt_stats(receipt))


@my_login.user_loader
def user_loader(account_id):
    return AccountPatient.query.get(account_id) if AccountPatient.query.get(account_id) \
        else AccountAssistant.query.get(account_id)


# Admin Login
@app.route("/admin-login", methods=["post"])
def admin_login_exe():
    username = request.form.get("username")
    password = request.form.get("password")


    user = Account.query.filter(AccountAssistant.email == username,
                                AccountAssistant.password == password).first()
    if user:
        login_user(user)


    return redirect("/admin")


# User Login
@app.route("/user-login", methods=['get', 'post'])
def user_login_exe():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        password = dao.hmac_sha256(password)

        user = Account.query.filter(AccountPatient.email == email,
                                    AccountPatient.password == password).first()

        if user:
            if user.active:
                login_user(user)
                return jsonify({"redirect": request.args.get("next", "/")}), 200
            else:
                if dao.email_verification(email):
                    return jsonify({"message": "You have to be ACTIVE for your email!"}), 406  # Not Acceptable

                return jsonify({"message": "The system has some errors!. PLease try later"})

        return jsonify({"message": "Incorrect username or password!"}), 401  # Unauthorized
    else:
        return render_template("login-user.html")


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route("/user-login/google")
def loginWithGoogle():

    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]


    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/user-login/google/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]


    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )


    client.parse_request_body_response(json.dumps(token_response.json()))


    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)


    if userinfo_response.json().get("email_verified"):

        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    if AccountPatient.query.filter(AccountPatient.email == users_email).first():
        account_patient = AccountPatient.query.filter(AccountPatient.email == users_email).first()
    else:

        if not dao.exist_user(users_email):

            patient = Patient(name=users_name, email=users_email, avatar=picture)
            db.session.add(patient)
        else:
            if Patient.query.filter(Patient.email == users_email).first():
                patient = Patient.query.filter(Patient.email == users_email).first()
            else:
                customer = Customer.query.filter(Customer.email == users_email).first()
                patient = dao.customerToPatient(customer, avatar=picture)

        password = dao.create_password(users_email)
        account_patient = AccountPatient(active=True, email=patient.email, password=password, patient=patient)
        db.session.add(account_patient)
        db.session.commit()


    login_user(account_patient)


    return redirect("/")


# Log out
@app.route("/user-logout")
def user_logout_exe():
    logout_user()

    return redirect("/")


@app.route("/api/validate-email", methods=["post"])
def validate_email():
    email = request.values["registerEmail"]
    user_email = Account.query.filter(Account.email == email).first()
    if user_email:
        return jsonify(False)
    return jsonify(True)


@app.route("/api/change-password", methods=["post"])
def change_password():
    old = request.form.get("oldPassword")
    new = request.form.get("newPassword")

    if dao.change_password(current_user.patient.account.email, old, new):
        return jsonify({"message": "Change Successful!"}), 200

    return jsonify({"message": "ERROR: Incorrect password!"}), 405


@app.route("/api/check-booking-date", methods=["post"])
def check_booking_date():
    date = request.form.get("bookingdate")
    if dt.strptime(date, '%d/%m/%Y') > dt.now():
        return jsonify(True)
    return jsonify(False)


@app.route("/api/check-booking-time", methods=["post"])
def check_booking_time():
    booking_time = request.form.get("bookingtime")
    booking_time = dt.strptime(booking_time, '%I:%M %p').time()
    if booking_time < time(8, 0, 0) or booking_time > time(19, 0, 0) \
            or time(13, 0, 0) > booking_time > time(12, 0, 0):
        return jsonify(False)
    return jsonify(True)


@app.route("/user-register", methods=['post'])
def user_register():
    data = {
        "name": request.form.get("registerName"),
        "email": request.form.get("registerEmail"),
        "password": request.form.get("registerPassword"),
        # default avatar
        "avatar": "https://res.cloudinary.com/dtsahwrtk/image/upload/v1635424275/samples/people/smiling-man.jpg"
    }

    if dao.add_user(**data):
        return jsonify({"message": "Create Account successful!!!"}), 200  # OK
    else:
        return jsonify({"message": "Data has some problems! Maybe."}), 404


@app.route("/user-register/complete")
def complete_registration():
    try:
        token = request.args.get("token")
        email = s.loads(token, salt="email-verification", max_age=60)  # max_age: milliseconds
        user = Account.query.filter(AccountPatient.email == email).first()
        user.active = True
        db.session.add(user)
        db.session.commit()
        return "<h1>Your Email has been verified</h1>"
    except SignatureExpired:
        return "<h1>The token is expired</h1>"


@app.route("/api/add-questions", methods=["post"])
def add_questions():
    questions = {
        "name": request.form.get("name", current_user.patient.name if current_user.is_authenticated else ""),
        "email": request.form.get("email", current_user.patient.email if current_user.is_authenticated else ""),
        "topic": request.form.get("topic"),
        "message": request.form.get("message")
    }
    if dao.add_questions(**questions):
        return jsonify({"message": "add questions success!"}), 200

    return jsonify({"message": "can't add questions!"}), 404


@app.route("/api/add-booking", methods=["post"])
def add_booking():
    books = {
        "name": request.form.get("bookingname", current_user.patient.name if current_user.is_authenticated else ""),
        "email": request.form.get("bookingemail", current_user.patient.name if current_user.is_authenticated else ""),
        "date": request.form.get("bookingdate")
    }

    books["date"] = dt.strptime(books["date"], '%d/%m/%Y')

    period = dt.strptime(request.form.get("bookingtime"), '%I:%M %p').hour
    period = f"{period:02d}:00 - {period + 1:02d}:00"
    booking_time = Time.query.filter(Time.period == period).first()

    if dao.get_amount_of_people(booking_time, books["date"]) == BOOKING_MAX:
        return jsonify({"message": "Maximum of people!"}), 400

    books["time"] = booking_time

    if dao.add_booking(**books):
        return jsonify({
            "message": "booking successfully!",
            "amount": dao.get_amount_of_people(booking_time, books["date"])
        }), 200

    return jsonify({"message": "can't add booking!"}), 404


@app.route("/api/load-schedule")
def load_schedule():
    try:
        booking_time = int(request.args.get('bookingtime'))
        period = f"{booking_time:02d}:00 - {booking_time + 1:02d}:00"
        booking_time = Time.query.filter(Time.period == period).first()

        date = request.args.get('bookingdate')
        date = dt.strptime(date, '%d/%m/%Y')

        amount = dao.get_amount_of_people(booking_time, date)

        return jsonify({"amount": amount}), 200
    except Exception as ex:
        print(ex)
        return jsonify({"message": "Error"}), 404


@app.route('/api/create-paypal-transaction', methods=['post'])
def create_paypal_transaction():
    receipt = dao.get_request_payment(current_user.patient_id)
    resp = CreateOrder().create_order(debug=True)
    return jsonify({"id": resp.result.id})


@app.route('/api/capture-paypal-transaction', methods=['post'])
def capture_paypal_transaction():
    order_id = request.json['orderID']
    resp = CaptureOrder().capture_order(order_id)
    status_code = resp.status_code

    if not dao.complete_payment(dao.get_request_payment(current_user.patient_id).id):
        status_code = 404

    return jsonify({
        "status_code": status_code
    })


@app.route("/pay-with-momo")
def pay_with_momo():
    data = MoMo().payment_order()

    return redirect(data['payUrl'])


@app.route("/momo/payment-result")
def payment_result():
    extra_data = request.args.get("extraData")
    data = json.loads(base64.b64decode(extra_data.encode('utf-8')).decode('utf-8'))

    if dao.complete_payment(int(data['receipt_id'])):
        return "Successful!<br/><a href='/'>Back to home -></a>"

    return "payment failed!. try later!<br/><a href='/'>Back to home -></a>"


@app.context_processor
def common_context():
    is_request_payment = False

    if current_user.is_authenticated:
        if hasattr(current_user, 'patient'):
            if dao.get_request_payment(current_user.patient_id):
                is_request_payment = True

    return {
        "is_request_payment": is_request_payment
    }


if __name__ == '__main__':
    app.run(debug=True)

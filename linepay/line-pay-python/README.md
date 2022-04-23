# line-pay-python-Heroku
LINE Pay API For Python

## Ref.
- [LINE Pay API](https://qiita.com/nkjm/items/b4f70b4daaf343a2bedc)

## Requirements
- LINE Pay Sandbox Api
- Python 3.6

## Try it
```bash
pip install -r requirements.txt
python app.py
```

## Sample code
```app.py
from flask import Flask, render_template, redirect, request
from line_pay import LinePay
from models import db, db_url, Transactions
from firebase import firebase
import datetime

LINE_PAY_URL = 'https://sandbox-api-pay.line.me'
LINE_PAY_CHANNEL_ID = 'your channel'
LINE_PAY_CHANNEL_SECRET = 'your secret'
LINE_PAY_CONFIRM_URL = 'https://app.herokuapp.com/pay/confirm'
app = Flask(__name__)
pay = LinePay(channel_id=LINE_PAY_CHANNEL_ID, channel_secret=LINE_PAY_CHANNEL_SECRET,
              line_pay_url=LINE_PAY_URL, confirm_url=LINE_PAY_CONFIRM_URL)
              
firebase = firebase.FirebaseApplication('URL_FIREBASE')

@app.route("/", methods=['GET'])
def index():
    return render_template('./index.html')


@app.route("/pay/reserve", methods=['POST'])
def pay_reserve():
    global firebase
    
    data = firebase.get('linepay/payid/','')
    print(data)
    #productImageUrl = 'https://www.qualitymatters.org/sites/default/files/illustrations-infographics/CPE-bug-300px_0.png'
    product_name = data['invoice']
    amount = data['price']
    currency = "THB"

    (order_id, response) = pay.request_payments(product_name=product_name, amount=amount, currency=currency)
    print('ID:',response["returnCode"])
    print('Pay:',response["returnMessage"])
    transaction_id = response["info"]["transactionId"]
    print(order_id, transaction_id, product_name, amount, currency)
    
    obj = Transactions(transaction_id=transaction_id, order_id=order_id,
                       product_name=product_name, amount=amount, currency=currency)
    print('obj=',obj)
    firebase.put('transaction',transaction_id, {'updated_at':str(datetime.datetime.now()), 'status':'Not paid'} )
    
    
##    db.session.add(obj)
##    db.session.commit()
##    db.session.close()
    redirect_url = response["info"]["paymentUrl"]["web"]
    print(redirect_url)

    return redirect(redirect_url)


@app.route("/pay/confirm", methods=['GET'])
def pay_confirm():
    global firebase
    
    transaction_id = request.args.get('transactionId')
    #obj = Transactions.query.filter_by(transaction_id=transaction_id).one_or_none()
    #if obj is None:
    #    raise Exception("Error: transaction_id not found.")

    data = firebase.get('linepay/payid/','')
    
    response = pay.confirm_payments(transaction_id=transaction_id, amount=data['price'], currency="THB")
    print(response["returnCode"])
    if(response["returnCode"] == "0000"):
        print("Paid")
    print(response["returnMessage"])
    print('SUCCESS:')
    print("transaction_id=",transaction_id)
    firebase.put('transaction',transaction_id, {'updated_at':str(datetime.datetime.now()), 'status':'Paid'} )
##    db.session.query(Transactions).filter(Transactions.transaction_id == transaction_id).delete()
##    db.session.commit()
##    db.session.close()
    #return "Payment successfully finished."
    return render_template('./paid.html')


def initialize_app(app: Flask) -> None:
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True
    db.init_app(app)
    db.create_all(app=app)


def main() -> None:
    initialize_app(app)
    app.run(host='0.0.0.0', threaded=True)


if __name__ == '__main__':
    main()

```

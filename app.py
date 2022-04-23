#-*- coding=utf-8 -*-
from lib2to3.pgen2.token import BACKQUOTE
from flask import Flask, render_template, Response, request,redirect
import cv2
from datetime import datetime
import time
from pyzbar import pyzbar
import pandas as pd
import keyboard
import time

app = Flask(__name__)

camera = cv2.VideoCapture(0)
Barcodes = []
xBarcodes = []
key_press = False
press_start = time.time()
finish_start = time.time()
showcustom_start = time.time()
start_nobody_time = time.time()
data_saved = False
customer = ''

df = pd.read_csv('data/products.csv') 
df_customer = pd.read_csv('data/customers.csv')  

notEnoughtMoneyState = False
showCustomState = ''

def find_index(df_customer,customer_id):
   for i,id in enumerate(df_customer['id']):
      if str(customer_id) == str(id):
         return i
   return None

def save_data():
   global data_saved,df,Barcodes,customer,df_customer,finish_start,notEnoughtMoneyState

   if data_saved == False:
      table = create_table(df,Barcodes)
      enought_money = False

      if customer == 'enter':
         enought_money = True
      else:
         i = find_index(df_customer,Barcodes[-1])
         balance = int(df_customer['balance'][i])
         buy = int(table.split('//')[0].split(' ')[1])
         if balance - buy > 0: 
            enought_money = True

      if enought_money:
         print('table',table)
         
         data = {
            'customer':customer,
            'table':table,
            'timestamp':datetime.now()
         }

         #update historys.csv
         df_hist = pd.DataFrame(columns = ['customer', 'table','timestamp'])
         df_hist = df_hist.append(data, ignore_index = True)
         df_hist.to_csv('data/historys.csv', mode='a', header=False,index=False)

         if customer != '' and customer != 'enter': 
            df_customer['balance'][i] -= int(buy)
            df_customer.to_csv('data/customers.csv',index=False)

         data_saved = True
         finish_start = time.time()

      else:
         notEnoughtMoneyState = True
         data_saved = True
         finish_start = time.time()

def get_keyboard():
   global Barcodes,key_press,press_start,df_customer,customer

   if Barcodes:
      if keyboard.is_pressed('-') and key_press == False:
         Barcodes.pop()
         key_press = True
         press_start = time.time()
      if time.time()-press_start > 0.5:
         key_press = False

      if Barcodes[-1] in str(df_customer['id']):
         customer = Barcodes[-1]
      if keyboard.is_pressed('enter'):
         customer = 'enter'         

def create_table(df,Barcodes):
    # table = 'Total 9999//aaaaa|12|120/bbbb|1|100/ccccc|12|120/ddddd|1|100'
    df_barcode = []
    for i in set(df['barcode']):
        df_barcode.append(str(i))
    keys = list(set(Barcodes).intersection(set(df_barcode)))  #get barcode key only in database
    
    table = ''
    Total = 0 
    for k in keys:
        barcode = k
        count = Barcodes.count(k)
        name,price = find_product_data(df,barcode)
        total = price*count
        Total += total
        table += f'/{name}|{count}|{total}'
    table += '/||'*(10-len(keys))   #add to 10 lists

    if Total == 0:
       table = 'Total 0//||/||/||/||'
    else:
       table = f'Total {Total}/{table}'

    
    return table

def find_product_data(df,barcode):
    for i,b in enumerate(df['barcode']):
        if str(b) == str(barcode):
            return df['name'][i],df['price'][i]
    else:
        return None,None

def read_barcodes(frame):
   global Barcodes,showCustomState,showcustom_start,customer
   barcodes = pyzbar.decode(frame)
   for barcode in barcodes:
      x, y , w, h = barcode.rect

      barcode_info = barcode.data.decode('utf-8')
      cv2.rectangle(frame, (x, y),(x+w, y+h), (0, 255, 0), 2)
      
      font = cv2.FONT_HERSHEY_DUPLEX
      cv2.putText(frame, barcode_info, (x + 6, y - 6), font, 2.0, (255, 255, 255), 1)

      #append item list
      if str(barcode_info) in str(df['barcode']):
         Barcodes.append(barcode_info)
         showCustomState = ''

      if Barcodes:
         #start show new custom case current still show old customer info
         if not Barcodes[-1] in str(df['barcode']) and customer == '':
            showCustomState = str(barcode_info)
            showcustom_start = time.time()
         #append customer id 
         elif str(barcode_info) in str(df_customer['id']):
            Barcodes.append(barcode_info)

      else:
         #show customer info
         if str(barcode_info) in str(df_customer['id']) and customer == '':
            showCustomState = str(barcode_info)
            showcustom_start = time.time()

   return frame

def gen_frames():
   while True:
      success, frame = camera.read() 
      if success:
         try:
            barcode_info = read_barcodes(frame)
            ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
         except Exception as e:
            pass
      else:
         pass

def gen_qr():
   while True:
      try:
         img = cv2.imread("static/images/qrcode.png", cv2.IMREAD_COLOR)
         # ret, buffer = cv2.imencode('.jpg', cv2.flip(img,1))
         ret, buffer = cv2.imencode('.jpg', img)
         frame = buffer.tobytes()
         yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
      except:
         pass
        
@app.route('/')
def index():
   return render_template('index.html')
 
@app.route('/video_feed')
def video_feed():
   return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/qr_feed')
def qr_feed():
   return Response(gen_qr(), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route('/requests',methods=['POST','GET'])
# def tasks():
#     global finish
#     if request.method == 'POST':
#         if request.form.get('click') == 'Capture':
#            print('aaaa')

#         elif  request.form.get('grey') == 'Grey':
#            print('aaaa')
   
#         elif  request.form.get('neg') == 'Negative':
#            print('aaaa')
     
#         elif  request.form.get('face') == 'Face Only':
#            print('aaaa')

#         elif  request.form.get('stop') == 'Stop/Start':
#            print('aaaa')
           
#          #   table = 'Finish//'
#            finish = True   
#         elif  request.form.get('rec') == 'Start/Stop Recording':
#            print('aaaa')
           
#     elif request.method=='GET':
#         return render_template('index.html')
#     return render_template('index.html')

@app.route('/time_feed')
def time_feed():
    def generate():
        yield datetime.now().strftime("%Y.%m.%d|%H:%M:%S")  # return also will work
    return Response(generate(), mimetype='text') 

@app.route('/item_feed')
def item_feed():
   def generate():
      global Barcodes,df,customer,finish_start,data_saved,notEnoughtMoneyState,showCustomState,showcustom_start,xBarcodes,start_nobody_time
      print('Barcodes',Barcodes)

      get_keyboard()

      table = create_table(df,Barcodes)

      if customer != '':
         save_data()

      if data_saved == True:
         if notEnoughtMoneyState:
            table = 'No Money//'+table.split('//')[1]
            print('notEnoughtMoneyState',notEnoughtMoneyState)
         else:
            table = 'Finish//||/||/||/||'

      if showCustomState != '':
         i = find_index(df_customer,showCustomState)
         balance = int(df_customer['balance'][i])
         name  = df_customer['name'][i]
         table = f'custom Data// | | /ID :|{showCustomState}|/Name :|{name}| /Balance :|{balance}| '
   

      #if not state change more than 60 sec >> reset state
      if xBarcodes != Barcodes:
         start_nobody_time = time.time()
      xBarcodes = Barcodes.copy()
      if time.time()-start_nobody_time > 60:
         customer = ''
         data_saved = False
         notEnoughtMoneyState = False
         Barcodes = []

      #after finished wait 5 sec before reset
      if data_saved and time.time()-finish_start > 5:
         # finish = False
         customer = ''
         data_saved = False
         notEnoughtMoneyState = False
         Barcodes = []

      #show customer data 15 sec
      if showCustomState and time.time()-showcustom_start > 15:
         showCustomState = ''

      print('table........',table)

      yield table
   return Response(generate(), mimetype='text') 

if __name__ == '__main__':
   
   app.run()
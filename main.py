import telebot
import os
import datetime
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint

# define the scope
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

# add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name('mamajo-edb5d6f38435.json', scope)

# authorize the clientsheet 
client = gspread.authorize(creds)
sheet = client.open("data_mamajo_bot").sheet1
sheet2 = client.open("data_mamajo_bot").worksheet('Sheet2')
sheet3 = client.open("data_mamajo_bot").worksheet('Sheet5')
sheet4 = client.open("data_mamajo_bot").worksheet('Sheet4')

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup,ReplyKeyboardMarkup,KeyboardButtonPollType
from telebot.types import KeyboardButton

data = sheet.get_all_records()
pprint(sheet.get_all_records())

def main_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Saya mau beli", callback_data="menu"),
        InlineKeyboardButton("Promo", callback_data="promo"),        
        InlineKeyboardButton("Kasih Ulasan", callback_data="ulasan"),        
        InlineKeyboardButton("Mau tau alamat kami ?", callback_data="myalamat"),        
    )
    return markup

txt_menu = ""
item = []
index = 1
harga_after_diskon = 0
status = ["diproses", "selesai", "batal"]
for i in data:
    if i["Diskon (%)"] != 0:
        txt_menu += str(index) + ". " + i['Nama'] + " \t\t\t| " +"Rp." +str( "{:,.2f}".format(i["Harga"])) + f" <b>Diskon {i['Diskon (%)']}%</b>" + "\n"     
        item.append(str(index))
    else:
        txt_menu += str(index) + ". " + i['Nama'] + " \t\t\t| " +"Rp." +str( "{:,.2f}".format(i["Harga"])) + "\n"     
        item.append(str(index))

    index += 1
print(txt_menu)    

@bot.callback_query_handler(func= lambda msg : msg.data == "promo" )
def show_promo(msg):    
    txt_promo = ''
    dt = sheet3.get_all_records()
    pprint(dt)
    indices = 1
    if dt != []:
        for i in dt:
            txt_promo += str(indices) + ". " + i['Promo'] + " \t\t\t| " +"Rp." +str( "{:,.2f}".format(i["Harga"])) + "\n"     
            item.append(str(indices))
            indices += 1
            bot.send_message(msg.message.chat.id, f"<b>Daftar Promo Hari ini</b>\n{txt_promo}", parse_mode="HTML")    
    else:
        bot.send_message(msg.message.chat.id, "Nampaknya belum ada promo, nantikan promo yang akan datang ya!")        
# print(txt_promo)    

@bot.message_handler(commands=["start"])
def show_main(message):
    first_name = message.chat.first_name
    last_name = message.chat.last_name
    bot.reply_to(message, "Hi, {} {}\nHarap membaca setiap instruksi dengan seksama ya!".format(first_name, last_name))
    bot.send_message(message.chat.id,"Silahkan pilih salah satu perintah!" ,reply_markup=main_menu())
    
@bot.callback_query_handler(func= lambda msg: msg.data == "myalamat")
def show_lokasi(msg):
    latitude = float(sheet.cell(3, 4).value) 
    longtitude =  float(sheet.cell(4,4).value)
    print(f'{latitude} {longtitude}') 
    bot.send_message(msg.message.chat.id, "Hi, kami senang Anda bertanya\nAlamat kami di : \n{}".format(sheet.cell(2,4).value))
    bot.send_location(msg.message.chat.id, latitude, longtitude)

@bot.callback_query_handler(func= lambda message: message.data == "menu")
def query_menu(message):
    bot.send_message( message.message.chat.id, "Berikut <b>adalah</b> daftar Menunya\n\nNama\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tHarga\n{}".format(txt_menu), parse_mode = "HTML")
    bot.send_message(message.message.chat.id, "Silahkan ketik pesanan dengan format : `nomer urut*jumlah barang` bila lebih dari 1 barang pisahkan dengan spasi\ncontoh : 2*2 3*1")
   
def findItemByNumber(number):
    dt = sheet.row_values(number + 1)
    return dt
        
def diskon(origin, diskon):
    return (origin) - (origin)*diskon/100

buy_what = []
@bot.message_handler(func=lambda msg: msg.text.find("*") != -1)
def choose_menu(msg):
    global buy_what
    b = ''
    stuf = ''
    total = 0
    #array nomer urut & jumlah barang
    itm = []
    itm2 = []
    txt = msg.text.split(" ")
    first_name = msg.chat.first_name
    last_name = msg.chat.last_name
    # print(txt)
    for i in txt:
        b = i.split("*")
        itm.append(b[0])
        itm2.append(b[1])
    
    nm = first_name + " " + last_name if (last_name is not None)  else first_name    
    
    buy_what.append(nm)
    for i in range(0, len(itm)):
        item_pick = findItemByNumber(int(itm[i]))
        print(item_pick)
        if item_pick[2] != '0':
            total += (diskon(int(item_pick[1]), int(item_pick[2])) * int(itm2[i]))
            stuf += item_pick[0] + " x" + itm2[i] + f" <b>diskon {item_pick[2]}% terpasang</b>"+ "\n"
        else:
            total += (int(item_pick[1]) * int(itm2[i]))
            # daftar pesanan di simpan di variabel ini
            stuf += item_pick[0] + " x" + itm2[i] + "\n"
        
    itm.clear()
    itm.append(stuf)
    itm.append(total)
    print(stuf)
    print(total)
    
    for i in itm:
        buy_what.append(i)
    bot.reply_to(msg,"baik pesanan Anda sudah kami simpan")
    bot.send_message(msg.chat.id,"Selanjutnya, berikan Alamat delivery-nya !\nbalas dengan format: /alm `alamat anda`\n<b>contoh : /alm jln.Gatotkaca, Tipes</b>", parse_mode = "HTML")
    
@bot.callback_query_handler(func= lambda msg:msg.data == "ulasan")
def user_feedback(msg):
    bot.send_message(msg.message.chat.id, "Ulasan Anda beguna bagi kami untuk meningkatkan kualitas pelayanan kami!\nSilahkan kirimkan ulasan Anda awali dengan ketik `/fb`\ncontoh: /fb banyakin event diskon dong :)")
    
@bot.message_handler(func=lambda query: '/fb' in query.text )
def ulasan_user(query):
    sheet4.append_row([query.text])
    bot.reply_to(query, "Ok, ulasan diterima, Terima kasih atas ulasannya\nSemoga hari mu menyenangkan ya!")
    
@bot.message_handler(func=lambda query: '/alm' in query.text )
def save_alamat(query):
    global buy_what
    alamat = query.text.split("/alm ")
    buy_what.append(alamat[1])
    bot.reply_to(query, "Ok, alamat Anda berhasil disimpan!")
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    contact_btn = KeyboardButton(
        text="Bagikan nomor kontak",
        request_contact=True
    )
    markup.add(contact_btn)
    bot.send_message(query.chat.id, "Klik tombol `<b>Bagikan nomor kontak</b>` di bawah agar kami dapat menyimpan nomor Anda!", reply_markup=markup, parse_mode = "HTML")
    
@bot.message_handler(content_types=["contact"])
def save_kontak(msg):
    global buy_what
    if msg.contact is not None:
        nomer = msg.contact.phone_number
        buy_what.append(nomer)
        bot.reply_to(msg, "Ok, nomor Anda sudah kami simpan!")
        bot.send_message(msg.chat.id, "Apakah ada catatan untuk pesanan ini ?\njika tidak ketik `/t`, jika ya awali dengan `/nt` untuk membalas.\ncontoh : <b>/nt gulanya sedikit saja.</b>", parse_mode="HTML")

def markup_order():
    markup = InlineKeyboardMarkup(
            row_width= 2,   
        )
    markup.add(
            InlineKeyboardButton(
                "Sudah, pesan sekarang",
                callback_data = "ok"
            ),
            InlineKeyboardButton(
                "Ulangi",
                callback_data = "ulangi"
            ),
        )
    return markup    

@bot.message_handler(commands=['cancel'])
def cancel_operation(msg):
    bot.send_message(msg.chat.id, "Baik, instruksi dibatalkan\nSemoga lain kali mampir lagi ya!")
    
chat_id_neo = 1620737884
chat_id_nopa = 5291303850
id_stiker = "CAACAgIAAxkBAAEKGGpk5OsNFh2HGd7pLDGx9vtqeKMuLwACLgEAAvcCyA89lj6kwiWnGjAE"
id_user = "MMJO" + str((len(sheet2.get_all_records()) + 1)) if sheet2.get_all_records() != None else "MMJO1"
@bot.message_handler(func=lambda query: '/nt' or '/t' in query.text )
def save_catatan(query):
    datetime_utc = datetime.datetime.utcfromtimestamp(query.date)
    # Mengubah waktu menjadi format yang lebih umum
    waktu_umum = datetime_utc.strftime('%d/%m/%Y %H:%M:%S')
    global buy_what
    if query.text.find('/nt') != -1 :
        note = query.text.split("/nt ")
        buy_what.append(note[1])
        buy_what.append(waktu_umum)
        buy_what.append(id_user)
        buy_what.append(status[0])
        print(buy_what)
        bot.reply_to(query, "Ok, catatan telah ditambahkan")
        bot.send_message(query.chat.id, "Detail pesanan Anda :\nId order : <b>{}</b>\nCustomer : <b>{}</b>\nPesanan :\n{}\nHarga : <b>Rp.{:,.2f}</b>\nAlamat : <b>{}</b>\nNo.Tele : {}\nCatatan : {}".format(buy_what[7],buy_what[0],buy_what[1],int(buy_what[2]),buy_what[3],buy_what[4], buy_what[5]), parse_mode="HTML")
        bot.send_message(query.chat.id, "Apakah pesanan sudah benar ?", reply_markup = markup_order())
        
    elif query.text.find('/t') != -1:
        buy_what.append("-")
        buy_what.append(waktu_umum)
        buy_what.append(id_user)
        buy_what.append(status[0])
        print(buy_what)
        bot.send_message(query.chat.id, "Detail pesanan Anda :\nId order : <b>{}</b>\nCustomer : <b>{}</b>\nPesanan :\n{}\nHarga : <b>Rp.{:,.2f}</b>\nAlamat : <b>{}</b>\nNo.Tele : {}\nCatatan : {}".format(buy_what[7],buy_what[0],buy_what[1],int(buy_what[2]),buy_what[3],buy_what[4], buy_what[5]), parse_mode="HTML")
        bot.send_message(query.chat.id, "Apakah pesanan sudah benar ?", reply_markup = markup_order())

def markup_status(callback):
    markup = InlineKeyboardMarkup(
        row_width= 2
    )
    markup.add(
        InlineKeyboardButton(
            text="Selesai",
            callback_data="done"+callback
        ),
        InlineKeyboardButton(
            text="Batalkan",
            callback_data="cancel"
        )
    )
    return markup

import random

@bot.message_handler(func=lambda msg: True)
def handle_exception(msg):
    respon = [
        "Maaf kami tidak dapat mengikuti instruksi ini.",
        "Kami tidak melayani permintaan ini",
        "Saya tidak tahu maksud Anda",
        "Harap memberikan instruksi sesuai petunjuk ya"
    ]
    acak = random.randint(0, 3)
    bot.reply_to(msg, respon[acak])
    
@bot.callback_query_handler(func= lambda msg: msg.data in ["ok", "ulangi"])
def response_order(msg):
    if msg.data == "ok":
        sheet2.append_row(buy_what)
        bot.send_message(msg.message.chat.id, "Baik pesanan Anda segera kami proses, mohon ditunggu ya!\nTerima Kasih atas pesanan Anda")
        bot.send_message(
            chat_id_neo, "Ada pesanan baru nih!\nDetail pesanan :\nId order : <b>{}</b>\nCustomer : <b>{}</b>\nPesanan :\n{}\nHarga : <b>Rp.{:,.2f}</b>\nAlamat : {}\nNo.Tele : +{}\nCatatan : {}"
            .format(buy_what[7],buy_what[0],buy_what[1],int(buy_what[2]),buy_what[3],buy_what[4], buy_what[5])
                # ,reply_markup=markup_status(id_user)
                ,parse_mode = "HTML"
                
            )
        bot.send_sticker(msg.message.chat.id, id_stiker)
        buy_what.clear()
    elif msg.data == "ulangi":
        # sheet2.append_row(buy_what)
        bot.send_message(msg.message.chat.id, "Baik kalau begitu silahkan ketik /start untuk mengulangi permintaan")
        buy_what.clear()

@bot.callback_query_handler(func= lambda msg: msg.data == "cancel" or msg.data.find("done") != -1)
def owner_command(msg):
    count = 1
    all_order = sheet2.get_all_records()
    if msg.data == ("done"+id_user):
        for i in all_order:
            count += 1
            if msg.data[4:] == i["Id"]:
                sheet2.update_cell(count,9, status[1])
        bot.send_message(chat_id_neo, "Good Job!, satu pesanan selesai")    
    elif msg.data == "cancel":
        for i in all_order:
            count += 1
            if msg.data[4:] == i["Id"]:
                sheet2.update_cell(count,9, status[2])
        bot.send_message(chat_id_neo, "Baiklah , Anda telah membatalkan pesanan")    
    else:
        print("Tidak dapat berbicara")    
        
bot.infinity_polling()   
        
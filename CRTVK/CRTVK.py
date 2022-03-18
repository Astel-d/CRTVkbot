import os #Импортируем стандартные модули питона.
import time
import json
import random
import urllib.request

import base64 #Импортируем стандартные бибилотеки
import vk_api
import socketio
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.upload import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType

from responses import responses
armed_stat = None
group_id ='196554920'  #id группы вк с ботом
token = "8e4b3482b35bb38baf15285b3d899155bb27b0fc483d726f36f4694352e42ffd9a09d268e0debc73cc875"  #Токен бота


vk_session = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, group_id)  #Проходим авторизацию нашего бота согласно документации библиотеки vk_api
vk = vk_session.get_api()
VkUpload = VkUpload(vk)

sio = socketio.Client()
 #Подключаемся к серверу согласно документации python socketio


with open("users.json", "r") as read_file: #Читаем json файл с данными о пользователях
	users_info = json.load(read_file)


class Main():

	def send_msg(self, message=None, attachment=None, keyboard=None):
		"""
		Функция отправки сообщения. Аргумениы не позициональны.
		"""
		vk.messages.send(
			peer_id = peer_id, #id пользователя, которому отправляется сообщение
			random_id = get_random_id(), #Обязательный аргумент согласно описанию функции messages.send
			message = message, #Текст сообщение
			keyboard = keyboard, #Название клавиатуры
			attachment = attachment #Идентификатор вложения в сообщение
		)


	def send_code(self, url=None, doc_name=None):
		"""
		Отправка миссии на коптер. Аргументы не позициональны.
		"""
		doc_name = doc_name
		url = url
		urllib.request.urlretrieve(url, doc_name) #Скачивание файла по прямой ссылке, предоставляемой vk_api
		f = open(doc_name, 'r') #Открытие файла
		file = f.read() #Чтение файла
		sio.emit('newMission', file) #Отправка файла на сервер



	def write_db(self, users_info):
		"""
		Функция записи данных о пользователях из словаря в json файл
		"""
		users_info = users_info
		with open("users.json", "w") as write_file:
			json.dump(users_info, write_file)



Main = Main() #Создаем экземпляр класса


class Keyboards():
	keyboard_menu = VkKeyboard(one_time=False) #Создаем три клавиатуры
	keyboard_stop = VkKeyboard(one_time=True)
	keyboard_language = VkKeyboard(one_time=True)
	keyboard_login = VkKeyboard(one_time=True)


	keyboard_menu.add_button('Land', color=VkKeyboardColor.POSITIVE) #Заполняем keyboard_menu
	keyboard_menu.add_button('Hover', color=VkKeyboardColor.POSITIVE)
	keyboard_menu.add_line()
	keyboard_menu.add_button('Get photo', color=VkKeyboardColor.POSITIVE)
	keyboard_menu.add_button('Disarm', color=VkKeyboardColor.NEGATIVE)
	keyboard_menu.add_line()
	keyboard_menu.add_button('Return', color=VkKeyboardColor.POSITIVE)
	keyboard_menu.add_button('Return settings', color = VkKeyboardColor.PRIMARY)
	keyboard_menu.add_line()
	keyboard_menu.add_button('Report', color=VkKeyboardColor.NEGATIVE)


	keyboard_stop.add_button('Stop', color=VkKeyboardColor.NEGATIVE) #Заполняем keyboard_stop

	keyboard_language.add_button('ru', VkKeyboardColor.POSITIVE) #Заполняем keyboard_language
	keyboard_language.add_button('en',VkKeyboardColor.POSITIVE)

	keyboard_login.add_button('sign in', VkKeyboardColor.POSITIVE)

settings_stat = False

for event in longpoll.listen(): #Ждём события от vk_api
	if event.type == VkBotEventType.MESSAGE_NEW: #Проверяем то, является ли событие сообщением


		vk_message = event.object['message'] #Получаем объект сообщения от vk_api
		user_id = str(vk_message['from_id']) #Получаем id пользователя, приславшего сообщениe
		peer_id = vk_message['peer_id'] #id диалога(в нашем случае будет равен user_id)
		text = vk_message['text'] #Получаем текст сообщения пользователя
		try:
		    sio.connect('https://48c5-94-29-124-254.eu.ngrok.io/', wait_timeout = 3)
		except socketio.exceptions.ConnectionError:
			time.sleep(1)

		try:
			uid = users_info[user_id]['uid']
			if uid != None:
				sio.emit('uid', uid)
				print(uid)
		except KeyError:
			pass

		"""
		Блок, отвечающий за обработку сообщений от новых пользователей
		"""
		try:

			if user_id not in users_info: #Проверяем, есть ли id нашего пользователя в базе данных
				users_info[user_id] = {'lang':None, 'location_stat':None, 'report_mode': None, 'send_mode': None, 'login_stat':[False,False], 'uid':None, 'return_settings':{'to':None, 'speed':None, 'alt':None, 'action': None}} #Если нет, то присваиваем пользователю по id стандартный набор значений
				Main.write_db(users_info = users_info) #Перезаписываем json файл, пополняя его актуальными данными

			if users_info[user_id]['lang'] == 'ru' or users_info[user_id]['lang'] == 'en':
				resp = responses[users_info[user_id]['lang']]

			if users_info[user_id]['lang'] == None and text.lower() != 'ru' and text.lower() != 'en': #Проверяем, выбран ли у пользователя язык
				Main.send_msg(message = 'Choose language', keyboard = Keyboards.keyboard_language.get_keyboard()) #Отправляем сообщение с клавиатурой для выбора языка

			if text.lower() == 'ru':
				users_info[user_id]['lang'] = 'ru'
				resp = responses[users_info[user_id]['lang']]
				Main.write_db(users_info=users_info)
				Main.send_msg(message = resp['auth'][0], keyboard = Keyboards.keyboard_login.get_keyboard())

			elif text.lower() == 'en':
				users_info[user_id]['lang'] = 'en'
				resp = responses[users_info[user_id]['lang']]
				Main.write_db(users_info=users_info)
				Main.send_msg(message = resp['auth'][0], keyboard = Keyboards.keyboard_login.get_keyboard())

			if text.lower() == 'sign in' and users_info[user_id]['lang'] != None and users_info[user_id]['uid'] == None and users_info[user_id]['login_stat'][0] == False and users_info[user_id]['login_stat'][1] == False:
				Main.send_msg(message=resp['auth'][1])
				users_info[user_id]['login_stat'][0] = True

			if users_info[user_id]['login_stat'][0] == True and text.lower() != 'sign in':
				Main.send_msg(message = resp['auth'][2])
				login = text.lower()
				users_info[user_id]['login_stat'][0] = False
				users_info[user_id]['login_stat'][1] = True

			elif users_info[user_id]['login_stat'][1] == True and text.lower != login:
				users_info[user_id]['login_stat'][1] = False
				password = text
				sio.emit('signin',{'nickname': login, 'password': password})
				time.sleep(3)
				@sio.on('signinres')
				def on_message(res):
					if res['body'] == "nickname_error":
						Main.send_msg(message = resp['auth'][3], keyboard = Keyboards.keyboard_login.get_keyboard())
					elif res['body'] == "password_error":
						Main.send_msg(message = resp['auth'][4], keyboard = Keyboards.keyboard_login.get_keyboard())
					elif res['body'] == "successful":
						users_info[user_id]['uid'] = res['uid']
						Main.write_db(users_info = users_info)
						Main.send_msg(message = resp['auth'][5], keyboard = Keyboards.keyboard_menu.get_keyboard())



			if users_info[user_id]['uid'] != None:

				if text.lower() == 'land':
					sio.emit('req', {'body':'land'})
					Main.send_msg(message = resp['done'])

				if text.lower() == 'hover':
					sio.emit('req', {'body':'hover'})
					Main.send_msg(message = resp['done'])

				if text.lower() == 'disarm':
					sio.emit('req', {'body':'disarm'})
					Main.send_msg(message = resp['done'])

				if text.lower() == 'get photo':
					sio.emit('req', {'body': 'photo'})
					time.sleep(3)
					@sio.on('photofromclover')
					def on_message(photo):
						photo_name = 'photo_' + user_id + '.png'
						with open(photo_name, 'wb') as write_photo:
							image_encode = bytes(str(photo), 'UTF-8')
							write_photo.write(base64.decodebytes(image_encode))
						photo_upload = VkUpload.photo_messages(photos = photo_name, peer_id = peer_id)
						Main.send_msg(message = resp['photo'], attachment = 'photo' + str(photo_upload[0]['owner_id']) + "_" + str(photo_upload[0]['id']))
						os.remove(photo_name)

				if text.lower() == 'st':
					print

				if text.lower() == 'return settings':
					settings_stat = True
					Main.send_msg(resp['settings'][0])

				elif settings_stat == True and text.lower() == 'return_settings':
					pass

				elif settings_stat == True and text.lower().startswith('speed'):
					if int(text.split()[1]) <= 10:
						users_info[user_id]['return_settings']['speed'] = int(text.split()[1])
						Main.write_db(users_info = users_info)

				elif settings_stat == True and text.lower().startswith('alt'):
					if int(text.split()[1]) <= 100:
						users_info[user_id]['return_settings']['alt'] = int(text.split()[1])
						Main.write_db(users_info = users_info)

				elif settings_stat == True and text.lower().startswith('action'):
					if text.lower().split()[1] == 'hover' or text.lower().split()[1] == 'land':
						users_info[user_id]['return_settings']['action'] = text.lower().split()[1]
						Main.write_db(users_info = users_info)

				elif settings_stat == True and text.lower().startswith('to'):
					if text.lower().split()[1] == 'user' or text.lower().split()[1] == 'takeoff':
						users_info[user_id]['return_settings']['to'] = text.lower().split()[1]
						Main.write_db(users_info = users_info)

				if text.lower() == 'return':
					users_info[user_id]['location_stat'] = True
					print('ok')
					print(users_info[user_id]['location_stat'])
				if users_info[user_id]['location_stat'] == True and text.lower() != 'return':
					print('ok2')
					if users_info[user_id]['location_stat'] == True and text.lower() == "stop":
						users_info[user_id]['location_stat'] = False
						pass
					if users_info[user_id]['return_settings']['to'] == 'user':
					    print(type(vk_message['geo']['coordinates']['latitude']))
					    print('ok3')
					    sio.emit('req', {'body':'returnToHome', 'data':{'to':'user', 'lat':vk_message['geo']['coordinates']['latitude'], 'lon':vk_message['geo']['coordinates']['longitude'], 'alt':users_info[user_id]['return_settings']['alt'], 'speed':users_info[user_id]['return_settings']['speed'], 'action':users_info[user_id]['return_settings']['action']}})
					    users_info[user_id]['location_stat'] = False
					elif users_info[user_id]['return_settings']['to'] == 'takeoff':
						print('ok4')
						users_info[user_id]['location_stat'] = False
						sio.emit('req', {'body':'returnToHome', 'data':{'to':'takeoff', 'alt':users_info[user_id]['return_settings']['alt'], 'speed':users_info[user_id]['return_settings']['speed'], 'action':users_info[user_id]['return_settings']['action']}})
				sio.disconnect()

				print("I'm disconnected!")
		except Exception as E:
			print(E)
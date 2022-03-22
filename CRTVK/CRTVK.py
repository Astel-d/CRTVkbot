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



group_id ='Your group id' 
token = "your token" 


vk_session = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, group_id)  #Проходим авторизацию нашего бота согласно документации библиотеки vk_api
vk = vk_session.get_api()
VkUpload = VkUpload(vk)

sio = socketio.Client() #Create an instance of the class according to the socket io documentation



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
		urllib.request.urlretrieve(url, doc_name) #Скачивание файла по прямой ссылке, предоставляемой vk_api
		f = open(doc_name, 'r', encoding='utf-8') #Открытие файла
		file = f.read() #Чтение файла
		sio.emit('newMission', file) #Отправка файла на сервер


	def send_photo(self):
		sio.emit('req', {'body': 'photo'})
		time.sleep(5)
		@sio.on('photofromclover')
		def on_message(photo):
			photo_name = 'photo_' + user_id + '.png'
			with open(photo_name, 'wb') as write_photo:
				image_encode = bytes(str(photo), 'UTF-8')
				write_photo.write(base64.decodebytes(image_encode))
			photo_upload = VkUpload.photo_messages(photos = photo_name, peer_id = peer_id)
			self.send_msg(message = resp['photo'], attachment = 'photo' + str(photo_upload[0]['owner_id']) + "_" + str(photo_upload[0]['id']))
			os.remove(photo_name)


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
	keyboard_language = VkKeyboard(one_time=True)
	keyboard_login = VkKeyboard(one_time=True)
	stop = VkKeyboard(one_time=True)

	keyboard_menu.add_button('Land', color=VkKeyboardColor.POSITIVE) #Заполняем keyboard_menu
	keyboard_menu.add_button('Hover', color=VkKeyboardColor.POSITIVE)
	keyboard_menu.add_line()
	keyboard_menu.add_button('Get photo', color=VkKeyboardColor.POSITIVE)
	keyboard_menu.add_button('Disarm', color=VkKeyboardColor.NEGATIVE)
	keyboard_menu.add_line()
	keyboard_menu.add_button('Return', color=VkKeyboardColor.POSITIVE)
	keyboard_menu.add_button('Send code', color=VkKeyboardColor.POSITIVE)
	keyboard_menu.add_line()
	keyboard_menu.add_button('Return settings', color = VkKeyboardColor.PRIMARY)

	stop.add_button('Stop', color=VkKeyboardColor.NEGATIVE)

	keyboard_language.add_button('ru', VkKeyboardColor.POSITIVE) #Заполняем keyboard_language
	keyboard_language.add_button('en',VkKeyboardColor.POSITIVE)

	keyboard_login.add_button('sign in', VkKeyboardColor.POSITIVE)

settings_stat = False


try:
	for event in longpoll.listen(): #Ждём события от vk_api
		if event.type == VkBotEventType.MESSAGE_NEW: #Проверяем то, является ли событие сообщением


			vk_message = event.object['message'] #Получаем объект сообщения от vk_api
			user_id = str(vk_message['from_id']) #Получаем id пользователя, приславшего сообщениe
			peer_id = vk_message['peer_id'] #id диалога(в нашем случае будет равен user_id)
			text = vk_message['text'] #Получаем текст сообщения пользователя
			try:
				sio.connect('https://48c5-94-29-124-254.eu.ngrok.io/', wait_timeout = 10)
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


			if user_id not in users_info: #Проверяем, есть ли id нашего пользователя в базе данных
				users_info[user_id] = {'settings_stat': False, 'lang':None, 'location_stat':None, 'report_mode': None, 'send_mode': False, 'login_stat':False, 'uid':None, 'return_settings':{'to':None, 'speed':None, 'alt':None, 'action': None}, 'login':None, 'password':None} #Если нет, то присваиваем пользователю по id стандартный набор значений
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

			if (text.lower() == 'sign in' or users_info[user_id]['login_stat'] == True) and users_info[user_id]['lang'] != None and users_info[user_id]['uid'] == None:
				users_info[user_id]['login_stat'] = True

				if users_info[user_id]['login'] == None:
					Main.send_msg(message = resp['auth'][1])

				if text.lower() != 'sign in' and users_info[user_id]['login'] == None:
					users_info[user_id]['login'] = text.lower()

				elif text.lower() != 'sign in' and text.lower() != users_info[user_id]['login'] and users_info[user_id]['login'] != None:
					users_info[user_id]['password'] = text
					sio.emit('signin',{'nickname': users_info[user_id]['login'], 'password': users_info[user_id]['password']})
					users_info[user_id]['login_stat'] = False
					@sio.on('signinres')
					def on_message(res):
						if res['body'] == "nickname_error":
							Main.send_msg(message = resp['auth'][2], keyboard = Keyboards.keyboard_login.get_keyboard())

						elif res['body'] == "password_error":
							Main.send_msg(message = resp['auth'][3], keyboard = Keyboards.keyboard_login.get_keyboard())

						elif res['body'] == "successful":
							users_info[user_id]['uid'] = res['uid']
							Main.write_db(users_info = users_info)
							Main.send_msg(message = resp['auth'][4], keyboard = Keyboards.keyboard_menu.get_keyboard())
							users_info[user_id].pop('login')
							users_info[user_id].pop('password')
							Main.write_db(users_info = users_info)



			if users_info[user_id]['uid'] != None:
				if users_info[user_id]['settings_stat'] != True:
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
						Main.send_photo()


					if text.lower() == 'send file' and users_info[user_id]['send_mode'] == False:
						Main.send_msg(message = "Отправьте файл для загрузки на коптер")
						users_info[user_id]['send_mode'] = True
					try:
						print(users_info[user_id]['send_mode'])
						if users_info[user_id]['send_mode'] == True and text.lower() == 'send file':
							pass
						elif users_info[user_id]['send_mode'] == True and vk_message['attachments'][0]['type'] != 'doc':
							print('ok')
							Main.send_msg("Это не похоже на код")
						elif users_info[user_id]['send_mode'] == True and vk_message['attachments'][0]['type'] == 'doc' and vk_message['attachments'][0]['doc']['ext'] == 'py':
							Main.send_code(url = vk_message['attachments'][0]['doc']['url'], doc_name = 'code_' + str(user_id) + '.py')
							os.remove('code_' + str(user_id) + '.py')
							users_info[user_id]['send_mode'] = False
							Main.send_msg(message = 'Выполняю')
					except Exception as E:
						print(E)


					if text.lower() == 'return':
						users_info[user_id]['location_stat'] = True
						print('ok')
					if users_info[user_id]['location_stat'] == True and text.lower() != 'return':
						print('yes')
						if users_info[user_id]['location_stat'] == True and text.lower() == "stop":
							users_info[user_id]['location_stat'] = False
						try:
							if users_info[user_id]['return_settings']['to'] == 'user':
								print(type(vk_message['geo']['coordinates']['latitude']))
								print('ok3')
								sio.emit('req', {'body':'returnToHome', 'data':{'to':'user', 'lat':vk_message['geo']['coordinates']['latitude'], 'lon':vk_message['geo']['coordinates']['longitude'], 'alt':users_info[user_id]['return_settings']['alt'], 'speed':users_info[user_id]['return_settings']['speed'], 'action':users_info[user_id]['return_settings']['action']}})
								users_info[user_id]['location_stat'] = False
							elif users_info[user_id]['return_settings']['to'] == 'takeoff':
								print('ok4')
								users_info[user_id]['location_stat'] = False
								sio.emit('req', {'body':'returnToHome', 'data':{'to':'takeoff', 'alt':users_info[user_id]['return_settings']['alt'], 'speed':users_info[user_id]['return_settings']['speed'], 'action':users_info[user_id]['return_settings']['action']}})
						except Exception as E:
							print(E)

				if text.lower() == 'return settings':
					users_info[user_id]['settings_stat'] = True
					Main.send_msg(resp['settings'][0])
					Main.send_msg(message = 'Текущие настройки:\n' + str(users_info[user_id]['return_settings']), keyboard = Keyboards.stop.get_keyboard())

				if users_info[user_id]['settings_stat'] == True and text.lower() == 'stop':
					users_info[user_id]['settings_stat'] = False
					Main.write_db(users_info = users_info)
					Main.send_msg(message = 'Приостановлено', keyboard = Keyboards.keyboard_menu.get_keyboard())

				elif users_info[user_id]['settings_stat'] == True and text.lower() == 'return_settings':
					pass

				elif users_info[user_id]['settings_stat'] == True and text.lower().startswith('speed'):
					try:
						if float(text.split()[1]) <= 10.0:
							users_info[user_id]['return_settings']['speed'] = float(text.split()[1])
							Main.write_db(users_info = users_info)
							Main.send_msg(message = resp['done'], keyboard = Keyboards.stop.get_keyboard())
					except ValueError:
						Main.send_msg(message = 'Кажется, вы ввели неверное знаечние', keyboard = Keyboards.stop.get_keyboard())

				elif users_info[user_id]['settings_stat'] == True and text.lower().startswith('alt'):
					try:
						if float(text.split()[1]) <= 100:
							users_info[user_id]['return_settings']['alt'] = float(text.split()[1])
							Main.write_db(users_info = users_info)
							Main.send_msg(message = resp['done'], keyboard = Keyboards.stop.get_keyboard())
					except ValueError:
						Main.send_msg(message = 'Кажется, вы ввели неверное знаечние', keyboard = Keyboards.stop.get_keyboard())

				elif users_info[user_id]['settings_stat'] == True and text.lower().startswith('action'):
					if text.lower().split()[1] == 'hover' or text.lower().split()[1] == 'land':
						users_info[user_id]['return_settings']['action'] = text.lower().split()[1]
						Main.write_db(users_info = users_info)
						Main.send_msg(message = resp['done'], keyboard = Keyboards.stop.get_keyboard())
					else:
						Main.send_msg(message = 'Кажется, вы ввели неверное знаечние', keyboard = Keyboards.stop.get_keyboard())

				elif users_info[user_id]['settings_stat'] == True and text.lower().startswith('to'):
					if text.lower().split()[1] == 'user' or text.lower().split()[1] == 'takeoff':
						users_info[user_id]['return_settings']['to'] = text.lower().split()[1]
						Main.write_db(users_info = users_info)
						Main.send_msg(message = resp['done'], keyboard = Keyboards.stop.get_keyboard())
					else:
						Main.send_msg(message = 'Кажется, вы ввели неверное знаечние', keyboard = Keyboards.stop.get_keyboard())


				sio.disconnect()

				print("I'm disconnected!")


except Exception as ex:
	print('ERROR NAME: ' + str(ex))
	time.sleep(1)
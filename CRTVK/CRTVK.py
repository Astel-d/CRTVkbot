import os #Import standart python modules.
import time
import json
import urllib.request

import base64 #Import libraries.
import vk_api
import socketio
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.upload import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType

from responses import responses #Import project file.



group_id ='Your group id' 
token = "Your bot token" 


vk_session = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, group_id)  #Auth bot.
vk = vk_session.get_api()
VkUpload = VkUpload(vk)

sio = socketio.Client() #Create an instance of the class according to the socket io documentation.



with open("users.json", "r") as read_file: #Read json db.
	users_info = json.load(read_file)


class Main():

	def send_msg(self, message=None, attachment=None, keyboard=None):
		"""
		Send message function.
		"""
		vk.messages.send(
			peer_id = peer_id, #message destination id
			random_id = get_random_id(), #required argument
			message = message, #Message text
			keyboard = keyboard, #Keyboard name
			attachment = attachment #Attachment id
		)


	def send_code(self, url=None, doc_name=None):
		"""
		Send code to clover function.
		"""
		urllib.request.urlretrieve(url, doc_name) #Download user code.
		f = open(doc_name, 'r', encoding='utf-8') #Open code file.
		file = f.read() #Read code
		sio.emit('newMission', file) #Send code to server 


	def send_photo(self):
		"""
		get photo from clover function.
		"""
		sio.emit('req', {'body': 'photo'}) #Send request to server.
		time.sleep(5) #Wait
		@sio.on('photofromclover') #Recive answer.
		def on_message(photo):
			photo_name = 'photo_' + user_id + '.png' #Assign a unique name for each user
			with open(photo_name, 'wb') as write_photo:
				image_encode = bytes(str(photo), 'UTF-8') #Endode photo frome base 64
				write_photo.write(base64.decodebytes(image_encode)) #Write photo to file
			photo_upload = VkUpload.photo_messages(photos = photo_name, peer_id = peer_id) #Get the url to upload to the server
			self.send_msg(message = resp['photo'], attachment = 'photo' + str(photo_upload[0]['owner_id']) + "_" + str(photo_upload[0]['id'])) #Send photo to user.
			os.remove(photo_name)


	def write_db(self, users_info):
		"""
		Write users info to data base function.
		"""
		users_info = users_info
		with open("users.json", "w") as write_file:
			json.dump(users_info, write_file)



Main = Main() #Create an instance of the class.


class Keyboards():
	"""
	All keyboards.
	"""
	keyboard_menu = VkKeyboard(one_time=False) #Create keyboards
	keyboard_language = VkKeyboard(one_time=True)
	keyboard_login = VkKeyboard(one_time=True)
	stop = VkKeyboard(one_time=False)
	location = VkKeyboard(one_time=False)

	keyboard_menu.add_button('Land', color=VkKeyboardColor.POSITIVE) #Add button to keyboards 
	keyboard_menu.add_button('Hover', color=VkKeyboardColor.POSITIVE)
	keyboard_menu.add_line() #Add line to keyboards
	keyboard_menu.add_button('Get photo', color=VkKeyboardColor.POSITIVE)
	keyboard_menu.add_button('Disarm', color=VkKeyboardColor.NEGATIVE)
	keyboard_menu.add_line()
	keyboard_menu.add_button('Return', color=VkKeyboardColor.POSITIVE)
	keyboard_menu.add_button('Send code', color=VkKeyboardColor.POSITIVE)
	keyboard_menu.add_line()
	keyboard_menu.add_button('Return settings', color = VkKeyboardColor.PRIMARY)
	keyboard_menu.add_line()
	keyboard_menu.add_button('Log out', color = VkKeyboardColor.PRIMARY)

	stop.add_button('Stop', color=VkKeyboardColor.NEGATIVE)

	location.add_location_button()
	location.add_line()
	location.add_button('Stop', color=VkKeyboardColor.NEGATIVE)

	keyboard_language.add_button('ru', VkKeyboardColor.POSITIVE) 
	keyboard_language.add_button('en',VkKeyboardColor.POSITIVE)

	keyboard_login.add_button('sign in', VkKeyboardColor.POSITIVE)


while True:
	try:
		for event in longpoll.listen(): #Wait vk_api event 
			
				if event.type == VkBotEventType.MESSAGE_NEW: #Check if it's a message.

										
					vk_message = event.object['message'] #Get message object.
					user_id = str(vk_message['from_id']) #Get user_id.
					peer_id = vk_message['peer_id'] #Dialog id.
					text = vk_message['text'] #Get message text.
					try:
						sio.connect('https://48c5-94-29-124-254.eu.ngrok.io/', wait_timeout = 10) #Connect to server
					except socketio.exceptions.ConnectionError:
						time.sleep(1)

					try:
						uid = users_info[user_id]['uid']
						if uid != None:
							sio.emit('uid', uid) #Send user uid to server.
					except KeyError:
						pass

					"""
					Handling messages from new users.
					"""


					if user_id not in users_info: #Check user id in db.
						users_info[user_id] = {'settings_stat': False, 'lang':None, 'location_stat':False, 'report_mode': None, 'send_mode': False, 'login_stat':False, 'uid':None, 'return_settings':{'to':None, 'speed':None, 'alt':None, 'action': None}, 'login':None, 'password':None} #If not, then we assign a standard set of values
						Main.write_db(users_info = users_info) #Rewrite json db.

					if users_info[user_id]['lang'] == 'ru' or users_info[user_id]['lang'] == 'en':
						resp = responses[users_info[user_id]['lang']]

					if users_info[user_id]['lang'] == None and text.lower() != 'ru' and text.lower() != 'en': #Check user language.
						Main.send_msg(message = 'Choose language', keyboard = Keyboards.keyboard_language.get_keyboard()) #Send message with keyboard to select a language. 

					if text.lower() == 'ru':
						users_info[user_id]['lang'] = 'ru'
						resp = responses[users_info[user_id]['lang']]
						Main.write_db(users_info=users_info)
						Main.send_msg(message = resp['auth'][0], keyboard = Keyboards.keyboard_login.get_keyboard()) #We assign ru lang

					elif text.lower() == 'en':
						users_info[user_id]['lang'] = 'en'
						resp = responses[users_info[user_id]['lang']]
						Main.write_db(users_info=users_info)
						Main.send_msg(message = resp['auth'][0], keyboard = Keyboards.keyboard_login.get_keyboard()) #We assign en lang

					if (text.lower() == 'sign in' or users_info[user_id]['login_stat'] == True) and users_info[user_id]['lang'] != None and users_info[user_id]['uid'] == None: #Sing in user algorithm
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
								if res['body'] == "nickname_error": #Not user name in db
									Main.send_msg(message = resp['auth'][2], keyboard = Keyboards.keyboard_login.get_keyboard())
									users_info[user_id]['login'] = None 
									users_info[user_id]['password'] = None

								elif res['body'] == "password_error": #Incorrect user password
									Main.send_msg(message = resp['auth'][3], keyboard = Keyboards.keyboard_login.get_keyboard())
									users_info[user_id]['login'] = None 
									users_info[user_id]['password'] = None

								elif res['body'] == "successful": #All ok
									users_info[user_id]['uid'] = res['uid']
									Main.write_db(users_info = users_info)
									Main.send_msg(message = resp['auth'][4], keyboard = Keyboards.keyboard_menu.get_keyboard())
									users_info[user_id].pop('login')
									users_info[user_id].pop('password')
									Main.write_db(users_info = users_info)



					if users_info[user_id]['uid'] != None: #If the user is sign in
						if users_info[user_id]['settings_stat'] != True:
							if text.lower() == 'land': #Send land command to server
								sio.emit('req', {'body':'land'})
								Main.send_msg(message = resp['done'])

							if text.lower() == 'hover': #Send hover command to server
								sio.emit('req', {'body':'hover'})
								Main.send_msg(message = resp['done'])

							if text.lower() == 'disarm': #Send disarm command to server
								sio.emit('req', {'body':'disarm'})
								Main.send_msg(message = resp['done'])

							if text.lower() == 'get photo': #Send get photo command to server 
								Main.send_photo()

							if text.lower() == 'log out': #Log out user command
								Main.send_msg(resp['log out']) 
								users_info.pop(user_id) #Delete user from db
								Main.write_db(users_info = users_info)
								Main.send_msg(message = 'Choose language', keyboard = Keyboards.keyboard_language.get_keyboard())

							if text.lower() == 'send code' and users_info[user_id]['send_mode'] == False: #Send code to clover algorithm
								Main.send_msg(message = resp['upload_file'], keyboard = Keyboards.stop.get_keyboard())
								users_info[user_id]['send_mode'] = True
							try:
								if users_info[user_id]['send_mode'] == True and text.lower() == 'send code':
									pass
								if users_info[user_id]['send_mode'] == True and text.lower() == 'stop': #Stop send code to clover
									Main.send_msg(message = resp['stop'], keyboard = Keyboards.keyboard_menu.get_keyboard())
									users_info[user_id]['send_mode'] = False
								elif users_info[user_id]['send_mode'] == True and vk_message['attachments'][0]['type'] != 'doc': #Check message type
									Main.send_msg(message = resp['dont_code'])
								elif users_info[user_id]['send_mode'] == True and vk_message['attachments'][0]['type'] == 'doc' and vk_message['attachments'][0]['doc']['ext'] == 'py': #If type = doc and .py
									Main.send_code(url = vk_message['attachments'][0]['doc']['url'], doc_name = 'code_' + str(user_id) + '.py')
									os.remove('code_' + str(user_id) + '.py')
									users_info[user_id]['send_mode'] = False
									Main.send_msg(message = resp['done'], keyboard = Keyboards.keyboard_menu.get_keyboard())
									
							except Exception as E:
								print(E)

							if text.lower() == 'return' or users_info[user_id]['location_stat']== True: #Return function 
								if users_info[user_id]['location_stat'] == False and users_info[user_id]['return_settings']['to'] == 'user' and users_info[user_id]['return_settings']['speed'] != None and users_info[user_id]['return_settings']['alt'] != None and users_info[user_id]['return_settings']['action'] != None and users_info[user_id]['return_settings']['to'] != None: 
									Main.send_msg(message = resp['location'], keyboard = Keyboards.location.get_keyboard())
								users_info[user_id]['location_stat'] = True
								if users_info[user_id]['location_stat'] == True and users_info[user_id]['return_settings']['speed'] != None and users_info[user_id]['return_settings']['alt'] != None and users_info[user_id]['return_settings']['action'] != None and users_info[user_id]['return_settings']['to'] != None:
									if users_info[user_id]['return_settings']['to'] == 'takeoff': #If clover return to takeoff
										users_info[user_id]['location_stat'] = False
										sio.emit('req', {'body':'returnToHome', 'data':{'to':'takeoff', 'alt':users_info[user_id]['return_settings']['alt'], 'speed':users_info[user_id]['return_settings']['speed'], 'action':users_info[user_id]['return_settings']['action']}})
										Main.send_msg(message = resp['return'][1], keyboard = Keyboards.keyboard_menu.get_keyboard())

									elif users_info[user_id]['location_stat'] == True and text.lower() == "stop": #Stop return function 
										users_info[user_id]['location_stat'] = False
										Main.send_msg(message = resp['stop'], keyboard = Keyboards.keyboard_menu.get_keyboard())
									
									elif text.lower() != 'return' and users_info[user_id]['return_settings']['to'] == 'user': #If clover return to user
										
										try:
											sio.emit('req', {'body':'returnToHome', 'data':{'to':'user', 'lat':vk_message['geo']['coordinates']['latitude'], 'lon':vk_message['geo']['coordinates']['longitude'], 'alt':users_info[user_id]['return_settings']['alt'], 'speed':users_info[user_id]['return_settings']['speed'], 'action':users_info[user_id]['return_settings']['action']}})
											users_info[user_id]['location_stat'] = False
											Main.send_msg(message = resp['return'][0], keyboard = Keyboards.keyboard_menu.get_keyboard())
										except Exception as E:
											time.sleep(0.1)
								else:
									Main.send_msg(message = resp['return'][2] + str(users_info[user_id]['return_settings']), keyboard = Keyboards.keyboard_menu.get_keyboard())
									users_info[user_id]['location_stat'] = False


						if text.lower() == 'return settings': #Set return settings function
							users_info[user_id]['settings_stat'] = True
							Main.send_msg(resp['settings'][0])
							Main.send_msg(message = resp['settings'][1] + str(users_info[user_id]['return_settings']), keyboard = Keyboards.stop.get_keyboard())

						if users_info[user_id]['settings_stat'] == True and text.lower() == 'stop': #Stop 
							users_info[user_id]['settings_stat'] = False
							Main.write_db(users_info = users_info)
							Main.send_msg(message = resp['stop'], keyboard = Keyboards.keyboard_menu.get_keyboard())

						elif users_info[user_id]['settings_stat'] == True and text.lower() == 'return_settings':
							pass

						elif users_info[user_id]['settings_stat'] == True and text.lower().startswith('speed'): #Set speed
							if float(text.split()[1]) <= 10.0:
								users_info[user_id]['return_settings']['speed'] = float(text.split()[1])
								Main.write_db(users_info = users_info)
								Main.send_msg(message = resp['done'], keyboard = Keyboards.stop.get_keyboard())
							else:
								Main.send_msg(message = resp['settings'][2], keyboard = Keyboards.stop.get_keyboard())


						elif users_info[user_id]['settings_stat'] == True and text.lower().startswith('alt'): #Set alt

							if float(text.split()[1]) <= 100:
								users_info[user_id]['return_settings']['alt'] = float(text.split()[1])
								Main.write_db(users_info = users_info)
								Main.send_msg(message = resp['done'], keyboard = Keyboards.stop.get_keyboard())
							else:
								Main.send_msg(message = resp['settings'][2], keyboard = Keyboards.stop.get_keyboard())


						elif users_info[user_id]['settings_stat'] == True and text.lower().startswith('action'): #Set action
							if text.lower().split()[1] == 'hover' or text.lower().split()[1] == 'land':
								users_info[user_id]['return_settings']['action'] = text.lower().split()[1]
								Main.write_db(users_info = users_info)
								Main.send_msg(message = resp['done'], keyboard = Keyboards.stop.get_keyboard())
							else:
								Main.send_msg(message = resp['settings'][2], keyboard = Keyboards.stop.get_keyboard())

						elif users_info[user_id]['settings_stat'] == True and text.lower().startswith('to'): #Set to
							if text.lower().split()[1] == 'user' or text.lower().split()[1] == 'takeoff':
								users_info[user_id]['return_settings']['to'] = text.lower().split()[1]
								Main.write_db(users_info = users_info)
								Main.send_msg(message = resp['done'], keyboard = Keyboards.stop.get_keyboard())
							else:
								Main.send_msg(message = resp['settings'][2], keyboard = Keyboards.stop.get_keyboard())

						sio.disconnect() #Disconnect from server

	except Exception as ex:
		print('ERROR NAME: ' + str(ex))
		time.sleep(1)


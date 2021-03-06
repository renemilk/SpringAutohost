# -*- coding: ISO-8859-1 -*-
import threading
import time
import socket
import hashlib, base64, binascii
#import LobbyBS
import random

class Lobby (threading.Thread):
	def __init__ (self, ClassServer, FunctionCallbackChat, FunctionCallbackEvent, LoginInfo):
		threading.Thread.__init__ (self)
		self.Debug = ClassServer.Debug
		self.Server = ClassServer
		self.CallbackChat = FunctionCallbackChat
		self.CallbackEvent = FunctionCallbackEvent
#		self.LobbyBS = LobbyBS.LobbyBS (ClassServer, self)
		self.User = LoginInfo[0]
		self.Passwd = LoginInfo[1]
		self.BattlePort = LoginInfo[2]
		self.IP = '188.165.214.142'
		self.Host = ClassServer.Config['LobbyServer']['Host']
		self.Port = ClassServer.Config['LobbyServer']['Port']
		self.Ping = LobbyPing (self, ClassServer.Debug)
		self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.Active = 0
		self.LoggedIn = 0
		self.LoggedInQueue = []
		
		self.Users = {}
		self.Battles = {}
		self.BattleUsers = {}
		self.BattleID = 0
		self.Channels = {}
		
		# I = Int, F = Float, V = String, S = Sentence, BXX = BitMask XX chars
		self.Commands = {
			'TASServer':['V', 'V', 'I', 'I'],
			'ACCEPTED':['V'],
			'MOTD':['S'],				# Ignore
			'LOGININFOEND':[],			# Ignore
			'PONG':[],					# Ignore
			'ADDUSER':['V', 'V', 'I', 'I'],
			'REMOVEUSER':['V'],
			'CLIENTSTATUS':['V', 'B7'],
			'BATTLEOPENED':['I', 'I', 'I', 'V', 'V', 'I', 'I', 'I', 'I', 'I', 'S', 'S', 'S'],
			'JOINEDBATTLE':['I', 'V', 'V'],
			'LEFTBATTLE':['I', 'V'],
			'BATTLECLOSED':['I'],
			'UPDATEBATTLEINFO':['I', 'I', 'I', 'I', 'S'],
			'SAIDPRIVATE':['V', 'S'],
			'SAIDPRIVATEEX':['V', 'S'],
			'SAYPRIVATE':['V', '*'],	# Ignore ECHO reply...
			'SAID':['V', 'V', 'S'],
			'SAIDEX':['V', 'V', 'S'],
			'SAIDBATTLE':['V', 'S'],
			'SAIDBATTLEEX':['V', 'S'],
			'REQUESTBATTLESTATUS':[],
			'JOINBATTLEREQUEST':['V', 'V'],
			'CLIENTBATTLESTATUS':['V', 'B32', 'I'],
			'OPENBATTLE':['I'],
			'JOIN':['V'],
			'CLIENTS':['V', 'S'],
			'JOINED':['V', 'V'],
			'LEFT':['V', 'V'],
			'AGREEMENTEND':[],
			'AGREEMENT':[],
		}
	
	
	def run (self):
		self.Debug ('Lobby start')
		self.Connect ()
		RawData = ''
		while (self.Active):
			Info = {"Time":int (time.time ()), "Loops":0}
			Data = ""
			while (self.Active):
				Data = self.Socket.recv (1)
				if (Data):
					RawData = RawData + Data
					Lines = RawData.split ("\n")
					if (len (Lines) > 1):
						RawData = Lines[1]
						self.HandleCommand (Lines[0])
				else:
					if (Info["Time"] == int (time.time ())):
						Info["Loops"] = Info["Loops"] + 1
						if (Info["Loops"] > 10):
							print "TERMINATING"
							self.Active = 0
					else:
						Info = {"Time":int (time.time ()), "Loops":0}
					print "*** No data :/"
		

	def HandleCommand (self, RawData):
#		self.Debug ('Command::' + str (Command))

		Command = self.ReturnValue (RawData, ' ')
		Data = RawData[len (Command) + 1:]
		if (self.Commands.has_key (Command)):
			Arg = []
			for Field in self.Commands[Command]:
				RawArg = ''
				if (Field == 'I'):
					NewArg = int (self.ReturnValue (Data, ' '))
				if (Field == 'F'):
					NewArg = float (self.ReturnValue (Data, ' '))
				elif (Field == 'V'):
					NewArg = str (self.ReturnValue (Data, ' '))
				elif (Field[0:1] == 'B'):
					RawArg = self.ReturnValue (Data, ' ')
					NewArg = self.dec2bin (RawArg, int (Field[1:]))
				elif (Field == 'S'):
					NewArg = self.ReturnValue (Data, '\t')
				elif Field == '*':
					NewArg = Data
				try:
					Arg.append (NewArg)
					if (len (RawArg) > 0):
						NewArg = RawArg
					Data = Data[len (str (NewArg)) + 1:]
				except:
					print '\n\nCOMMAND FAILED\n\n'
		else:
			self.Debug ('UnknownCommand::' + str (RawData))

		if (Command == "TASServer"):
			self.Login ()
		elif (Command == "ACCEPTED"):
			self.Ping.start ()
			self.SetLoggedIn ()
		elif (Command == 'LOGININFOEND' or Command == 'PONG' or Command == 'MOTD'):
			pass
		elif (Command == "ADDUSER"):
			if (not self.Users.has_key (Arg[1])):
				self.Users[Arg[0]] = {
					'Country':Arg[1],
					'CPU':Arg[2],
					'ID':Arg[3],
					'InGame':0,
					'Away':0,
					'Rank':0,
					'Moderator':0,
					'Bot':0,
					'InBattle':0,
				}
			else:
				self.Debug ('ERROR::User exsits' + str (RawData))
		elif (Command == "REMOVEUSER"):
			if (self.Users.has_key (Arg[0])):
				del (self.Users[Arg[0]])
			else:
				self.Debug ('ERROR::User doesn\'t exist::' + str (RawData))
		elif (Command == "CLIENTSTATUS"):
			if (self.Users.has_key (Arg[0])):
				self.Users[Arg[0]]["InGame"] = Arg[1][0]
				self.Users[Arg[0]]["Away"] = Arg[1][1]
				self.Users[Arg[0]]['Rank'] = Arg[1][4] * 4 + Arg[1][3] * 2 + Arg[1][2]
				self.Users[Arg[0]]['Moderator'] = Arg[1][5]
				self.Users[Arg[0]]['Bot'] = Arg[1][6]
			else:
				self.Debug ('ERROR::User doesn\'t exsits::' + str (RawData))
		elif Command == 'BATTLEOPENED':
			if (not self.Battles.has_key (Arg[0])):
				self.Battles[Arg[0]] = {
					'Type':{0:'B', 1:'R'}[Arg[1]],
					'Nat':Arg[2],
					'Founder':Arg[3],
					'IP':Arg[4],
					'Port':Arg[5],
					'MaxPlayers':Arg[6],
					'Passworded':Arg[7],
					'MinRank':Arg[8],
					'MapHash':Arg[9],
					'Map':Arg[10],
					'Title':Arg[11],
					'Mod':Arg[12],
					'Users':[Arg[3]],
					'Spectators':0,
					'Players':0,
					'Locked':0,
				}
				self.SmurfDetection (Arg[3], Arg[4])
			else:
				self.Debug ('ERROR::Battle exsits::' + str (RawData))
		elif Command == 'OPENBATTLE':
			self.BattleID = Arg[0]
			self.Users[self.User]['InBattle'] = Arg[0]
			self.BattleUsers[self.User] = {
				'Spectator':1,
				'Password':'Humbug',
				'Team':None,
				'Ally':None,
				'Side':None,
				'Color':None,
				'Handicap':None,
				'Synced':1,
			}
		elif Command == 'JOINEDBATTLE':
			if (self.Battles.has_key (Arg[0])):
				self.Battles[Arg[0]]['Users'].append (Arg[1])
				if Arg[0] == self.BattleID:
					self.BattleUsers[Arg[1]] = {
						'Password':Arg[2],
					}
			else:
				self.Debug ('ERROR::Battle doesn\'t exsits::' + str (RawData))
			if (self.Users.has_key (Arg[1])):
				self.Users[Arg[1]]['InBattle'] = Arg[0]
			else:
				self.Debug ('ERROR::User doesn\'t exsits::' + str (RawData))
		elif (Command == "LEFTBATTLE"):
			if (self.Battles.has_key (Arg[0])):
				self.Battles[Arg[0]]['Users'].remove (Arg[1])
			else:
				self.Debug ('ERROR::Battle doesn\'t exsits::' + str (RawData))
			if (self.Users.has_key (Arg[1])):
				self.Users[Arg[1]]['InBattle'] = 0
			else:
				self.Debug ('ERROR::User doesn\'t exsits::' + str (RawData))
		elif (Command == "BATTLECLOSED"):
			if (self.Battles.has_key (Arg[0])):
				del (self.Battles[Arg[0]])
			else:
				self.Debug ('ERROR::Battle doesn\'t exsits::' + str (RawData))
		elif Command == 'UPDATEBATTLEINFO':
			if (self.Battles.has_key (Arg[0])):
				self.Battles[Arg[0]]['Spectators'] = Arg[1]
				self.Battles[Arg[0]]['Players'] = len (self.Battles[Arg[0]]['Users']) - Arg[1]
				self.Battles[Arg[0]]['Locked'] = Arg[2]
				self.Battles[Arg[0]]['MapHash'] = Arg[3]
				self.Battles[Arg[0]]['Map'] = Arg[4]
			else:
				self.Debug ('ERROR::Battle doesn\'t exsits::' + str (RawData))
		elif Command == 'SAIDPRIVATE' or Command == 'SAID' or Command == 'SAIDEX' or Command == 'SAIDBATTLE' or Command == 'SAIDBATTLEEX' or Command == 'SAIDPRIVATEEX':
			print (RawData)
			if Arg[0] != self.User:
				self.CallbackChat (Command, Arg)
		elif Command == 'REQUESTBATTLESTATUS':
			self.Send ('MYBATTLESTATUS 4194304 000000')
		elif Command == 'JOINBATTLEREQUEST':
			self.Send ('JOINBATTLEACCEPT ' + str (Arg[0]))
			self.SmurfDetection (Arg[0], Arg[1])
		elif Command == 'CLIENTBATTLESTATUS':
			self.BattleUsers[Arg[0]]['Ready'] = int (Arg[1][1])
			self.BattleUsers[Arg[0]]['Team'] = int (Arg[1][5]) * 8 + int (Arg[1][4]) * 4 + int (Arg[1][3]) * 2 + int (Arg[1][2])
			self.BattleUsers[Arg[0]]['Ally'] = int (Arg[1][9]) * 8 + int (Arg[1][8]) * 4 + int (Arg[1][7]) * 2 + int (Arg[1][6])
			self.BattleUsers[Arg[0]]['Spectator'] = {0:1, 1:0}[int (Arg[1][10])]
			self.BattleUsers[Arg[0]]['Handicap'] = int (Arg[1][17]) * 64 + int (Arg[1][16]) * 32 + int (Arg[1][15]) * 16 + int (Arg[1][14]) * 8 + int (Arg[1][13]) * 4 + int (Arg[1][12]) * 2 + int (Arg[1][11])
			self.BattleUsers[Arg[0]]['Synced'] = int (Arg[1][23]) * 2 + int (Arg[1][22])
			self.BattleUsers[Arg[0]]['Side'] = int (Arg[1][27]) * 8 + int (Arg[1][26]) * 4 + int (Arg[1][25]) * 2 + int (Arg[1][24])
			self.BattleUsers[Arg[0]]['Color'] = "%X" % int (Arg[2])
			while (len (self.BattleUsers[Arg[0]]['Color']) < 6):
				self.BattleUsers[Arg[0]]['Color'] = str (0) + self.BattleUsers[Arg[0]]['Color']
		elif Command == 'JOIN':
			self.Channels[Arg[0]] = {'Users':{}}
		elif Command == 'CLIENTS':
			for User in Arg[1].split (' '):
				self.Channels[Arg[0]]['Users'][User] = User
		elif Command == 'JOINED':
			self.Channels[Arg[0]]['Users'][Arg[1]] = Arg[1]
		elif Command == 'LEFT':
			del (self.Channels[Arg[0]]['Users'][Arg[1]])
		elif Command == 'AGREEMENTEND':
			self.Send ('CONFIRMAGREEMENT')

#			print ('\n' + str (RawData))
#			print (str (Arg))
#			print (self.BattleUsers[Arg[0]])
		if (self.Commands.has_key (Command)):
			self.CallbackEvent (Command, Arg)

	
	def Login (self):
		self.Debug ('Lobby Login')
		self.Send ("LOGIN " + str (self.User) + " " + str (base64.b64encode (binascii.a2b_hex (hashlib.md5 (self.Passwd).hexdigest ()))) + " 0 " + str (self.IP) + " DoxBot\t\ta b sp", 1)
		
	def Logout (self):
		self.Debug ('Lobby exit')
		self.Send ("EXIT")
		self.Ping.Active = False
		self.LoggedIn = False
	
	def Quit(self):
		if self.LoggedIn:
			self.Logout()
		self.Socket.shutdown(socket.SHUT_RDWR)
		self.Socket.close()
		self.Active = False
			
	
	def BattleOpen (self, Mod, Map, Title, MaxPlayers, MinRank = 0, Password = '*', Type = 0, Nat = 0):
		self.Send ("OPENBATTLE " + str (Type) + ' ' + str (Nat) + ' ' + str (Password) + ' ' + str (self.BattlePort) + ' ' + str (MaxPlayers) + ' ' + str (self.Server.Mods[Mod]['Hash']) + ' ' + str (MinRank) + ' ' + str (self.Server.Maps[Map]['Hash']) + ' ' + str (Map) + '\t' + str (Title) + '\t' + str (Mod))
		#self.Send ("OPENBATTLE %d %d %s %d %d %s %d %s %s %s %s"%(Type,Nat,Password,self.BattlePort,MaxPlayers,self.Server.Mods[Mod]['Hash'],MinRank,self.Server.Maps[Map]['Hash'],Map,Title,Mod) )
	
	def BattleMap (self, Map):
		self.Battles[self.BattleID]['Map'] = Map
		self.BattleUpdate ()
#		self.Send ('UPDATEBATTLEINFO ' + str (self.Battles[self.BattleID]['Spectators']) + ' ' + str (self.Battles[self.BattleID]['Locked']) + ' ' + str (self.Server.Maps[Map]['Hash']) + ' ' + str (Map))
	
	def BattleSay (self, Message, Me = 0):
		if (Me):
			self.Send ('SAYBATTLEEX ' + str (Message))
		else:
			self.Send ('SAYBATTLE ' + str (Message))
	
	def BattleStart (self):
		self.Send ('MYSTATUS 1')

	def BattleStop (self):
		self.Send ('MYSTATUS 0')
	
	def BattleLock (self, Lock):
		if self.Battles[self.BattleID]['Locked'] != Lock:
			self.Battles[self.BattleID]['Locked'] = Lock
			self.BattleUpdate ()
	
	def BattleUpdate (self):		
		self.Send ('UPDATEBATTLEINFO ' + str (self.Battles[self.BattleID]['Spectators']) + ' ' + str (self.Battles[self.BattleID]['Locked']) + ' ' + str (self.Server.Maps[self.Battles[self.BattleID]['Map']]['Hash']) + ' ' + str (self.Battles[self.BattleID]['Map']))
	
	def BattleKick (self, User):
		self.Send ('KICKFROMBATTLE ' + str (User))
	
	def BattleRing (self, User):
		self.Send ('RING ' + str (User))
	
	def BattleAddBox (self, Ally, Left, Top, Right, Bottom):
		self.Send ('ADDSTARTRECT ' + str (Ally) + ' ' + str (Left) + ' ' + str (Top) + ' ' + str (Right) + ' ' + str (Bottom))
	
	
	def UserSay (self, User, Message):
		self.Send ('SAYPRIVATE ' + str (User) + ' ' + str (Message))
	
	
	def ChannelJoin (self, Channel, Password = ''):
		self.Send ('JOIN ' + str (Channel))
	
	
	def Send (self, Command, Force = 0):
		if (self.LoggedIn or Force == 1):
			self.Debug ("SEND::" + str (Command))
			self.Socket.send (Command + "\n")
		else:
			self.Debug ("SEND_QUEUE::" + str (Command))
			self.LoggedInQueue.append (Command)
	
	
	def Connect (self):
		self.Debug ('Lobby connect')
		self.Socket.connect ((str (self.Host), int (self.Port)))
		self.Active = 1
	
	
	def SetLoggedIn (self):
		self.Debug ('Logged in')
		self.LoggedIn = 1
		if (len (self.LoggedInQueue)):
			for Command in self.LoggedInQueue:
				self.Send (Command)
			self.LoggedInQueue = []
	
	
	def dec2bin (self, value, numdigits):
		val = int (value)
		digits = [0 for i in range (numdigits)]
		for i in range (numdigits):
			val, digits[i] = divmod (val, 2)
		return (digits)
	
	
	def ReturnValue (self, String, StopChar):
#		print 'Return::' + str (String) + '::[[' + str (StopChar) + ']]'
		if (String.find (StopChar) != -1):
#			print 'Found[[' + str (String[0:String.find (StopChar)]) + ']]'
			return (String[0:String.find (StopChar)])
#		print 'NotFound[[' + str (String) + ']]'
		return (String)
	
	
	def SmurfDetection (self, User, IP):
		Ignore = 1
#		self.Debug ('SMURF_DATA::' + User + '::' + IP)
	

class LobbyPing (threading.Thread):
	def __init__ (self, ClassLobby, FunctionDebug):
		threading.Thread.__init__ (self)
		self.Lobby = ClassLobby
		self.Debug = FunctionDebug
		self.Active = 1
	
	
	def run (self):
		self.Debug ('Lobby Ping start')
		while (self.Active):
#			self.Debug ('Lobby PING')
			self.Lobby.Send ("PING")
			time.sleep (25)
#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
import LoadCFG
import Debug
import Master, Host
import time
import Unitsync


class Server:
	def __init__ (self):
		self.ClassDebug = Debug.Debug ()
		self.Debug = self.ClassDebug.Debug
		self.Debug ("Initiate")
		self.LoadCFG = LoadCFG.LoadCFG (self)
		
		self.Unitsync = Unitsync.Unitsync (self.Config['UnitsyncPath'])
		self.Unitsync.Init (True, 1)
		self.LoadMaps ()
		self.LoadMods ()

		self.Master = Master.Master (self)
		self.Hosts = {}

		
		self.Start ()
		
	
	def Start (self):
		self.Debug ("Start server")
#		self.Master.start ()
		print (self.Groups['teh']['Accounts'][0])
		self.SpawnHost ('teh', self.Groups['teh']['Accounts'][0])		#Debug testing
		
	
	def SpawnHost (self, Group, HostAccount):
		self.Debug ("Spawn Host (" + str (Group) + "/" + str (HostAccount) + ")")
		if (self.Groups.has_key (Group)):
			if (self.Hosts.has_key (HostAccount[0])):
				self.Hosts[HostAccount[0]].HostBattle (Group)
			else:
				self.Hosts[HostAccount[0]] = Host.Host (self, Group, HostAccount)
				self.Hosts[HostAccount[0]].start ()
		else:
			self.Debug ("ERROR::Group unknown" + str (Group))
	

	def LoadMaps (self):
		self.Debug ('Load maps')
		self.Maps = {}
		for iMap in range (0, self.Unitsync.GetMapCount ()):
			Map = self.Unitsync.GetMapName (iMap)
			self.Maps[Map] = {'Hash':self.SignInt (self.Unitsync.GetMapChecksum (iMap))}
			if (self.Unitsync.GetMapOptionCount (Map)):
				self.Maps[Map]['Options'] = {}
				for iOpt in range (0, self.Unitsync.GetMapOptionCount (Map)):
					self.Maps[Map]['Options'][iOpt] = self.LoadOption (iOpt)
					if (len (self.Maps[Map]['Options'][iOpt]) == 0):
						del (self.Maps[Map]['Options'][iOpt])
	
	
	def LoadMods (self):
		self.Debug ('Load mods')
		self.Mods = {}
		for iMod in range (0, self.Unitsync.GetPrimaryModCount ()):
			self.Unitsync.AddAllArchives (self.Unitsync.GetPrimaryModArchive (iMod))
			Mod = self.Unitsync.GetPrimaryModName (iMod)
			self.Mods[Mod] = {
				'Hash':self.SignInt (self.Unitsync.GetPrimaryModChecksum (iMod)),
				'Title':self.Unitsync.GetPrimaryModName (iMod),
				'Sides':{},
				'Options':{},
			}
			if (self.Unitsync.GetSideCount()):
				for iSide in xrange (self.Unitsync.GetSideCount()):
					self.Mods[Mod]['Sides'][iSide] = self.Unitsync.GetSideName (iSide)
			if (self.Unitsync.GetModOptionCount ()):
				for iOpt in xrange (self.Unitsync.GetModOptionCount ()):
					self.Mods[Mod]['Options'][iOpt] = self.LoadOption (iOpt)
					if (len (self.Mods[Mod]['Options'][iOpt]) == 0):
						del (self.Mods[Mod]['Options'][iOpt])
	
	
	def LoadOption (self, iOpt):
		Data = {}
		if (self.Unitsync.GetOptionType (iOpt) == 1):
			Data = {
				'Key':self.Unitsync.GetOptionKey (iOpt),
				'Title':self.Unitsync.GetOptionName (iOpt),
				'Type':'Boolean',
				'Default':self.Unitsync.GetOptionBoolDef (iOpt),
			}
		elif (self.Unitsync.GetOptionType (iOpt) == 2):
			Data = {
				'Key':self.Unitsync.GetOptionKey (iOpt),
				'Title':self.Unitsync.GetOptionName (iOpt),
				'Type':'Select',
				'Default':self.Unitsync.GetOptionListDef (iOpt),
				'Options':{},
			}
			if (self.Unitsync.GetOptionListCount (iOpt)):
				for iItem in range (0, self.Unitsync.GetOptionListCount (iOpt)):
					Data['Options'][self.Unitsync.GetOptionListItemKey (iOpt, iItem)] = self.Unitsync.GetOptionListItemName (iOpt, iItem) + ' (' + self.Unitsync.GetOptionListItemDesc (iOpt, iItem) + ')'
		elif (self.Unitsync.GetOptionType (iOpt) == 3):
			Data = {
				'Key':self.Unitsync.GetOptionKey (iOpt),
				'Title':self.Unitsync.GetOptionName (iOpt),
				'Type':'Numeric',
				'Default':self.Unitsync.GetOptionNumberDef (iOpt),
				'Min':self.Unitsync.GetOptionNumberMin (iOpt),
				'Max':self.Unitsync.GetOptionNumberMax (iOpt),
				'Step':self.Unitsync.GetOptionNumberStep (iOpt),
			}
		elif (self.Unitsync.GetOptionType (iOpt) == 5):
			Ignore = 1
		else:
			self.Debug ('ERROR::Unkown options type (' + str (self.Unitsync.GetOptionType (iOpt)) + ')')
		return (Data)
	
	
	def SignInt (self, Int):
		if Int > 2147483648:
			Int = Int - 2147483648 * 2
		return (Int)

S = Server ()

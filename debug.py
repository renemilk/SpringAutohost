# -*- coding: ISO-8859-1 -*-
import os
import inspect
import time

class Debug:
	def __init__ (self):
		i = 1
	
	
	def Debug (self, info):
		frame = inspect.currentframe ()
		filename = os.path.basename (frame.f_back.f_code.co_filename)
		fileline = frame.f_back.f_lineno
		function = frame.f_back.f_code.co_name
#		print (function)
		if not info == 'SEND::PING':
			print (time.strftime ('%Y%m%d %H:%M') + '\t' + filename + '\t' + function + '\t' + info)
#			print (time.strftime ('%Y%m%d %H:%M') + '\t' + filename + ':' + str (fileline) + '\t' + function + '\t' + info)
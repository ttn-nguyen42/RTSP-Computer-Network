from tkinter import *
import tkinter.messagebox
import PIL
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		self.rtp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""Setup button handler."""
		if(self.state==self.INIT):
			self.sendRtspRequest(self.SETUP)
	
	def exitClient(self):
		"""Teardown button handler."""
		if(self.state==self.READY or self.state==self.PLAYING):
			self.sendRtspRequest(self.TEARDOWN)
			self.master.destroy()
			os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)

	def pauseMovie(self):
		"""Pause button handler."""
		if(self.state==self.PLAYING):
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		if(self.state==self.READY):
			threading.Thread(target=self.listenRtp).start()
			self.playEvent=threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY) 
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		while True:
			try:
				data=self.rtp.recv(20480)
				if(data):
					Packet=RtpPacket()
					Packet.decode(data)

					currentframe=Packet.seqNum()

					print('Current Frame: ' +str(currentframe))

					if(currentframe > self.frameNbr):
						self.frameNbr=currentframe
						self.updateMovie(self.writeFrame(Packet.getPayload()))
			except:
				if self.playEvent.isSet():
					break
				if self.teardownAcked==1:
					self.rtp.shutdown(socket.SHUT_RDWR)
					self.rtp.close()
					break
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		name=CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file=open(name,'wb')
		file.write(data)
		file.close()

		return name
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		photo=ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image=photo,height=300)
		self.label.image=photo
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtsp=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		try:
			self.rtsp.connect((self.serverAddr,self.serverPort))
		except:
			tkinter.messagebox.showwarning('Connection Failed','Connection to {} failed'.format(self.serverAddr))
   
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		if requestCode ==  self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
			self.rtspSeq=1

			request= 'SETUP ' + str(self.fileName) + '\n '+ str(self.rtspSeq) + '\n RTSP/1.0 HTP/UDP ' +  str(self.rtpPort) 
			self.rtsp.send(request.encode())
			self.requestSent=self.SETUP
   
		elif requestCode == self.PLAY and self.state == self.READY:
			self.rtspSeq += 1

			request='PLAY ' + '\n '+ str(self.rtspSeq)
			self.rtsp.send(request.encode())
			print('-'*60 + '\n' + 'PLAY request send to Server... \n'+'-'*60)
			self.requestSent=self.PLAY
		elif requestCode ==  self.PAUSE and self.state == self.PLAYING:
			self.rtspSeq +=1

			request='PAUSE ' +'\n '+str(self.rtspSeq)
			self.rtsp.send(request.encode())
			print('-'*60+ '\n'+'PAUSE request sent to Server... \n' + '-'*60)
			self.requestSent=self.PAUSE
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			self.rtspSeq +=1

			request='TEARDOWN '+ '\n '+str(self.rtspSeq)
			self.rtsp.send(request.encode())
			print('-'*60 + '\n' + 'TEARDOWN request send to Server... \n'+'-'*60)
			self.requestSent=self.TEARDOWN
		else:
			return

		print('Data sent : \n {} \n'.format(request))
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while TRUE:
			reply=self.rtsp.recv(1024)
			if reply:
				self.parseRtspReply(reply.decode())
			
			if self.requestSent== self.TEARDOWN:
				self.rtsp.shutdown(socket.SHUT_RDWR)
				self.rtsp.close()
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		lines=data.split('\n')
		seqnum = int (lines[1].split(' ')[1])
		if seqnum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			if(self.sessionId == 0):
				self.sessionId = session
			if(self.sessionId == session):
				print('here')
				if(int(lines[0].split(' ')[1]) == 200):
					if(self.requestSent == self.SETUP):
						print('Updating RTSP state....')
						self.state=self.READY
						print('Setting Up RtpPort for Video Stream')
						self.openRtpPort()
					elif self.requestSent== self.PLAY:
						print('Updating RTSP state.... ')
						self.state=self.PLAYING
						print('-'*60 + '\n Client is Playing ... \n'+'-'*60)
					elif self.requestSent == self.PAUSE:
						print('Updating RTSP state....')
						self.state=self.READY
						self.playEvent.set()
					elif self.requestSent == self.TEARDOWN:
						self.teardownAcked=1
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		
		# Set the timeout value of the socket to 0.5sec
		# ...
		self.rtp.settimeout(0.5)
		try:
			self.rtp.bind((self.serverAddr,self.rtpPort))
			print('Bind RtpPort Success')
		except:
			tkinter.messagebox.showwarning('Unable to Bind','Unable to bind PORT {}'.format(self.rtpPort))

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
		self.pauseMovie()
		if tkinter.messagebox.askokcancel('Exit','Are you want to quit ?'):
			self.exitClient()
		else:
			self.playMovie()

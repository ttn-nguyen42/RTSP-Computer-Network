from tkinter import *
import tkinter.messagebox
import PIL
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
from tkinter import ttk
from RtpPacket import RtpPacket
import os
CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	SWITCHING=3
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	FORWARD	=4
	BACKWARD=5
	SWITCH=6
	
	
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
		self.sendRtspRequest(self.SETUP)
		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		self.play_img = tkinter.PhotoImage(file="./assets/Play Button.png")
		self.pause_img = tkinter.PhotoImage(file="./assets/Pause Button.png")
		self.skip_img = tkinter.PhotoImage(file="./assets/Forward Button.png")
		self.back_img = tkinter.PhotoImage(file="./assets/Backward Button.png")
  
		# # Create Setup button
		# self.setup = Button(self.master, width=20, padx=3, pady=3)
		# self.setup["text"] = "Setup"
		# self.setup["command"] = self.setupMovie
		# self.setup.grid(row=2, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=40, height=40, padx=3, pady=3)
		self.start["image"] = self.play_img
		self.start["text"] = "Play/Pause"
		self.start["command"] = self.playMovie
		self.start.grid(row=2, column=2, padx=2, pady=2)
		
		# # Create Pause button			
		# self.pause = Button(self.master, width=20, padx=3, pady=3)
		# self.pause["text"] = "Pause"
		# self.pause["command"] = self.pauseMovie
		# self.pause.grid(row=2, column=3, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=10, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] = self.exitClient
		self.teardown.grid(row=0, column=4, padx=2, pady=2)
		
		#Create Skip button
		self.skip = Button(self.master, width=40, height=40, padx=3, pady=3)
		self.skip["image"] = self.skip_img
		self.skip["text"] = "Forward"
		self.skip["command"] =  self.forward
		self.skip.grid(row=2, column=3, padx=2, pady=2)
  
		#Create Back button
		self.back = Button(self.master, width=40, height=40, padx=3, pady=3)
		self.back["image"] = self.back_img
		self.back["text"] = "Backward"
		self.back["command"] =  self.backward
		self.back.grid(row=2, column=1, padx=2, pady=2)
  
		#Create Switch button
		self.SW = Button(self.master, width=10, padx=3, pady=3)
		self.SW["text"] = "Switch Video"
		self.SW["command"] =  self.switch
		self.SW.grid(row=0, column=0, padx=2, pady=2)	

		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=1, column=0, columnspan=6, sticky=W+E+N+S, padx=8, pady=8) 
	
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
	
		elif(self.state==self.PLAYING):
			self.sendRtspRequest(self.PAUSE)
	
	def forward(self):
		if(self.state==self.PLAYING or self.state==self.READY):
			self.sendRtspRequest(self.FORWARD)
   
	def backward(self):
		if(self.state==self.PLAYING or self.state==self.READY):
			self.sendRtspRequest(self.BACKWARD)
	
	def switching(self):
		self.fileName=self.listbox.get(self.listbox.curselection())
		self.box.destroy()
		self.sendRtspRequest(self.SWITCH)
	
	def handler_switch(self):
		if tkinter.messagebox.askokcancel('Exit','Are you want to quit ?'):
			self.state=self.READY
			self.box.destroy()
		else:
			pass

	def switch(self):
		self.pauseMovie()
		self.state=self.SWITCHING
		self.box=Tk()
		self.box.protocol("WM_DELETE_WINDOW",self.handler_switch)
		self.box.title('Switch to another video')
		self.box.geometry('750x250')
		self.boxlabel=Label(self.box, text="", font=("Courier 22 bold"))
		self.boxlabel.pack()
		self.entry= Entry(self.box, width= 40)
		self.entry.focus_set()
		self.entry.pack()
		ttk.Button(self.box, text= "Switch",width= 20, command= self.switching).pack(pady=20)
		self.box.mainloop()

	def listenRtp(self):		
		"""Listen for RTP packets."""
		while True:
			try:
				data=self.rtp.recv(40960)
				if(data):
					Packet=RtpPacket()
					Packet.decode(data)

					currentframe=Packet.seqNum()

					print('Current Frame: ' +str(currentframe))

					# if(currentframe > self.frameNbr):
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
		self.label.configure(image=photo,height=400)
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
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
			self.rtspSeq=1

			request= 'SETUP ' + str(self.fileName) + '\n '+ str(self.rtspSeq) + '\n RTSP/1.0 HTP/UDP ' +  str(self.rtpPort) 
			self.rtsp.send(request.encode())
			self.requestSent=self.SETUP
   
		elif requestCode == self.PLAY and self.state == self.READY:
			self.start["image"] = self.pause_img
			self.rtspSeq += 1

			request='PLAY ' + '\n '+ str(self.rtspSeq)
			self.rtsp.send(request.encode())
			print('-'*60 + '\n' + 'PLAY request send to Server... \n'+'-'*60)
			self.requestSent=self.PLAY
   
		elif requestCode ==  self.PAUSE and self.state == self.PLAYING:
			self.start["image"] = self.play_img
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
   
		elif requestCode == self.FORWARD:
			self.rtspSeq +=1
			request='FORWARD '+'\n '+str(self.rtspSeq)
			self.rtsp.send(request.encode())
			print('-'*60+ '\n'+'FORWARD request sent to Server... \n' + '-'*60)
			self.requestSent=self.FORWARD
   
		elif requestCode == self.BACKWARD:
			self.rtspSeq +=1
			request='BACKWARD '+'\n '+str(self.rtspSeq)
			self.rtsp.send(request.encode())
			print('-'*60+ '\n'+'BACKWARD request sent to Server... \n' + '-'*60)
			self.requestSent=self.BACKWARD
   
		elif requestCode == self.SWITCH:
			self.rtspSeq +=1
			request='SWITCH ' +str(self.fileName) +'\n '+str(self.rtspSeq)
			self.rtsp.send(request.encode())
			print('-'*60+ '\n'+'SWITCHING request sent to Server... \n' + '-'*60)
			self.requestSent=self.SWITCH
		else:
			return

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
				if(int(lines[0].split(' ')[1]) == 200):
					if(self.requestSent == self.SETUP):
						print('Updating RTSP state....')
						self.state=self.READY
						print('Setting Up RtpPort for Video Stream')
						self.openRtpPort()
						self.totalframe=int(lines[3].split(' ')[1]) # use to draw time bar
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
					elif self.requestSent == self.FORWARD:
						print('SKIP SUCCESSFULLY')
					elif self.requestSent == self.BACKWARD:
						print('BACKWARD SUCCESSFULLY')
					elif self.requestSent == self.SWITCH:
						print('SWITCH SUCCESSFULLY')
						self.totalframe=int(lines[3].split(' ')[1])
						self.state=self.READY
						self.frameNbr=0
					
	
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

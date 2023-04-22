class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		self.history  = []
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		
	def totaltime(self):
		totalframe=0
		while True:
			try:
				data=self.file.read(5)
				length=int(data)
				self.file.seek(length,1)
				totalframe+=1
			except:
				self.file.seek(0)
				break
		return totalframe

	def nextFrame(self):
		"""Get next frame."""
		data = self.file.read(5) # Get the framelength from the first 5 bits
		if data: 
			framelength = int(data)
							
			# Read the current frame
			data = self.file.read(framelength)
			self.history.append(framelength+5)
			self.frameNum += 1
		return data
	
	def preFrame(self):
		if(self.history):
			self.file.seek(-int(self.history[-1]),1)
			self.history.pop()
			self.frameNum-=1
	
	def skipFrame(self):
		data=self.file.read(5)
		if(data):
			framelength=int(data)
			self.file.seek(framelength,1)
			self.frameNum+=1
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	
	
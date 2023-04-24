import os
class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		self.history  = []
		try:
			self.file = open(os.path.join('data',filename), 'rb')
		except:
			raise IOError
		self.frameNum = 0
		
	def totaltime(self):
		self.totalframe=0
		while True:
			try:
				data=self.file.read(5)
				length=int(data)
				self.file.seek(length,1)
				self.totalframe+=1
			except:
				self.file.seek(0)
				break
		return self.totalframe

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
		iter =0
		while self.frameNum>=1:
			self.file.seek(-int(self.history[-1]),1)
			self.history.pop()
			self.frameNum-=1
			iter+=1
			if(iter==20):
				break
	
	def skipFrame(self):
		iter =0
		while self.frameNum<=self.totalframe:
			data=self.file.read(5)
			framelength=int(data)
			self.file.seek(framelength,1)
			self.history.append(framelength+5)
			self.frameNum+=1
			iter+=1
			if(iter==20):
				break

	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	
	
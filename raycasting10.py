# Basic Ray Casting Engine Version 9
# Arkia
# November 8th, 2009

import pygame
import math
import bitmapFont
from collections import deque

class MessageBox:
	def __init__(self, x, y, charWidth, lines, messageLife):
		self.x = x
		self.y = y
		self.charWidth = charWidth
		self.lines = lines
		self.messageLife = messageLife
		self.messageTime = 0
		self.messages = deque([])
		
	def addLine(self, string):
		self.messages.append(string)
		self.messageTime += self.messageLife
		if len(self.messages) > self.lines:
			self.messages.popleft()
			
	def tick(self):
		if self.messageTime > 0:
			self.messageTime -= 1
			if self.messageTime % self.messageLife == 0 and len(self.messages) > 0:
				self.messages.popleft()
		else:
			self.messageTime = 0

class LineSeg:
	# Line segment wall
	def __init__(self, x1, y1, x2, y2, textureIndex, textureTile):
		self.x1 = x1
		self.y1= y1
		self.x2 = x2
		self.y2 = y2
		if x1 != x2:
			self.m = float((y1 - y2)/(x1 - x2))
			self.vertical = 0
		else:
			self.m = 0
			self.vertical = 1
		self.b = float(y1 - self.m * x1)
		self.texture = int(textureIndex)
		self.tTexture = textureTile
	
	def intersectionSlopeInt(self, m, b):
		x = 0
		y = 0
		texVert = 0.0
		if m == self.m:
			return (-1, 0, 0, 0)
		
		if self.vertical:
			y = m * self.x1 + b
			if self.y1 > self.y2 and y <= self.y1 and y >= self.y2:
				x = self.x1
			elif y >= self.y1 and y <= self.y2:
				x = self.x1
			else:
				return (-1, 0, 0, 0)
		else:
			x = (b - self.b)/(self.m - m)
			y = self.m * x + self.b
			if not(self.x1 >= self.x2 and x <= self.x1 and x >= self.x2 or x >= self.x1 and x <= self.x2):
				return (-1, 0, 0, 0)
				
		texVert = (1 - (math.sqrt((self.x1 - x)**2 + (self.y1 - y)**2) / math.sqrt((self.x1 - self.x2)**2 + (self.y1 - self.y2)**2))) * self.tTexture
		while texVert > 1:
			texVert -= 1
		return (self.texture, x, y, texVert)
				
	def intersectionVertical(self, x):
		y = 0
		if self.vertical:
			return (-1, 0, 0, 0)
		else:
			y = self.m * x + self.b
			if not(self.x1 >= self.x2 and x <= self.x1 and x >= self.x2 or x >= self.x1 and x <= self.x2):
				return (-1, 0, 0, 0)
				
		texVert = (1 - (math.sqrt((self.x1 - x)**2 + (self.y1 - y)**2) / math.sqrt((self.x1 - self.x2)**2 + (self.y1 - self.y2)**2))) * self.tTexture
		while texVert > 1:
			texVert -= 1
		return (self.texture, x, y, texVert)
		
class DynamicLine (LineSeg):
	def __init__(self, x1, y1, x2, y2, textureIndex, textureTile, frames = []):
		self.x1 = x1
		self.x2 = x2
		self.y1 = y1
		self.y2 = y2
		self.textureIndex = textureIndex
		self.textureTile = textureTile
		self.frames = frames
		if self.frames == []:
			self.frames.append(textureIndex)
		self.frameCount = len(self.frames)
		self.cFrame = 0
		self.vx = 0
		self.vy = 0
		self.dx = 0
		self.dy = 0
		
	def move(self, dx, dy, vx, vy):
		self.dx = dx
		self.dy = dy
		self.vx = vx
		self.vy = vy
		
	def update(self):
		if self.frameCount > 1:
			self.cFrame += 1
			self.cFrame %= self.frameCount
			self.textureIndex = self.frames[self.cFrame]
		
		if self.dx != 0:
			oldDX = self.dx
			self.x1 += self.vx
			self.x2 += self.vx
			self.dx += self.vx
			if self.dx * oldDX < 0:
				self.dx = 0
				
		if self.dy != 0:
			oldDY = self.dy
			self.y1 += self.vy
			self.y2 += self.vy
			self.dy += self.vy
			if self.dy * oldDY < 0:
				self.dy = 0
		
class Triangle:
	# Collision object
	def __init__(self, points):
		self.points = points
		self.sides = []
		i = 0
		while i < len(points):
			m = 0
			b = 0
			vert = 0
			neg = 0
			nextIndex = (i + 1) % 3
			other = i - 1
			if points[i][0] == points[nextIndex][0]:
				vert = 1
				b = points[i][0]
				if points[other][0] < points[i][0]:
					neg = 1
			else:
				m = float(points[i][1] - points[nextIndex][1])/float(points[i][0] - points[nextIndex][0])
				b = float(points[i][1] - (m * points[i][0]))
				if points[other][1] < (m * points[other][0] + b):
					neg = 1
					
			i += 1
					
			self.sides.append((vert, neg, m, b))
		
	def isInside(self, point):
		inside = 1
			
		for side in self.sides:
			if side[0]:
				if side[1]:
					if point[0] > side[3]:
						inside = 0
				else:
					if point[0] < side[3]:
						inside = 0
			else:
				if side[1]:
					if point[1] > float((side[2] * point[0]) + side[3]):
						inside = 0
				else:
					if point[1] < float((side[2] * point[0]) + side[3]):
						inside = 0
		
		for side in self.sides:
			if side[0]:
				if point[0] == side[3]:
					inside = 1
			else:
				if point[1] == float((side[2] * point[0]) + side[3]):
					inside = 1
		
		return inside
	
class CollisionRegion:
		def __init__(self, triangles, effects = 0):
			self.triangles = triangles
			self.effects = effects
		
		def isInside(self, point):
			inside = 0			
			for triangle in self.triangles:
				if triangle.isInside(point):
					inside = 1
			
			return inside
		
class VisRegion:
	def __init__(self, lines):
		self.lines = lines
		
class Player:
	# Player and camera data
	def __init__(self, x, y, angle, fov, clip):
		self.x = x
		self.y = y
		self.angle = angle
		self.fov = fov
		self.clip = clip
		self.r = 0.1
			
class StaticSprite:
	def __init__(self, index, x, y, z, r = 0.1, offX = 0.5, offY = 0.5):
		self.index = int(index)
		self.x = x
		self.y = y
		self.z = float(z)
		self.offX = float(offX)
		self.offY = float(offY)
		self.screenX = 0
		self.screenY = 0
		self.r = r
		self.type = 0
		
	def getScale(self, distance, fov):
		return 2 * math.atan(1 / distance) / fov
		
class AnimatedSprite (StaticSprite):
	def __init__(self, index, x, y, z, frames = [], r = 0.1, offX = 0.5, offY = 0.5):
		self.index = int(index)
		self.x = x
		self.y = y
		self.z = float(z)
		self.offX = float(offX)
		self.offY = float(offY)
		self.screenX = 0
		self.screenY = 0
		self.r = r
		self.type = 2
		self.frames = frames
		if len(self.frames) == 0:
			self.frames.append(index)
		self.cFrame = 0
		self.frameCount = len(self.frames)
			
	def update(self):
		if self.frameCount > 1:
			self.cFrame += 1
			self.cFrame %= self.frameCount
			self.index = self.frames[self.cFrame]
		
class Item (StaticSprite):
	def __init__(self, index, x, y, z, type = 0, r = 0.1, offX = 0.5, offY = 1.0):
		self.index = int(index)
		self.x = x
		self.y = y
		self.z = float(z)
		self.offX = float(offX)
		self.offY = float(offY)
		self.screenX = 0
		self.screenY = 0
		self.r = r
		self.type = int(type)

def updateSpriteList(sprites):
	worldSprites = []
	for sprite in sprites:
		worldSprites.append([300, 0, sprite])
		
	return worldSprites
	
def qSort(list):
	qSortR(list, 0, len(list) - 1)
	
def qSortR(list, first, last):
	if last > first:
		pivot = qSortPart(list, first, last)
		qSortR(list, first, pivot - 1)
		qSortR(list, pivot + 1, last)
		
def qSortPart(list, first, last):
	s = (first + last)/2
	if list[first][0] < list[s][0]:
		list[first], list[s] = list[s], list[first]
	if list[first][0] < list[last][0]:
		list[first], list[last] = list[last], list[first]
	if list[s] < list[last]:
		list[s], list[last], list[last], list[s]
		
	list[s], list[first] = list[first], list[s]
	pivot = first
	i = first + 1
	j = last
	
	while 1:
		while i <= last and list[i][0] >= list[pivot][0]:
			i += 1
		while j >= first and list[j][0] < list[pivot][0]:
			j -= 1
		if i >= j:
			break
		else:
			list[i], list[j] = list[j], list[i]
			
	list[j], list[pivot] = list[pivot], list[j]
	return j

def loadTextures(sections, textures, mapFile):
	isNewSection = 0
	nextSection = ""
	while not isNewSection:
		newTex = mapFile.readline()
		if newTex != "" and newTex != "\n":
			newTex = newTex[:-1]
		elif newTex == "":
			nextSection = "eof"
			isNewSection = 1
			
		for header in sections:
			if newTex == header:
				isNewSection = 1
				nextSection = header
				
		if newTex != "\n" and not isNewSection:
			textures.append(pygame.image.load(newTex))
	
	return nextSection
	
def loadImages(sections, images, mapFile):
	isNewSection = 0
	nextSection = ""
	while not isNewSection:
		newImage = mapFile.readline()
		if newImage != "" and newImage != "\n":
			newImage = newImage[:-1]
		elif newImage == "":
			isNewSection = 1
			nextSection = "eof"
			
		for header in sections:
			if newImage == header:
				isNewSection = 1
				nextSection = header
				
		if newImage != "\n" and not isNewSection:
			images.append(pygame.image.load(newImage))
			
	return nextSection

def loadFrameSets(sections, frameSets, mapFile):
	isNewSection = 0
	nextSection = ""
	while not isNewSection:
		newFrameSet = mapFile.readline()
		if newFrameSet != "" and newFrameSet != "\n":
			newFrameSet = newFrameSet[:-1]
		elif newFrameSet == "":
			isNewSection = 1
			nextSection = "eof"
			
		for header in sections:
			if newFrameSet == header:
				isNewSection = 1
				nextSection = header
			
		if newFrameSet != "\n" and not isNewSection:
			frameSet = newFrameSet.split()
			i = 0
			while i < len(frameSet):
				frameSet[i] = int(frameSet[i])
				i += 1
			frameSets.append(frameSet)
		
	return nextSection
	
def loadWalls(sections, lines, mapFile):
	isNewSection = 0
	nextSection = ""
	while not isNewSection:
		paraString = mapFile.readline()
		if paraString != "" and paraString != "\n":
			paraString = paraString[:-1]
		elif paraString == "":
			isNewSection = 1
			nextSection = "eof"
		
		for header in sections:
			if paraString == header:
				isNewSection = 1
				nextSection = header
		
		if paraString != "\n" and not isNewSection:
			params = paraString.split()
			i = 0
			while i < len(params):
				params[i] = float(params[i])
				i += 1
				
			lines.append(LineSeg(params[0], params[1], params[2], params[3], params[4], params[5]))
			
	return nextSection
	
def loadRegions(sections, regions, mapFile):
	isNewSection = 0
	nextSection = ""
	rString = mapFile.readline()
	while not isNewSection:
		newRegion = 0
		regionTriangles = []
		while not newRegion:
			paraString = mapFile.readline()
			if paraString == "":
				newRegion = 1
				isNewSection = 1
				nextSection = "eof"
			elif paraString[0] == "R":
				newRegion = 1
			elif paraString != "\n":
				paraString = paraString[:-1]
				
				for header in sections:
					if paraString == header:
						isNewSection = 1
						nextSection = header
				
				params = paraString.split()
				i = 0
				if not isNewSection:
					while i < len(params):
						params[i] = float(params[i])
						i += 1
					
					regionTriangles.append(Triangle([(params[0], params[1]), (params[2], params[3]), (params[4], params[5])]))
		
		regions.append(CollisionRegion(regionTriangles))
		
	return nextSection

def loadStaticObjects(sections, sprites, mapFile):
	isNewSection = 0
	nextSection = ""
	while not isNewSection:
		paraString = mapFile.readline()
		if paraString == "":
			isNewSection = 1
			nextSection = "eof"
		elif paraString != "\n":
			paraString = paraString[:-1]
			
			for header in sections:
				if paraString == header:
					isNewSection = 1
					nextSection = header
			
			params = paraString.split()
			i = 0
			if not isNewSection:
				while i < len(params):
					params[i] = float(params[i])
					i += 1
				
				if len(params) < 5:
					sprites.append(StaticSprite(params[0], params[1], params[2], params[3]))
				elif len(params) < 6:
					sprites.append(StaticSprite(params[0], params[1], params[2], params[3], params[4]))
				elif len(params) < 7:
					sprites.append(StaticSprite(params[0], params[1], params[2], params[3], params[4], params[5]))
				else:
					sprites.append(StaticSprite(params[0], params[1], params[2], params[3], params[4], params[5], params[6]))
				
	return nextSection

def loadAnimatedObjects(sections, sprites, frameSets, mapFile):
	isNewSection = 0
	nextSection = ""
	while not isNewSection:
		paraString = mapFile.readline()
		if paraString == "":
			isNewSection = 1
			nextSection = "eof"
		elif paraString != "\n":
			paraString = paraString[:-1]
			
			for header in sections:
				if paraString == header:
					isNewSection = 1
					nextSection = header
			
			params = paraString.split()
			i = 0
			if not isNewSection:
				while i < len(params):
					params[i] = float(params[i])
					i += 1
				
				if len(params) < 5:
					sprites.append(AnimatedSprite(params[0], params[1], params[2], params[3]))
				elif len(params) < 6:
					sprites.append(AnimatedSprite(params[0], params[1], params[2], params[3], frameSets[int(params[4])]))
				elif len(params) < 7:
					sprites.append(AnimatedSprite(params[0], params[1], params[2], params[3], frameSets[int(params[4])], params[5]))
				elif len(params) < 8:
					sprites.append(AnimatedSprite(params[0], params[1], params[2], params[3], frameSets[int(params[4])], params[5], params[6]))
				else:
					sprites.append(AnimatedSprite(params[0], params[1], params[2], params[3], frameSets[int(params[4])], params[5], params[6], params[7]))
				
	return nextSection
	
def loadItems(sections, sprites, mapFile):
	isNewSection = 0
	nextSection = ""
	while not isNewSection:
		paraString = mapFile.readline()
		if paraString == "":
			isNewSection = 1
			nextSection = "eof"
		elif paraString != "\n":
			paraString = paraString[:-1]
			
			for header in sections:
				if paraString == header:
					isNewSection = 1
					nextSection = header
			
			params = paraString.split()
			i = 0
			if not isNewSection:
				while i < len(params):
					params[i] = float(params[i])
					i += 1
					
				if len(params) < 5:
					sprites.append(Item(params[0], params[1], params[2], params[3]))
				elif len(params) < 6:
					sprites.append(Item(params[0], params[1], params[2], params[3], params[4]))
				elif len(params) < 7:
					sprites.append(Item(params[0], params[1], params[2], params[3], params[4], params[5]))
				elif len(params) < 8:
					sprites.append(Item(params[0], params[1], params[2], params[3], params[4], params[5], params[6]))
				else:
					sprites.append(Item(params[0], params[1], params[2], params[3], params[4], params[5], params[6], params[7]))
					
	return nextSection		
	
def loadMap(fileName, sprImages, textures, lines, regions, sprites, frameSets):
	sections = ["Textures:", "Sprites:", "Lines:", "Static:", "Item:", "Collision:", "Animated:", "FrameSet:"]
	mapFile = open(fileName, "r")
	currentSection = mapFile.readline()
	currentSection = currentSection[:-1]
	while currentSection != "eof":
		if currentSection == sections[0]:
			currentSection = loadTextures(sections, textures, mapFile)
		elif currentSection == sections[1]:
			currentSection = loadImages(sections, sprImages, mapFile)
		elif currentSection == sections[2]:
			currentSection = loadWalls(sections, lines, mapFile)
		elif currentSection == sections[3]:
			currentSection = loadStaticObjects(sections, sprites, mapFile)
		elif currentSection == sections[4]:
			currentSection = loadItems(sections, sprites, mapFile)
		elif currentSection == sections[5]:
			currentSection = loadRegions(sections, regions, mapFile)
		elif currentSection == sections[6]:
			currentSection = loadAnimatedObjects(sections, sprites, frameSets, mapFile)
		elif currentSection == sections[7]:
			currentSection = loadFrameSets(sections, frameSets, mapFile)
	
		
def main():
	# Key states
	keys = {"Up":0, "Down":0, "Left":0, "Right":0, "Z":0, "X":0, "Fire":0}
	
	# Clock for timing
	clock = pygame.time.Clock()
	
	# Screen height and width
	resHeight = 240
	screenWidth = 320
	
	# Set caption
	pygame.display.set_caption("Ray Casting")
	
	# Create display window
	screen = pygame.display.set_mode((screenWidth, resHeight))
	
	# Background sky/floor image
	background = pygame.image.load("rcBackground.png")
	
	# Where the scene is rendered
	render = pygame.Surface((screenWidth, resHeight))
	render.set_colorkey((0, 0, 0))
	
	# Where hud/weapon are drawn
	overlay = pygame.Surface((screenWidth, resHeight))
	overlay.set_colorkey((255, 0, 255))
	
	# Simple weapon image
	gun = pygame.image.load("vwepHandgun1.png")
	gun.set_colorkey((255, 0, 255))
	gunFired = pygame.image.load("vwepHandgun2.png")
	gunFired.set_colorkey((255, 0, 255))
	
	# Create the player/camera
	player = Player(0, 0, 0, 0.25 * math.pi, 30)
	
	# Width of each vertical division
	rectWidth = 1
	
	rectHeight = 0
	# Number of divisions
	resWidth = screenWidth / rectWidth
	
	running = 1
	rendered = 0
	# A bitmapped font
	font = bitmapFont.BitmapFont("zmfont.bmp", 8, 8)
	
	messageBox = MessageBox(2, 2, 38, 5, 30)
	messageBox.addLine("Welcome to the raycaster")
	
	itemMessages = ["", "Got health vial", "Got blinking orb"]
	
	# Number of screenshots taken, used to change filename each screenshot
	imgSaves = 0
	
	reloadTime = 0
	RELOAD = 10
	frameDel = 0
	
	# A sprite for an in world object
	#sprImages = [pygame.image.load("rcTestSprite.png"), pygame.image.load("itmHealth1.png")]
	
	# Wall textures
	#textures = [pygame.image.load("rcTestTexture.png"), pygame.image.load("rcTestTexture1.png"), pygame.image.load("rcTestTexture2.png"), pygame.image.load("rcTestTexture3.png"), pygame.image.load("rcTestTexture4.png")]
	#for image in sprImages:
		#image.set_colorkey((255, 0, 255))
	
	# Sample map data
	sprImages = []
	textures = []
	frameSets = []
	map = []
	regions = []
	sprites = []
	
	loadMap("test.map", sprImages, textures, map, regions, sprites, frameSets)
	
	screenLineIndex = []
	worldSprites = []
	
	for image in sprImages:
		image.set_colorkey((255, 0, 255))
	
	i = 0
	while i < len(sprites):
		worldSprites.append([player.clip, 0, sprites[i]])
		i += 1
	
	while running:
		# Flag for if we want a screen shot
		screenRequest = 0
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = 0
				
			# Update the keystates
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_UP:
					keys["Up"] = 1
				elif event.key == pygame.K_DOWN:
					keys["Down"] = 1
				elif event.key == pygame.K_LEFT:
					keys["Left"] = 1
				elif event.key == pygame.K_RIGHT:
					keys["Right"] = 1
				elif event.key == pygame.K_z:
					keys["Z"] = 1
				elif event.key == pygame.K_x:
					keys["X"] = 1
				elif event.key == pygame.K_SPACE:
					keys["Fire"] = 1
				elif event.key == pygame.K_F12:
					screenRequest = 1
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_UP:
					keys["Up"] = 0
				elif event.key == pygame.K_DOWN:
					keys["Down"] = 0
				elif event.key == pygame.K_LEFT:
					keys["Left"] = 0
				elif event.key == pygame.K_RIGHT:
					keys["Right"] = 0
				elif event.key == pygame.K_z:
					keys["Z"] = 0
				elif event.key == pygame.K_x:
					keys["X"] = 0
				elif event.key == pygame.K_SPACE:
					keys["Fire"] = 0
				
		if keys["Up"]:
			# Move forwards
			oldx = player.x
			player.x += math.cos(player.angle) / 8
			#for block in blocks:
			if len(regions) > 0 and not [r for r in regions if r.isInside((player.x, player.y))]:
				player.x = oldx
			for sprite in sprites:
				if player.r + sprite.r > math.sqrt((player.x - sprite.x)**2 + (player.y - sprite.y)**2):
					if sprite.type == 0:
						player.x = oldx
						break
					else:
						sprites.remove(sprite)
						worldSprites = updateSpriteList(sprites)
						messageBox.addLine(itemMessages[sprite.type])
						
					
			oldy = player.y
			player.y += math.sin(player.angle) / 8
			if len(regions) > 0 and not [r for r in regions if r.isInside((player.x, player.y))]:
				player.y = oldy
			for sprite in sprites:
				if player.r + sprite.r > math.sqrt((player.x - sprite.x)**2 + (player.y - sprite.y)**2):
					if sprite.type == 0:
						player.y = oldy
						break
					else:
						sprites.remove(sprite)
						worldSprites = updateSpriteList(sprites)
						messageBox.addLine(itemMessages[sprite.type])
					
		if keys["Down"]:
			# Move backwards
			oldx = player.x
			player.x -= math.cos(player.angle) / 8
			if len(regions) > 0 and not [r for r in regions if r.isInside((player.x, player.y))]:
				player.x = oldx
			for sprite in sprites:
				if player.r + sprite.r > math.sqrt((player.x - sprite.x)**2 + (player.y - sprite.y)**2):
					if sprite.type == 0:
						player.x = oldx
						break
					else:
						sprites.remove(sprite)
						worldSprites = updateSpriteList(sprites)
						messageBox.addLine(itemMessages[sprite.type])
							
			oldy = player.y
			player.y -= math.sin(player.angle) / 8
			if len(regions) > 0 and not [r for r in regions if r.isInside((player.x, player.y))]:
				player.y = oldy
			for sprite in sprites:
				if player.r + sprite.r > math.sqrt((player.x - sprite.x)**2 + (player.y - sprite.y)**2):
					if sprite.type == 0:
						player.y = oldy
						break
					else:
						sprites.remove(sprite)
						worldSprites = updateSpriteList(sprites)
						messageBox.addLine(itemMessages[sprite.type])
							
		if keys["Left"]:
			# Turn left
			player.angle += math.pi / 36
			
			# Keep angle within 0 - 2pi
			while player.angle > 2 * math.pi:
				player.angle -= 2 * math.pi
					
		if keys["Right"]:
			# Turn right
			player.angle -= math.pi / 36
			
			# Keep angle within 0 - 2pi
			while player.angle < 0:
				player.angle += 2 * math.pi
			
		if keys["Z"]:
			# Strafe left
			oldx = player.x
			player.x += math.cos(player.angle + math.pi / 2) / 8
			if len(regions) > 0 and not [r for r in regions if r.isInside((player.x, player.y))]:
				player.x = oldx
			for sprite in sprites:
				if player.r + sprite.r > math.sqrt((player.x - sprite.x)**2 + (player.y - sprite.y)**2):
					if sprite.type == 0:
						player.x = oldx
						break
					else:
						sprites.remove(sprite)
						worldSprites = updateSpriteList(sprites)
						messageBox.addLine(itemMessages[sprite.type])
					
			oldy = player.y
			player.y += math.sin(player.angle + math.pi / 2) / 8
			if len(regions) > 0 and not [r for r in regions if r.isInside((player.x, player.y))]:
				player.y = oldy
			for sprite in sprites:
				if player.r + sprite.r > math.sqrt((player.x - sprite.x)**2 + (player.y - sprite.y)**2):
					if sprite.type == 0:
						player.y = oldy
						break
					else:
						sprites.remove(sprite)
						worldSprites = updateSpriteList(sprites)
						messageBox.addLine(itemMessages[sprite.type])
					
		if keys["X"]:
			# Strafe right
			oldx = player.x
			player.x += math.cos(player.angle - math.pi / 2) / 8
			if len(regions) > 0 and not [r for r in regions if r.isInside((player.x, player.y))]:
				player.x = oldx
			for sprite in sprites:
				if player.r + sprite.r > math.sqrt((player.x - sprite.x)**2 + (player.y - sprite.y)**2):
					if sprite.type == 0:
						player.x = oldx
						break
					else:
						sprites.remove(sprite)
						worldSprites = updateSpriteList(sprites)
						messageBox.addLine(itemMessages[sprite.type])
					
			oldy = player.y
			player.y += math.sin(player.angle - math.pi / 2) / 8
			if len(regions) > 0 and not [r for r in regions if r.isInside((player.x, player.y))]:
				player.y = oldy
			for sprite in sprites:
				if player.r + sprite.r > math.sqrt((player.x - sprite.x)**2 + (player.y - sprite.y)**2):
					if sprite.type == 0:
						player.y = oldy
						break
					else:
						sprites.remove(sprite)
						worldSprites = updateSpriteList(sprites)
						messageBox.addLine(itemMessages[sprite.type])
					
		if keys["Fire"] and not reloadTime:
			frameDel = 5
			reloadTime = RELOAD
					
		# Reset divCount and clear surfaces for rendering		
		divCount = 0
		screen.blit(background, (0, 0))
		render.fill((0, 0, 0))
		overlay.fill((255, 0, 255))
		
		screenLineIndex = []
		
		# Render the scene
		while divCount < resWidth:
			# Calculate the rays angle
			angle = player.angle + player.fov / 2
			angle -= (player.fov / resWidth) * divCount
			rX = player.x
			rY = player.y
			negX = 0
			negY = 0
			if angle != math.pi / 2 and angle != (3 * math.pi) / 2:
				rM = math.tan(angle)
				rB = rY - rM * rX
				rVertical = 0
			else:
				rM = 0
				rVertical = 1
			
			if math.cos(angle) < 0:
				negX = 1
			if math.sin(angle) < 0:
				negY = 1
			cross = (-1, 0, 0, 0)
			distance = player.clip
			index = 0
			for line in map:
				found = 0
				if rVertical:
					newCross = line.intersectionVertical(rX)
				else:
					newCross = line.intersectionSlopeInt(rM, rB)
				
				if newCross[0] != -1:
					newDist = math.sqrt((rX - newCross[1])**2 + (rY - newCross[2])**2)
					if newDist < player.clip:
						if negX and newCross[1] < rX:
							if negY and newCross[2] < rY:
								found = 1
							elif not negY and newCross[2] > rY:
								found = 1
						elif not negX and newCross[1] > rX:
							if negY and newCross[2] < rY:
								found = 1
							elif not negY and newCross[2] > rY:
								found = 1
							
					if found:
						cross = newCross
						distance = newDist
						
						texture = cross[0]
						textVert = cross[3]
						if texture != -1:
							# Calculate height of the vertical
							rectHeight = screenWidth * (math.atan(1 / (distance * math.cos(abs(angle - player.angle)))) / player.fov)
						else:
							rectHeight = 0
				
						# Store vertical in list
						screenLineIndex.append((distance, texture, rectHeight, divCount, textVert))
			
			# Next vertical division
			divCount += 1
		
		i = 0
		while i < len(worldSprites):
			worldSprites[i][1] = 0
			if worldSprites[i][2].x != player.x:
				mSpr = (worldSprites[i][2].y - player.y)/(worldSprites[i][2].x - player.x)
			else:
				mSpr = 0
				
			distance = math.sqrt((worldSprites[i][2].x - player.x)**2 + (worldSprites[i][2].y - player.y)**2)
			angle = 0
			
			negX = 0
			negY = 0
			if worldSprites[i][2].x < player.x:
				negX = 1
			if worldSprites[i][2].y < player.y:
				negY = 1
				
			if negX:
				if worldSprites[i][2].y == player.y:
					angle = math.pi
				else:
					angle = math.pi + math.atan(mSpr)
			elif worldSprites[i][2].x == player.x:
				if negY:
					angle = (3 * math.pi)/2
				else:
					angle = math.pi / 2
			else:
				if worldSprites[i][2].y == player.y:
					angle = 0
				elif negY:
					angle = 2 * math.pi + math.atan(mSpr)
				else:
					angle = math.atan(mSpr)
			#if angle <= player.angle + player.fov / 2 and angle >= player.angle - player.fov / 2:
			if distance > 0.125:
				worldSprites[i][1] = 1
				nAngle = angle - (player.angle - player.fov / 2)
				worldSprites[i][2].screenX = screenWidth - ((nAngle / player.fov) * screenWidth)
				vertHeight = screenWidth * (math.atan(1 / (distance * math.cos(abs(angle - player.angle)))) / player.fov)
				worldSprites[i][2].screenY = resHeight - (((resHeight - vertHeight) / 2) + (worldSprites[i][2].z * vertHeight))
				
			worldSprites[i][0] = distance
			
			i += 1
		
		qSort(worldSprites)
		qSort(screenLineIndex)
		
		i = 0
		j = 0
		while i < len(worldSprites) or j < len(screenLineIndex):
			if j >= len(screenLineIndex) or (i < len(worldSprites) and worldSprites[i][0] > screenLineIndex[j][0]):
				if worldSprites[i][1]:
					sprScale = worldSprites[i][2].getScale(worldSprites[i][0], player.fov)
					newImage = pygame.transform.rotozoom(sprImages[worldSprites[i][2].index], 0, sprScale)
					newImage.set_colorkey((255, 0, 255))
					render.blit(newImage, (worldSprites[i][2].screenX - newImage.get_width() * worldSprites[i][2].offX, worldSprites[i][2].screenY - newImage.get_height() * worldSprites[i][2].offY))
				i += 1
			elif j <= len(screenLineIndex):
				textureX = screenLineIndex[j][4] * textures[screenLineIndex[j][1]].get_width()
				if textureX >= textures[screenLineIndex[j][1]].get_width():
					textureX = textures[screenLineIndex[j][1]]. get_width() - 1
				if textureX < 0:
					textureX = 0
				textVert = textures[screenLineIndex[j][1]].subsurface((textureX, 0, 1, textures[screenLineIndex[j][1]].get_height()))
				textVert = pygame.transform.smoothscale(textVert, (rectWidth, int(screenLineIndex[j][2])))
				render.blit(textVert, (screenLineIndex[j][3] * rectWidth, int((resHeight - screenLineIndex[j][2]) / 2)))
				j += 1
		
		i = -len(messageBox.messages)
		while i < 0:
			font.bitmapPrint(overlay, messageBox.x, messageBox.y + (-i - 1) * font.subHeight, messageBox.messages[i], (0, 255, 0))
			i += 1
		
		screen.blit(render, (0, 0))
		screen.blit(overlay, (0, 0))
		
		messageBox.tick()
		
		if frameDel:
			screen.blit(gunFired, (screenWidth / 2 - 48, resHeight - 96))
			frameDel -= 1
		else:
			screen.blit(gun, (screenWidth / 2 - 48, resHeight - 96))
		
		if reloadTime > 0:
			reloadTime -= 1
		
		for sprite in sprites:
			if sprite.type == 2:
				sprite.update()
		
		# Save a screenshot if F12 was pressed
		if screenRequest:
			pygame.image.save(screen, "rc10Screenshot%d.png" % (imgSaves,))
			imgSaves += 1
		
		pygame.display.flip()
		clock.tick(30)
		
if __name__ == "__main__":
	main()
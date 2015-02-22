import pygame

class BitmapFont:

	def __init__(self, image, width, height, subWidth = 16, subHeight = 8, length = 128):
		self.image = pygame.image.load(image)
		self.width = width
		self.height = height
		self.subWidth = subWidth
		self.subHeight = subHeight
		self.length = length
		self.curColor = (255, 255, 255)
		
	def bitmapPrint(self, target, x, y, s, color = (255, 255, 255)):
		tempArray = pygame.PixelArray(self.image)
		tempArray.replace(self.curColor, color)
		self.curColor = color
		newImage = tempArray.make_surface()
		for char in s:
			if ord(char) < self.length:
				target.blit(newImage, (x, y), pygame.Rect((ord(char) % self.subWidth) * self.width, (ord(char) / self.subWidth) * self.height, self.width, self.height))
			else:
				target.blit(newImage, (x, y), pygame.Rect(105, 42, self.width, self.height))
			x += self.width

def main():
	clock = pygame.time.Clock()
	pygame.display.set_caption("Bitmap Font Test")
	screen = pygame.display.set_mode((256, 256))
	testFont = BitmapFont("metfont.bmp", 7, 14)
	testFont.bitmapPrint(screen, 4, 4, "This is a bitmap font")
	testFont.bitmapPrint(screen, 4, 18, "Now in red...", (255, 0, 0))
	testFont.bitmapPrint(screen, 4, 32, "...green...", (0, 255, 0))
	testFont.bitmapPrint(screen, 4, 46, "...and blue", (0, 0, 255))
	pygame.display.flip()
	running = 1
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = 0
		clock.tick(60)

if __name__ == "__main__":
	main()
	
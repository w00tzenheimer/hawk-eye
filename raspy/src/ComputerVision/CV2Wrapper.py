import numpy as np
import cv2
import os, sys

class CV2Wrapper(object):
	"""OpenCV 2 Wrapper"""

	def __init__(self, 
				 maxWidth = 640.0, 
				 maxHeight = 640.0,
				 distanceFactor = 0.6,
				 minGoodsPercentaje = 0.069,
				 minSize = (100, 100),
				 scaleFactor = 1.08,
				 minNeighbors = 1,
				 templateMatchingLimit = 0.4):
		self.maxWidth = maxWidth
		self.maxHeight = maxHeight
		self.distanceFactor = distanceFactor
		self.minGoodsPercentaje = minGoodsPercentaje
		self.minSize = minSize
		self.scaleFactor = scaleFactor
		self.minNeighbors = minNeighbors
		self.templateMatchingLimit = templateMatchingLimit
		cascades = [
			#'static/haarcascade_eye.xml',
			#'static/haarcascade_eye_tree_eyeglasses.xml',
			#'static/haarcascade_lefteye_2splits.xml',
			#'static/haarcascade_licence_plate_rus_16stages.xml',
			#os.getcwd().replace("src", "static") + '/haarcascade_profileface.xml',
			#'static/haarcascade_righteye_2splits.xml',
			#'static/haarcascade_russian_plate_number.xml',
			#'static/haarcascade_smile.xml',

			# Face related
			#os.getcwd().replace("src", "static") + '/lbpcascade_frontalface.xml',
			#os.getcwd().replace("src", "static") + '/haarcascade_frontalface_alt.xml',
			os.getcwd().replace("src", "static") + '/haarcascade_frontalface_alt2.xml',
			#os.getcwd().replace("src", "static") + '/haarcascade_frontalface_alt_tree.xml',
			#os.getcwd().replace("src", "static") + '/haarcascade_frontalface_default.xml'
		]

		# Loads trained XML data
		self.faceCascades = [cv2.CascadeClassifier(x) for x in cascades]
		
		# Initiate SIFT detector
		self.sift = cv2.xfeatures2d.SIFT_create()

		# Calculates Flann
		FLANN_INDEX_KDTREE = 0
		indexParams = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
		searchParams = dict(checks = 50)
		self.flann = cv2.FlannBasedMatcher(indexParams, searchParams)
		self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
		self.bf = cv2.BFMatcher()


	def createFaceRecognizer(self):
		return cv2.face.createLBPHFaceRecognizer()


	def imageRead(self, path):
	  return cv2.imread(path)


	def imageFromBinary(self, data):
	  imgArray = np.asarray(bytearray(data), dtype = np.uint8)
	  return cv2.imdecode(imgArray, cv2.IMREAD_UNCHANGED)


	# for documentation only
	def imageReadUsingOpen(self, path):
	  with open(path, 'rb') as f:
	    return self.imageFromBinary(f.read())


	def toGrayScale(self, imageColor):
		return cv2.cvtColor(imageColor, cv2.COLOR_BGR2GRAY)
	

	def detectFacesLimits(self, imageGray):
		x = []
		for cascade in self.faceCascades:
			detected = cascade.detectMultiScale(
				image = imageGray, 
				minNeighbors = self.minNeighbors,
				scaleFactor = self.scaleFactor,
				flags = cv2.CASCADE_SCALE_IMAGE | cv2.CASCADE_FIND_BIGGEST_OBJECT | cv2.CASCADE_DO_ROUGH_SEARCH,
				minSize = self.minSize)
			
			x.extend(detected)
		return x


	def detectFaces(self, imageColor):
		height, width = imageColor.shape[:2]
		minSide = height if height < width else width
		imageColor = imageColor[height/2 - minSide/2:height/2 + minSide/2, width/2 - minSide/2:width/2 + minSide/2]

		imageScaled, scaleFactor = self._scaleToDefaultSize(imageColor)

		imageGray = self.toGrayScale(imageScaled)
		imageGray = self.clahe.apply(imageGray)
		imageGray = cv2.equalizeHist(imageGray)
		faces = []
		rects = self.detectFacesLimits(imageGray)
		#rects[:,2:] += rects[:,:2]
		idx = 0
		for (x,y,w,h) in rects:
			idx += 1
			up = int((1.0 * y) / scaleFactor)
			down = int((1.0 * (y + h)) / scaleFactor)
			left = int((1.0 * x) / scaleFactor)
			right = int((1.0 * (x + w)) / scaleFactor)

			face = imageColor[up:down, left:right]
			face, __dummy = self._scaleToDefaultSize(face)			
			faces.append(face)
			cv2.imwrite('face_%d.jpg' % idx, face)

		return faces


	def imageToBinary(self, image):
		return cv2.imencode('.jpg', image)[1].tostring()


	def toSIFTMatrix(self, image):
		# find the keypoints and descriptors with SIFT
		image = self.toGrayScale(image)
		image = self.clahe.apply(image)
		image = cv2.equalizeHist(image)

		__kp, des = self.sift.detectAndCompute(image, None)
		return des

	
	def compareSIFTMatrix(self, matrix1, matrix2):
		if matrix1 is None or matrix2 is None:
			return False
		if matrix1.size == 0 or matrix2.size == 0:
			return False
		matches = self.flann.knnMatch(matrix1, trainDescriptors = matrix2, k=2)

		good = 0.0
		allMatches = 0.0
		for m,n in matches:
			allMatches += 1
			if m.distance < self.distanceFactor * n.distance:
				good += 1
		
		print "%d/%d" % (good, allMatches)
		if allMatches == 0:
			return False
		print good/allMatches
		#return ((good / allMatches) > self.minGoodsPercentaje)
		return (good >= 5)


	def imagesCompareSIFT(self, image1, image2):
		# find the keypoints and descriptors with SIFT
		des1 = self.toSIFTMatrix(image1)
		des2 = self.toSIFTMatrix(image2)

		return self.compareSIFTMatrix(des1, des2)


	def imagesCompare(self, image1, image2):
		return self.imagesCompareSIFT(image1, image2)
		# return self.imagesCompareTempleateMatching(image1, image2)


	def imagesCompareTempleateMatching(self, image1, image2):
		res = cv2.matchTemplate(
			self.toGrayScale(image1),
			self.toGrayScale(image2),
			cv2.TM_CCOEFF_NORMED)
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
		return (max_val > self.templateMatchingLimit)


	def imagesCompareMaths(self, image1, image2):
		im1Gray = self.toGrayScale(image1)
		im2Gray = self.toGrayScale(image2)
		image1_norm = im1Gray / np.sqrt(np.sum(im1Gray ** 2))
		image2_norm = im2Gray / np.sqrt(np.sum(im2Gray ** 2))

		product = image1_norm * image2_norm

		return (np.sum(product) > 0.9)


	def _scaleToDefaultSize(self, image):
		height, width = image.shape[:2]

		scaleH = 1.0 * self.maxHeight / height
		scaleW = 1.0 * self.maxWidth / width

		scaleFactor = scaleH if scaleH < scaleW else scaleW

		return cv2.resize(
				image,
				None,
				fx=scaleFactor,
				fy=scaleFactor,
				interpolation=cv2.INTER_AREA
			), scaleFactor

# import the necessary packages
import numpy as np
import cv2

# initialize our cached reference points
CAHCED_PTS = None

def aruco_ar(frame, source, display_boxes, cornerIDs, arucoDict, arucoParams):
	# grab a reference to our cached reference points
	global CAHCED_PTS

	# Grab the H and W of both image frames
	(imgH, imgW) = frame.shape[:2]
	(srcH, srcW) = source.shape[:2]

	# Try to detect respective AruCo markers in frame.
	(corners, ids, rejected) = cv2.aruco.detectMarkers(
		frame, arucoDict, parameters=arucoParams)

	# Check if we want to display AruCo detection boxes
	if display_boxes:
		# Copy frame to display markers
		frame_outline = frame.copy()

		# verify *at least* one ArUco marker was detected
		if len(corners) > 0:
			# Flatten to list
			ids_temp = ids.flatten()

			# Loop over all detected corners
			for (markerCorner, markerID) in zip(corners, ids_temp):

				# Extract the ArUco marker corners (they are always returned
				# in order of top_left, top_right, bottom_right, and bottom_left)
				corners_temp = markerCorner.reshape((4, 2))
				(topLeft, topRight, bottomRight, bottomLeft) = corners_temp

				# Convert the (x, y)-coordinate pairs to integers
				topRight = (int(topRight[0]), int(topRight[1]))
				bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
				bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
				topLeft = (int(topLeft[0]), int(topLeft[1]))

				# Draw bounding box around ArUco markers
				cv2.line(frame_outline, topLeft, topRight, (0, 255, 0), 2)
				cv2.line(frame_outline, topRight, bottomRight, (0, 255, 0), 2)
				cv2.line(frame_outline, bottomRight, bottomLeft, (0, 255, 0), 2)
				cv2.line(frame_outline, bottomLeft, topLeft, (0, 255, 0), 2)

				# Add a red dot at the center of the markers
				cX = int((topLeft[0] + bottomRight[0]) / 2.0)
				cY = int((topLeft[1] + bottomRight[1]) / 2.0)
				cv2.circle(frame_outline, (cX, cY), 4, (0, 0, 255), -1)

				# Add the marker ID name to image
				cv2.putText(frame_outline, str(markerID),
							(topLeft[0], topLeft[1] - 15),
							cv2.FONT_HERSHEY_SIMPLEX,
							0.5, (0, 255, 0), 2)

	else:
		frame_outline = []

	# Create empty list (if not 4 found) or flatten list
	ids = np.array([]) if len(corners) != 4 else ids.flatten()

	# Init list of reference points
	refPts = []

	# loop over the IDs of the ArUco markers in top_left, top_right,
	# bottom_right, and bottom_left order
	for i in cornerIDs:
		# grab the index of the corner with the current ID
		j = np.squeeze(np.where(ids == i))

		# if we receive an empty list instead of an integer index,
		# then we could not find the marker with the current ID
		if j.size == 0:
			continue

		# otherwise, append the corner (x, y)-coordinates to our list
		# of reference points
		corner = np.squeeze(corners[j])
		refPts.append(corner)

	# check to see if we failed to find the four ArUco markers
	if len(refPts) != 4:
		# if we are allowed to use cached reference points, fall
		# back on them
		if CAHCED_PTS is not None:
			refPts = CAHCED_PTS

		# otherwise, we cannot use the cache and/or there are no
		# previous cached reference points, so return early
		else:
			return None, None

	# Update cached points (use if we haven't found an updated transform)
	CAHCED_PTS = refPts

	# Use our ArUco reference points to define the transform matrix
	(refPtTL, refPtTR, refPtBR, refPtBL) = refPts
	dstMat = [refPtTL[0], refPtTR[1], refPtBR[2], refPtBL[3]]
	dstMat = np.array(dstMat)

	# Create the transform matrix for the source image in top-left,
	# top-right, bottom-right, and bottom-left order
	srcMat = np.array([[0, 0], [srcW, 0], [srcW, srcH], [0, srcH]])

	# Compute homography image and warp it
	(H, _) = cv2.findHomography(srcMat, dstMat)
	warped_im = cv2.warpPerspective(source, H, (imgW, imgH))

	# construct a mask for the source image now that the perspective
	# warp has taken place (we'll need this mask to copy the source
	# image into the destination)
	mask = np.zeros((imgH, imgW), dtype="uint8")
	cv2.fillConvexPoly(mask, dstMat.astype("int32"), (255, 255, 255),
		cv2.LINE_AA)

	# Add a black border tomimage
	rect = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
	mask = cv2.dilate(mask, rect, iterations=2)

	# Make three channels
	maskScaled = mask.copy() / 255.0
	maskScaled = np.dstack([maskScaled] * 3)

	# Create final output image by combining and overlaying
	warpedMultiplied = cv2.multiply(warped_im.astype("float"),
		maskScaled)
	imageMultiplied = cv2.multiply(frame.astype(float),
		1.0 - maskScaled)
	output = cv2.add(warpedMultiplied, imageMultiplied)
	output = output.astype("uint8")

	# return the output frame to the calling function
	return output, frame_outline
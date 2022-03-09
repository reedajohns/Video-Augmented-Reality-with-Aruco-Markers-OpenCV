# USAGE
# python ar_main.py --source PATH_TO_VIDEO

# Imports
from aux.augmented_reality import aruco_ar
import argparse
import imutils
import cv2
from selenium import webdriver

# Set:
# Whether or not to display AruCo markers on raw image
display_aruco_boxes = True
# Weather.com URL for respectve city
weather_URL = "https://weather.com/weather/today/l/f2a75f4d0ceadba8e629bb2bacb40414bb499eb922989f847a9fa0659bf127e3"
# Where temp weather screenshot it saved / read (this shouldn't need to be changed)
temp_save_image_path = '../temp/temp_image.png'

# AruCo info (based off markers that we're generated and printed)
aruco_dictionary = cv2.aruco.DICT_5X5_100
aruco_IDs = (24, 42, 70, 66)

# Main Function
if __name__ == '__main__':
    ### Parse Command line Arguments ###
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--source", type=str, default='../video/ar_test_video.MOV',
                    help="path to input video for AR")
    args = vars(ap.parse_args())

    ### Use selenium to open a webpage of the local weather, and take a screenshot to overlay ###
    driver = webdriver.Chrome('/home/reed/Documents/chromedriver_linux64/chromedriver')
    # Set browser size
    driver.set_window_size(1792, 828)
    webpage_url = weather_URL
    # Navigate to URL
    driver.get(webpage_url)

    # Capture image and save to temp file
    driver.get_screenshot_as_file(temp_save_image_path)
    # Close browser
    driver.quit()

    # Load image to memory
    overlay_image = cv2.imread(temp_save_image_path)

    # Setup Aruco Dict and Parameters
    print("Initializing AruCo Dict and Parameters...")
    arucoDict = cv2.aruco.Dictionary_get(aruco_dictionary)
    arucoParams = cv2.aruco.DetectorParameters_create() # Using default

    # initialize the video file stream
    print("Loading video file: {}".format(args['source']))
    video_source = cv2.VideoCapture(args["source"])

    # Loop through entire video frame by frame
    image_count = 0
    while (video_source.isOpened()):

        # Grab current frame
        ret, frame = video_source.read()
        # Check if we've reached the end, if so, exit loop
        if ret == False:
            break
        # Resize frame to speed up
        frame = imutils.resize(frame, width=1200)

        # Find the AruCo markers in the current frame, and if found, overlay the
        # weather image
        output_image, output_outline = aruco_ar(
            frame, overlay_image, display_aruco_boxes,
            cornerIDs=aruco_IDs,
            arucoDict=arucoDict,
            arucoParams=arucoParams)

        # Check that the function returned with valid image (we know the aruco markers were detected properly)
        if output_image is not None:
            # set equal to output to display
            frame = output_image
            frame_outline = output_outline
            # Print status
            print('\t{}: AruCo markers found in image.'.format(image_count))
        else:
            # All AruCo markers not found
            print('\t{}: -- One or more AruCo marker not detected in image. --'.format(image_count))
            frame_outline = frame

        # Display the resulting frame
        cv2.imshow('Frame', frame)
        # show the output frame
        cv2.imshow("AruCo Detection", frame_outline)

        # Check if exit button hit (q)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        # Increase image count
        image_count += 1

    # Close any open windows
    cv2.destroyAllWindows()

    # Finished
    print('Finished!')


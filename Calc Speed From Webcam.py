import Image, ImageChops, os, glob, ImageFont, ImageDraw

# Requires Python Imaging Library (PIL)
#     Download at http://www.pythonware.com/products/pil/
# Requires YawCam
#     Download at http://www.yawcam.com/download.php

# YawCam should take an array of 3 photos when the motion sensor is activated.
# The camera should be pointed perpendicular to the objects path.


# CalibrationFactor is the multiplyer to go from
# Pixels per millisecond to your desired units (MPH, KPH, m/s...)
# This has to be calculated by running this script on objects
# with known speeds several times and taking an average. Your motion
# detection area (defined in YawCam) should be centered within the picture so that
# left-bound and right-bound objects get their 2nd and 3rd pictures in the same region
# of the frame.

# Formula:
# CalibrationFactor = (known velocity / velocity inicated on output photos) * Current CalibrationFactor Value
# Set CalibrationFactor
CalibrationFactor = 128.8

# Set desired units
Unit = "MPH"

# Box defines where to crop the pictures so that the timestamp is left off
# for analysis of movement.
box = (0, 0, 320, 218)

# Set to 1 if you want output photos for sensitivity testing, otherwise 0
TestSensitivity = 1
# Use higher value if any white spots are present other than on the object
# Use lower value if there is not enough white to tell where the front of the object is.
Sensitivity = 90

#####################################################################################


# Extracts information about all the files in the directory starting with 'motion'.
filelist = []
fileMS = []
fileS = []
fileM = []
fileH = []
for infile in glob.glob('motion*'):
    filelist = filelist + [infile]
    # the numbers in brackets define where times are found
    # in the file name.
    fileMS = fileMS + [infile[27:30]]
    fileS = fileS + [infile[24:26]]
    fileM = fileM + [infile[21:23]]
    fileH = fileH + [infile[18:20]]

# Counts motion files and raises exeption if there is not a multiple of 3.
FileCount = len(filelist)
if float(FileCount)/float(3)-int(FileCount/3) <> 0:
    print 'The number of files is not divisible by 3.'
    print 'Photo software must be set to capture 3 images'
    print 'each time motion is detected.'
    h = raw_input('press enter to quit')
    raise NameError('Number of files not divisible by 3')


# Asigns variables a,b,and c to designate the 1st, 2nd and 3rd photo of each set.
for x in range(1,(FileCount/3+1)):
    a = x*3-3
    b = x*3-2
    c = x*3-1
    Start = int(fileMS[b])+int(fileS[b])*1000+int(fileM[b])*60000+int(fileH[b])*3600000
    End = int(fileMS[c])+int(fileS[c])*1000+int(fileM[c])*60000+int(fileH[c])*3600000

    Time = End - Start
    if Time <0:
        # Adds a day (in MS) if the end time falls in the next day.
        Time = End + (3600000*24) - Start

    # Converts to greyscale and crops to remove timestamp. Timestamp must not be visible.
    im1 = (Image.open(filelist[a]).convert("L")).crop(box)
    im2 = (Image.open(filelist[b]).convert("L")).crop(box)
    im3 = (Image.open(filelist[c]).convert("L")).crop(box)

    # compares the photos and makes new pictures where changed pixels are white and
    # unchanged are black.
    diff2 = ImageChops.difference(im1, im2)
    diff3 = ImageChops.difference(im1, im3)
    EvalPic2 = ImageChops.invert(Image.eval(diff2, lambda px: px <= Sensitivity and 255 or 0))
    EvalPic3 = ImageChops.invert(Image.eval(diff3, lambda px: px <= Sensitivity and 255 or 0))

    # Saves copies of the above photos if needed for testing.
    if TestSensitivity == 1:
        EvalPic2.save("Test2_" + filelist[b], quality=100)
        EvalPic3.save("Test3_" + filelist[b], quality=100)

    # Finds the difference in x-axis coordinates of the leading edge of each photo.
    # If the object is moving left, the difference in left leading edges will be greater.
    # If the object is moving right, the difference in right leading edges will be greater.
    # This is because the trailing side of the photo is always the same in each photo,
    # it is where the object was in picture 1 (or picture a).
    L = EvalPic2.getbbox()[0] - EvalPic3.getbbox()[0]
    R = EvalPic3.getbbox()[2] - EvalPic2.getbbox()[2]
    Speed = max(L,R)

    # Prepares the string for printing on picture. Number of decimal places is set here.
    Vel = ("%.1f" % (float(Speed)/float(Time)*CalibrationFactor))
    txt =  str(Vel + " " + Unit)

    # writes the velocity text onto the picture
    picTxt = Image.open(filelist[b])
    saveName = "Velocity_" + filelist[b][7:100]
    draw = ImageDraw.Draw(picTxt)
    font = ImageFont.truetype("arial.ttf", 14)
    draw.text((175,222), txt, font=font)
    picTxt.save(saveName, quality=100)
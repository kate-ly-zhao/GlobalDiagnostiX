# -*- coding: utf-8 -*-

"""
Script to read and display the experiments done with the iAi electronics
prototype in the x-ray lab
"""

from __future__ import division

import os
import glob
import numpy
import matplotlib.pylab as plt
import platform
import random
import scipy.misc  # for saving to b/w png

import lineprofiler


def my_display_image(image):
    """
    Display an image with the 'bone' color map, bicubic interpolation and with
    the gray values from the minimum of the image to the mean plus three times
    the standard deviation of the image
    """
    plt.imshow(image, cmap='bone', interpolation='bicubic',
               vmin=numpy.min(image),
               vmax=numpy.mean(image) + 3 * numpy.std(image))
    plt.axis('off')


def my_display_histogram(image, howmanybins=64, histogramcolor='k',
                         rangecolor='r'):
    """
    Display the histogram of an input image, including the ranges we have set
    in the MyDisplayImage function above as dashed lines
    """
    plt.hist(image.flatten(), bins=howmanybins, histtype='stepfilled',
             fc=histogramcolor, alpha=0.309)
    plt.axvline(x=numpy.min(image), color=rangecolor, linestyle='--')
    plt.axvline(x=numpy.mean(image), color='k', linestyle='--')
    plt.axvline(x=numpy.mean(image) + 3 * numpy.std(image), color=rangecolor,
                linestyle='--')
    # turn off y-ticks: http://stackoverflow.com/a/2176591/323100
    plt.gca().axes.get_yaxis().set_ticks([])
    plt.title('Histogram. Black = mean, Red = Display range')

# Setup
CameraWidth = 1280
CameraHeight = 1024

# Get images
if platform.node() == 'anomalocaris':
    RootPath = '/Volumes/slslc/EssentialMed/Images/DetectorElectronicsTests'
else:
    RootPath = '/afs/psi.ch/project/EssentialMed/Images' \
               '/DetectorElectronicsTests'

# Get all subfolders: http://stackoverflow.com/a/973488/323100
FolderList = os.walk(RootPath).next()[1]

shuffle = False
if shuffle:
    # Shuffle the Folderlist to make clicking less boring...
    random.shuffle(FolderList)

# Get images from the module with IP 44, since that was the one that was focus
# and aligned properly for this test
RadiographyName = [glob.glob(os.path.join(RootPath, i, '*1-44.gray'))[0] for
                   i in FolderList]
DarkName = [glob.glob(os.path.join(RootPath, i, '*0-44.gray'))[0] for i in
            FolderList]

# Read files
print 'Reading all radiographies'
Radiography = [numpy.fromfile(i, dtype=numpy.int16).reshape(CameraHeight,
                                                            CameraWidth) for
               i in RadiographyName]
print 'Reading all darks'
Dark = [numpy.fromfile(i, dtype=numpy.int16).reshape(CameraHeight,
                                                     CameraWidth) for i in
        DarkName]
print 'Calculating all corrected images'
CorrectedData = [Radiography[i] - Dark[i] for i in range(len(FolderList))]

# Grab parameters from filename
kV = [int(os.path.basename(i).split('kV_')[0].split('_')[-1])
      for i in FolderList]
mAs = [int(os.path.basename(i).split('mAs_')[0].split('kV_')[-1])
       for i in FolderList]
XrayExposureTime = [int(os.path.basename(i).split('ms_')[0].split('mAs_')[-1])
                    for i in FolderList]
CMOSExposureTime = [int(os.path.basename(i).split('-e')[1].split('-g')[0])
                    for i in RadiographyName]
Gain = [int(os.path.basename(i).split('-g')[1].split('-i')[0])
        for i in RadiographyName]

# Calculate surface entrance dose (according to DoseCalculation.py)
K = 0.1  # mGy m^2 mAs^-1
BSF = 1.35
SED = [K * (CurrentVoltage / 100) ** 2 * CurrentmAs * (100 / 120) ** 2 * BSF
       for CurrentVoltage, CurrentmAs in zip(kV, mAs)]

# Write some data to a data.txt file we use for
# ~/Documents/DemonstratorAnalysis/DemonstratorAnalysis.Rmd
outputfile = open('/afs/psi.ch/project/EssentialMed/Documents'
                  '/DemonstratorAnalysis/data.txt', 'w')
outputfile.write(
    'Item, kV, mAs, SourceExposureTime, Gain, SurfaceEntranceDose\n')
for item in zip(FolderList, kV, mAs, XrayExposureTime, Gain, SED):
    outputfile.write(str(item)[1:-1] + '\n')
outputfile.close()

# Grab information from files
ValuesImage = [[numpy.min(i), numpy.mean(i), numpy.max(i), numpy.std(i)] for
               i in Radiography]
ValuesDark = [[numpy.min(i), numpy.mean(i), numpy.max(i), numpy.std(i)] for i
              in Dark]
ValuesCorrectedData = [[numpy.min(i), numpy.mean(i), numpy.max(i), numpy.std(
    i)] for i in CorrectedData]

for counter, Folder in enumerate(FolderList):
    print 80 * '-'
    print str(counter + 1) + '/' + str(len(FolderList)), '|', \
        os.path.basename(Folder)

    # Inform the user
    print '\nFor the experiment with', kV[counter], 'kV,', mAs[counter], \
        'mAs we have the following image properties'
    print '\tMin\tMean\tMax\tSTD'
    print 'Image\t', round(ValuesImage[counter][0], 1), '\t', \
        round(ValuesImage[counter][1], 1), '\t', \
        round(ValuesImage[counter][2], 1), '\t', \
        round(ValuesImage[counter][3], 1)
    print 'Dark\t', round(ValuesDark[counter][0], 1), '\t', \
        round(ValuesDark[counter][1], 1), '\t', \
        round(ValuesDark[counter][2], 1), '\t', \
        round(ValuesDark[counter][3], 1)
    print 'Img-Drk\t', round(ValuesCorrectedData[counter][0], 1), '\t', \
        round(ValuesCorrectedData[counter][1], 1), '\t', \
        round(ValuesCorrectedData[counter][2], 1), '\t', \
        round(ValuesCorrectedData[counter][3], 1)

    print 'Saving corrected image as', os.path.join(RootPath,
                                                    FolderList[counter],
                                                    'corrected.png')
    # scipy.misc.imsave
    scipy.misc.imsave(os.path.join(RootPath, FolderList[counter],
                                   'corrected.png'), CorrectedData[counter])

    # Display all the important things
    plt.figure(counter + 1, figsize=(16, 9))
    FigureTitle = str(counter + 1) + '/' + str(len(FolderList)), \
        '| Xray shot with', str(kV[counter]), 'kV and', str(mAs[counter]), \
        'mAs (' + str(XrayExposureTime[counter]) + \
        'ms source exposure time). Captured with', \
        str(CMOSExposureTime[counter]), 'ms CMOS exposure time and Gain', \
        str(Gain[counter])
    plt.suptitle(' '.join(FigureTitle))

    plt.subplot(441)
    my_display_image(Radiography[counter])
    plt.title('Image')

    plt.subplot(442)
    my_display_histogram(Radiography[counter])

    plt.subplot(445)
    my_display_image(Dark[counter])
    plt.title('Dark')

    plt.subplot(446)
    my_display_histogram(Dark[counter])
    plt.title('')

    plt.subplot(243)
    my_display_image(CorrectedData[counter])
    plt.title('Image - Dark')

    plt.subplot(244)
    my_display_histogram(CorrectedData[counter])

    # Select two line profiles on corrected image.
    # The two profiles are along the first two lines of the resolution phantom
    Coordinates = [((566, 350), (543, 776)), ((726, 350), (703, 776))]
    MyColors = ["#D1B9D4", "#D1D171", "#84DEBD"]

    for ProfileCounter, CurrentCoordinates in enumerate(Coordinates):
        SelectedPoints, LineProfile = lineprofiler.lineprofile(
            CorrectedData[counter], CurrentCoordinates, showimage=False)

        # Draw selection on corrected image
        plt.figure(counter + 1, figsize=(16, 9))
        plt.subplot(243)
        my_display_image(CorrectedData[counter])
        plt.plot((SelectedPoints[0][0], SelectedPoints[1][0]),
                 (SelectedPoints[0][1], SelectedPoints[1][1]),
                 color=MyColors[ProfileCounter], marker='o')
        plt.plot(SelectedPoints[0][0], SelectedPoints[0][1], color='yellow',
                 marker='o')
        plt.plot(SelectedPoints[1][0], SelectedPoints[1][1], color='black',
                 marker='o')
        plt.title('Image - Dark')

        # Draw both line profiles
        plt.figure(counter + 1, figsize=(16, 9))
        plt.subplot(4, 1, ProfileCounter + 3)
        plt.plot(LineProfile, color=MyColors[ProfileCounter],
                 label='Line profile')
        plt.plot(0, LineProfile[0], color='yellow', marker='o',
                 markersize=25, alpha=0.309)
        plt.plot(len(LineProfile) - 1, LineProfile[-1], color='black',
                 marker='o', markersize=25, alpha=0.309)
        plt.axhline(numpy.mean(CorrectedData[counter]), color=MyColors[2],
                    label=u'Image mean ± STD')
        plt.fill_between(range(len(LineProfile)),
                         numpy.mean(CorrectedData[counter]) + numpy.std(
                             CorrectedData[counter]),
                         numpy.mean(CorrectedData[counter]) - numpy.std(
                             CorrectedData[counter]), alpha=0.309,
                         color=MyColors[2])

        plt.figure(counter + 1, figsize=(16, 9))
        plt.legend(loc='upper left')
        plt.xlim([0, len(LineProfile) - 1])
        plt.ylim([numpy.mean(CorrectedData[counter]) - 2 *
                  numpy.std(CorrectedData[counter]),
                  numpy.mean(CorrectedData[counter]) + 2 *
                  numpy.std(CorrectedData[counter])])
        if not ProfileCounter:
            plt.title('Line profiles along selections')

    print 'Saving figure as', os.path.join(RootPath, Folder + '.png')
    plt.savefig(os.path.join(RootPath, Folder + '.png'), bbox_inches='tight')
    plt.show()

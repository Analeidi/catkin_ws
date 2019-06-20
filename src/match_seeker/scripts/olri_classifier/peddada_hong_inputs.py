# This program divides the image data into two parts, overrepped, with images corresponding to cells that have too much
# and underrepped, with images corresponding to cells that have too little. To cull the overrepped data, for each
# overrepped cell we iteratively removed a random image with the most represented heading until we had the desired
# number of images. To add additional data

import olin_factory as factory
import cv2
import numpy as np
import os
import random
from datetime import datetime

numCells = 271

def getCellCounts():
    with open(factory.paths.cell_data_path,'r') as masterlist:
        lines = masterlist.readlines()
        cell_counts = dict()
        cell_frame_dict = dict()
        for i in range(numCells):
            cell_frame_dict[str(i)] = []

        for line in lines:
            splitline = line.split()
            if splitline[1] not in cell_counts.keys():
                cell_counts[splitline[1]] = 1
            else:
                cell_counts[splitline[1]] += 1

            cell_frame_dict[splitline[1]].append('%04d'%int(splitline[0]))

    return cell_counts, cell_frame_dict

def getFrameCellDict():
    frame_cell_dict = {}
    with open(factory.paths.cell_data_path,'r') as masterlist:
        lines = masterlist.readlines()
        for line in lines:
            split = line.split()
            frame_cell_dict['%04d'%int(split[0])] = split[1]
    return frame_cell_dict

def getHeadingRep():
    cellHeadingCounts = dict()
    for i in range(numCells):
        cellHeadingCounts[str(i)] = [['0',0],['45',0],['90',0],['135',0],['180',0],['225',0],['270',0],['315',0]]
    with open(factory.paths.cell_data_path,'r') as masterlist:
        lines = masterlist.readlines()
        for line in lines:
            split = line.split()
            for pair in cellHeadingCounts[str(split[1])]:
                if pair[0] == split[-1]:
                    pair[1] += 1
                    break

    return  cellHeadingCounts

def getUnderOverRep(cell_counts):
    underRep = []
    overRep = []

    for key in cell_counts.keys():
        if int(cell_counts[key]) <= 300:
            underRep.append(key)
        else:
            overRep.append(key)

    return underRep, overRep

def getHeadingFrameDict():
    heading_frame_dict = {'0':[],'45':[],'90':[],'135':[],'180':[],'225':[],'270':[],'315':[]}

    with open(factory.paths.cell_data_path,'r') as masterlist:
        lines = masterlist.readlines()
        for line in lines:
            split = line.split()
            heading_frame_dict[split[-1]].append('%04d'%int(split[0]))

    return heading_frame_dict

def getFrameHeadingDict():
    fhd = {}
    with open(factory.paths.cell_data_path,'r') as masterlist:
        lines = masterlist.readlines()
        for line in lines:
            split = line.split()
            fhd['%04d'%int(split[0])] = split[-1]

    return fhd

def getOneHotLabel(number,size):
    onehot = [0] * size
    onehot[number] = 1
    return onehot

def cullOverRepped():
    cell_counts, cell_frame_dict = getCellCounts()
    cell_heading_counts = getHeadingRep()
    under, overRepList = getUnderOverRep(cell_counts)
    heading_frame_dict = getHeadingFrameDict()
    frame_to_heading = getFrameHeadingDict()
    remove = []
    overreppedFrames = []
    i = 1
    for cell in overRepList:
        print('Cell '+ str(i) + " of " + str(len(overRepList)))
        i+=1

        for frame in cell_frame_dict[cell]:
            overreppedFrames.append(frame)
        while cell_counts[cell] > 300:
            headingList = sorted(cell_heading_counts[cell],key= lambda x: x[1])
            largestHeading = headingList[-1][0]
            headingList[-1][1] = headingList[-1][1] -1

            potentialCulls = []
            for frame in heading_frame_dict[largestHeading]:
                if frame in cell_frame_dict[cell]:
                    potentialCulls.append(frame)
            toBeRemoved = potentialCulls[random.randint(0,len(potentialCulls)-1)]
            overreppedFrames.remove(toBeRemoved)

            cell_frame_dict[cell].remove(toBeRemoved)
            cell_counts[cell] -= 1

    print(len(overreppedFrames))
    # for frame in remove:
    #     try:
    #         overreppedFrames.remove(frame)
    #     except ValueError:
    #         print(frame)

    np.save('/home/macalester/PycharmProjects/catkin_ws/src/match_seeker/scripts/olri_classifier/newdata_overreppedFrames.npy',overreppedFrames)
    return overreppedFrames

def addUnderRepped():
    cell_counts, cell_frame_dict = getCellCounts()
    cell_heading_counts = getHeadingRep()
    underRepList, over = getUnderOverRep(cell_counts)
    heading_frame_dict = getHeadingFrameDict()
    remove = []
    underreppedFrames = []
    i = 1
    for cell in underRepList:
        print('Cell '+ str(i) + " of " + str(len(underRepList)),cell)
        i+=1

        for frame in cell_frame_dict[cell]:
            underreppedFrames.append(frame)
        while cell_counts[cell] < 300:
            headingList = sorted(cell_heading_counts[cell],key= lambda x: x[1])
            smallestHeading = headingList[0][0]
            headingList[0][1] = headingList[0][1] + 1
            potentialAdditions = []
            for frame in heading_frame_dict[smallestHeading]:
                if frame in cell_frame_dict[cell]:
                    potentialAdditions.append(frame)
            if len(potentialAdditions) == 0:
                print(cell, 'has very little data')
                continue
            toBeAdded = random.choice(potentialAdditions)
            underreppedFrames.append(toBeAdded)
            cell_frame_dict[cell].append(toBeAdded)
            cell_counts[cell] += 1

    print(len(underreppedFrames))
    np.save('/home/macalester/PycharmProjects/catkin_ws/src/match_seeker/scripts/olri_classifier/newdata_underreppedFrames.npy',underreppedFrames)
    return underreppedFrames

def resizeAndCrop(image):
    # Original size 341x256 cropped to 224x224
    # smaller size 170x128 cropped to 100x100
    image = cv2.resize(image,(170,128))
    x = random.randrange(0,70)
    y = random.randrange(0,28)

    cropped_image = image[y:y+100, x:x+100]
    cropped_image = cv2.cvtColor(cropped_image,cv2.COLOR_BGR2GRAY)

    return cropped_image

def getTrainingData(overRepped=None,underRepped=None):
    frame_cell_dict = getFrameCellDict()
    frame_heading_dict = getFrameHeadingDict()
    training_data = []

    def processFrame(frame):
        print('Processing frame', frame)
        image = cv2.imread(factory.paths.train_data_dir + '/frame' + frame + '.jpg')
        image = resizeAndCrop(image)
        training_data.append([np.array(image), getOneHotLabel(int(frame_cell_dict[frame]), numCells),
                              getOneHotLabel(int(frame_heading_dict[frame]) // 45, 8)])


    if underRepped is not None:
        for frame in underRepped:
            processFrame(frame)
    else:
        for frame in addUnderRepped():
            processFrame(frame)

    if overRepped is not None:
        for frame in overRepped:
            processFrame(frame)
    else:
        for frame in cullOverRepped():
            processFrame(frame)

    np.save('/home/macalester/PycharmProjects/catkin_ws/src/match_seeker/scripts/olri_classifier/NEWTRAININGDATA_95k_100_gray.npy',training_data)

    print('Done!')
    return training_data
if __name__ == '__main__':
    # getTrainingData(underRepped=np.load('/home/macalester/PycharmProjects/catkin_ws/src/match_seeker/scripts/olri_classifier/newdata_underreppedFrames.npy'),
    # overRepped=np.load('/home/macalester/PycharmProjects/catkin_ws/src/match_seeker/scripts/olri_classifier/newdata_overreppedFrames.npy'))
    # getTrainingData()

    # over = np.load(
    #    '/home/macalester/PycharmProjects/catkin_ws/src/match_seeker/scripts/olri_classifier/newdata_overreppedFrames.npy')
    #under = np.load(
    #   '/home/macalester/PycharmProjects/catkin_ws/src/match_seeker/scripts/olri_classifier/newdata_underreppedFrames.npy')
    arr = []
    for cell in getCellCounts()[0].keys():

        arr.append(int(cell))
    arr.sort()
    print(arr)
    for i in range(len(arr)-1):
        if arr[i+1] - arr[i] != 1:
            print(i,arr[i])
# for i in range(95837):
    #     if '%04d'%i not in over and '%04d'%i not in under:
    #         print i

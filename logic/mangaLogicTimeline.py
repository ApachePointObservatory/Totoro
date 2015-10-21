#!/usr/bin/env python
# encoding: utf-8
"""
mangaLogicTimeline.py

Created by José Sánchez-Gallego on 3 Aug 2014.
Licensed under a 3-clause BSD license.

Revision history:
    3 Aug 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
import numpy as np
from sdss.internal.manga.Totoro import utils
from sdss.internal.manga.Totoro import config, site


expTime = config['exposure']['exposureTime']


def getOptimalPlate(plates, jdRanges, prioritisePlugged=True,
                    mode='plugger', **kwargs):
    """Gets the optimal plate to observe in a range of JDs."""

    efficiency = kwargs.pop('efficiency', config[mode]['efficiency'])

    jdRanges = np.atleast_2d(jdRanges).copy()

    observablePlates = [plate for plate in plates
                        if isObservable(plate, jdRanges)]
    incompletePlates = [plate for plate in observablePlates
                        if plate.isComplete is False]

    if prioritisePlugged:

        pluggedPlates = []
        notPlugged = []
        for plate in incompletePlates:
            if plate.isPlugged:
                pluggedPlates.append(plate)
            else:
                notPlugged.append(plate)

        if len(pluggedPlates) > 0:
            return getOptimalPlate(pluggedPlates, jdRanges,
                                   prioritisePlugged=False, mode=mode,
                                   efficiency=efficiency, **kwargs)
    else:
        notPlugged = incompletePlates

    startedPlates = [plate for plate in notPlugged
                     if len(plate.getTotoroExposures(onlySets=True)) > 0]

    if len(startedPlates) > 0:
        observedFlag = simulatePlates(startedPlates, jdRanges, mode=mode,
                                      efficiency=efficiency)
        if observedFlag is True:
            optimal = selectOptimal(startedPlates, jdRanges)
            cleanupPlates(startedPlates, optimal)
            return optimal

    observedFlag = simulatePlates(notPlugged, jdRanges, mode=mode,
                                  efficiency=efficiency)
    if observedFlag is False:
        return None

    optimal = selectOptimal(notPlugged, jdRanges)
    cleanupPlates(notPlugged, optimal)

    return optimal


def selectOptimal(plates, jdRanges, **kwargs):
    """Returns the optimal plate to observe."""

    plates = np.array(plates)

    newPlates = []
    for plate in plates:
        exps = plate.getTotoroExposures(onlySets=True)
        for exp in exps:
            if hasattr(exp, '_tmp') and exp._tmp is True:
                newPlates.append(plate)
                break
    newPlates = np.array(newPlates)

    # Sorts jdRanges
    jdRanges = jdRanges[jdRanges[:, 0].argsort()]

    # Selects plates that contain the earliest JD
    minJD = jdRanges[0][0]
    minLST = site.localSiderealTime(minJD)
    platesMinJD = [plate for plate in newPlates
                   if utils.isPointInInterval(minLST, plate.getLSTRange())]

    # If there are such plates, uses those. Otherwise, uses all.
    if len(platesMinJD) > 0:
        newPlates = np.array(platesMinJD)
    else:
        pass

    # First tries to select the complete plate with the fewer number
    # of exposures
    completedPlates = [plate for plate in newPlates if plate.isComplete]
    if len(completedPlates) > 0:
        nExposures = [
            len(plate.getTotoroExposures(onlySets=True)) / plate.priority
            for plate in completedPlates]
        return completedPlates[np.argmin(nExposures)]

    marked = np.array([plate for plate in newPlates
                       if len(plate.statuses) > 0
                       if plate.statuses[0].label == 'Accepted'])
    markedOptimal = _getOptimalFromList(marked) if len(marked) > 0 else None

    if markedOptimal is not None:
        return markedOptimal
    else:
        return _getOptimalFromList(newPlates)


def _getOptimalFromList(plates):
    """Returns the optimal plate from a list."""

    # If no completed plates, calculates the plate completion using only
    # complete sets
    plateCompletion = np.array(
        [plate.getPlateCompletion(includeIncompleteSets=True)
         for plate in plates])

    maxPlateCompletion = plateCompletion.max()

    # Selects the plates with maximum completion
    platesMaxCompletion = plates[np.where(
        plateCompletion == maxPlateCompletion)]

    if len(platesMaxCompletion) == 1:
        # If only one plate with maximum completion
        return platesMaxCompletion[0]
    else:
        nExposures = [
            len(plate.getTotoroExposures(onlySets=True)) / plate.priority
            for plate in platesMaxCompletion]
        return platesMaxCompletion[np.argmin(nExposures)]

        # If several plates with maximum completion, returns that with the
        # maximum overall completion (including incomplete sets).
        # plateCompletionIncomplete = np.array(
        #     [plate.getPlateCompletion(includeIncompleteSets=True)
        #      for plate in platesMaxCompletion])
        # return platesMaxCompletion[plateCompletionIncomplete.argmax()]

    return None


def simulatePlates(plates, jdRanges, mode='plugger', efficiency=None):
    """Simulates exposures for a list of plates withing a range of JDs."""

    jdRanges = np.atleast_2d(jdRanges)
    observedFlag = False

    efficiency = config[mode]['efficiency'] if efficiency is None \
        else efficiency

    expTimeEff = expTime / efficiency
    maxAlt = config[mode]['maxAltitude']

    for plate in plates:

        plateLST = plate.getLSTRange()
        stopPlate = False

        for jdRange in jdRanges:

            jd = jdRange[0]
            while jd < jdRange[1]:

                if plate.isComplete:
                    stopPlate = True
                    break

                lst = site.localSiderealTime(jd)
                lstMean = site.localSiderealTime(jd+expTimeEff/2./86400.)

                if (not utils.isPointInInterval(lst, plateLST, wrapAt=24)):
                    pass
                elif plate.getAltitude(lstMean) > maxAlt:
                    stopPlate = True
                    break
                else:
                    result = plate.addMockExposure(
                        set=None, startTime=jd, expTime=expTimeEff,
                        silent=True)
                    if result is not False:
                        observedFlag = True
                        result._tmp = True

                jd += expTimeEff / 86400.

            if stopPlate:
                break

    return observedFlag  # True if we have added at least one exposure


def isObservable(plate, jdRanges):
    """Returns True if a plate is observable in a range of JDs."""

    jdRanges = np.atleast_2d(jdRanges)
    plateLSTRange = plate.getLSTRange()

    for jdRange in jdRanges:
        lstRange = site.localSiderealTime(jdRange)
        if (utils.getIntervalIntersection(plateLSTRange, lstRange, wrapAt=24.)
                is not False):
            return True

    return False


def cleanupPlates(plates, optimumPlate):
    """Clears exposures in plates that are not the optimum and removes the
    temporary flag in the optimum one."""

    for plate in plates:

        if plate is optimumPlate:
            for exp in plate.getValidExposures():
                if hasattr(exp, '_tmp'):
                    delattr(exp, '_tmp')
            for set in plate.sets:
                if len(set.totoroExposures) == 0:
                    plate.sets.remove(set)
            continue

        for set in plate.sets:
            set.totoroExposures = [exp for exp in set.totoroExposures
                                   if not hasattr(exp, '_tmp') or
                                   exp._tmp is not True]
        plate.sets = [set for set in plate.sets
                      if len(set.totoroExposures) > 0]

    return

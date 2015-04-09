#!/usr/bin/env python
# encoding: utf-8
"""
scheduler.py

Created by José Sánchez-Gallego on 17 Feb 2014.
Licensed under a 3-clause BSD license.

Revision history:
    17 Feb 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from sdss.internal.manga.Totoro import exceptions
from sdss.internal.manga.Totoro import log, site
from sdss.internal.manga.Totoro.scheduler import observingPlan
from plugger import Plugger
from planner import PlannerScheduler
from astropy import time


__ALL__ = ['BaseScheduler', 'Planner', 'Nightly', 'Plugger']


class BaseScheduler(object):
    """The base class for the autoscheduler.

    This class provides the common base to plan observations
    and is inherited by Scheduler, Plugger and Planner.

    """

    def __init__(self, startDate=None, endDate=None, **kwargs):

        self._observingPlan = observingPlan

        if self._observingPlan is None:
            raise exceptions.TotoroError(
                'observing plan not found. Not possible to create an '
                'instance of BaseScheduler.')

        self.site = site
        self._setStartEndDate(startDate, endDate, **kwargs)

        scope = kwargs.get('scope', 'planner')

        if scope != 'plugger':
            self.observingBlocks = self._observingPlan.getObservingBlocks(
                self.startDate, self.endDate)
        else:
            self.observingBlocks = self._observingPlan._createObservingBlock(
                self.startDate, self.endDate)

    def _setStartEndDate(self, startDate, endDate, scope='planner', **kwargs):
        """Sets the start and end date if they haven't been defined."""

        if scope == 'planner':
            if startDate is None:
                startDate = time.Time.now().jd
            if startDate is None or endDate is None:
                raise exceptions.TotoroError('planner end date.')

        elif scope == 'nightly':
            if startDate is None or endDate is None:
                startDate, endDate = self._observingPlan.getJD(startDate)

        elif scope == 'plugger':
            if startDate >= endDate:
                raise exceptions.TotoroError('startDate must be < endDate')

        self.startDate = startDate
        self.endDate = endDate
        self.currentDate = time.Time.now().jd

        log.info('start date: {0}'.format(self.startDate))
        log.info('end date: {0}'.format(self.endDate))


class Planner(BaseScheduler):

    def __init__(self, startDate=None, endDate=None, **kwargs):

        log.info('entering PLANNER mode.')

        super(Planner, self).__init__(startDate=startDate,
                                      endDate=endDate, scope='planner',
                                      **kwargs)

        self._plannerScheduler = PlannerScheduler(self.observingBlocks,
                                                  **kwargs)
        self._plannerScheduler.schedule(**kwargs)


class Nightly(object):

    def __init__(self, startDate=None, endDate=None, plates=None, **kwargs):

        log.info('entering NIGHTLY mode.')

        self.startDate = startDate
        self.endDate = endDate
        self.currentDate = time.Time.now().jd

        if plates is None:
            self.plates = self.getPlates(**kwargs)
        else:
            log.info('using programmatic input for plates.')
            log.info('{0} input plates'.format(len(plates)))
            self.plates = plates

    def getPlates(self, **kwargs):
        """Gets the plugged plates."""

        from sdss.internal.manga.Totoro import dbclasses

        plates = dbclasses.getPlugged(**kwargs)

        if len(plates) == 0:
            log.info('no plugged plates found.')
        else:
            log.info('found {0} plugged plates'.format(len(plates)))

        return plates

    def printTabularOutput(self):
        """Prints a series of tables with information about the schedule."""

        from sdss.internal.manga.Totoro import output

        output.printTabularOutput(self.plates)

    def getOutput(self, format='dict'):
        """Returns the nightly output in the selected format."""

        from sdss.internal.manga.Totoro import output

        if format == 'table':
            return output.getTabularOutput(self.plates)
        else:
            return output.getNightlyOutput(self, format=format)

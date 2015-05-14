#!/usr/bin/env python
# encoding: utf-8
"""
testAPOcomplete.py

Created by José Sánchez-Gallego on 14 Jul 2014.
Licensed under a 3-clause BSD license.

Revision history:
    3 May 2015 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from sdss.internal.manga.Totoro import TotoroDBConnection
from sdss.internal.manga.Totoro.dbclasses import fromPlateID


db = TotoroDBConnection()
session = db.session


class testSetArrangement():

    def testExposureAssignment(self):
        """Tests if an exposure is assigned to a correct incomplete set."""

        db = TotoroDBConnection()

        with session.begin(subtransactions=True):
            exposure = session.query(db.mangaDB.Exposure).get(1348)
            exposure.set_pk = None

        plate = fromPlateID(8484, rearrangeIncomplete=False, force=True)

        assert len(plate.sets) == 6

        setExposurePK = [exp._mangaExposure.pk
                         for exp in plate.sets[4].totoroExposures]
        assert 1348 in setExposurePK

    def testIncompleteSetsRearrangement(self):
        """Tests whether the rearrang. of incomplete sets works properly."""

        # Removes all set assignment for plate 8551
        with session.begin(subtransactions=True):
            plate8551 = fromPlateID(8551)
            exposures = plate8551.getScienceExposures()
            for exp in exposures:
                setPK = exp.mangadbExposure[0].set_pk
                exp.mangadbExposure[0].set_pk = None
                if setPK is not None:
                    ss = session.query(db.mangaDB.Set).get(setPK)
                    session.delete(ss)

        # Reloads plate 8551
        plate8551 = fromPlateID(8551, force=True)
        for ss in plate8551.sets:
            print(ss.pk, [exp.exposure_no for exp in ss.totoroExposures])





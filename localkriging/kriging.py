# -*- coding: utf-8 -*-

"""Main module."""
from os.path import basename, splitext
from collections import OrderedDict
import numpy as np
import rasterio as rio
from sklearn.ensemble import RandomForestRegressor
from geopandas import read_file
from configs.config import shapefile, covariates
from localkriging import mpiops

targets = read_file(shapefile)

xy = [(p.x, p.y) for p in targets['geometry']]

# rfr = RandomForestRegressor()
# X = np.hstack([lons, lats])
# rfr.fit(X=X, y=targets['K_ppm_imp_'])
# print(rfr.score(X=X, y=targets['K_ppm_imp_']))


def _join_dicts(dicts):
    if dicts is None:
        return
    d = {k: v for D in dicts for k, v in D.items()}
    return OrderedDict(sorted(d.items()))


def gather_covariates(xy, covariates):
    p_covaraites = mpiops.array_split(covariates, mpiops.rank)
    p_features = process_gather_covariates(xy, p_covaraites)
    features = _join_dicts(mpiops.comm.allgather(p_features))
    return features


def process_gather_covariates(xy, covariates):
    features = {}
    for c in covariates:
        src = rio.open(c)
        features[splitext(basename(c))[0]] = np.array(list(src.sample(xy)))
    return features


features = gather_covariates(xy, covariates)

X = np.hstack([v for v in features.values()])

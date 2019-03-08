# Inspired by shapely-geojson at https://github.com/alekzvik/shapely-geojson

import json

import shapely.affinity as affine
import shapely.geometry as geo


class Feature(object):
    def __init__(self, geometry, **kwds):
        self._geometry = affine.affine_transform(geometry, [10, 0, 0, -10, 0, 10000])
        self._properties = kwds

    @property
    def __geo_interface__(self):
        return {
            'type': 'Feature',
            'geometry': self._geometry.__geo_interface__,
            'properties': self._properties,
        }


class FeatureCollection(object):
    def __init__(self, features, **kwds):
        self.features = features
        self._properties = kwds

    @property
    def features(self):
        return self._features

    @features.setter
    def features(self, objects):
        all_are_features = all(
            isinstance(feature, Feature)
            for feature in objects
        )
        if all_are_features:
            self._features = objects
        else:
            try:
                self._features = [
                    Feature(geometry)
                    for geometry in objects
                ]
            except ValueError:
                raise ValueError(
                    'features can be either a Feature or shapely geometry.')

    def __iter__(self):
        return iter(self.features)

    def geometries_iterator(self):
        for feature in self.features:
            yield feature.geometry

    @property
    def __geo_interface__(self):
        return {
            'type': 'FeatureCollection',
            'features': [
                feature.__geo_interface__
                for feature in self.features
            ],
            'properties': self._properties,
        }


def dump(obj, fp, *args, **kwargs):
    """Dump shapely geometry object :obj: to a file :fp:."""
    json.dump(geo.mapping(obj), fp, *args, **kwargs)


def dumps(obj, *args, **kwargs):
    """Dump shapely geometry object :obj: to a string."""
    return json.dumps(geo.mapping(obj), *args, **kwargs)

# encoding: utf-8

"""Definition of the base class from which all spec elements inherit."""


import six
import os
import importlib

import platform
from os.path import join, dirname, relpath

from ..lexicon.feature import PARTICLE
from ..lexicon.feature.number import PLURAL
from ..lexicon.feature.gender import FEMININE

PY3 = int(platform.python_version_tuple()[0]) == 3


class FeatureModulesLoader(type):

    """Metaclass injecting the feature module property onto a class."""

    def __new__(cls, clsname, bases, dct):
        features = {}
        feature_pkg_path = relpath(
            join(dirname(__file__), '..', 'lexicon', 'feature'))
        for dirpath, _, filenames in os.walk(feature_pkg_path):
            pkg_root = dirpath[dirpath.rfind("pynlg"):].replace(os.sep, '.')
            for filename in filenames:
                if not filename.endswith('.py'):
                    continue
                pkg_path = pkg_root + '.' + filename.replace('.py', '')
                mod = importlib.import_module(pkg_path)
                mod_features = [c for c in dir(mod) if c.isupper()]
                for feat in mod_features:
                    features[feat] = getattr(mod, feat)

        dct['_feature_constants'] = features

        return super(FeatureModulesLoader, cls).__new__(
            cls, clsname, bases, dct)


@six.add_metaclass(FeatureModulesLoader)
@six.python_2_unicode_compatible
class NLGElement(object):

    """Base spec element class from which all spec element classes inherit."""

    def __init__(self, features=None, category=u'', realisation=u'',
                 lexicon=None):
        self.features = features if features else {}
        self.category = category
        self.realisation = realisation
        self.lexicon = lexicon
        self.base_form = None
        self.parent = None
        self.children = []

    def __eq__(self, other):
        if isinstance(other, NLGElement):
            return (self.features == other.features
                    and self.category == other.category)
        elif isinstance(other, (six.text_type, six.binary_type)):
            return self.realisation == other
        else:
            raise TypeError("Can't compare NLGElement to %s" % (
                str(type(other))))

    def __hash__(self):
        feat = {k: v for k, v in self.features.items() if not isinstance(v, (list, tuple))}
        features = tuple(sorted(tuple(feat)))
        return hash((features, self.realisation, self.category, self.base_form))

    def __contains__(self, feature_name):
        """Check if the argument feature name is contained in the element."""
        return feature_name in self.features

    def __setitem__(self, feature_name, feature_value):
        """Set the feature name/value in the element feature dict."""
        self.features[feature_name] = feature_value

    def __getitem__(self, feature_name):
        """Return the value associated with the feature name, from the
        element feature dict.

        If the feature name is not found in the feature dict, return None.

        """
        return self.features.get(feature_name)

    def __delitem__(self, feature_name):
        """Remove the argument feature name and its associated value from
        the element feature dict.

        If the feature name was not initially present in the feature dict,
        a KeyError will be raised.

        """
        if feature_name in self.features:
            del self.features[feature_name]

    def __str__(self):
        return "<{} (realisation={}, category={}, features={})>".format(
            self.__class__.__name__,
            self.realisation,
            self.category,
            self.features)

    def __repr__(self):
        _repr = u"<{} (realisation={}, category={})>".format(
            self.__class__.__name__,
            self.realisation,
            self.category)
        if PY3:
            return _repr
        else:
            return _repr.encode('utf-8')

    def __getattr__(self, name):
        """When a undefined attribute name is accessed, try to return
        self.features[name] if it exists.

        If name is not in self.features, but name.upper() is defined as
        a feature constant, don't raise an AttribueError. Instead, try
        to return the feature value associated with the feature constant
        value.

        This allows us to have a more consistant API when
        dealing with NLGElement and instances of sublclasses.

        If no such match is found, raise an AttributeError.

        Example:
        >>> elt = NLGElement(features={'plural': 'plop', 'infl': ['lala']})
        >>> elt.plural
        'plop'  # because 'plural' is in features
        >>> elt.infl
        ['lala']  # because 'infl' is in features
        >>> elt.inflections
        ['lala']  # because INFLECTIONS='infl' is defined as a feature constant
                # constant, and elt.features['infl'] = ['lala']

        """
        n = name.upper()
        if name in self.features:
            return self.features[name]
        elif n in self._feature_constants:
            new_name = self._feature_constants[n]
            return self.features.get(new_name)
        raise AttributeError(name)

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__()
        copyobj.features = self.features.copy()
        copyobj.category = self.category
        copyobj.realisation = self.realisation
        copyobj.lexicon = self.lexicon
        copyobj.base_form = self.base_form
        return copyobj

    @property
    def feature_names(self):
        """Return all feature names, the keys in the element feature dict."""
        return list(self.features.keys())

    @property
    def language(self):
        """Return the language lexicon."""
        if self.lexicon:
            return self.lexicon.language

    @property
    def is_plural(self):
        return self.number == PLURAL

    @property
    def is_feminine(self):
        return self.gender == FEMININE

    @property
    def particle(self):
        return ('-' + self.features[PARTICLE] if self.features.get(PARTICLE)
                else '')

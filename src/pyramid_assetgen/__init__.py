#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides a py:function:`~pyramid_assetgen.add_assetgen_manifest` 
  `configuration directive`_ and 
  py:class:`~pyramid_assetgen.AssetGenRequestFactoryMixin` 
  `custom request factory`_ mixin class that can be used to integrate
  `Assetgen`_ with a `Pyramid`_ application.
  
  Configure your `Pyramid`_ app (e.g.: in your main / WSGI app factory
  function)::
  
      from pyramid.request import Request
      class MyRequest(Request, AssetGenRequestFactoryMixin):
          pass
      
      config.set_request_factory(MyRequest)
      config.add_directive('add_assetgen_manifest', add_assetgen_manifest)
  
  Expose the directory your assetgen'd static files are in as per normal using
  ``add_static_view`` and then register the assetgen manifest::
  
      config.add_static_view('static', '/var/www/static')
      config.add_assetgen_manifest('static', '/var/www/static')
  
  This assumes you have a manifest file at ``/var/www/static/assets.json``.
  If your manifest file is somewhere else, use the ``manifest_path`` keyword
  argument with either a relative (from the static files directory) or an
  absolute path, e.g. the following are equivalent::
  
      config.add_assetgen_manifest('static', '/var/www/static',
                                   manifest_path='../assets.json')
      config.add_assetgen_manifest('static', '/var/www/static',
                                   manifest_path='/var/www/assets.json')
  
  Once configured, you can use ``request.assetgen_url(name, path)`` in your
  view and template code.  Note that you use the name of the manifest with
  a path that's relative to the static files directory, e.g.::
  
      # looks for ``base.js`` in ``/var/www/static``
      request.assetgen_url('static', 'base.js')
  
  Under the hood, these work with a py:class:`~pyramid_assetgen.AssetGenManifest`
  utility that lazy loads and encapsulates an `Assetgen`_ manifest file.  Calling
  ``assetgen_url(name, path)`` looks up the ``AssetGenManifest`` instance that's
  registered against the ``name``, checks the manifest data to see if it has a 
  key matching ``path`` and, if so, gets the corresponding value.  The path is
  then appended to the ``spec`` the manifest was registered with and this is
  passed to ``static_url`` as the asset specification.
  
  So, for example, if you registered::
  
      config.add_assetgen_manifest('foo', 'mypkg:var/foo')
  
  Calling::
  
      request.assetgen_url('foo', 'base.js')
  
  Might end up calling (and returning the return value of) something like::
  
      request.static_url('mypkg:var/foo/base-2656z75f678sdf867567sf5s6d78.js')
  
  _`assetgen`: http://pypi.python.org/pypi/assetgen
  _`configuration directive`: http://readthedocs.org/docs/pyramid/en/latest/narr/extconfig.html
  _`custom request factory`: http://readthedocs.org/docs/pyramid/en/latest/narr/hooks.html#changing-the-request-factory
  _`pyramid`: http://readthedocs.org/docs/pyramid
"""

__all__ = [
    'IAssetGenManifest',
    'AssetGenManifest',
    'AssetGenRequestFactoryMixin',
    'add_assetgen_manifest',
]

import json
try: # pragma: no coverage
    import urlparse
except ImportError: # pragma: no coverage
    from urllib import parse as urlparse

from zope.interface import Interface, implements

from pyramid.asset import resolve_asset_spec
from pyramid.decorator import reify
from pyramid.path import AssetResolver

class IAssetGenManifest(Interface):
    """A utility that wraps a data dict of keys to file paths."""
    
    def expand(path):
        """Return the expanded ``path``."""
    

class AssetGenManifest(object):
    """Lazy load and encapsulate an `Assetgen`_ manifest file.  For example, if
      we write a trivial manifest data file to disk::
      
          >>> import os
          >>> import tempfile
          >>> f = tempfile.NamedTemporaryFile(delete=False)
          >>> l = f.write('{"base.js": "base-1234.js"}'.encode())
          >>> f.close()
      
      We can use it like so::
      
          >>> manifest = AssetGenManifest('spec', f.name)
          >>> manifest.expand('base.js') == 'spec/base-1234.js'
          True
          >>> manifest.expand('not/in/manifest.js') == 'spec/not/in/manifest.js'
          True
      
      Teardown::
      
          >>> os.unlink(f.name)
      
      _`Assetgen`: http://pypi.python.org/pypi/assetgen
    """
    
    implements(IAssetGenManifest)
    
    def __init__(self, spec, manifest_path):
        if not spec.endswith('/'):
            spec += '/'
        self._spec = spec
        self._manifest_path = manifest_path
    
    @reify
    def _data(self):
        sock = open(self._manifest_path, 'rb')
        data = json.loads(sock.read().decode('UTF-8'))
        sock.close()
        return self._compress(data)
    
    def _compress(self, data):
        """We can safely remove all keys that refer to themselves::
          
              >>> data = {'a': 'a', 'b': 'c'}
              >>> manifest = AssetGenManifest('spec', None)
              >>> manifest._data = manifest._compress(data)
              >>> manifest._data
              {'b': 'c'}
              >>> manifest.expand('a')
              'spec/a'
              >>> manifest.expand('b')
              'spec/c'
          
        """
        
        compressed = {}
        for k, v in data.items():
            if not k == v:
               compressed[k] = v
        return compressed
    
    def expand(self, path):
        return urlparse.urljoin(self._spec, self._data.get(path, path))
        
    

class AssetGenRequestFactoryMixin(object):
    """Mixin to a request factory that adds ``assetgen_url(name, path)`` and
      ``assetgen_path(name, path)`` methods to the ``request``.
    """
    
    def _expand_assetgen_path(self, name, path):
        manifest = self.registry.getUtility(IAssetGenManifest, name=name)
        return manifest.expand(path)
    
    def assetgen_url(self, name, path, **kw):
        spec = self._expand_assetgen_path(name, path)
        return self.static_url(spec, **kw)
    
    def assetgen_path(self, name, path, **kw):
        spec = self._expand_assetgen_path(name, path)
        return self.static_path(spec, **kw)
    


def _resolve_abspath(spec, resolve_=resolve_asset_spec, Resolver_=AssetResolver):
    """Resolve an asset spec to an absolute path."""
    
    pname, filepath = resolve_(spec)
    return Resolver_(pname).resolve(filepath).abspath()

def add_assetgen_manifest(config, name, spec, manifest_path='assets.json'):
    """Register a named IAssetGenManifest utility."""
    
    if not spec.endswith('/'):
        spec += '/'
    
    if manifest_path.startswith('/'):
        abspath = manifest_path
    else:
        manifest_spec = urlparse.urljoin(spec, manifest_path)
        abspath = _resolve_abspath(manifest_spec)
    
    manifest = AssetGenManifest(spec, abspath)
    config.registry.registerUtility(manifest, IAssetGenManifest, name=name)


def includeme(config):
    """Allow developers to use ``config.include('pyramid_assetgen')`` to register
      the ``add_assetgen_manifest`` configuration directive.
    """
    
    config.add_directive('add_assetgen_manifest', add_assetgen_manifest)


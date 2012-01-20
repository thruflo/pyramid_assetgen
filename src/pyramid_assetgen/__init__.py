#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides an ``add_assetgen_manifest`` `configuration directive`_ and 
  ``AssetGenRequestMixin`` `custom request factory`_ mixin class that can be
  used to integrate `Assetgen`_ with a `Pyramid`_ application.
  
  Configure your `Pyramid`_ app (e.g.: in your main / WSGI app factory
  function)::
  
      from pyramid.request import Request
      class MyRequest(AssetGenRequestMixin, Request): pass
      config.set_request_factory(MyRequest)
      config.add_directive('add_assetgen_manifest', add_assetgen_manifest)
  
  (Note that the ``AssetGenRequestMixin`` argument must come before ``Request``
  in your request factory class definition).
  
  Expose the directory your assetgen'd static files are in as per normal using
  ``add_static_view`` and then register an assetgen manifest for the directory
  you've exposed by calling ``add_assetgen_manifest`` with the same path or
  pyramid asset specification you passed to ``add_static_view``, e.g., assuming
  you have a manifest file at ``'mypkg:static/assets.json``::
  
      config.add_static_view('static', 'mypkg:static')
      config.add_assetgen_manifest('mypkg:static')
  
  If your manifest file is somewhere else, use the ``manifest`` keyword argument
  to specify where it is, e.g.::
  
      config.add_assetgen_manifest('mypkg:static', manifest='/foo/bar.json')
  
  Once configured, you can use ``request.static_path(path, **kw)`` and
  ``request.static_url(path, **kw)`` as normal, e.g.::
  
      request.static_url('mypkg:static/base.js')
  
  Under the hood, ``static_url`` will now check the path to the static file
  you're serving and, if it's in a directory that you've exposed with an
  assetgen manifest, will look in the manifest file for a key that matches
  the path (relative to the directory) and, if found, will expand it.
  
  So, for example, if you have registered a manifest containing::
  
      {'foo.js': 'foo-fdsf465ds4f567ds4ds5674567f4s7.js'}
  
  Calling::
  
      request.static_url('mypkg:static/foo.js')
  
  Will return::
  
      '/static/foo-fdsf465ds4f567ds4ds5674567f4s7.js'
  
  _`assetgen`: http://pypi.python.org/pypi/assetgen
  _`configuration directive`: http://readthedocs.org/docs/pyramid/en/latest/narr/extconfig.html
  _`custom request factory`: http://readthedocs.org/docs/pyramid/en/latest/narr/hooks.html#changing-the-request-factory
  _`pyramid`: http://readthedocs.org/docs/pyramid
"""

__all__ = [
    'IAssetGenManifest',
    'AssetGenManifest',
    'AssetGenRequestMixin',
    'add_assetgen_manifest',
]

import json
import logging

from os.path import exists as path_exists

try: # pragma: no coverage
    import urlparse
except ImportError: # pragma: no coverage
    from urllib import parse as urlparse

from zope.interface import Interface, implements

from pyramid.asset import resolve_asset_spec
from pyramid.decorator import reify
from pyramid.path import AssetResolver
from pyramid import request

def _resolve_abspath(spec, resolve_=resolve_asset_spec, Resolver_=AssetResolver):
    """Resolve an asset spec to an absolute path."""
    
    pname, filepath = resolve_(spec)
    return Resolver_(pname).resolve(filepath).abspath()


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
          >>> manifest.expand('spec/base.js') == 'spec/base-1234.js'
          True
          >>> manifest.expand('not/in/manifest.js') == 'not/in/manifest.js'
          True
      
      Note that if you don't provide a valid file path, it will complain, (which
      allows us to throw an error at compile time, rather than when a request
      happens to come in)::
      
          >>> manifest = AssetGenManifest('spec', None)
          Traceback (most recent call last):
          ...
          ValueError: You must provide a manifest file.
          >>> manifest = AssetGenManifest('spec', '/not/a/valid/path')
          Traceback (most recent call last):
          ...
          IOError: File does not exist: `/not/a/valid/path`.
      
      Teardown::
      
          >>> os.unlink(f.name)
      
      _`Assetgen`: http://pypi.python.org/pypi/assetgen
    """
    
    implements(IAssetGenManifest)
    
    def __init__(self, directory, manifest_file, strict=True):
        if not directory.endswith('/'):
            directory += '/'
        self._directory = directory
        self._manifest_file = manifest_file
        if strict:
            if not self._manifest_file:
                raise ValueError('You must provide a manifest file.')
            elif not path_exists(self._manifest_file):
                msg = 'File does not exist: `{0}`.'.format(self._manifest_file)
                raise IOError(msg)
    
    @reify
    def _data(self):
        sock = open(self._manifest_file, 'rb')
        data = json.loads(sock.read().decode('UTF-8'))
        sock.close()
        return self._compress(data)
    
    def _compress(self, data):
        """We can safely remove all keys that refer to themselves::
          
              >>> data = {'a': 'a', 'b': 'c'}
              >>> manifest = AssetGenManifest('spec', None, strict=False)
              >>> manifest._data = manifest._compress(data)
              >>> manifest._data
              {'b': 'c'}
              >>> manifest.expand('spec/a')
              'spec/a'
              >>> manifest.expand('spec/b')
              'spec/c'
          
        """
        
        compressed = {}
        for k, v in data.items():
            if not k == v:
               compressed[k] = v
        return compressed
    
    def expand(self, path):
        if not path.startswith(self._directory):
            return path
        path = self._directory.join(path.split(self._directory)[1:])
        path = self._data.get(path, path)
        return urlparse.urljoin(self._directory, path)
    

class AssetGenRequestMixin(object):
    """Mixin to a request factory that effectively patches ``self.static_url``
      with an equivalent that first checks to see if the ``path`` its called
      with resolves to a static directory that has had an ``IAssetGenManifest``
      utility registered for it.  If so, the path is expanded by that utility
      before being passed to the original ``static_url`` function.
      
      **Note**: this class must be mixed in as the *first* superclass, e.g.::
      
          class MyRequest(AssetGenRequestMixin, Request):
              pass
          
      
    """
    
    def _assetgen_expand_path(self, path):
        path = _resolve_abspath(path)
        for _, manifest in self.registry.getUtilitiesFor(IAssetGenManifest):
            path = manifest.expand(path)
        return path
    
    def static_url(self, path, **kw):
        path = self._assetgen_expand_path(path)
        return super(AssetGenRequestMixin, self).static_url(path, **kw)
    


def add_assetgen_manifest(config, path, manifest=None, default='assets.json'):
    """Register an IAssetGenManifest utility against ``path``."""
    
    # Generate an unambiguous absolute path from the ``path`` provided, which,
    # just as with the built in ``add_static_view`` directive can be an absolute
    # or relative path, or an asset specification.
    static_directory = _resolve_abspath(config._make_spec(path))
    if not static_directory.endswith('/'):
        static_directory += '/'
    
    # Get the abspath to the manifest file to associate with static directory.
    if manifest is None:
        manifest_file = urlparse.urljoin(static_directory, default)
    else:
        manifest_file = _resolve_abspath(config._make_spec(manifest))
    
    # Register the ``AssetGenManifest`` instance against ``static_directory``.
    manifest = AssetGenManifest(static_directory, manifest_file)
    register = config.registry.registerUtility
    register(manifest, IAssetGenManifest, name=static_directory)


def includeme(config):
    """Allow developers to use ``config.include('pyramid_assetgen')`` to register
      the ``add_assetgen_manifest`` configuration directive.
    """
    
    config.add_directive('add_assetgen_manifest', add_assetgen_manifest)


#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import hashlib
import logging
import re

try: # py2
    from urllib2 import urlopen
except ImportError: # py3
    from urllib.request import urlopen

from os.path import basename
from os.path import exists as path_exists
from os.path import join as join_path

try: # pragma: no coverage
    import urlparse
except ImportError: # pragma: no coverage
    from urllib import parse as urlparse

from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import implementer

from pyramid.asset import resolve_asset_spec
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPNotFound
from pyramid.path import AssetResolver
from pyramid.renderers import render as render_template
from pyramid.request import Request
from pyramid.security import NO_PERMISSION_REQUIRED as PUBLIC

valid_digest = re.compile(r'^[a-z0-9]{56}$', re.U)

def compress_data(data):
    """Remove all keys from ``data`` that refer to themselves::
      
          >>> data = {'a': 'a', 'b': 'c'}
          >>> compress_data(data)
          {'b': 'c'}
      
    """
    
    compressed = {}
    for k, v in data.items():
        if not k == v:
           compressed[k] = v
    return compressed

def is_a_url(path_or_url):
    """Return whether ``path_or_url`` is a URL.  XXX Currently a tad naive.
      
          >>> is_a_url('http://google.com')
          True
          >>> is_a_url('//cdn.com/path.js')
          True
          >>> is_a_url('pkg:dir/path.js')
          False
      
    """
    
    return '://' in path_or_url or path_or_url.startswith('//')

def open_resource(path_or_url, is_url=None, open_url=None, file_exists=None):
    """Open a resource, no matter whether it's a URL or a local file."""
    
    # Test jig.
    if is_url is None:
        is_url = is_a_url
    if open_url is None:
        open_url = urlopen
    if file_exists is None:
        file_exists = path_exists
    
    # If it's a URL then use ``open_url``.
    if is_url(path_or_url):
        try:
            sock = open_url(path_or_url)
        except IOError:
            pass
        else:
            if sock.code == 200:
                return sock
    # Otherwise treat it as a file path.
    if file_exists(path_or_url):
        return open(path_or_url)

def resolve_abspath(spec, resolve=None, Resolver=None):
    """Resolve an asset spec to an absolute path."""
    
    # Test jig.
    if resolve is None:
        resolve = resolve_asset_spec
    if Resolver is None:
        Resolver = AssetResolver
    
    pname, filepath = resolve(spec)
    return Resolver(pname).resolve(filepath).abspath()

def sha224_digest(s):
    return hashlib.sha224(s).hexdigest()


class IAssetGenManifest(Interface):
    """Marker interface."""

@implementer(IAssetGenManifest)
class AssetGenManifest(object):
    """Utility that expands static url paths using the data in an assetgen
      manifest file.
    """
    
    def __init__(self, manifest, asset_path, serving_path=None, **kwargs):
        """Store references to the paths and read in the manifest data."""
        
        # Compose.
        open_ = kwargs.get('_open', open_resource)
        compress = kwargs.get('compress', compress_data)
        to_digest = kwargs.get('to_digest', sha224_digest)
        
        # ``self.manifest_file`` is a url or local file path to an assetgen
        # manifest file.
        self.manifest_file = manifest
        
        # Make sure the manifest file exists.
        sock = open_(self.manifest_file)
        if not sock:
            msg = 'Does not exist: `{0}`.'.format(self.manifest_file)
            raise IOError(msg)
        
        # Read in the data from it.
        data = json.loads(sock.read().decode('UTF-8'))
        sock.close()
        self.data = compress(data)
        
        # ``self.asset_path`` is the root directory / asset spec provided
        # to ``request.static_url()``, e.g.: the ``pkg:dir`` in 
        # ``request.static_url('pkg:dir/foo.js')``.
        self.asset_path = asset_path
        
        # ``self.serving_path`` is the root directory / asset spec or
        # url path returned from ``self.expand()``, e.g.:: with a ``serving_path``
        # of ``http://myassets.com``, a call to ``self.expand('foo.js')`` might
        # return ``http://myassets.com/foo.js``.
        if serving_path is None:
            serving_path = self.asset_path
        self.serving_path = serving_path
        
        # Set the digest.
        self.digest = to_digest(json.dumps(self.__json__()))
    
    def __json__(self):
        """JSON representation (can be passed to a template and thus through to
          ``./coffee/assetgen.coffee``).
        """
        
        return {
            'data': self.data, 
            'asset_path': self.asset_path,
            'serving_path': self.serving_path
        }
    
    def expand(self, path):
        """Expand a path using the manifest data."""
        
        if not path.startswith(self.asset_path):
            return path
        path = self.asset_path.join(path.split(self.asset_path)[1:])
        return self.serving_path + self.data.get(path, path)
    


def get_assetgen_manifest_script_tag(request, asset_path, **kwargs):
    """Render a script tag that loads the manifest data for the asset_path."""
    
    # Compose.
    render = kwargs.get('render', render_template)
    spec = kwargs.get('spec', u'pyramid_assetgen:templates/script_tag.mako')
    
    # Lookup.
    manifest = request.assetgen_manifest(asset_path)
    if '://' in manifest.manifest_file:
        url = manifest.manifest_file
    else:
        filename = basename(manifest.manifest_file)
        url = join_path(manifest.serving_path, filename)
    
    # Render the <script /> tag.
    tmpl_vars = {
        'asset_path': manifest.asset_path,
        'serving_path': manifest.serving_path,
        'url': u'{0}?v={1}'.format(url, manifest.digest),
    }
    return render(spec, tmpl_vars, request=request)


def get_static_url(request, is_url=None, request_cls=None):
    """Returns a manifest aware ``static_url`` function that can be used as a
      ``request.static_url``.
    """
    
    # Test jig.
    if is_url is None:
        is_url = is_a_url
    if request_cls is None:
        request_cls = Request
    
    # Cache the original static url method.
    original_static_url = request_cls(request.environ).static_url
    
    def static_url(path, **kw):
        original_path = path
        for _, manifest in request.registry.getUtilitiesFor(IAssetGenManifest):
            path = manifest.expand(original_path)
            if path != original_path:
                break
        if is_url(path):
            return path
        return original_static_url(path, **kw)
    
    return static_url

def get_assetgen_manifest(request):
    """Returns a ``assetgen_manifest`` function to get a registered ``IAssetGenManifest``
      instance by asset_path.
    """
    
    def assetgen_manifest(asset_path, as_json=False, interface_cls=None, dumps=None):
        """Get the manifest data registered for ``assets``."""
        
        # Test jig.
        if interface_cls is None:
            interface_cls = IAssetGenManifest
        if dumps is None:
            dumps = json.dumps
        
        if not asset_path.endswith('/'):
            asset_path += '/'
        manifest = request.registry.getUtility(interface_cls, name=asset_path)
        if as_json:
            return json.dumps(manifest.__json__())
        return manifest
    
    return assetgen_manifest

def get_assetgen_hash(request):
    """Returns a function that returns the sha224 hash of a registered
      ``IAssetGenManifest`` identified by asset_path.
    """
    
    def assetgen_hash(asset_path, get_manifest=None):
        """Get the hash of the manifest data registered for ``assets``."""
        
        # Compose
        if get_manifest is None:
            get_manifest = get_assetgen_manifest(request)
        
        manifest = get_manifest(asset_path)
        return manifest.digest
    
    return assetgen_hash

def add_assetgen_manifest(config, asset_path, manifest_file=None, default='assets.json',
        serving_path=None, is_url=None, resolve=None, join_url=None):
    """Register an IAssetGenManifest utility."""
    
    # Test jig.
    if is_url is None:
        is_url = is_a_url
    if resolve is None:
        resolve = resolve_abspath
    if join_url is None:
        join_url = urlparse.urljoin
    
    # Make sure the directory paths end with a `/`.
    if not asset_path.endswith('/'):
        asset_path += '/'
    if serving_path and not serving_path.endswith('/'):
        serving_path += '/'
    
    # Get the absolute path to the manifest file.
    if manifest_file is None:
        abspath = resolve(config._make_spec(asset_path))
        if not abspath.endswith('/'):
            abspath += '/'
        manifest_file = join_url(abspath, default)
    elif not is_url(manifest_file):
        manifest_file = resolve(config._make_spec(manifest_file))
    
    # Register the ``AssetGenManifest`` instance against ``static_directory``.
    manifest = AssetGenManifest(manifest_file, asset_path, serving_path=serving_path)
    config.registry.registerUtility(manifest, IAssetGenManifest, name=asset_path)
    
    # And register it against the hash, so we can look it up from its
    # manifest.js view.
    digest = manifest.digest
    config.registry.registerUtility(manifest, IAssetGenManifest, name=digest)  

def includeme(config):
    """Allow developers to use ``config.include('pyramid_assetgen')`` to register
      the ``add_assetgen_manifest`` configuration directive.
    """
    
    # Register directive.
    config.add_directive('add_assetgen_manifest', add_assetgen_manifest)
    
    # Override ``request.static_url``.
    config.set_request_property(get_static_url, 'static_url', reify=True)
    config.set_request_property(get_assetgen_manifest, 'assetgen_manifest', reify=True)
    config.set_request_property(get_assetgen_hash, 'assetgen_hash', reify=True)
    
    # Provide ``request.assetgen_manifest_script_tag(asset_path)``.
    config.add_request_method(get_assetgen_manifest_script_tag,
            'assetgen_manifest_script_tag')
    
    # If ``assetgen.assets_path`` is provided in the config, register a 
    # static view with an assetgen manifest.
    settings = config.registry.settings
    if settings.has_key('assetgen.assets_path'):
        assets_path = settings['assetgen.assets_path']
        serving_path = settings.get('assetgen.serving_path', assets_path)
        manifest_file=settings.get('assetgen.manifest_file', None)
        config.add_static_view('assets', assets_path)
        config.add_assetgen_manifest(assets_path, serving_path=serving_path, 
                manifest_file=manifest_file)


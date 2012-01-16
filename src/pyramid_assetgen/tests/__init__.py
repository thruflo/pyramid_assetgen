#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Integration tests for :py:mod:`~pyramid_assetgen`."""

import unittest

from pyramid import testing

class TestConfiguration(unittest.TestCase):
    def setUp(self):
        import pyramid_assetgen
        class Request(testing.DummyRequest, pyramid_assetgen.AssetGenRequestFactoryMixin):
            pass
        
        self.config = testing.setUp(request=Request())
        self.config.include('pyramid_assetgen')
    
    def tearDown(self):
        testing.tearDown()
    
    def test_directive_available(self):
        """The ``config.add_assetgen_manifest`` directive is available."""
        
        has_directive = callable(self.config.add_assetgen_manifest)
        self.assertTrue(has_directive)
    
    def test_request_has_assetgen_methods(self):
        """``request`` has ``assetgen_url`` and ``assetgen_path`` methods."""
        
        from pyramid.threadlocal import get_current_request
        request = get_current_request()
        
        self.assertTrue(callable(request.assetgen_url))
        self.assertTrue(callable(request.assetgen_path))
    

class TestUsage(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        try: # pragma: no coverage
            import urlparse
        except ImportError: # pragma: no coverage
            from urllib import parse as urlparse
        import pyramid_assetgen
        class Request(testing.DummyRequest, pyramid_assetgen.AssetGenRequestFactoryMixin):
            pass
        
        self.config = testing.setUp(request=Request())
        self.config.include('pyramid_assetgen')
        self.f = tempfile.NamedTemporaryFile(delete=False)
        self.f.write('{"base.js": "base-1234.js"}'.encode())
        self.f.close()
        dirname = os.path.dirname(self.f.name)
        filename = os.path.split(self.f.name)[-1]
        self.config.add_static_view('foo', dirname)
        self.config.add_assetgen_manifest('foo', dirname, manifest_path=filename)
    
    def tearDown(self):
        import os
        testing.tearDown()
        os.unlink(self.f.name)
    
    def test_assetgen_url(self):
        """Test expanding an assetgen url that is in the manifest."""
        
        from pyramid.threadlocal import get_current_request
        request = get_current_request()
        
        url = request.assetgen_url('foo', 'base.js')
        self.assertTrue(url == 'http://example.com/foo/base-1234.js')
    
    def test_assetgen_url_passthrough(self):
        """Test expanding an assetgen url that isn't in the manifest."""
        
        from pyramid.threadlocal import get_current_request
        request = get_current_request()
        
        url = request.assetgen_url('foo', 'blah.js')
        self.assertTrue(url == 'http://example.com/foo/blah.js')
    
    def test_assetgen_path(self):
        """Test expanding an assetgen path."""
        
        from pyramid.threadlocal import get_current_request
        request = get_current_request()
        
        path = request.assetgen_path('foo', 'base.js')
        self.assertTrue(path == '/foo/base-1234.js')
    
    def test_absolute_manifest_path(self):
        """Test using an absolute manifest path."""
        
        self.config.add_static_view('bar', '/bar')
        self.config.add_assetgen_manifest('bar', '/bar', manifest_path=self.f.name)
        
        from pyramid.threadlocal import get_current_request
        request = get_current_request()
        
        path = request.assetgen_path('bar', 'base.js')
        self.assertTrue(path == '/bar/base-1234.js')
    
    def test_unregistered_manifest_path(self):
        """Test that using a manifest name that hasn't been registered errors."""
        
        from pyramid.threadlocal import get_current_request
        request = get_current_request()
        
        from zope.interface.interfaces import ComponentLookupError
        self.assertRaises(ComponentLookupError, request.assetgen_path, 'baz', 'base.js')
    


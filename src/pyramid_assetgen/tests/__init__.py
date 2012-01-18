#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Integration tests for :py:mod:`~pyramid_assetgen`."""

import unittest

from pyramid import testing

class TestConfiguration(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_assetgen')
    
    def tearDown(self):
        testing.tearDown()
    
    def test_directive_available(self):
        """The ``config.add_assetgen_manifest`` directive is available."""
        
        self.assertTrue(callable(self.config.add_assetgen_manifest))
    

class TestUsage(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        from pyramid_assetgen import AssetGenRequestMixin
        class MyRequest(AssetGenRequestMixin, testing.DummyRequest):
            pass
        
        self.config = testing.setUp(request=MyRequest())
        self.config.include('pyramid_assetgen')
        self.f = tempfile.NamedTemporaryFile(delete=False)
        self.f.write('{"base.js": "base-1234.js"}'.encode())
        self.f.close()
        self.dirname = os.path.dirname(self.f.name)
    
    def tearDown(self):
        import os
        testing.tearDown()
        os.unlink(self.f.name)
    
    def test_expand_static_url(self):
        """Test expanding a static url that is in the manifest."""
        
        from pyramid.threadlocal import get_current_request
        request = get_current_request()
        
        self.config.add_static_view('static', '/foo')
        self.config.add_assetgen_manifest('/foo', manifest=self.f.name)
        
        url = request.static_url('/foo/base.js')
        self.assertTrue(url == 'http://example.com/static/base-1234.js')
    
    def test_static_url_passthrough(self):
        """Test a static url that isn't in the manifest."""
        
        from pyramid.threadlocal import get_current_request
        request = get_current_request()
        
        self.config.add_static_view('static', '/foo')
        self.config.add_assetgen_manifest('/foo', manifest=self.f.name)
        
        url = request.static_url('/foo/foo.js')
        self.assertTrue(url == 'http://example.com/static/foo.js')
    
    def test_static_path(self):
        """Test expanding an static path."""
        
        from pyramid.threadlocal import get_current_request
        request = get_current_request()
        
        self.config.add_static_view('static', '/foo')
        self.config.add_assetgen_manifest('/foo', manifest=self.f.name)
        
        url = request.static_path('/foo/base.js')
        self.assertTrue(url == '/static/base-1234.js')
    
    def test_relative_manifest_path(self):
        """Test using a relative manifest path."""
        
        from pyramid.threadlocal import get_current_request
        request = get_current_request()
        
        import os
        filename = os.path.split(self.f.name)[1]
        
        self.config.add_static_view('static', self.dirname)
        self.config.add_assetgen_manifest(self.dirname, default=filename)
        
        path = request.static_path(self.dirname + '/' + 'base.js')
        self.assertTrue(path == '/static/base-1234.js')
    


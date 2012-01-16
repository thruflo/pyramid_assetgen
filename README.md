# Pyramid Assetgen

[pyramid_assetgen][] allows you to integrate [Assetgen][] with a [Pyramid][]
project, using an `add_assetgen_manifest` configuration directive and 
`AssetGenRequestFactoryMixin`.

Using it allows you to code in languages (like CoffeeScript and SASS) that
compile to JavaScript and CSS, swapping between a refresh-the-page-to-see-changes
development environment and an optimal HTTP caching production setup -- without
ever having to change any of the code in your [Pyramid][] application.

## Configuration

If we presume `config` is a `pyramid.config.Configurator` instance, (perhaps
available in your main / WSGI app factory function), we can add the directive
either using:

    from pyramid_assetgen import add_assetgen_manifest
    config.add_directive('add_assetgen_manifest', add_assetgen_manifest)

Or more simply:

    config.include('pyramid_assetgen')

In addition, you'll need to extend the default request factory using, e.g.:
    
    from pyramid.request import Request
    from pyramid_assetgen import AssetGenRequestFactoryMixin
    
    class MyRequest(Request, AssetGenRequestFactoryMixin):
        pass
    
    config.set_request_factory(MyRequest)

## Usage

With that configuration, when you expose a static directory using 
`add_static_view`, you can now associate an Assetgen manifest with it, using
something like:

    config.add_static_view('static', 'mypkg:var/static')
    config.add_assetgen_manifest('assets', 'mypkg:var/static', 
                                 manifest_path='assets.json')

You can then use `request.assetgen_url` and `request.assetgen_path` to generate
urls to your static files using *relative paths* that are referenced against
the paths in the manifest file before being expanded by Pyramid's `static_url`
machinery.

For example, if there was a manifest file at `mypkg:var/static/assets.json` with
a key: value pair of `"base.js": "base-25675235267526785784536.js"` then (with
the config from above) calling:

    request.assetgen_path('assets', 'base.js')

Would return `/static/base-25675235267526785784536.js`.

## Tests

I've run the tests under Python2.6 and Python3.2 using, e.g.:

    $ ../bin/nosetests --cover-package=src/pyramid_assetgen --cover-erase --with-coverage --with-doctest
    .........
    Name                                          Stmts   Miss  Cover   Missing
    ---------------------------------------------------------------------------
    src/pyramid_assetgen/__init__                    53      0   100%   
    src/pyramid_assetgen/tests/__init__              68      0   100%   
    ---------------------------------------------------------------------------
    TOTAL                                           121      0   100%   
    ----------------------------------------------------------------------
    Ran 9 tests in 0.551s
    
    OK

[assetgen]: http://github.com/tav/assetgen
[pyramid]: http://pypi.python.org/pypi/pyramid
[pyramid_assetgen]: http://github.com/thruflo/pyramid_assetgen
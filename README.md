# Pyramid Assetgen

[pyramid_assetgen][] allows you to integrate [Assetgen][] with a [Pyramid][]
project.

## tl;dr

Include the package, set a custom request factory (using `AssetGenRequestMixin`
as the *first* class you inherit from):

    class MyRequest(AssetGenRequestMixin, Request): pass
    config.set_request_factory(MyRequest)
    config.include('pyramid_assetgen')

Use the `add_assetgen_manifest` configuration directive to associate an Assetgen
manifest file with a static directory:

    config.add_static_view('static', 'mypkg:static')
    # defaults to look for an assets.json file in the same directory
    config.add_assetgen_manifest('mypkg:static')

And then just use Pyramid's built-in `request.static_url(path, **kw)` as normal.

## Rationale

[Assetgen]() is a static file build tool.  When using in production, you can
enable its hashing mode to output files with a hash in the filename.  This means
that when you change a file (for example, maybe updating your site's stylesheet)
its name will change.

On the one hand this is excellent news, as it allows you to implement an optimal
HTTP caching strategy (telling browser clients to cache your static files
forever).  On the other, it means you need to update your templates and / or view
code to serve the right url to resolves to the hashed filename.  This is
relatively easy when you're using [Pyramid]() as you're already using a dynamic
function to generate your static urls: `request.static_url`.

This package, [pyramid_assetgen]() extends the Pyramid machinery to automatically
update your static urls so that they resolve to the correct hashed file names.
You can use it to integrate [Assetgen]() with your [Pyramid]() application without
having to change any of your templates or view code or learn any new APIs.

## Workflow

If you run a Pyramid application configured to look for a manifest file, then the
file needs to be there, otherwise the application will throw an exception (at
configuration time).  You should thus build your manifest file using something
like:

    assetgen etc/assetgen.yaml --force

Before you run your Pyramid app with something like:

    pserve etc/production.ini

If running in development mode using [paste.reloader], e.g.:

    pserve etc/development.ini --reload

You could add your manifest file to the list of files the reloader should watch
using, e.g.:

    from paste.reloader import add_file_callback
    def watch_manifest_files():
        return ['/var/www/static/assets.json',]
    add_file_callback(watch_manifest_files)

However, you're unlikely to need this, as you shouldn't auto-reload in production
and in development mode you shouldn't hash your assetgen files.

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
    from pyramid_assetgen import AssetGenRequestMixin
    
    class MyRequest(AssetGenRequestMixin, Request):
        pass
    
    config.set_request_factory(MyRequest)

(Note that the `AssetGenRequestMixin` argument must come **before** `Request` in
your request factory class definition.  Otherwise the `static_url` method will
not be overridden).

## Usage

With that configuration, when you expose a static directory using 
`config.add_static_view`, you can now associate an Assetgen manifest with it:

    config.add_static_view('static', 'mypkg:static')
    config.add_assetgen_manifest('mypkg:static')

This will look for a manifest file in `mypkg:static/assets.json`.  If the
file is somewhere else use:

    config.add_assetgen_manifest('mypkg:static', manifest='/foo/bar.json')

You can then use `request.static_path` and `request.static_url` as normal.
So, for example, if you have registered a manifest containing:

    {'foo.js': 'foo-fdsf465ds4f567ds4ds5674567f4s7.js'}

Calling:

    request.static_path('mypkg:static/foo.js')

Will return:

    '/static/foo-fdsf465ds4f567ds4ds5674567f4s7.js'

## Tests

I've run the tests under Python2.6 and Python3.2 using, e.g.:

    $ ../bin/nosetests --cover-package=src/pyramid_assetgen --cover-erase --with-coverage --with-doctest
    .......
    Name                                  Stmts   Miss  Cover   Missing
    -------------------------------------------------------------------
    src/pyramid_assetgen/__init__            59      0   100%   
    src/pyramid_assetgen/tests/__init__      58      0   100%   
    -------------------------------------------------------------------
    TOTAL                                   117      0   100%   
    ----------------------------------------------------------------------
    Ran 7 tests in 0.552s
    
    OK

[assetgen]: http://github.com/tav/assetgen
[pyramid]: http://pypi.python.org/pypi/pyramid
[pyramid_assetgen]: http://github.com/thruflo/pyramid_assetgen
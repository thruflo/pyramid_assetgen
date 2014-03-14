
## 0.5

Provide framework machinery to embed a `manifest.js` script tag, rather
than writing the manifest's json data into the page template, thus allowing
the request and data to be http cached.

## 0.4.3

Include `.coffee` files in source distribution.

## 0.4.2

Test rendering README.md on PYPI.

## 0.4.1

Provide `request.assetgen_hash(asset_path)` path to get the hash of an assetgen
manifest.

## 0.4

Refactor to support external urls and implicitly register assets when the default
configuration is provided.

Added coffeescript lib with methods to accept a JSON representation of a
registered assetgen manifest and generate static urls on the client side.

## 0.3

Fixed major bug causing the `add_static_view` integration to break when the
static view was configured with an asset specification.

## 0.2.2

Added a strict mode (enabled by default) to the ``AssetGenManifest`` so that
if the manifest file doesn't exist, it will throw an error at configure time,
rather than when the first request happens to come in.

## 0.2.1

Minor tweak to the docs.

## 0.2

Completely changed the api.  Instead of using:

    request.assetgen_url(name, relative_path)

The integration is now much tighter with Pyramid, using the built in:

    request.static_url(path_or_asset_specification, **kw)

And a simpler configuration directive:

    # use this: no name
    config.add_static_view('static', 'mypkg:static')
    config.add_assetgen_manifest('mypkg:static')
    
    # not this: with name
    config.add_static_view('static', 'mypkg:static')
    config.add_assetgen_manifest(name, 'mypkg:static')

To achieve this, the `AssetGenRequestMixin` now needs to be inherited as the
**first** superclass to your custom request factory, i.e.:

    # use this
    class MyRequest(AssetGenRequestMixin, Request): pass
    
    # not this
    class MyRequest(Request, AssetGenRequestMixin): pass


## 0.1

Initial version.
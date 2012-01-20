
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
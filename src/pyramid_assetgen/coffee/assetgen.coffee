# Use `assetgen.static_url()` to unpack static paths into expanded urls using the
# pyramid_assetgen machinery, e.g.:
# 
#     assetgen.add_manifest
#         asset_path: 'pkg:assets'
#         serving_path: '/static'
#         data:
#             'foo.js': 'foo-5678565f87ds5f68758.js'
#     assetgen.static_url 'pkg:assets/foo.js'
#     => '/static/foo-5678565f87ds5f68758.js'
# 
# XXX: this needs to have tests and be integrated into `pyramid_assetgen`.
define 'assetgen', (exports, root) ->
  
  if not String::startsWith?
    String::startsWith = (s) -> @indexOf(s) is 0
  if not String::endsWith?
    String::endsWith = (s) -> -1 isnt @indexOf s, @length - s.length
  
  _manifests = {}
  
  add_manifest = (manifest) -> 
    path = manifest['asset_path']
    if not path.endsWith('/') then path + '/' else path
    _manifests[path] = manifest
  
  static_url = (path) ->
    for k, v of _manifests
      if path.startsWith k 
        parts = path.split k
        relative_path = parts[1...parts.length].join(k)
        if relative_path of v['data']
          relative_path = v['data'][relative_path]
        return v['serving_path'] + relative_path
    path
  
  exports.add_manifest = add_manifest
  exports.static_url = static_url
  exports.static_path = static_url


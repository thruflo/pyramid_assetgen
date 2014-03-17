<script type="text/javascript">
  $.ajax({
      async: false,
      dataType: 'json',
      success: function (data) {
        assetgen.add_manifest({
            'data': data,
            'asset_path': '${asset_path}',
            'serving_path': '${serving_path}'
        });
      },
      type: 'GET',
      url: '${url}'
  });
</script>
# scratch/test_drawio_format.py
import urllib.parse
import zlib
import base64

xml_model = """<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="1100" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    <mxCell id="2" value="Test Node" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
      <mxGeometry x="100" y="100" width="120" height="60" as="geometry" />
    </mxCell>
  </root>
</mxGraphModel>"""

# Draw.io standard encoding:
# 1. URL encode (RFC 3986)
# 2. Deflate (raw deflate without zlib header: wbits = -15)
# 3. Base64 encode
quoted = urllib.parse.quote(xml_model, safe='~()*!.\'')
deflated = zlib.compress(quoted.encode('utf-8'), 9)[2:-4] # strip zlib 2-byte header and 4-byte checksum
encoded = base64.b64encode(deflated).decode('utf-8')

# Verify decoding
raw = zlib.decompress(base64.b64decode(encoded), -15).decode('utf-8')
unquoted = urllib.parse.unquote(raw)
assert unquoted == xml_model
print("Encoding/decoding test passed! Encoded length:", len(encoded))

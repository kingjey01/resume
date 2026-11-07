import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'dart:typed_data';

/// Sur Flutter Web, `record` renvoie une URL `blob:` après l'arrêt.
/// On récupère les octets réels via `fetch(blobUrl).arrayBuffer()`.
@JS('fetch')
external JSPromise<JSObject> _fetch(JSString url);

Future<Uint8List?> readBlobBytes(String url) async {
  try {
    final response = await _fetch(url.toJS).toDart;
    final arrayBuffer = await response
        .callMethod<JSPromise<JSArrayBuffer>>('arrayBuffer'.toJS)
        .toDart;
    return arrayBuffer.toDart.asUint8List();
  } catch (_) {
    return null;
  }
}

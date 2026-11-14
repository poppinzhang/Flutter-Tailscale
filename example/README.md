# Minimal consumer

Use a local path dependency while developing both projects. Released consumers
should pin a verified source revision or an immutable source snapshot.

```yaml
dependencies:
  flutter_tailscale:
    path: ../Flutter-Tailscale
```

Build and bundle the native runtime as described in
[the implementation record](../docs/08-implementation.md). The host supplies an
application-private state directory and opens login URLs using its normal browser
integration. Never log, copy into diagnostics, or persist those URLs.

```dart
import 'package:flutter_tailscale/flutter_tailscale.dart';
import 'package:flutter_tailscale/grpc.dart';

final node = await TailscaleNode.open(
  stateDirectory: privateStateDirectory,
  hostname: 'my-flutter-app',
);

// Invoke from the user's explicit login action. First login does not call start.
var status = await node.login();
// If authUrl is not ready yet, use bounded status polling while login is active.
status = await node.status();
if (status.authUrl != null) {
  await openSystemBrowser(status.authUrl!);
}

// Only after a registered status: these are network candidates, not app peers.
final candidates = await node.peers();
final selected = candidates.first.ref;
final channel = TailscaleChannel(node, selected, port: yourServicePort);
// Use your generated gRPC client with channel and verify the application's ID.

// Publish only to sources explicitly authorized by the user/application.
final service = await node.publishTcp(
  port: yourServicePort,
  allowedPeers: {selected},
  onConnection: (connection) {
    serveGrpcConnection(yourGrpcServer, connection);
  },
);

await service.updatePolicy({}); // Revoke all sources, including active streams.
await service.close();
await channel.terminate();
await node.dispose(); // Preserve identity for the host's next explicit restore.
```

On later application startup, restore only if the host remembers that the user
enabled the feature. `await node.start()` returns `loginRequired` if there is no
restorable login. `logout()` disables restoration and revokes the application
node's connections without deleting host-owned application data.

The package performs no automatic app discovery, media synchronization, address
scanning, or retry/replay of business requests. A host must separately verify its
service and device identity before trusting any candidate.

# App driving options

How to launch and drive a project's app for verification, by project type. Use what the project already has first: its documented dev command, end-to-end suite, and test fixtures. Install a new driver only when the user has authorized dependency changes; otherwise report the path as blocked and name the missing tool.

## Every project type

- **Launch:** the documented dev or start command, with a throwaway data directory, port, and profile. Run long-lived servers in the background and record their process IDs.
- **Ready:** wait on a signal (a health URL answering, a log line, a prompt), not a fixed sleep.
- **Doctor:** before the first drive and after anything surprising, confirm the instance is the one you started, on the current revision, and healthy.
- **Cleanup:** stop the processes you started by ID, never by name. Delete scratch data, keep evidence.
- **Sandbox:** binding a port, using the network, or opening a browser may need approval. Ask for it through the host's normal flow; if it is denied, the path is blocked.

## Web apps

- Prefer the project's Playwright, Cypress, or WebdriverIO setup. Run the specs for the changed route against the live dev server, or add a short spec when the change warrants one.
- Otherwise script a headless browser with Playwright (Python or Node) or use a browser tool the host provides. Use accessible names, labels, and routes as handles, not coordinates.
- Evidence: a screenshot with the app identity visible, an accessibility snapshot or relevant DOM text, and console errors.
- `curl` proves server-rendered HTML or a redirect, not client behavior.

## CLIs and TUIs

- Build or install once, then run the real binary or entry point in a temporary working directory with an isolated config and home where the tool allows.
- Evidence: the exact command, stdout, stderr, and exit code; for files it writes, list or diff them.
- For interactive prompts or TUIs, use `expect`, a PTY helper, or `tmux send-keys` and `tmux capture-pane`.

## HTTP and RPC APIs

- Start the server locally and send real requests with `curl`, `httpie`, or the project's client: the changed endpoint, then an error or unauthorized case.
- Evidence: the request (with secrets removed), status, relevant headers, and the response body saved to a file; for writes, a follow-up read or database query.
- For gRPC, use `grpcurl` or the generated client.

## Mobile apps

- iOS: `xcrun simctl` to boot a simulator, install, and launch; `xcrun simctl io booted screenshot` for evidence. macOS only.
- Android: an emulator with `adb install`, `adb shell am start`, and `adb exec-out screencap -p` for evidence.
- Prefer the project's Maestro, Detox, XCUITest, or Espresso flows when present.
- A Linux container usually has no iOS simulator and often no Android emulator; that path is blocked, not verified by unit tests.

## Desktop and Electron

- Electron: Playwright's Electron support or the Chrome DevTools Protocol with a remote debugging port.
- Native desktop: the platform UI automation the project already uses; otherwise report blocked.

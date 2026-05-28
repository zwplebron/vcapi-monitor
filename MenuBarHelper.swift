import Cocoa

// python_pid is passed as first argument
let args = CommandLine.arguments
guard args.count >= 2, let pythonPid = Int32(args[1]) else {
    print("Usage: MenuBarHelper <python_pid>")
    exit(1)
}

let titleFile = "/tmp/deepseek_statusbar_title.txt"

// Only create initial title file if it doesn't already exist
if !FileManager.default.fileExists(atPath: titleFile) {
    try? "¥ --.--".write(toFile: titleFile, atomically: true, encoding: .utf8)
}

// Load custom icon from Resources folder, resize to fit menu bar
var statusIcon: NSImage? = nil
if let resourcePath = Bundle.main.resourcePath {
    let iconPath = resourcePath + "/status_icon.png"
    if FileManager.default.fileExists(atPath: iconPath) {
        if let icon = NSImage(contentsOfFile: iconPath) {
            icon.isTemplate = true
            // 适配状态栏高度（通常 24pt，留 4pt 边距）
            let barThickness = NSStatusBar.system.thickness
            let iconSize = barThickness - 6
            icon.size = NSSize(width: iconSize, height: iconSize)
            statusIcon = icon
        }
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

class HelperDelegate: NSObject, NSApplicationDelegate {
    let statusItem: NSStatusItem
    let pythonPid: Int32
    let icon: NSImage?

    init(statusItem: NSStatusItem, pythonPid: Int32, icon: NSImage?) {
        self.statusItem = statusItem
        self.pythonPid = pythonPid
        self.icon = icon
        super.init()
    }

    @objc func statusItemClicked() {
        guard let event = NSApp.currentEvent else { return }

        if event.type == .rightMouseUp {
            let menu = NSMenu()

            let settingsItem = NSMenuItem(title: "设置", action: #selector(HelperDelegate.openSettings), keyEquivalent: "")
            settingsItem.target = self
            menu.addItem(settingsItem)

            menu.addItem(NSMenuItem.separator())

            let quitItem = NSMenuItem(title: "退出", action: #selector(HelperDelegate.quitApp), keyEquivalent: "q")
            quitItem.target = self
            menu.addItem(quitItem)

            NSMenu.popUpContextMenu(menu, with: event, for: statusItem.button!)
        } else {
            kill(pythonPid, SIGUSR1)
        }
    }

    @objc func openSettings() {
        let settingsFile = "/tmp/deepseek_statusbar_settings.txt"
        try? "1".write(toFile: settingsFile, atomically: true, encoding: .utf8)
        kill(pythonPid, SIGUSR1)
    }

    @objc func quitApp() {
        let quitFile = "/tmp/deepseek_statusbar_quit.txt"
        try? "1".write(toFile: quitFile, atomically: true, encoding: .utf8)
        kill(pythonPid, SIGUSR1)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            NSApp.terminate(nil)
        }
    }

    func updateButton(title: String) {
        guard let button = statusItem.button else { return }
        if title == "▪" && icon != nil {
            button.image = icon
            button.title = ""
        } else {
            button.image = nil
            button.title = title
        }
    }
}

let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

let initialTitle: String
if let text = try? String(contentsOfFile: titleFile, encoding: .utf8) {
    initialTitle = text.trimmingCharacters(in: .whitespacesAndNewlines)
} else {
    initialTitle = "¥ --.--"
}

if let button = statusItem.button {
    if initialTitle == "▪" && statusIcon != nil {
        button.image = statusIcon
        button.title = ""
    } else {
        button.title = initialTitle
    }
}

let delegate = HelperDelegate(statusItem: statusItem, pythonPid: pythonPid, icon: statusIcon)
NSApp.delegate = delegate

if let button = statusItem.button {
    button.target = delegate
    button.action = #selector(HelperDelegate.statusItemClicked)
    // 同时响应左键和右键
    button.sendAction(on: [.leftMouseUp, .rightMouseUp])
}

// Timer to read title from file every 2 seconds
Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { _ in
    if let text = try? String(contentsOfFile: titleFile, encoding: .utf8) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmed.isEmpty {
            DispatchQueue.main.async {
                delegate.updateButton(title: trimmed)
            }
        }
    }
}

app.run()

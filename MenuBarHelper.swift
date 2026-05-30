import Cocoa

// python_pid is passed as first argument
let args = CommandLine.arguments
guard args.count >= 2, let pythonPid = Int32(args[1]) else {
    print("Usage: MenuBarHelper <python_pid>")
    exit(1)
}

let titleFile = "/tmp/deepseek_statusbar_title.txt"
let widthModeFile = "/tmp/deepseek_statusbar_width_mode.txt"

// Only create initial title file if it doesn't already exist
if !FileManager.default.fileExists(atPath: titleFile) {
    try? "ICON".write(toFile: titleFile, atomically: true, encoding: .utf8)
}
if !FileManager.default.fileExists(atPath: widthModeFile) {
    try? "auto".write(toFile: widthModeFile, atomically: true, encoding: .utf8)
}

func loadMenuBarTemplateIcon(resourcePath: String) -> NSImage? {
    let p20 = resourcePath + "/assets/icons/menu_bar_icon_20.png"
    let p40 = resourcePath + "/assets/icons/menu_bar_icon_40.png"
    let fallback = resourcePath + "/status_icon.png"
    let image = NSImage(size: NSSize(width: 20, height: 20))
    var added = false

    if let d20 = try? Data(contentsOf: URL(fileURLWithPath: p20)),
       let rep20 = NSBitmapImageRep(data: d20) {
        image.addRepresentation(rep20)
        added = true
    }
    if let d40 = try? Data(contentsOf: URL(fileURLWithPath: p40)),
       let rep40 = NSBitmapImageRep(data: d40) {
        image.addRepresentation(rep40)
        added = true
    }
    if !added, let fallbackImage = NSImage(contentsOfFile: fallback) {
        fallbackImage.size = NSSize(width: 18, height: 18)
        fallbackImage.isTemplate = true
        return fallbackImage
    }

    if !added { return nil }
    image.size = NSSize(width: 18, height: 18)
    image.isTemplate = true
    return image
}

// Load custom icon from Resources folder.
var statusIcon: NSImage? = nil
if let resourcePath = Bundle.main.resourcePath {
    statusIcon = loadMenuBarTemplateIcon(resourcePath: resourcePath)
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
        if title == "ICON", let icon = icon {
            button.image = icon
            button.imageScaling = .scaleProportionallyUpOrDown
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
    initialTitle = "ICON"
}

if let button = statusItem.button {
    if initialTitle == "ICON", let icon = statusIcon {
        button.image = icon
        button.imageScaling = .scaleProportionallyUpOrDown
        button.title = ""
    } else {
        button.image = nil
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
    if let widthMode = try? String(contentsOfFile: widthModeFile, encoding: .utf8) {
        let mode = widthMode.trimmingCharacters(in: .whitespacesAndNewlines)
        DispatchQueue.main.async {
            statusItem.length = (mode == "fixed") ? 106 : NSStatusItem.variableLength
        }
    }
}

app.run()

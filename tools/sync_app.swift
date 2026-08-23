// 옵시디언 → 대시보드 동기화 데스크탑 앱 (macOS 네이티브)
//
// 더블클릭으로 실행하면 수집 → 정규화 → 검증 → 생성 → 배포를 순서대로 진행하고,
// 단계별 진행 상황과 로그를 보여준 뒤 완료를 표시합니다.
// 시스템 Tk 8.5가 최신 macOS에서 렌더링되지 않아 AppKit으로 작성했습니다.
//
// 빌드: swiftc -O tools/sync_app.swift -o "<앱번들>/Contents/MacOS/launcher"

import AppKit

let home = FileManager.default.homeDirectoryForCurrentUser.path
let root = home + "/biz-portal"
let tokenPath = root + "/.notion_token"
let dashboardURL = "http://34.83.67.147/dashboard/"

struct Step {
    let name: String
    let command: [String]
    let hint: String
}

let steps: [Step] = [
    Step(name: "옵시디언에서 수집",
         command: ["/usr/bin/python3", root + "/tools/fetch_obsidian.py"],
         hint: "볼트(MyBrain/Personal/Portfolio/BizPortal) 노트의 표 형식을 확인하세요."),
    Step(name: "정규화",
         command: ["/usr/bin/python3", root + "/tools/normalize.py"],
         hint: "볼트 표의 열 이름이 바뀌었을 수 있습니다. 00 대시보드 홈의 편집 규칙을 확인하세요."),
    Step(name: "정합성 검증",
         command: ["/usr/bin/python3", root + "/tools/verify.py"],
         hint: "표끼리 숫자가 어긋납니다. 로그의 [오류] 항목을 옵시디언 볼트에서 고친 뒤 다시 실행하세요."),
    Step(name: "data.js 생성",
         command: ["/usr/bin/python3", root + "/tools/build.py"],
         hint: ""),
    Step(name: "VM 배포",
         command: ["/bin/bash", root + "/tools/deploy.sh", "--skip-verify"],
         hint: "gcloud 로그인 상태(portfolio 구성)를 확인하세요."),
]

func loadToken() -> String {
    if let env = ProcessInfo.processInfo.environment["NOTION_TOKEN"], !env.isEmpty { return env }
    return (try? String(contentsOfFile: tokenPath, encoding: .utf8))?
        .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
}

func saveToken(_ token: String) {
    try? (token + "\n").write(toFile: tokenPath, atomically: true, encoding: .utf8)
    try? FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: tokenPath)
}

final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate {
    var window: NSWindow!
    let statusLabel = NSTextField(labelWithString: "준비 중…")
    let subLabel = NSTextField(labelWithString: "")
    let progress = NSProgressIndicator()
    let logView = NSTextView()
    let openButton = NSButton(title: "대시보드 열기", target: nil, action: nil)
    let retryButton = NSButton(title: "다시 실행", target: nil, action: nil)
    let tokenBox = NSStackView()
    let tokenField = NSSecureTextField()
    var running = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        let rect = NSRect(x: 0, y: 0, width: 680, height: 560)
        window = NSWindow(contentRect: rect,
                          styleMask: [.titled, .closable, .miniaturizable, .resizable],
                          backing: .buffered, defer: false)
        window.title = "옵시디언 → 대시보드 동기화"
        window.center()
        window.delegate = self
        window.minSize = NSSize(width: 540, height: 420)

        statusLabel.font = .boldSystemFont(ofSize: 20)
        subLabel.font = .systemFont(ofSize: 13)
        subLabel.textColor = .secondaryLabelColor

        progress.isIndeterminate = false
        progress.minValue = 0
        progress.maxValue = Double(steps.count)
        progress.style = .bar

        logView.isEditable = false
        logView.font = NSFont.monospacedSystemFont(ofSize: 12, weight: .regular)
        logView.backgroundColor = NSColor(calibratedWhite: 0.12, alpha: 1)
        logView.textColor = NSColor(calibratedWhite: 0.85, alpha: 1)
        logView.autoresizingMask = [.width]
        logView.textContainerInset = NSSize(width: 8, height: 8)
        let scroll = NSScrollView()
        scroll.documentView = logView
        scroll.hasVerticalScroller = true
        scroll.translatesAutoresizingMaskIntoConstraints = false

        openButton.target = self
        openButton.action = #selector(openDashboard)
        retryButton.target = self
        retryButton.action = #selector(startSync)
        openButton.isHidden = true
        retryButton.isHidden = true

        // 토큰 입력 영역 (필요할 때만 표시)
        let guide = NSTextField(wrappingLabelWithString:
            "노션 통합 토큰이 필요합니다 (ntn_… / secret_…).\n" +
            "notion.so → 설정 → 개발자 → [+ 신규 연결]로 내부 통합을 만들고,\n" +
            "'BI 대시보드 모음' 페이지 ⋯ → 연결에서 통합을 추가한 뒤 토큰을 붙여넣으세요.")
        guide.font = .systemFont(ofSize: 12)
        tokenField.placeholderString = "ntn_…"
        let saveButton = NSButton(title: "저장하고 시작", target: self, action: #selector(saveTokenAndStart))
        saveButton.keyEquivalent = "\r"
        let tokenRow = NSStackView(views: [tokenField, saveButton])
        tokenRow.orientation = .horizontal
        tokenField.setContentHuggingPriority(.defaultLow, for: .horizontal)
        tokenBox.orientation = .vertical
        tokenBox.alignment = .leading
        tokenBox.spacing = 8
        tokenBox.addArrangedSubview(guide)
        tokenBox.addArrangedSubview(tokenRow)
        tokenRow.widthAnchor.constraint(equalTo: tokenBox.widthAnchor).isActive = true
        tokenBox.isHidden = true

        let buttonRow = NSStackView(views: [NSView(), retryButton, openButton])
        buttonRow.orientation = .horizontal
        (buttonRow.views.first!).setContentHuggingPriority(.defaultLow, for: .horizontal)

        let stack = NSStackView(views: [statusLabel, subLabel, progress, tokenBox, scroll, buttonRow])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 10
        stack.edgeInsets = NSEdgeInsets(top: 16, left: 16, bottom: 16, right: 16)
        stack.translatesAutoresizingMaskIntoConstraints = false
        window.contentView = NSView()
        window.contentView!.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.topAnchor.constraint(equalTo: window.contentView!.topAnchor),
            stack.bottomAnchor.constraint(equalTo: window.contentView!.bottomAnchor),
            stack.leadingAnchor.constraint(equalTo: window.contentView!.leadingAnchor),
            stack.trailingAnchor.constraint(equalTo: window.contentView!.trailingAnchor),
            progress.widthAnchor.constraint(equalTo: stack.widthAnchor, constant: -32),
            tokenBox.widthAnchor.constraint(equalTo: stack.widthAnchor, constant: -32),
            scroll.widthAnchor.constraint(equalTo: stack.widthAnchor, constant: -32),
            buttonRow.widthAnchor.constraint(equalTo: stack.widthAnchor, constant: -32),
        ])

        NSApp.setActivationPolicy(.regular)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)

        startSync()  // 옵시디언 볼트가 원본 — 토큰 불필요
    }

    func windowWillClose(_ notification: Notification) { NSApp.terminate(nil) }

    @objc func openDashboard() {
        NSWorkspace.shared.open(URL(string: dashboardURL)!)
    }

    @objc func saveTokenAndStart() {
        let token = tokenField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        if token.isEmpty {
            subLabel.stringValue = "토큰이 비어 있습니다."
            return
        }
        saveToken(token)
        tokenBox.isHidden = true
        startSync()
    }

    @objc func startSync() {
        guard !running else { return }
        running = true
        openButton.isHidden = true
        retryButton.isHidden = true
        progress.doubleValue = 0
        logView.string = ""

        DispatchQueue.global().async { self.runPipeline() }
    }

    func runPipeline() {
        var env = ProcessInfo.processInfo.environment
        env["NOTION_TOKEN"] = loadToken()
        if env["CLOUDSDK_ACTIVE_CONFIG_NAME"] == nil { env["CLOUDSDK_ACTIVE_CONFIG_NAME"] = "portfolio" }
        let gcloudBin = home + "/google-cloud-sdk/bin"
        if FileManager.default.fileExists(atPath: gcloudBin) {
            env["PATH"] = gcloudBin + ":" + (env["PATH"] ?? "/usr/bin:/bin")
        }

        for (i, step) in steps.enumerated() {
            ui {
                self.statusLabel.stringValue = "진행 중… (\(i + 1)/\(steps.count))"
                self.subLabel.stringValue = step.name
                self.append("\n── \(step.name) ──\n")
            }
            let proc = Process()
            proc.executableURL = URL(fileURLWithPath: step.command[0])
            proc.arguments = Array(step.command.dropFirst())
            proc.currentDirectoryURL = URL(fileURLWithPath: root)
            proc.environment = env
            let pipe = Pipe()
            proc.standardOutput = pipe
            proc.standardError = pipe
            pipe.fileHandleForReading.readabilityHandler = { handle in
                let data = handle.availableData
                if let text = String(data: data, encoding: .utf8), !text.isEmpty {
                    self.ui { self.append(text) }
                }
            }
            do {
                try proc.run()
            } catch {
                self.fail(step: step, message: "실행 실패: \(error.localizedDescription)")
                return
            }
            proc.waitUntilExit()
            pipe.fileHandleForReading.readabilityHandler = nil
            if proc.terminationStatus != 0 {
                self.fail(step: step, message: nil)
                return
            }
            ui { self.progress.doubleValue = Double(i + 1) }
        }

        ui {
            self.running = false
            self.statusLabel.stringValue = "✅ 완료"
            self.subLabel.stringValue = "대시보드에 반영되었습니다 · " + dashboardURL
            self.append("\n✅ 완료 — 대시보드에 반영되었습니다.\n")
            self.openButton.isHidden = false
            self.retryButton.isHidden = false
        }
    }

    func fail(step: Step, message: String?) {
        ui {
            self.running = false
            self.statusLabel.stringValue = "❌ 실패 — \(step.name)"
            self.subLabel.stringValue = message ?? (step.hint.isEmpty ? "로그를 확인하세요." : step.hint)
            if let message = message { self.append("\n" + message + "\n") }
            self.retryButton.isHidden = false
        }
    }

    func append(_ text: String) {
        logView.textStorage?.append(NSAttributedString(
            string: text,
            attributes: [
                .font: NSFont.monospacedSystemFont(ofSize: 12, weight: .regular),
                .foregroundColor: text.contains("[오류]")
                    ? NSColor(calibratedRed: 0.96, green: 0.53, blue: 0.44, alpha: 1)
                    : NSColor(calibratedWhite: 0.85, alpha: 1),
            ]))
        logView.scrollToEndOfDocument(nil)
    }

    func ui(_ block: @escaping () -> Void) {
        DispatchQueue.main.async(execute: block)
    }
}

// 메뉴 바 — 이게 없으면 Cmd+V(붙여넣기) 등 표준 단축키가 동작하지 않습니다.
func buildMainMenu() -> NSMenu {
    let main = NSMenu()

    let appItem = NSMenuItem()
    main.addItem(appItem)
    let appMenu = NSMenu()
    appMenu.addItem(withTitle: "대시보드 동기화 종료",
                    action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
    appItem.submenu = appMenu

    let editItem = NSMenuItem()
    main.addItem(editItem)
    let edit = NSMenu(title: "편집")
    edit.addItem(withTitle: "실행 취소", action: Selector(("undo:")), keyEquivalent: "z")
    edit.addItem(withTitle: "다시 실행", action: Selector(("redo:")), keyEquivalent: "Z")
    edit.addItem(NSMenuItem.separator())
    edit.addItem(withTitle: "오려두기", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
    edit.addItem(withTitle: "복사", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
    edit.addItem(withTitle: "붙여넣기", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
    edit.addItem(withTitle: "전체 선택", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
    editItem.submenu = edit

    return main
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.mainMenu = buildMainMenu()
app.run()

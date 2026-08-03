# -*- coding: utf-8 -*-
"""노션 → 대시보드 동기화 데스크탑 앱.

더블클릭으로 실행하면 수집 → 정규화 → 검증 → 생성 → 배포를 순서대로 진행하고,
단계별 진행 상황과 로그를 보여준 뒤 완료를 표시합니다.

노션 접근에는 내부 통합 토큰이 필요합니다. 첫 실행 때 입력받아
~/biz-portal/.notion_token (본인만 읽기 가능)에 저장하고 이후엔 자동으로 씁니다.

    /usr/bin/python3 tools/sync_app.py
"""
import os
import queue
import stat
import subprocess
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, scrolledtext

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
TOKEN_PATH = os.path.join(ROOT, ".notion_token")
DASHBOARD_URL = "http://34.83.67.147/dashboard/"

# (표시 이름, 명령, 실패 시 안내)
STEPS = [
    ("노션에서 수집", [sys.executable, os.path.join(TOOLS, "fetch_notion.py")],
     "노션 토큰이 유효한지, 통합이 'BI 대시보드 모음' 페이지에 연결됐는지 확인하세요."),
    ("정규화", [sys.executable, os.path.join(TOOLS, "normalize.py")],
     "노션 DB 구조가 바뀌었을 수 있습니다. tools/config.py를 확인하세요."),
    ("정합성 검증", [sys.executable, os.path.join(TOOLS, "verify.py")],
     "노션 DB끼리 숫자가 어긋납니다. 로그의 [오류] 항목을 노션에서 고친 뒤 다시 실행하세요."),
    ("data.js 생성", [sys.executable, os.path.join(TOOLS, "build.py")], ""),
    ("VM 배포", ["bash", os.path.join(TOOLS, "deploy.sh"), "--skip-verify"],
     "gcloud 로그인 상태(portfolio 구성)를 확인하세요."),
]


def load_token():
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    try:
        with open(TOKEN_PATH, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def save_token(token):
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(token.strip() + "\n")
    os.chmod(TOKEN_PATH, stat.S_IRUSR | stat.S_IWUSR)  # 600 — 본인만 읽기


class SyncApp:
    def __init__(self, root):
        self.root = root
        root.title("노션 → 대시보드 동기화")
        root.geometry("640x520")
        root.minsize(520, 400)

        self.q = queue.Queue()
        self.running = False

        outer = ttk.Frame(root, padding=16)
        outer.pack(fill="both", expand=True)

        self.status = ttk.Label(outer, text="준비 중…", font=("AppleGothic", 18, "bold"))
        self.status.pack(anchor="w")

        self.substatus = ttk.Label(outer, text="", foreground="#666")
        self.substatus.pack(anchor="w", pady=(2, 10))

        self.bar = ttk.Progressbar(outer, maximum=len(STEPS), mode="determinate")
        self.bar.pack(fill="x", pady=(0, 10))

        self.log = scrolledtext.ScrolledText(outer, height=16, state="disabled",
                                             font=("Menlo", 11), background="#1e1e1e",
                                             foreground="#d4d4d4", insertbackground="#d4d4d4")
        self.log.pack(fill="both", expand=True)
        self.log.tag_configure("err", foreground="#f48771")
        self.log.tag_configure("ok", foreground="#89d185")

        btns = ttk.Frame(outer)
        btns.pack(fill="x", pady=(10, 0))
        self.open_btn = ttk.Button(btns, text="대시보드 열기",
                                   command=lambda: webbrowser.open(DASHBOARD_URL))
        self.retry_btn = ttk.Button(btns, text="다시 실행", command=self.start)

        # 토큰 입력 영역 (필요할 때만 표시)
        self.token_frame = ttk.Frame(outer)
        ttk.Label(self.token_frame,
                  text="노션 통합 토큰이 필요합니다 (ntn_… / secret_…).\n"
                       "notion.so/my-integrations 에서 내부 통합을 만들고,\n"
                       "'BI 대시보드 모음' 페이지 ⋯ → 연결에서 통합을 추가한 뒤 토큰을 붙여넣으세요.",
                  justify="left").pack(anchor="w", pady=(0, 6))
        row = ttk.Frame(self.token_frame)
        row.pack(fill="x")
        self.token_entry = ttk.Entry(row, show="•")
        self.token_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="저장하고 시작", command=self.save_token_and_start)\
            .pack(side="left", padx=(8, 0))

        root.after(200, self.boot)

    # ── 시작 흐름 ──────────────────────────────────────────────
    def boot(self):
        if load_token():
            self.start()
        else:
            self.status.config(text="노션 토큰 설정")
            self.substatus.config(text="최초 1회만 입력하면 저장됩니다.")
            self.token_frame.pack(fill="x", pady=(0, 10), before=self.log)

    def save_token_and_start(self):
        token = self.token_entry.get().strip()
        if not token:
            self.substatus.config(text="토큰이 비어 있습니다.")
            return
        save_token(token)
        self.token_frame.pack_forget()
        self.start()

    def start(self):
        if self.running:
            return
        self.running = True
        self.retry_btn.pack_forget()
        self.open_btn.pack_forget()
        self.bar["value"] = 0
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        threading.Thread(target=self.worker, daemon=True).start()
        self.root.after(100, self.drain)

    # ── 백그라운드 실행 ─────────────────────────────────────────
    def worker(self):
        env = dict(os.environ)
        env["NOTION_TOKEN"] = load_token()
        env.setdefault("CLOUDSDK_ACTIVE_CONFIG_NAME", "portfolio")
        gcloud_bin = os.path.expanduser("~/google-cloud-sdk/bin")
        if os.path.isdir(gcloud_bin):
            env["PATH"] = gcloud_bin + os.pathsep + env.get("PATH", "")

        for i, (name, cmd, hint) in enumerate(STEPS):
            self.q.put(("step", i, name))
            proc = subprocess.Popen(cmd, cwd=ROOT, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
            for line in proc.stdout:
                self.q.put(("log", line))
            proc.wait()
            if proc.returncode != 0:
                self.q.put(("fail", name, hint))
                return
            self.q.put(("done_step", i))
        self.q.put(("success",))

    # ── UI 갱신 ────────────────────────────────────────────────
    def drain(self):
        try:
            while True:
                msg = self.q.get_nowait()
                kind = msg[0]
                if kind == "step":
                    _, i, name = msg
                    self.status.config(text="진행 중… (%d/%d)" % (i + 1, len(STEPS)))
                    self.substatus.config(text=name)
                    self.append("\n── %s ──\n" % name, "ok")
                elif kind == "log":
                    self.append(msg[1], "err" if "[오류]" in msg[1] else None)
                elif kind == "done_step":
                    self.bar["value"] = msg[1] + 1
                elif kind == "fail":
                    _, name, hint = msg
                    self.running = False
                    self.status.config(text="❌ 실패 — %s" % name)
                    self.substatus.config(text=hint or "로그를 확인하세요.")
                    self.retry_btn.pack(side="right")
                    return
                elif kind == "success":
                    self.running = False
                    self.status.config(text="✅ 완료")
                    self.substatus.config(text="대시보드에 반영되었습니다 · " + DASHBOARD_URL)
                    self.append("\n✅ 완료 — 대시보드에 반영되었습니다.\n", "ok")
                    self.open_btn.pack(side="right")
                    self.retry_btn.pack(side="right", padx=(0, 8))
                    return
        except queue.Empty:
            pass
        if self.running:
            self.root.after(100, self.drain)

    def append(self, text, tag=None):
        self.log.configure(state="normal")
        self.log.insert("end", text, tag)
        self.log.see("end")
        self.log.configure(state="disabled")


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    SyncApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

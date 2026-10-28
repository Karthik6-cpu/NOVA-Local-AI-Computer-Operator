import json
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from nova.config import APP_NAME, WORKSPACE
from nova.planner import plan_request
from nova.tools import execute_plan
from nova.audit import log_event
from nova.voice import listen_once, listen_for_decision

class NovaApp:
    def __init__(self, root):
        self.root = root
        root.title(f"{APP_NAME} | Local AI Computer Operator")
        root.geometry("960x720")
        root.minsize(780, 580)
        self.pending_plan = None
        self.busy = False
        self.approval_listening = False
        self.approval_stop = threading.Event()

        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        header = ttk.Frame(root, padding=(18, 16, 18, 6))
        header.pack(fill="x")
        ttk.Label(header, text="NOVA", font=("Segoe UI", 25, "bold")).pack(side="left")
        ttk.Label(header, text="LOCAL AI COMPUTER OPERATOR", font=("Segoe UI", 9)).pack(side="left", padx=14, pady=(8, 0))
        self.status = tk.StringVar(value="Ready · Local AI · No cloud API key required")
        ttk.Label(root, textvariable=self.status, padding=(18, 4)).pack(fill="x")

        inp = ttk.LabelFrame(root, text="Tell NOVA what you want to do", padding=12)
        inp.pack(fill="x", padx=18, pady=8)
        self.command = tk.StringVar()
        self.entry = ttk.Entry(inp, textvariable=self.command, font=("Segoe UI", 11))
        self.entry.pack(fill="x", pady=(0, 10))
        self.entry.bind("<Return>", lambda _event: self.make_plan())
        row = ttk.Frame(inp)
        row.pack(fill="x")
        self.plan_button = ttk.Button(row, text="Plan task", command=self.make_plan)
        self.plan_button.pack(side="left")
        self.voice_button = ttk.Button(row, text="🎙 Speak command", command=self.start_voice)
        self.voice_button.pack(side="left", padx=8)
        ttk.Button(row, text="Clear", command=self.clear).pack(side="left")

        frame = ttk.LabelFrame(root, text="Plan preview and results", padding=10)
        frame.pack(fill="both", expand=True, padx=18, pady=8)
        self.output = scrolledtext.ScrolledText(frame, wrap="word", font=("Consolas", 10), height=18, state="disabled")
        self.output.pack(fill="both", expand=True)

        footer = ttk.Frame(root, padding=(18, 8, 18, 16))
        footer.pack(fill="x")
        self.run_button = ttk.Button(footer, text="Approve and run plan", command=self.approve_and_run, state="disabled")
        self.run_button.pack(side="left")
        ttk.Label(
            footer,
            text="Voice approval listens for 60 seconds · No shell commands · No file deletion",
            wraplength=550
        ).pack(side="left", padx=12)

        self.write_output(
            "Welcome to NOVA — local-first edition.\n\n"
            "Try: Open Notepad\n"
            "Try: Open File Explorer\n"
            "Try: Open Settings\n"
            "Try: Open Task Manager\n"
            "Try: List applications\n"
            "Try: Open Chrome (if its Start Menu shortcut is installed)\n"
            "Try: Open WhatsApp\n"
            "Try: Create a note called DSA plan with text: revise arrays tomorrow\n\n"
            "NOVA previews each plan. When a plan is ready, say 'Approve' or 'Reject' within 60 seconds, or use the button."
        )
        self.entry.focus_set()

    def write_output(self, text):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")

    def set_busy(self, busy, message):
        self.busy = busy
        self.status.set(message)
        state = "disabled" if busy else "normal"
        self.plan_button.configure(state=state)
        self.voice_button.configure(state=state)
        self.entry.configure(state=state)
        if not busy:
            self.voice_button.configure(text="🎙 Listen for approval" if self.pending_plan else "🎙 Speak command")

    def make_plan(self):
        if self.busy:
            return
        request = self.command.get().strip()
        if not request:
            return
        self.pending_plan = None
        self.approval_stop.set()
        self.approval_listening = False
        self.run_button.configure(state="disabled")
        self.voice_button.configure(text="🎙 Speak command")
        self.set_busy(True, "Planning with local AI…")
        self.write_output("NOVA is asking the local model to prepare a plan…")
        threading.Thread(target=self._plan_worker, args=(request,), daemon=True).start()

    def _plan_worker(self, request):
        try:
            plan = plan_request(request)
            log_event("plan_created", {"request": request, "plan": plan})
            self.root.after(0, lambda: self._show_plan(plan))
        except Exception as exc:
            self.root.after(0, lambda: self._plan_failed(str(exc)))

    def _show_plan(self, plan):
        self.pending_plan = plan
        lines = [f"Goal: {plan.get('summary', '')}", "", "Proposed actions:"]
        for i, action in enumerate(plan.get("actions", []), 1):
            lines.append(f"{i}. {action.get('tool')}  {json.dumps(action.get('args', {}), ensure_ascii=False)}")
        if plan.get("actions"):
            lines += [
                "",
                "Voice approval is active for 60 seconds.",
                "Say exactly: 'Approve' or 'Reject'.",
                "You can also use the button below.",
            ]
        else:
            lines += ["", "No supported actions were proposed. Try a more specific request."]
        self.write_output("\n".join(lines))
        self.set_busy(False, "Plan ready · Approval required" if plan.get("actions") else "No actions to run")
        self.run_button.configure(state="normal" if plan.get("actions") else "disabled")
        self.voice_button.configure(text="🎙 Listen for approval" if plan.get("actions") else "🎙 Speak command")
        if plan.get("actions"):
            self.root.after(250, self._start_auto_approval_listener)

    def _plan_failed(self, error):
        self.write_output("Could not create a plan.\n\n" + error)
        self.set_busy(False, "Local planning failed")
        self.run_button.configure(state="disabled")
        messagebox.showerror("NOVA planning error", error)

    def _start_auto_approval_listener(self):
        if not self.pending_plan or self.busy or self.approval_listening:
            return
        self.approval_stop = threading.Event()
        self.approval_listening = True
        self.status.set("Listening for spoken 'Approve' or 'Reject' · 60 seconds")
        threading.Thread(target=self._approval_voice_worker, args=(self.approval_stop,), daemon=True).start()

    def _approval_voice_worker(self, stop_event):
        try:
            decision = listen_for_decision(timeout=60, stop_event=stop_event)
            self.root.after(0, lambda: self._approval_voice_done(decision))
        except Exception as exc:
            self.root.after(0, lambda: self._approval_voice_failed(str(exc)))

    def _approval_voice_done(self, decision):
        self.approval_listening = False
        if not self.pending_plan:
            return
        if decision == "approve":
            self._execute_pending_plan(source="voice")
        elif decision == "reject":
            log_event("plan_rejected", {"source": "voice", "plan": self.pending_plan})
            self.pending_plan = None
            self.run_button.configure(state="disabled")
            self.voice_button.configure(text="🎙 Speak command")
            self.write_output("Plan rejected by voice. No actions were executed.\n\nEnter or speak another task when ready.")
            self.set_busy(False, "Plan rejected · Nothing executed")
        else:
            self.status.set("Approval timed out · Say 'Approve' or click the button")
            self.voice_button.configure(text="🎙 Listen for approval")

    def _approval_voice_failed(self, error):
        self.approval_listening = False
        if self.pending_plan:
            self.status.set("Voice approval unavailable · Use button or check microphone")
            self.voice_button.configure(text="🎙 Listen for approval")
            self.write_output(self.output.get("1.0", "end-1c") + "\n\nVoice approval could not start: " + error)
        else:
            self.status.set("Ready")

    def start_voice(self):
        if self.busy:
            return
        if self.pending_plan:
            if self.approval_listening:
                self.status.set("Already listening · Say 'Approve' or 'Reject'")
                return
            self._start_auto_approval_listener()
            return
        self.set_busy(True, "Listening with offline speech recognition…")
        self.write_output("Listening… speak a short command.")
        threading.Thread(target=self._voice_worker, daemon=True).start()

    def _voice_worker(self):
        try:
            text = listen_once()
            self.root.after(0, lambda: self._voice_done(text))
        except Exception as exc:
            self.root.after(0, lambda: self._voice_failed(str(exc)))

    def _voice_done(self, text):
        self.command.set(text)
        self.set_busy(False, "Voice captured · Planning request")
        if text:
            self.make_plan()

    def _voice_failed(self, error):
        self.set_busy(False, "Voice input unavailable")
        messagebox.showwarning("NOVA voice input", error)

    def approve_and_run(self):
        if not self.pending_plan or self.busy:
            return
        if not messagebox.askyesno("Approve NOVA plan", "Run the displayed actions? Review the plan first."):
            return
        self._execute_pending_plan(source="button")

    def _execute_pending_plan(self, source):
        if not self.pending_plan or self.busy:
            return
        plan = self.pending_plan
        self.pending_plan = None
        self.approval_stop.set()
        self.approval_listening = False
        log_event("plan_approved", {"source": source, "plan": plan})
        self.run_button.configure(state="disabled")
        self.voice_button.configure(text="🎙 Speak command")
        self.set_busy(True, f"Executing approved plan ({source})…")
        threading.Thread(target=self._execute_worker, args=(plan,), daemon=True).start()

    def _execute_worker(self, plan):
        try:
            results = execute_plan(plan)
            log_event("plan_executed", {"plan": plan, "results": results})
            text = "Execution results:\n\n" + "\n\n".join(
                f"{i}. {'SUCCESS' if r['ok'] else 'FAILED'} — {r['message']}"
                for i, r in enumerate(results, 1)
            )
        except Exception as exc:
            log_event("execution_error", {"error": str(exc)})
            text = "Execution error:\n" + str(exc)
        self.root.after(0, lambda: self._execution_done(text))

    def _execution_done(self, text):
        self.write_output(text)
        self.set_busy(False, "Finished · Check results")
        self.run_button.configure(state="disabled")
        self.entry.focus_set()

    def clear(self):
        if self.busy:
            return
        self.approval_stop.set()
        self.approval_listening = False
        self.command.set("")
        self.pending_plan = None
        self.run_button.configure(state="disabled")
        self.voice_button.configure(text="🎙 Speak command")
        self.write_output("Cleared. Enter a new request to create a plan.")
        self.status.set("Ready")
        self.entry.focus_set()

def main():
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    NovaApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

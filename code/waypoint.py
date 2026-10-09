import math
import time
import threading
import json
import argparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ─── Dynamixel (optional – GUI works without hardware) ────────────────────────
try:
    from dynamixel_sdk import (
        PortHandler, PacketHandler, GroupSyncWrite,
        COMM_SUCCESS, DXL_LOBYTE, DXL_HIBYTE, DXL_LOWORD, DXL_HIWORD
    )
    DYNAMIXEL_AVAILABLE = True
except ImportError:
    DYNAMIXEL_AVAILABLE = False

# ─── Control Table ────────────────────────────────────────────────────────────
ADDR_TORQUE_ENABLE    = 64
ADDR_GOAL_CURRENT     = 102   # 2-byte, unit = ~3.36 mA per tick (XM/XH series)
ADDR_GOAL_POSITION    = 116
ADDR_PRESENT_POSITION = 132

# Current unit conversion (XM430/XH series): 1 tick ≈ 2.69 mA
CURRENT_UNIT_MA = 2.69   # mA per tick

# ─── Port / Protocol ─────────────────────────────────────────────────────────
PROTOCOL_VERSION = 2.0
BAUDRATE         = 1000000
DEVICENAME       = 'COM5'   # ← change to your port

# ─── Servo IDs ────────────────────────────────────────────────────────────────
ID_BASE     = 10
ID_SHOULDER = 11
ID_ELBOW    = 13
ID_WRIST    = 14
ID_HAND     = 15

# ─── Base motor gear ratio ────────────────────────────────────────────────────
# The base is geared 3.0:1 — 3.0 motor rotations = 1 base rotation.
# The motor runs in multi-turn mode: position counts beyond 4095 as it rotates
# (e.g. one full base rotation = 3.00 × 4096 ≈ 12,288 motor ticks).
# We record the raw motor ticks at startup as the home reference.
# IK gives a joint angle in degrees; we convert to motor ticks as:
#   motor_ticks = home_ticks + joint_degrees × TPD × BASE_GEAR_RATIO
# Waypoints store raw motor ticks directly — no conversion needed for replay.
BASE_GEAR_RATIO = 3.00

HAND_OPEN   = 1000   # ticks — open position
HAND_CLOSED = 4000   # ticks — closed position

# ─── Position Limits ─────────────────────────────────────────────────────────
DXL_MIN = 0
DXL_MAX = 4095
DXL_CTR = 2048
TPD     = 4096.0 / 360.0       # ticks per degree

# ─── Robot Geometry (metres) ─────────────────────────────────────────────────
L1 = 0.00
L2 = 0.22
L3 = 0.22

_L2_SQ     = L2 ** 2
_L3_SQ     = L3 ** 2
_2L2L3     = 2 * L2 * L3
_2L2       = 2 * L2

# Shoulder calibration offset — tuned via the UI spinner.
# Set to 0 initially; adjust until canvas vertical matches physical vertical.
_ELBOW_OFF = 0.0   # radians — overwritten at runtime by RobotArmGUI._shoulder_offset_var

# ─── Colours ─────────────────────────────────────────────────────────────────
BG     = "#0e1117"
PANEL  = "#161b27"
BORDER = "#1f2840"
ACCENT = "#00e5a0"
RED    = "#ff6b6b"
YELLOW = "#ffd166"
PURPLE = "#c084fc"
TEXT   = "#c8d0e7"
MUTED  = "#4a5370"
GRID   = "#1a2035"


# ─── IK ──────────────────────────────────────────────────────────────────────
def inverse_kinematics(x, y, z, t4=0.0):
    theta1 = math.atan2(y, x)
    r      = math.hypot(x, y)
    h      = z - L1
    d2     = r * r + h * h
    d      = math.sqrt(d2)

    if d > L2 + L3 or d < abs(L2 - L3) or d < 1e-9:
        return []

    cos_t3 = max(-1.0, min(1.0, (_L2_SQ + _L3_SQ - d2) / _2L2L3))
    theta3 = math.pi - math.acos(cos_t3)

    alpha    = math.atan2(h, r)
    cos_beta = max(-1.0, min(1.0, (_L2_SQ + d2 - _L3_SQ) / (_2L2 * d)))
    beta     = math.pi - (alpha + math.acos(cos_beta))
    theta2   = math.pi / 2 - beta + _ELBOW_OFF

    return [(theta1, -theta2, -theta3, t4)]


def angle_to_dxl(deg):
    deg = (deg + 180.0) % 360.0 - 180.0
    return max(DXL_MIN, min(DXL_MAX, int(DXL_CTR + deg * TPD + 0.5)))


# ─── Dynamixel sync write ─────────────────────────────────────────────────────
def sync_write_positions(gsw, ids, positions):
    gsw.clearParam()
    for did, pos in zip(ids, positions):
        param = [
            DXL_LOBYTE(DXL_LOWORD(pos)), DXL_HIBYTE(DXL_LOWORD(pos)),
            DXL_LOBYTE(DXL_HIWORD(pos)), DXL_HIBYTE(DXL_HIWORD(pos)),
        ]
        gsw.addParam(did, param)
    return gsw.txPacket() == COMM_SUCCESS


# ═══════════════════════════════════════════════════════════════════════════════
class ArmCanvas(tk.Canvas):
    """Live 2-D side-view (X-Z plane) of the robot arm."""

    PAD      = 30
    BASE_FRC = 0.78

    INTERP_STEPS = 12

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, highlightthickness=0, **kw)
        self._angles        = (0.0, 0.0, math.pi/2, 0.0)
        self._from_angles   = self._angles
        self._target_angles = self._angles
        self._interp_step   = self.INTERP_STEPS
        self._reachable     = True
        self.bind("<Configure>", lambda e: self.after(20, self._redraw))

    def set_pose(self, angles, reachable):
        if reachable and angles is not None:
            if not self._reachable:
                # Re-entering workspace: smooth interpolation from current drawn pose
                self._from_angles = self._angles
                self._interp_step = 0
            else:
                # Normal update: snap target, no interpolation needed
                self._target_angles = angles
                self._interp_step = self.INTERP_STEPS
            self._target_angles = angles
        # When unreachable: _angles/_target_angles stay frozen at last valid pose
        self._reachable = reachable
        self.after(0, self._redraw)

    def _advance_interp(self):
        if self._interp_step >= self.INTERP_STEPS:
            self._angles = self._target_angles
            return False
        t = (self._interp_step + 1) / self.INTERP_STEPS
        t = t * t * (3 - 2 * t)   # smooth-step easing
        self._angles = tuple(a + (b - a) * t for a, b in zip(self._from_angles, self._target_angles))
        self._interp_step += 1
        return self._interp_step < self.INTERP_STEPS

    def _redraw(self):
        # Advance interpolation one step; schedule another frame if still moving
        still_moving = self._advance_interp()
        if still_moving:
            self.after(16, self._redraw)   # ~60 fps while interpolating

        W = self.winfo_width()
        H = self.winfo_height()
        if W < 20 or H < 20:
            self.after(50, self._redraw)
            return

        self.delete("all")

        # Split canvas: left = side view (X-Z), right = top-down view (X-Y)
        mid = W // 2

        # ── Shared scale (same for both views) ───────────────────────────────
        view_w = mid - self.PAD
        view_h = H - 2 * self.PAD
        scale  = min(view_w, view_h) / ((L2 + L3) * 1.3)

        # ══════════════════════════════════════════════════════════════════════
        # LEFT: Side view (X-Z plane)
        # ══════════════════════════════════════════════════════════════════════
        cx    = mid // 2
        base_y = H * self.BASE_FRC

        # Grid (left half only)
        for i in range(0, mid, 30):
            self.create_line(i, 0, i, H, fill=GRID, width=1)
        for j in range(0, H, 30):
            self.create_line(0, j, mid, j, fill=GRID, width=1)

        # Divider
        self.create_line(mid, 0, mid, H, fill=BORDER, width=1, dash=(4, 4))

        # Ground line
        self.create_line(self.PAD, base_y, mid - self.PAD, base_y,
                         fill=BORDER, width=2, dash=(6, 4))

        # Base mount
        bw, bh = 26, 16
        self.create_rectangle(cx - bw, base_y - bh, cx + bw, base_y + 6,
                               fill=PANEL, outline=BORDER, width=2)
        for offset in [-8, 0, 8]:
            self.create_line(cx + offset - 4, base_y - bh,
                             cx + offset + 4, base_y,
                             fill=MUTED, width=1)

        # Reach limit arcs (side view)
        max_r = (L2 + L3) * scale
        min_r = 0.05 * scale
        self.create_arc(cx - max_r, base_y - max_r, cx + max_r, base_y + max_r,
                        start=0, extent=180, outline=MUTED, width=1, style="arc", dash=(6, 6))
        self.create_arc(cx - min_r, base_y - min_r, cx + min_r, base_y + min_r,
                        start=0, extent=180, outline=MUTED, width=1, style="arc", dash=(3, 8))
        self.create_text(cx + max_r - 4, base_y - 10,
                         text=f"{L2+L3:.2f}m", fill=MUTED, font=("Courier", 7), anchor="e")

        # Arm geometry
        t1, t2, t3, t4 = self._angles
        col = ACCENT if self._reachable else RED
        t2_geom = t2 - _ELBOW_OFF
        sa = math.pi / 2 - t2_geom
        ea = sa + t3

        x_sign = -1.0 if abs(t1) > math.pi / 2 else 1.0

        x0, y0 = cx, base_y
        x1 = x0 + x_sign * L2 * scale * math.cos(sa)
        y1 = y0 - L2 * scale * math.sin(sa)
        x2 = x1 + x_sign * L3 * scale * math.cos(ea)
        y2 = y1 - L3 * scale * math.sin(ea)
        x3 = x2 + x_sign * 20 * math.cos(ea - t4)
        y3 = y2 - 20 * math.sin(ea - t4)

        # Shadows
        for ax, ay, bx, by in [(x0, y0, x1, y1), (x1, y1, x2, y2)]:
            self.create_line(ax+4, ay+4, bx+4, by+4,
                             fill="#07090f", width=12, capstyle="round")

        # Links
        self.create_line(x0, y0, x1, y1, fill=col,    width=9, capstyle="round")
        self.create_line(x1, y1, x2, y2, fill=col,    width=7, capstyle="round")
        self.create_line(x2, y2, x3, y3, fill=YELLOW, width=4, capstyle="round")

        # Joints
        for jx, jy, jr, jc in [(x0, y0, 12, ACCENT),
                                 (x1, y1, 10, YELLOW),
                                 (x2, y2,  8, PURPLE),
                                 (x3, y3,  5, RED)]:
            self.create_oval(jx-jr-3, jy-jr-3, jx+jr+3, jy+jr+3,
                             fill=BG, outline=jc, width=2)
            self.create_oval(jx-jr+2, jy-jr+2, jx+jr-2, jy+jr-2,
                             fill=jc, outline="")

        self.create_oval(x2-6, y2-6, x2+6, y2+6, fill=col, outline=BG, width=2)

        # Angle labels
        lbl_anchor = "w" if x_sign > 0 else "e"
        for jx, jy, seg_angle, val, name, color in [
            (x0, y0, sa, t2, "θ2", ACCENT),
            (x1, y1, ea, t3, "θ3", YELLOW),
        ]:
            lx = jx + x_sign * (24 * math.cos(seg_angle) + 6)
            ly = jy - 24 * math.sin(seg_angle) - 6
            self.create_text(lx, ly, text=f"{name} {math.degrees(val):.1f}°",
                             fill=color, font=("Courier", 8), anchor=lbl_anchor)

        # Side view labels
        self.create_text(cx + max_r, base_y + 12, text="+X",
                         fill=MUTED, font=("Courier", 8), anchor="e")
        self.create_text(self.PAD + 4, H - self.PAD + 2, text="SIDE VIEW (X-Z)",
                         fill=MUTED, font=("Courier", 7), anchor="w")

        # ══════════════════════════════════════════════════════════════════════
        # RIGHT: Top-down view (X-Y plane)
        # ══════════════════════════════════════════════════════════════════════
        tcx = mid + (W - mid) // 2   # centre of right panel
        tcy = H // 2                  # vertical centre

        # Grid (right half only)
        for i in range(mid, W, 30):
            self.create_line(i, 0, i, H, fill=GRID, width=1)
        for j in range(0, H, 30):
            self.create_line(mid, j, W, j, fill=GRID, width=1)

        # Reach circle (full 360° from above)
        self.create_oval(tcx - max_r, tcy - max_r, tcx + max_r, tcy + max_r,
                         outline=MUTED, width=1, dash=(6, 6))
        self.create_oval(tcx - min_r, tcy - min_r, tcx + min_r, tcy + min_r,
                         outline=MUTED, width=1, dash=(3, 8))

        # Axis lines
        self.create_line(tcx - max_r - 8, tcy, tcx + max_r + 8, tcy,
                         fill=GRID, width=1, dash=(4, 4))
        self.create_line(tcx, tcy - max_r - 8, tcx, tcy + max_r + 8,
                         fill=GRID, width=1, dash=(4, 4))

        # Axis labels
        self.create_text(tcx + max_r + 10, tcy, text="+X",
                         fill=MUTED, font=("Courier", 8), anchor="w")
        self.create_text(tcx - max_r - 10, tcy, text="-X",
                         fill=MUTED, font=("Courier", 8), anchor="e")
        self.create_text(tcx, tcy - max_r - 10, text="+Y",
                         fill=MUTED, font=("Courier", 8), anchor="s")
        self.create_text(tcx, tcy + max_r + 10, text="-Y",
                         fill=MUTED, font=("Courier", 8), anchor="n")

        # Top-down arm: project onto X-Y plane using t1 and reach r1, r2
        # Upper arm: from base to elbow, reach = L2*cos(sa)
        # Full arm:  from base to tip,  reach = L2*cos(sa) + L3*cos(ea)
        r_elbow = L2 * math.cos(sa)            # horizontal reach to elbow
        r_tip   = L2 * math.cos(sa) + L3 * math.cos(ea)   # horizontal reach to tip

        # Top-down coords (screen): X rightward, Y upward → screen Y is negated
        tx0 = tcx
        ty0 = tcy
        tx1 = tcx + r_elbow * scale * math.cos(t1)
        ty1 = tcy - r_elbow * scale * math.sin(t1)   # negate for screen
        tx2 = tcx + r_tip   * scale * math.cos(t1)
        ty2 = tcy - r_tip   * scale * math.sin(t1)

        # Shadow
        self.create_line(tx0+3, ty0+3, tx2+3, ty2+3,
                         fill="#07090f", width=10, capstyle="round")

        # Upper arm
        self.create_line(tx0, ty0, tx1, ty1, fill=col,    width=9, capstyle="round")
        # Forearm
        self.create_line(tx1, ty1, tx2, ty2, fill=col,    width=7, capstyle="round")

        # Joints (top-down)
        for jx, jy, jr, jc in [(tx0, ty0, 12, ACCENT),
                                 (tx1, ty1, 10, YELLOW),
                                 (tx2, ty2,  8, PURPLE)]:
            self.create_oval(jx-jr-3, jy-jr-3, jx+jr+3, jy+jr+3,
                             fill=BG, outline=jc, width=2)
            self.create_oval(jx-jr+2, jy-jr+2, jx+jr-2, jy+jr-2,
                             fill=jc, outline="")

        # θ1 label
        self.create_text(tcx + 30, tcy - 14,
                         text=f"θ1 {math.degrees(t1):.1f}°",
                         fill=ACCENT, font=("Courier", 8), anchor="w")

        self.create_text(mid + 4, H - self.PAD + 2, text="TOP VIEW (X-Y)",
                         fill=MUTED, font=("Courier", 7), anchor="w")

        # Status badge
        s_txt = "● REACHABLE" if self._reachable else "● UNREACHABLE"
        self.create_text(W - self.PAD, 16, text=s_txt, fill=col,
                         font=("Courier", 9, "bold"), anchor="ne")


# ═══════════════════════════════════════════════════════════════════════════════
class RobotArmGUI:

    def __init__(self, root: tk.Tk, autorun_file: str = None):
        self.root     = root
        self._running = True
        self._lock    = threading.Lock()
        self._cmd     = None
        self._base_home_ticks = 0
        self._base_t1_startup = 0.0

        root.title("TSL Robot Arm")
        root.configure(bg=BG)
        root.minsize(1100, 660)

        self._build_ui()
        self._setup_hardware()

        self._ui_sync_in_progress = False
        self._hand_cmd = None

        # ── Teach / Replay state ─────────────────────────────────────────────
        self._waypoints      = []
        self._teach_mode     = False
        self._teach_hand_open = True
        self._replaying      = False
        self._replay_thread  = None

        self._thread = threading.Thread(target=self._comms_loop, daemon=True)
        self._thread.start()

        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Trigger initial canvas draw
        root.update_idletasks()
        root.after(50, self._on_slider_change)

        # ── Auto-load and run waypoint file if supplied on command line ───────
        if autorun_file:
            root.after(800, lambda: self._autorun(autorun_file))

    # ── Auto-run ──────────────────────────────────────────────────────────────
    def _autorun(self, path: str):
        """Load a waypoint file and immediately start replay. Called once at startup."""
        import os
        if not os.path.exists(path):
            self._wp_status.config(
                text=f"⚠  Auto-run file not found: {path}", fg=RED)
            self.status_lbl.config(
                text=f"⚠  Auto-run file not found: {path}", fg=RED)
            return
        try:
            with open(path) as f:
                data = json.load(f)
            wps = []
            for wp in data["waypoints"]:
                if isinstance(wp, dict):
                    t = wp.get("type", "")
                    if t == "STOP":
                        wps.append({"type": "STOP"})
                    elif t == "WAIT":
                        wps.append({"type": "WAIT", "seconds": float(wp.get("seconds", 1.0))})
                else:
                    wp = tuple(wp)
                    if len(wp) == 2:
                        wp = wp + (2048,)
                    if len(wp) == 3:
                        wp = wp + (0, HAND_OPEN)
                    if len(wp) == 4:
                        wp = wp + (HAND_OPEN,)
                    wps.append(wp)
            self._waypoints = wps
            if "speed" in data:
                self._speed_var.set(data["speed"])
            if "hold" in data:
                self._gap_var.set(data["hold"])
            if "shoulder_offset" in data:
                global _ELBOW_OFF
                self._shoulder_offset_var.set(data["shoulder_offset"])
                try:
                    _ELBOW_OFF = (int(data["shoulder_offset"]) / 4096) * (2 * math.pi)
                except (ValueError, TypeError):
                    pass
            self._refresh_listbox()
            self._wp_status.config(
                text=f"Auto-loaded {len(wps)} waypoints from {path} — starting replay…",
                fg=ACCENT)
            # Start replay after a short delay to let hardware finish initialising
            self.root.after(500, self._start_replay)
        except Exception as ex:
            self._wp_status.config(
                text=f"⚠  Auto-run load failed: {ex}", fg=RED)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=BG, pady=10)
        hdr.pack(fill="x", padx=20)
        tk.Label(hdr, text=" ", bg=BG, fg=ACCENT,
                 font=("Courier", 15, "bold")).pack(side="left")
        tk.Label(hdr, text="  TSL ROBOT ARM", bg=BG, fg=TEXT,
                 font=("Courier", 15)).pack(side="left")
        self.hw_badge = tk.Label(hdr, text="● CONNECTING…", bg=BG, fg=YELLOW,
                                  font=("Courier", 9))
        self.hw_badge.pack(side="right", padx=(12, 0))

        tk.Button(hdr, text="⏻  EXIT",
                  bg=RED, fg=BG, activebackground="#ff6666", activeforeground=BG,
                  relief="flat", font=("Courier", 9, "bold"), padx=10, pady=2,
                  command=self._safe_exit).pack(side="right", padx=(8, 0))

        # Shoulder calibration offset spinner
        tk.Label(hdr, text="Shoulder offset:", bg=BG, fg=MUTED,
                 font=("Courier", 8)).pack(side="right")
        self._shoulder_offset_var = tk.StringVar(value="0")
        offset_entry = tk.Entry(hdr, textvariable=self._shoulder_offset_var,
                                width=5, bg="#0a0d14", fg=ACCENT,
                                insertbackground=ACCENT, relief="flat",
                                highlightthickness=1, highlightbackground=BORDER,
                                highlightcolor=ACCENT,
                                font=("Courier", 10, "bold"), justify="center")
        offset_entry.pack(side="right", padx=(4, 2))
        tk.Label(hdr, text="ticks", bg=BG, fg=MUTED,
                 font=("Courier", 8)).pack(side="right")

        def _apply_offset(*_):
            global _ELBOW_OFF
            try:
                ticks = int(self._shoulder_offset_var.get())
            except ValueError:
                return
            _ELBOW_OFF = (ticks / 4096) * (2 * math.pi)
            self._on_slider_change()

        offset_entry.bind("<Return>",   _apply_offset)
        offset_entry.bind("<FocusOut>", _apply_offset)

        # +/- nudge buttons
        def _nudge(delta):
            try:
                v = int(self._shoulder_offset_var.get()) + delta
            except ValueError:
                v = delta
            self._shoulder_offset_var.set(str(v))
            _apply_offset()

        tk.Button(hdr, text="▲", bg="#1a2035", fg=ACCENT,
                  activebackground=ACCENT, activeforeground=BG,
                  relief="flat", font=("Courier", 8), width=2,
                  command=lambda: _nudge(1)).pack(side="right")
        tk.Button(hdr, text="▼", bg="#1a2035", fg=ACCENT,
                  activebackground=ACCENT, activeforeground=BG,
                  relief="flat", font=("Courier", 8), width=2,
                  command=lambda: _nudge(-1)).pack(side="right", padx=(0, 2))

        # Base gear ratio live-edit
        tk.Label(hdr, text="Base Gear Ratio:", bg=BG, fg=MUTED,
                 font=("Courier", 8)).pack(side="right", padx=(20, 4))
        self._gear_ratio_var = tk.StringVar(value=str(BASE_GEAR_RATIO))
        gear_entry = tk.Entry(hdr, textvariable=self._gear_ratio_var,
                              width=6, bg="#0a0d14", fg=YELLOW,
                              insertbackground=ACCENT, relief="flat",
                              highlightthickness=1, highlightbackground=BORDER,
                              highlightcolor=YELLOW,
                              font=("Courier", 9, "bold"), justify="right")
        gear_entry.pack(side="right", padx=(0, 2))

        def _apply_gear_ratio(*_):
            global BASE_GEAR_RATIO
            try:
                v = float(self._gear_ratio_var.get())
                if v > 0:
                    BASE_GEAR_RATIO = v
            except ValueError:
                pass

        gear_entry.bind("<Return>",   _apply_gear_ratio)
        gear_entry.bind("<FocusOut>", _apply_gear_ratio)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=20)

        # Body
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=14)

        # Left panel — wrapped in a scrollable canvas so it works on small screens
        ctrl_outer = tk.Frame(body, bg=PANEL,
                              highlightthickness=1, highlightbackground=BORDER)
        ctrl_outer.pack(side="left", fill="y", padx=(0, 14))

        ctrl_canvas = tk.Canvas(ctrl_outer, bg=PANEL, highlightthickness=0, width=330)
        ctrl_canvas.pack(side="left", fill="both", expand=True)

        ctrl_scroll = tk.Scrollbar(ctrl_outer, orient="vertical",
                                   command=ctrl_canvas.yview,
                                   bg=BORDER, troughcolor=BG, width=10)
        ctrl_scroll.pack(side="right", fill="y")
        ctrl_canvas.configure(yscrollcommand=ctrl_scroll.set)

        ctrl = tk.Frame(ctrl_canvas, bg=PANEL, padx=18, pady=18)
        ctrl_win = ctrl_canvas.create_window((0, 0), window=ctrl, anchor="nw")

        def _ctrl_configure(e):
            ctrl_canvas.configure(scrollregion=ctrl_canvas.bbox("all"))
        def _ctrl_canvas_resize(e):
            ctrl_canvas.itemconfig(ctrl_win, width=e.width)

        ctrl.bind("<Configure>", _ctrl_configure)
        ctrl_canvas.bind("<Configure>", _ctrl_canvas_resize)

        # Mouse-wheel scrolling on the left panel
        def _on_mousewheel(e):
            ctrl_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        ctrl_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        ctrl_canvas.bind_all("<Button-4>", lambda e: ctrl_canvas.yview_scroll(-1, "units"))
        ctrl_canvas.bind_all("<Button-5>", lambda e: ctrl_canvas.yview_scroll( 1, "units"))

        tk.Label(ctrl, text="TARGET POSITION", bg=PANEL, fg=ACCENT,
                 font=("Courier", 11, "bold")).pack(anchor="w", pady=(0, 12))

        self._sliders    = {}
        self._val_labels = {}

        axes = [
            ("X",   -0.44,  0.44, 0.22, "m"),
            ("Y",   -0.30,  0.30, 0.00, "m"),
            ("Z",    0.05,  0.44, 0.22, "m"),
            ("Roll", -180,  180,  0.00, "°"),
        ]
        for args in axes:
            self._make_slider(ctrl, *args)

        # ── Add Waypoint & Move button ─────────────────────────────────────────
        tk.Frame(ctrl, bg=BORDER, height=1).pack(fill="x", pady=(10, 6))
        self._add_wp_btn = tk.Button(
            ctrl, text="💾  SAVE & GOTO POSITION  (Space)",
            bg="#1a2035", fg=MUTED,
            activebackground=ACCENT, activeforeground=BG,
            relief="flat", font=("Courier", 10, "bold"),
            pady=6,
            command=self._add_waypoint_from_sliders)
        self._add_wp_btn.pack(fill="x", pady=(0, 4))
        self._slider_reachable = False   # track reachability for button guard

        # ── Hand panel ────────────────────────────────────────────────────────
        tk.Frame(ctrl, bg=BORDER, height=1).pack(fill="x", pady=12)
        tk.Label(ctrl, text="HAND  (ID 15)", bg=PANEL, fg=PURPLE,
                 font=("Courier", 9, "bold")).pack(anchor="w", pady=(0, 6))

        # Position slider (0–8191 ticks = 2 full rotations)
        hand_pos_frame = tk.Frame(ctrl, bg=PANEL)
        hand_pos_frame.pack(fill="x", pady=3)
        hand_pos_top = tk.Frame(hand_pos_frame, bg=PANEL)
        hand_pos_top.pack(fill="x")
        tk.Label(hand_pos_top, text="POS", bg=PANEL, fg=YELLOW,
                 font=("Courier", 11, "bold"), width=5, anchor="w").pack(side="left")
        self._hand_pos_var = tk.DoubleVar(value=0)
        self._hand_pos_entry_var = tk.StringVar(value="0")
        hand_pos_entry = tk.Entry(hand_pos_top, textvariable=self._hand_pos_entry_var,
                                   width=8, bg="#0a0d14", fg=TEXT,
                                   insertbackground=ACCENT, relief="flat",
                                   highlightthickness=1, highlightbackground=BORDER,
                                   highlightcolor=PURPLE,
                                   font=("Courier", 10, "bold"), justify="right")
        hand_pos_entry.pack(side="right", padx=(4, 0))
        tk.Label(hand_pos_top, text="ticks", bg=PANEL, fg=MUTED,
                 font=("Courier", 9)).pack(side="right")
        ttk.Scale(hand_pos_frame, from_=0, to=8191,
                  variable=self._hand_pos_var, orient="horizontal",
                  length=280).pack(fill="x", pady=2)
        tk.Label(hand_pos_frame, text="0  ──────────────  8191  (2 rotations)",
                 bg=PANEL, fg=MUTED, font=("Courier", 7)).pack(anchor="w")

        # Current limit slider (0–1 A, stored internally as mA ticks)
        hand_cur_frame = tk.Frame(ctrl, bg=PANEL)
        hand_cur_frame.pack(fill="x", pady=3)
        hand_cur_top = tk.Frame(hand_cur_frame, bg=PANEL)
        hand_cur_top.pack(fill="x")
        tk.Label(hand_cur_top, text="CUR", bg=PANEL, fg=RED,
                 font=("Courier", 11, "bold"), width=5, anchor="w").pack(side="left")
        self._hand_cur_var = tk.DoubleVar(value=0.1)   # amps
        self._hand_cur_entry_var = tk.StringVar(value="0.100")
        hand_cur_entry = tk.Entry(hand_cur_top, textvariable=self._hand_cur_entry_var,
                                   width=8, bg="#0a0d14", fg=TEXT,
                                   insertbackground=ACCENT, relief="flat",
                                   highlightthickness=1, highlightbackground=BORDER,
                                   highlightcolor=RED,
                                   font=("Courier", 10, "bold"), justify="right")
        hand_cur_entry.pack(side="right", padx=(4, 0))
        tk.Label(hand_cur_top, text="A", bg=PANEL, fg=MUTED,
                 font=("Courier", 9)).pack(side="right")
        ttk.Scale(hand_cur_frame, from_=0.0, to=1.0,
                  variable=self._hand_cur_var, orient="horizontal",
                  length=280).pack(fill="x", pady=2)
        tk.Label(hand_cur_frame, text="0.0 A  ──────────  1.0 A",
                 bg=PANEL, fg=MUTED, font=("Courier", 7)).pack(anchor="w")

        # Wire traces
        def _hand_pos_to_entry(*_):
            v = int(self._hand_pos_var.get())
            self._hand_pos_entry_var.set(str(v))
            self._on_hand_change()
        self._hand_pos_var.trace_add("write", _hand_pos_to_entry)

        def _hand_pos_entry_to_slider(*_):
            try:
                v = max(0, min(2048, int(self._hand_pos_entry_var.get())))
                self._hand_pos_var.set(v)
            except ValueError:
                pass
        hand_pos_entry.bind("<Return>",   _hand_pos_entry_to_slider)
        hand_pos_entry.bind("<FocusOut>", _hand_pos_entry_to_slider)

        def _hand_cur_to_entry(*_):
            v = self._hand_cur_var.get()
            self._hand_cur_entry_var.set(f"{v:.3f}")
            self._on_hand_change()
        self._hand_cur_var.trace_add("write", _hand_cur_to_entry)

        def _hand_cur_entry_to_slider(*_):
            try:
                v = max(0.0, min(1.0, float(self._hand_cur_entry_var.get())))
                self._hand_cur_var.set(v)
            except ValueError:
                pass
        hand_cur_entry.bind("<Return>",   _hand_cur_entry_to_slider)
        hand_cur_entry.bind("<FocusOut>", _hand_cur_entry_to_slider)

        # Close / Open buttons + keybind
        hand_btn_row = tk.Frame(ctrl, bg=PANEL)
        hand_btn_row.pack(fill="x", pady=(6, 0))

        self._hand_close_btn = tk.Button(
            hand_btn_row, text="🖐  OPEN  (K)",
            bg=PURPLE, fg=BG,
            activebackground="#e0b0ff", activeforeground=BG,
            relief="flat", font=("Courier", 9, "bold"), padx=10, pady=4,
            command=self._hand_close)
        self._hand_close_btn.pack(side="left", padx=(0, 6))

        tk.Button(
            hand_btn_row, text="✊  CLOSE",
            bg="#1a2035", fg=TEXT,
            activebackground=ACCENT, activeforeground=BG,
            relief="flat", font=("Courier", 9, "bold"), padx=10, pady=4,
            command=self._hand_open).pack(side="left")

        # Right panel: canvas
        cf = tk.Frame(body, bg=PANEL,
                       highlightthickness=1, highlightbackground=BORDER)
        cf.pack(side="left", fill="both", expand=True)

        tk.Label(cf, text="ARM VISUALISER  —  SIDE VIEW  (X-Z PLANE)",
                 bg=PANEL, fg=MUTED,
                 font=("Courier", 8, "bold"), pady=7).pack()

        self.canvas = ArmCanvas(cf)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # ── Teach / Replay panel ─────────────────────────────────────────────
        tr = tk.Frame(self.root, bg=PANEL,
                       highlightthickness=1, highlightbackground=BORDER)
        tr.pack(fill="both", padx=20, pady=(10, 0))

        def _mk_btn(parent, text, fg, cmd, bg="#1a2035"):
            return tk.Button(parent, text=text, bg=bg, fg=fg,
                             activebackground=fg, activeforeground=BG,
                             relief="flat", font=("Courier", 9, "bold"),
                             padx=8, pady=3, command=cmd)

        def _mk_entry(parent, var, width=6):
            return tk.Entry(parent, textvariable=var, width=width,
                            bg="#0a0d14", fg=TEXT, insertbackground=ACCENT,
                            relief="flat", highlightthickness=1,
                            highlightbackground=BORDER, highlightcolor=ACCENT,
                            font=("Courier", 10, "bold"), justify="right")

        # ── LEFT: teach controls + waypoint list ──────────────────────────────
        left = tk.Frame(tr, bg=PANEL, padx=14, pady=10)
        left.pack(side="left", fill="both", expand=True)

        # Header row
        hdr = tk.Frame(left, bg=PANEL)
        hdr.pack(fill="x")
        tk.Label(hdr, text="TEACH  &  WAYPOINTS", bg=PANEL, fg=ACCENT,
                 font=("Courier", 10, "bold")).pack(side="left")
        tk.Label(hdr,
                 text="Space = sliders  |  T = teach/pose  |  H = hand  |  Z = calibrate",
                 bg=PANEL, fg=MUTED, font=("Courier", 7)).pack(side="left", padx=8)

        # File buttons (right-aligned in header)
        file_row = tk.Frame(hdr, bg=PANEL)
        file_row.pack(side="right")
        _mk_btn(file_row, "💾 SAVE", ACCENT,  self._save_waypoints).pack(side="left", padx=(0,4))
        _mk_btn(file_row, "📂 LOAD", YELLOW,  self._load_waypoints).pack(side="left")

        # Record / clear / special buttons — all on one row
        btn_row = tk.Frame(left, bg=PANEL)
        btn_row.pack(fill="x", pady=(6, 4))
        self._record_btn = _mk_btn(btn_row, "⏺  RECORD  (T)", TEXT, self._record_waypoint)
        self._record_btn.pack(side="left", padx=(0, 6))
        _mk_btn(btn_row, "⏹  STOP",   RED,    self._insert_stop,  bg="#1a2035").pack(side="left", padx=(0, 6))
        _mk_btn(btn_row, "⏸  WAIT",   YELLOW, self._insert_wait,  bg="#1a2035").pack(side="left", padx=(0, 6))
        _mk_btn(btn_row, "✕  CLEAR",  RED,    self._clear_waypoints).pack(side="left")

        # Waypoint listbox
        list_frame = tk.Frame(left, bg=PANEL)
        list_frame.pack(fill="both", expand=True, pady=(4, 0))

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", bg=BORDER,
                                  troughcolor=BG, width=10)
        scrollbar.pack(side="right", fill="y")

        self._wp_listbox = tk.Listbox(
            list_frame,
            bg="#0a0d14", fg=TEXT, selectbackground=ACCENT, selectforeground=BG,
            font=("Courier", 9), relief="flat", height=5,
            highlightthickness=1, highlightbackground=BORDER,
            activestyle="none",
            yscrollcommand=scrollbar.set)
        self._wp_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._wp_listbox.yview)

        # Per-item edit buttons
        edit_row = tk.Frame(left, bg=PANEL)
        edit_row.pack(fill="x", pady=(4, 0))
        _mk_btn(edit_row, "▲ UP",     TEXT,   self._wp_move_up).pack(side="left", padx=(0,3))
        _mk_btn(edit_row, "▼ DOWN",   TEXT,   self._wp_move_down).pack(side="left", padx=(0,3))
        _mk_btn(edit_row, "✎ EDIT",   YELLOW, self._wp_edit).pack(side="left", padx=(0,3))
        _mk_btn(edit_row, "✕ DELETE", RED,    self._wp_delete).pack(side="left")

        self._wp_status = tk.Label(left, text="No waypoints", bg=PANEL,
                                    fg=MUTED, font=("Courier", 8))
        self._wp_status.pack(anchor="w", pady=(3, 0))

        # ── DIVIDER ───────────────────────────────────────────────────────────
        tk.Frame(tr, bg=BORDER, width=1).pack(side="left", fill="y", padx=8)

        # ── RIGHT: replay controls ────────────────────────────────────────────
        right = tk.Frame(tr, bg=PANEL, padx=14, pady=10)
        right.pack(side="left", fill="y")

        tk.Label(right, text="REPLAY", bg=PANEL, fg=YELLOW,
                 font=("Courier", 10, "bold")).pack(anchor="w")

        speed_row = tk.Frame(right, bg=PANEL)
        speed_row.pack(anchor="w", pady=(6, 2))
        tk.Label(speed_row, text="Speed:", bg=PANEL, fg=MUTED,
                 font=("Courier", 8)).pack(side="left")
        self._speed_var = tk.StringVar(value="400")
        _mk_entry(speed_row, self._speed_var).pack(side="left", padx=(6,4))
        tk.Label(speed_row, text="ticks/sec", bg=PANEL, fg=MUTED,
                 font=("Courier", 8)).pack(side="left")

        gap_row = tk.Frame(right, bg=PANEL)
        gap_row.pack(anchor="w", pady=(0, 8))
        tk.Label(gap_row, text="Hold time:", bg=PANEL, fg=MUTED,
                 font=("Courier", 8)).pack(side="left")
        self._gap_var = tk.StringVar(value="0")
        _mk_entry(gap_row, self._gap_var).pack(side="left", padx=(6,4))
        tk.Label(gap_row, text="sec", bg=PANEL, fg=MUTED,
                 font=("Courier", 8)).pack(side="left")

        self._replay_btn = _mk_btn(right, "▶  PLAY", YELLOW, self._toggle_replay)
        self._replay_btn.pack(anchor="w")

        self._replay_status = tk.Label(right, text="—", bg=PANEL,
                                        fg=MUTED, font=("Courier", 8))
        self._replay_status.pack(anchor="w", pady=(6, 0))

        # Space = add waypoint from sliders and move arm
        def _on_space(e):
            self._add_waypoint_from_sliders()
            return "break"
        self.root.bind_all("<space>", _on_space)
        self.root.bind_all("<t>", lambda e: self._record_waypoint())
        self.root.bind_all("<T>", lambda e: self._record_waypoint())
        self.root.bind_all("<h>", lambda e: self._teach_hand_toggle())
        self.root.bind_all("<H>", lambda e: self._teach_hand_toggle())
        self.root.bind_all("<k>", lambda e: self._hand_close())
        self.root.bind_all("<K>", lambda e: self._hand_close())

        # Status bar
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=20)
        sb = tk.Frame(self.root, bg=BG, pady=5)
        sb.pack(fill="x", padx=20)
        self.status_lbl = tk.Label(sb, text="Initialising…",
                                    bg=BG, fg=MUTED, font=("Courier", 8))
        self.status_lbl.pack(side="left")

    def _make_slider(self, parent, name, lo, hi, init, unit):
        frame = tk.Frame(parent, bg=PANEL)
        frame.pack(fill="x", pady=5)

        # ── Row: axis label + entry box ───────────────────────────────────────
        top = tk.Frame(frame, bg=PANEL)
        top.pack(fill="x")
        tk.Label(top, text=name, bg=PANEL, fg=YELLOW,
                 font=("Courier", 11, "bold"), width=5, anchor="w").pack(side="left")

        # Entry box – typed value
        entry_var = tk.StringVar(value=f"{init:.3f}" if unit == "m" else f"{init:.1f}")
        entry = tk.Entry(top, textvariable=entry_var, width=8,
                         bg="#0a0d14", fg=TEXT, insertbackground=ACCENT,
                         relief="flat", highlightthickness=1,
                         highlightbackground=BORDER, highlightcolor=ACCENT,
                         font=("Courier", 10, "bold"), justify="right")
        entry.pack(side="right", padx=(4, 0))
        tk.Label(top, text=unit, bg=PANEL, fg=MUTED,
                 font=("Courier", 9)).pack(side="right")

        var = tk.DoubleVar(value=init)
        s = ttk.Scale(frame, from_=lo, to=hi, variable=var, orient="horizontal", length=280)
        s.pack(fill="x", pady=2)

        tk.Label(frame,
                 text=f"{lo}{unit}  ──────────────  {hi}{unit}",
                 bg=PANEL, fg=MUTED, font=("Courier", 7)).pack(anchor="w")

        self._sliders[name] = var
        self._val_labels[name] = entry_var   # reuse _val_labels to store entry StringVar

        # Slider → entry: update text when slider moves
        def _slider_to_entry(*_):
            v = var.get()
            entry_var.set(f"{v:.3f}" if unit == "m" else f"{v:.1f}")
            self._on_slider_change()
        var.trace_add("write", _slider_to_entry)

        # Entry → slider: parse typed value on Enter or focus-out
        def _entry_to_slider(*_):
            try:
                v = float(entry_var.get())
                v = max(lo, min(hi, v))   # clamp to valid range
                var.set(v)
            except ValueError:
                pass   # ignore invalid input until corrected
        entry.bind("<Return>",   _entry_to_slider)
        entry.bind("<FocusOut>", _entry_to_slider)

    # ── Hand callback ────────────────────────────────────────────────────────────
    def _on_hand_change(self):
        pos_ticks = int(self._hand_pos_var.get())
        amps      = self._hand_cur_var.get()
        cur_ticks = int(round(amps * 1000.0 / CURRENT_UNIT_MA))
        cur_ticks = max(0, min(1193, cur_ticks))   # 1193 ≈ 1A / 2.69mA per tick (XM430 limit)
        with self._lock:
            self._hand_cmd = (pos_ticks, cur_ticks)

    def _hand_close(self):
        """Button labelled OPEN — drives hand to open position (HAND_OPEN ticks)."""
        cur_ticks = int(round(self._hand_cur_var.get() * 1000.0 / CURRENT_UNIT_MA))
        cur_ticks = max(0, min(1193, cur_ticks))
        with self._lock:
            self._hand_cmd = (HAND_OPEN, cur_ticks)
        self._hand_pos_var.set(max(0, min(8191, HAND_OPEN)))
        self._hand_close_btn.config(bg="#e0b0ff", fg=BG)
        self.root.after(300, lambda: self._hand_close_btn.config(bg=PURPLE, fg=BG))
        # Record waypoint with hand state
        self._record_hand_waypoint(HAND_OPEN, "OPEN")

    def _hand_open(self):
        """Button labelled CLOSE — drives hand to closed position (HAND_CLOSED ticks)."""
        cur_ticks = int(round(self._hand_cur_var.get() * 1000.0 / CURRENT_UNIT_MA))
        cur_ticks = max(0, min(1193, cur_ticks))
        with self._lock:
            self._hand_cmd = (HAND_CLOSED, cur_ticks)
        self._hand_pos_var.set(max(0, min(8191, HAND_CLOSED)))
        # Record waypoint with hand state
        self._record_hand_waypoint(HAND_CLOSED, "CLOSED")

    def _record_hand_waypoint(self, hand_ticks: int, state_label: str):
        """Record a waypoint at the current arm position with the given hand state.
        Called by the OPEN and CLOSE buttons so hand transitions are logged in the list."""
        if self._replaying:
            return
        with self._lock:
            cmd = self._cmd
        if cmd is not None and len(cmd) >= 4:
            # _cmd = (base, shoulder, elbow, wrist)
            arm_pos  = (cmd[1], cmd[2], cmd[3])
            base_pos = cmd[0]
            self._waypoints.append(arm_pos + (base_pos, hand_ticks))
            self._refresh_listbox()
            self._wp_listbox.selection_clear(0, tk.END)
            self._wp_listbox.selection_set(tk.END)
            self._wp_listbox.see(tk.END)
            self._wp_status.config(
                text=f"Hand → {state_label}  — WP {len(self._waypoints)} added",
                fg=YELLOW)

    # ── Negative-X mode ──────────────────────────────────────────────────────────
    # ── Slider / IK callback ──────────────────────────────────────────────────
    def _sync_sliders_to_hardware(self):
        """On startup: set sliders to match physical arm position."""
        if self.hw_ok and self._cmd is not None:
            cmd = self._cmd
            s = cmd[1] if len(cmd) > 1 else 2048
            e = cmd[2] if len(cmd) > 2 else 2048
            w = cmd[3] if len(cmd) > 3 else 2048
            b = cmd[0] if len(cmd) > 0 else self._base_home_ticks
            # Startup direction is defined as our X-axis reference (t1_startup = 0).
            # All base rotations are relative to wherever the arm was at power-on.
            self._base_t1_startup = 0.0
            self._sync_ui_to_ticks(s, e, w, b)
        self._on_slider_change()

    def _on_slider_change(self):
        """Update canvas preview from sliders — does NOT move the arm or write _cmd."""
        if self._ui_sync_in_progress:
            return
        x    = self._sliders["X"].get()
        y    = self._sliders["Y"].get()
        z    = self._sliders["Z"].get()
        roll = self._sliders["Roll"].get()

        sols = inverse_kinematics(x, y, z, math.radians(roll))

        if sols:
            t1, t2, t3, t4 = sols[0]
            self.canvas.set_pose((t1, t2, t3, t4), True)
            self._slider_reachable = True
            self._add_wp_btn.config(bg=ACCENT, fg=BG)
            # Show geometric angles: sa = shoulder from vertical, ea = forearm from horizontal
            sa_deg = 90.0 - math.degrees(t2 - _ELBOW_OFF)
            ea_deg = math.degrees(t2 - _ELBOW_OFF + t3)
            self.status_lbl.config(
                text=f"Preview: X={x:.3f}  Y={y:.3f}  Z={z:.3f}  "
                     f"θ1={math.degrees(t1):.1f}°  "
                     f"shoulder={sa_deg:.1f}° from vert  "
                     f"elbow={ea_deg:.1f}° from horiz  "
                     f"— press SAVE & GOTO to commit",
                fg=MUTED)
        else:
            self.canvas.set_pose(None, False)
            self._slider_reachable = False
            self._add_wp_btn.config(bg="#1a2035", fg=MUTED)
            self.status_lbl.config(
                text="⚠  Position unreachable — target outside workspace", fg=RED)

    def _add_waypoint_from_sliders(self):
        """Compute IK from slider values, add to waypoint list, and move the arm."""
        if self._replaying or self._teach_mode or not self._slider_reachable:
            return
        x    = self._sliders["X"].get()
        y    = self._sliders["Y"].get()
        z    = self._sliders["Z"].get()
        roll = self._sliders["Roll"].get()

        sols = inverse_kinematics(x, y, z, math.radians(roll))
        if not sols:
            self.status_lbl.config(
                text="⚠  Position unreachable — cannot add waypoint", fg=RED)
            return

        t1, t2, t3, t4 = sols[0]
        t2_hw = t2
        t3_hw = t3

        # Base: convert target t1 to motor ticks relative to startup reference.
        # Normalise delta to [-180, +180] so the base always takes the shortest
        # path and never jumps 360° when atan2 wraps at ±π.
        delta_t1_deg = math.degrees(t1 - self._base_t1_startup)
        delta_t1_deg = (delta_t1_deg + 180.0) % 360.0 - 180.0   # wrap to ±180°
        pb = int(round(self._base_home_ticks + delta_t1_deg * TPD * BASE_GEAR_RATIO))
        ps = angle_to_dxl(math.degrees(t2_hw))
        pe = angle_to_dxl(math.degrees(t3_hw) + math.degrees(_ELBOW_OFF))
        pw = angle_to_dxl(math.degrees(t4))

        # Advance the base reference to the new position so future deltas are
        # always computed relative to the last committed waypoint — this lets
        # the base rotate continuously beyond ±180° without wrapping artifacts.
        self._base_t1_startup = t1
        self._base_home_ticks = pb

        # Waypoint stored as (shoulder, elbow, wrist, base, hand)
        arm_pos = (ps, pe, pw, pb)
        with self._lock:
            hand_ticks = self._hand_cmd[0] if self._hand_cmd else HAND_OPEN

        # Add to waypoint list first
        self._waypoints.append(arm_pos + (hand_ticks,))
        self._refresh_listbox()
        self._wp_listbox.selection_clear(0, tk.END)
        self._wp_listbox.selection_set(tk.END)
        self._wp_listbox.see(tk.END)

        # Move arm smoothly in background using the same interpolation as replay
        try:
            speed = float(self._speed_var.get())
            if speed <= 0:
                speed = 200.0
        except ValueError:
            speed = 200.0

        def _do_move():
            self._move_to_ticks(arm_pos, speed)
        threading.Thread(target=_do_move, daemon=True).start()

        self.canvas.set_pose((t1, t2, t3, t4), True)
        self.status_lbl.config(
            text=f"✓ Waypoint {len(self._waypoints)} added — "
                 f"X={x:.3f}  Y={y:.3f}  Z={z:.3f}  "
                 f"θ2={math.degrees(t2):.1f}°  θ3={math.degrees(t3):.1f}°",
            fg=ACCENT)

    # ── Teach / Replay ───────────────────────────────────────────────────────────
    def _read_present_positions(self):
        """Read current tick positions from all servos.
        Returns (shoulder_ticks, elbow_ticks, wrist_ticks, base_ticks) or None on error."""
        if not self.hw_ok:
            return None
        try:
            with self._lock:
                # ── TTL motors (shoulder, elbow, wrist) ───────────────────────
                results = []
                for did in self.ids:
                    val, res, err = self.pk.read4ByteTxRx(
                        self.ph, did, ADDR_PRESENT_POSITION)
                    if res != COMM_SUCCESS or err != 0:
                        return None
                    if val > 0x7FFFFFFF:
                        val -= 0x100000000
                    results.append(max(DXL_MIN, min(DXL_MAX, val)))

                # ── Base motor (RS485) — read raw multi-turn ticks separately ──
                val, res, err = self.pk.read4ByteTxRx(
                    self.ph, ID_BASE, ADDR_PRESENT_POSITION)
                if res != COMM_SUCCESS or err != 0:
                    return None
                if val > 0x7FFFFFFF:
                    val -= 0x100000000
                base_ticks = val   # raw multi-turn ticks — do not clamp

            # Return as (shoulder, elbow, wrist, base)
            return tuple(results) + (base_ticks,)
        except Exception:
            return None

    def _torque_off(self):
        """Disable torque on all motors with a small delay between each
        to ensure the bus is clear for each packet."""
        if not self.hw_ok:
            return
        with self._lock:
            all_ids = self.ids + [ID_BASE]
            if self.hand_ok:
                all_ids = all_ids + [ID_HAND]
            for did in all_ids:
                self.pk.write1ByteTxRx(self.ph, did, ADDR_TORQUE_ENABLE, 0)
                time.sleep(0.01)

    def _torque_on(self):
        """Re-enable torque on all motors, writing goal = present first.
        Runs in a background thread since it needs reads before writes."""
        if not self.hw_ok:
            return
        with self._lock:
            # TTL motors — read present, sync write goal, then enable
            present = []
            for did in self.ids:
                val, res, err = self.pk.read4ByteTxRx(
                    self.ph, did, ADDR_PRESENT_POSITION)
                if val > 0x7FFFFFFF:
                    val -= 0x100000000
                present.append(max(DXL_MIN, min(DXL_MAX, val)))
            try:
                sync_write_positions(self.gsw, self.ids, present)
            except Exception:
                pass
            for did in self.ids:
                self.pk.write1ByteTxRx(self.ph, did, ADDR_TORQUE_ENABLE, 1)
            # Base motor — read present, write goal, enable
            val, res, err = self.pk.read4ByteTxRx(
                self.ph, ID_BASE, ADDR_PRESENT_POSITION)
            if val > 0x7FFFFFFF:
                val -= 0x100000000
            base_present = max(0, min(65535, val))
            self.pk.write4ByteTxRx(
                self.ph, ID_BASE, ADDR_GOAL_POSITION, base_present)
            self.pk.write1ByteTxRx(self.ph, ID_BASE, ADDR_TORQUE_ENABLE, 1)
            # Hand motor
            if self.hand_ok:
                self.pk.write1ByteTxRx(self.ph, ID_HAND, ADDR_TORQUE_ENABLE, 1)

    def _set_torque(self, enabled: bool):
        """Convenience wrapper — routes to _torque_on/_torque_off."""
        if enabled:
            self._torque_on()
        else:
            self._torque_off()

    def _record_waypoint(self):
        """First press: depower motors and wait. Second press: read position + re-enable."""
        if self._replaying:
            return
        # Debounce: ignore repeated keydown events (key held or double-fire)
        now = time.perf_counter()
        if hasattr(self, '_last_record_time') and now - self._last_record_time < 0.4:
            return
        self._last_record_time = now

        if not self._teach_mode:
            # ── First press: go limp ──────────────────────────────────────────
            # Hold the lock for the entire operation: set _teach_mode, null
            # _cmd, and send all torque-off writes without ever releasing it.
            # This guarantees the comms loop cannot send anything in between.
            with self._lock:
                self._teach_mode = True
                self._cmd = None
                if self.hw_ok:
                    print("[TEACH] Sending torque-off...")
                    # Send torque-off to each motor individually with a small
                    # delay between each so the bus is clear for each packet.
                    # Base (RS485) is sent last as it is on a different protocol.
                    all_ids = self.ids + [ID_BASE]
                    if self.hand_ok:
                        all_ids = all_ids + [ID_HAND]
                    for did in all_ids:
                        res, err = self.pk.write1ByteTxRx(
                            self.ph, did, ADDR_TORQUE_ENABLE, 0)
                        print(f"[TEACH]   ID {did}: res={res} err={err}")
                        time.sleep(0.01)   # 10 ms gap between motors
                    print("[TEACH] Torque-off complete.")
            self._record_btn.config(fg=RED, text="● POSING…  (T to capture)")
            self._wp_status.config(
                text="Arm is depowered — pose it, then press T to capture",
                fg=YELLOW)
            # Start live canvas updates so the user can see angles while posing
            self.root.after(100, self._poll_teach_pose)
        else:
            # ── Second press: read position, re-enable, store waypoint ────────
            self._teach_mode = False
            self._finish_record()

    # ── Listbox helpers ───────────────────────────────────────────────────────
    def _refresh_listbox(self):
        """Rebuild the listbox from self._waypoints.
        Entries are either position tuples or special dicts {type:'STOP'} / {type:'WAIT', seconds:n}.
        """
        self._wp_listbox.delete(0, tk.END)
        for i, wp in enumerate(self._waypoints):
            if isinstance(wp, dict):
                t = wp.get("type", "?")
                if t == "STOP":
                    row = f"  WP {i+1:02d}   ⏹  STOP"
                elif t == "WAIT":
                    row = f"  WP {i+1:02d}   ⏸  WAIT  {wp.get('seconds', 1.0):.1f} s"
                else:
                    row = f"  WP {i+1:02d}   ? {t}"
            else:
                b_str = f"   B={wp[3]:4d}" if len(wp) > 3 else ""
                if len(wp) > 4:
                    h_label = "OPEN" if wp[4] <= (HAND_OPEN + HAND_CLOSED) // 2 else "CLOSED"
                    h_str = f"   H={h_label}"
                else:
                    h_str = ""
                row = f"  WP {i+1:02d}   S={wp[0]:4d}   E={wp[1]:4d}   W={wp[2]:4d}{b_str}{h_str}"
            self._wp_listbox.insert(tk.END, row)
        n = len(self._waypoints)
        self._wp_status.config(
            text=f"{n} waypoint{'s' if n != 1 else ''}" if n else "No waypoints",
            fg=TEXT if n else MUTED)

    def _selected_idx(self):
        sel = self._wp_listbox.curselection()
        return sel[0] if sel else None

    def _wp_move_up(self):
        i = self._selected_idx()
        if i is None or i == 0:
            return
        self._waypoints[i-1], self._waypoints[i] = self._waypoints[i], self._waypoints[i-1]
        self._refresh_listbox()
        self._wp_listbox.selection_set(i - 1)
        self._wp_listbox.see(i - 1)

    def _wp_move_down(self):
        i = self._selected_idx()
        if i is None or i >= len(self._waypoints) - 1:
            return
        self._waypoints[i], self._waypoints[i+1] = self._waypoints[i+1], self._waypoints[i]
        self._refresh_listbox()
        self._wp_listbox.selection_set(i + 1)
        self._wp_listbox.see(i + 1)

    def _wp_delete(self):
        i = self._selected_idx()
        if i is None:
            return
        del self._waypoints[i]
        self._refresh_listbox()
        # Keep selection on same index (or last item)
        new_i = min(i, len(self._waypoints) - 1)
        if new_i >= 0:
            self._wp_listbox.selection_set(new_i)

    def _wp_edit(self):
        """Open a dialog to edit the selected waypoint — handles position, STOP, and WAIT."""
        i = self._selected_idx()
        if i is None:
            return
        wp = self._waypoints[i]

        dlg = tk.Toplevel(self.root)
        dlg.title(f"Edit Waypoint {i+1}")
        dlg.configure(bg=PANEL)
        dlg.resizable(False, False)
        dlg.grab_set()

        def _lbl(parent, text, fg=MUTED):
            return tk.Label(parent, text=text, bg=PANEL, fg=fg, font=("Courier", 9))

        def _entry_dlg(parent, var):
            return tk.Entry(parent, textvariable=var, width=10,
                            bg="#0a0d14", fg=TEXT, insertbackground=ACCENT,
                            relief="flat", highlightthickness=1,
                            highlightbackground=BORDER, highlightcolor=ACCENT,
                            font=("Courier", 11, "bold"), justify="center")

        tk.Label(dlg, text=f"  Waypoint {i+1}  ", bg=PANEL, fg=ACCENT,
                 font=("Courier", 11, "bold")).grid(row=0, column=0, columnspan=2,
                                                    pady=(12, 8), padx=16)

        # ── Type selector ──────────────────────────────────────────────────────
        cur_type = wp.get("type", "POSITION") if isinstance(wp, dict) else "POSITION"
        type_var = tk.StringVar(value=cur_type)

        type_row = tk.Frame(dlg, bg=PANEL)
        type_row.grid(row=1, column=0, columnspan=2, pady=(0, 8), padx=12)
        _lbl(type_row, "Type: ").pack(side="left")
        for t in ("POSITION", "STOP", "WAIT"):
            tk.Radiobutton(type_row, text=t, variable=type_var, value=t,
                           bg=PANEL, fg=TEXT, selectcolor=PANEL,
                           activebackground=PANEL, activeforeground=ACCENT,
                           font=("Courier", 9, "bold"),
                           command=lambda: _refresh_fields()).pack(side="left", padx=4)

        # ── Dynamic fields frame ───────────────────────────────────────────────
        fields_frame = tk.Frame(dlg, bg=PANEL)
        fields_frame.grid(row=2, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        # Vars for POSITION
        s_var = tk.StringVar(value=str(wp[0]) if not isinstance(wp, dict) else "2048")
        e_var = tk.StringVar(value=str(wp[1]) if not isinstance(wp, dict) else "2048")
        w_var = tk.StringVar(value=str(wp[2]) if not isinstance(wp, dict) and len(wp) > 2 else "2048")
        b_var = tk.StringVar(value=str(wp[3]) if not isinstance(wp, dict) and len(wp) > 3 else "0")
        h_var = tk.StringVar(value=str(wp[4]) if not isinstance(wp, dict) and len(wp) > 4 else str(HAND_OPEN))

        # Var for WAIT
        secs_var = tk.StringVar(value=str(wp.get("seconds", 1.0)) if isinstance(wp, dict) else "1.0")

        def _refresh_fields():
            for w in fields_frame.winfo_children():
                w.destroy()
            t = type_var.get()
            if t == "POSITION":
                for row_i, (label, var) in enumerate([
                    ("Shoulder (S):", s_var),
                    ("Elbow (E):",    e_var),
                    ("Wrist (W):",    w_var),
                    ("Base (B):",     b_var),
                    ("Hand (H):",     h_var),
                ]):
                    _lbl(fields_frame, label).grid(row=row_i, column=0, sticky="e", padx=(0,4), pady=3)
                    _entry_dlg(fields_frame, var).grid(row=row_i, column=1, pady=3)
                _lbl(fields_frame, "0–4095 ticks", TEXT).grid(row=5, column=0, columnspan=2, pady=(4,0))
            elif t == "STOP":
                _lbl(fields_frame, "Replay will stop at this point.", TEXT).grid(
                    row=0, column=0, columnspan=2, pady=12)
            elif t == "WAIT":
                _lbl(fields_frame, "Wait time (seconds):").grid(row=0, column=0, sticky="e", padx=(0,4), pady=8)
                _entry_dlg(fields_frame, secs_var).grid(row=0, column=1, pady=8)

        _refresh_fields()

        def _apply():
            t = type_var.get()
            if t == "STOP":
                self._waypoints[i] = {"type": "STOP"}
            elif t == "WAIT":
                try:
                    secs = max(0.0, float(secs_var.get()))
                except ValueError:
                    messagebox.showerror("Invalid", "Wait time must be a number.", parent=dlg)
                    return
                self._waypoints[i] = {"type": "WAIT", "seconds": secs}
            else:  # POSITION
                try:
                    s = max(DXL_MIN, min(DXL_MAX, int(s_var.get())))
                    e = max(DXL_MIN, min(DXL_MAX, int(e_var.get())))
                    w = max(DXL_MIN, min(DXL_MAX, int(w_var.get())))
                    b = int(b_var.get())
                    h = int(h_var.get())
                except ValueError:
                    messagebox.showerror("Invalid", "Position values must be integers.", parent=dlg)
                    return
                self._waypoints[i] = (s, e, w, b, h)
            self._refresh_listbox()
            self._wp_listbox.selection_set(i)
            dlg.destroy()

        btn_row = tk.Frame(dlg, bg=PANEL)
        btn_row.grid(row=3, column=0, columnspan=2, pady=(12, 12))
        tk.Button(btn_row, text="✓  APPLY", bg="#1a2035", fg=ACCENT,
                  activebackground=ACCENT, activeforeground=BG,
                  relief="flat", font=("Courier", 9, "bold"), padx=10, pady=4,
                  command=_apply).pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="✕  CANCEL", bg="#1a2035", fg=MUTED,
                  activebackground=MUTED, activeforeground=BG,
                  relief="flat", font=("Courier", 9, "bold"), padx=10, pady=4,
                  command=dlg.destroy).pack(side="left")

        dlg.bind("<Return>", lambda e: _apply())

    def _insert_stop(self):
        """Insert a STOP marker after the currently selected waypoint (or at end)."""
        i = self._selected_idx()
        insert_at = (i + 1) if i is not None else len(self._waypoints)
        self._waypoints.insert(insert_at, {"type": "STOP"})
        self._refresh_listbox()
        self._wp_listbox.selection_set(insert_at)
        self._wp_listbox.see(insert_at)
        self._wp_status.config(text=f"⏹ STOP inserted at position {insert_at+1}", fg=RED)

    def _insert_wait(self):
        """Ask for a duration then insert a WAIT marker after the selected waypoint."""
        # Quick inline dialog for wait time
        dlg = tk.Toplevel(self.root)
        dlg.title("Insert Wait")
        dlg.configure(bg=PANEL)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="  Insert WAIT  ", bg=PANEL, fg=YELLOW,
                 font=("Courier", 11, "bold")).grid(row=0, column=0, columnspan=2,
                                                    pady=(12, 4), padx=16)
        tk.Label(dlg, text="Wait time (seconds):", bg=PANEL, fg=MUTED,
                 font=("Courier", 9)).grid(row=1, column=0, sticky="e", padx=(12,4), pady=8)
        secs_var = tk.StringVar(value="2.0")
        tk.Entry(dlg, textvariable=secs_var, width=8,
                 bg="#0a0d14", fg=TEXT, insertbackground=ACCENT,
                 relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=YELLOW,
                 font=("Courier", 11, "bold"), justify="center").grid(
                     row=1, column=1, padx=(0,12), pady=8)

        def _apply():
            try:
                secs = max(0.0, float(secs_var.get()))
            except ValueError:
                messagebox.showerror("Invalid", "Must be a number.", parent=dlg)
                return
            i = self._selected_idx()
            insert_at = (i + 1) if i is not None else len(self._waypoints)
            self._waypoints.insert(insert_at, {"type": "WAIT", "seconds": secs})
            self._refresh_listbox()
            self._wp_listbox.selection_set(insert_at)
            self._wp_listbox.see(insert_at)
            self._wp_status.config(text=f"⏸ WAIT {secs:.1f}s inserted at position {insert_at+1}", fg=YELLOW)
            dlg.destroy()

        btn_row = tk.Frame(dlg, bg=PANEL)
        btn_row.grid(row=2, column=0, columnspan=2, pady=(4, 12))
        tk.Button(btn_row, text="✓  INSERT", bg="#1a2035", fg=YELLOW,
                  activebackground=YELLOW, activeforeground=BG,
                  relief="flat", font=("Courier", 9, "bold"), padx=10, pady=4,
                  command=_apply).pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="✕  CANCEL", bg="#1a2035", fg=MUTED,
                  activebackground=MUTED, activeforeground=BG,
                  relief="flat", font=("Courier", 9, "bold"), padx=10, pady=4,
                  command=dlg.destroy).pack(side="left")
        dlg.bind("<Return>", lambda e: _apply())

    # ── Save / Load ───────────────────────────────────────────────────────────
    def _save_waypoints(self):
        if not self._waypoints:
            messagebox.showwarning("Nothing to save", "Record some waypoints first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save waypoints",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        data = {
            "version": 2,
            "speed":            self._speed_var.get(),
            "hold":             self._gap_var.get(),
            "shoulder_offset":  self._shoulder_offset_var.get(),
            "waypoints": [
                wp if isinstance(wp, dict) else list(wp)
                for wp in self._waypoints
            ]
        }
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            self._wp_status.config(
                text=f"Saved {len(self._waypoints)} waypoints → {path}", fg=ACCENT)
        except Exception as ex:
            messagebox.showerror("Save failed", str(ex))

    def _load_waypoints(self):
        path = filedialog.askopenfilename(
            title="Load waypoints",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path) as f:
                data = json.load(f)
            # Back-compat: pad old 2-value waypoints; pass through dict entries unchanged
            wps = []
            for wp in data["waypoints"]:
                if isinstance(wp, dict):
                    t = wp.get("type", "")
                    if t == "STOP":
                        wps.append({"type": "STOP"})
                    elif t == "WAIT":
                        wps.append({"type": "WAIT", "seconds": float(wp.get("seconds", 1.0))})
                    # unknown dict types are silently skipped
                else:
                    wp = tuple(wp)
                    if len(wp) == 2:
                        wp = wp + (2048,)
                    if len(wp) == 3:
                        wp = wp + (0, HAND_OPEN)
                    if len(wp) == 4:
                        wp = wp + (HAND_OPEN,)
                    if len(wp) < 3 or not all(isinstance(v, (int, float)) for v in wp):
                        raise ValueError(f"Bad waypoint: {wp}")
                    wps.append(wp)
            self._waypoints = wps
            # Restore speed/hold if present
            if "speed" in data:
                self._speed_var.set(data["speed"])
            if "hold" in data:
                self._gap_var.set(data["hold"])
            if "shoulder_offset" in data:
                global _ELBOW_OFF
                self._shoulder_offset_var.set(data["shoulder_offset"])
                try:
                    _ELBOW_OFF = (int(data["shoulder_offset"]) / 4096) * (2 * math.pi)
                except (ValueError, TypeError):
                    pass
            self._refresh_listbox()
            self._wp_status.config(
                text=f"Loaded {len(wps)} waypoints from {path}", fg=YELLOW)
        except Exception as ex:
            messagebox.showerror("Load failed", str(ex))

    def _sync_ui_to_ticks(self, s_ticks: int, e_ticks: int, w_ticks: int = 2048,
                           b_ticks: int = None):
        """
        Update sliders, entry boxes and canvas to reflect a position given as
        raw Dynamixel tick values (shoulder, elbow, wrist, base).
        Safe to call from any thread via root.after(0, ...).
        Does NOT send any hardware commands.
        """
        self._ui_sync_in_progress = True
        try:
            s_deg = (s_ticks - DXL_CTR) / TPD
            e_deg = (e_ticks - DXL_CTR) / TPD
            w_deg = (w_ticks - DXL_CTR) / TPD

            t2      = math.radians(s_deg)
            t3      = math.radians(e_deg)
            t4      = math.radians(w_deg)
            t2_geom = t2 - _ELBOW_OFF

            # Forward kinematics — ea = sa + t3 (t3 is negative, so ea < sa)
            sa   = math.pi / 2 - t2_geom
            ea   = sa + t3
            r    = L2 * math.cos(sa) + L3 * math.cos(ea)
            fk_z = L2 * math.sin(sa) + L3 * math.sin(ea)

            # Base angle t1 from motor ticks relative to startup reference
            if b_ticks is not None:
                delta_deg = (b_ticks - self._base_home_ticks) / (TPD * BASE_GEAR_RATIO)
                t1 = self._base_t1_startup + math.radians(delta_deg)
                # Advance reference so the next IK delta is computed from here
                self._base_t1_startup = t1
                self._base_home_ticks = b_ticks
            else:
                t1 = self._base_t1_startup

            fk_x = r * math.cos(t1)
            fk_y = r * math.sin(t1)

            fk_x = max(-0.44, min(0.44, fk_x))
            fk_y = max(-0.30, min(0.30, fk_y))
            fk_z = max(0.05,  min(0.44, fk_z))

            self._sliders["X"].set(fk_x)
            self._sliders["Y"].set(fk_y)
            self._sliders["Z"].set(fk_z)
            self._sliders["Roll"].set(w_deg)
            self._val_labels["X"].set(f"{fk_x:.3f}")
            self._val_labels["Y"].set(f"{fk_y:.3f}")
            self._val_labels["Z"].set(f"{fk_z:.3f}")
            self._val_labels["Roll"].set(f"{w_deg:.1f}")

            self.canvas.set_pose((t1, t2, t3, t4), True)

            self.status_lbl.config(
                text=f"X≈{fk_x:.3f}  Y≈{fk_y:.3f}  Z≈{fk_z:.3f}  "
                     f"θ1={math.degrees(t1):.1f}°  θ2={s_deg:.1f}°  "
                     f"θ3={e_deg:.1f}°  θ4={w_deg:.1f}°",
                fg=MUTED)
        finally:
            self._ui_sync_in_progress = False

    def _poll_teach_pose(self):
        """Called repeatedly via root.after() while in teach mode.
        Reads present motor positions in a background thread and updates the
        canvas and angle display so the user can see the pose as they move it."""
        if not self._teach_mode:
            return   # stopped teaching — don't reschedule

        def _do_read():
            pos = self._read_present_positions()
            if pos is not None:
                self.root.after(0, lambda p=pos: self._sync_ui_to_ticks(p[0], p[1], p[2], p[3]))

        threading.Thread(target=_do_read, daemon=True).start()
        # Reschedule — 100 ms gives smooth feedback without hammering the serial port
        self.root.after(100, self._poll_teach_pose)

    def _teach_hand_toggle(self):
        """Toggle hand open/closed and add a waypoint at the current arm position.
        Works both in teach mode (motors off) and normal mode (motors on)."""
        if self._replaying:
            return

        self._teach_hand_open = not self._teach_hand_open
        ticks = HAND_OPEN if self._teach_hand_open else HAND_CLOSED
        state = "OPEN" if self._teach_hand_open else "CLOSED"

        # Update _hand_cmd and write immediately
        with self._lock:
            if self._hand_cmd is not None:
                _, cur = self._hand_cmd
                self._hand_cmd = (ticks, cur)
            else:
                self._hand_cmd = (ticks, 0)
        if self.hand_ok:
            try:
                with self._lock:
                    self.pk.write4ByteTxRx(
                        self.ph, ID_HAND, ADDR_GOAL_POSITION, ticks)
            except Exception:
                pass
        self._hand_pos_var.set(max(0, min(8191, ticks)))

        # Add waypoint at current arm position with the new hand state
        with self._lock:
            cmd = self._cmd
        if cmd is not None and len(cmd) >= 4:
            # _cmd = (base, shoulder, elbow, wrist)
            arm_pos = (cmd[1], cmd[2], cmd[3])
            base_pos = cmd[0]
            self._waypoints.append(arm_pos + (base_pos, ticks))
            self._refresh_listbox()
            self._wp_listbox.selection_clear(0, tk.END)
            self._wp_listbox.selection_set(tk.END)
            self._wp_listbox.see(tk.END)
            status_extra = f"  — WP {len(self._waypoints)} added"
        else:
            status_extra = ""

        if self._teach_mode:
            msg = f"Hand → {state} ({ticks} ticks)  — pose arm, press T to capture{status_extra}"
        else:
            msg = f"Hand → {state} ({ticks} ticks){status_extra}"
        self._wp_status.config(text=msg, fg=YELLOW)

    def _finish_record(self):
        pos = self._read_present_positions()

        # Re-enable torque in background — needs reads before writes
        threading.Thread(target=self._torque_on, daemon=True).start()
        self._record_btn.config(fg=TEXT, text="⏺  POSE & RECORD  (T)")

        if pos is not None:
            # pos = (shoulder, elbow, wrist, base)
            arm_pos = pos[:3]
            base_pos = pos[3]

            if self.hw_ok:
                try:
                    sync_write_positions(self.gsw, self.ids, list(arm_pos))
                except Exception:
                    pass
                try:
                    self.pk.write4ByteTxRx(
                        self.ph, ID_BASE, ADDR_GOAL_POSITION, base_pos)
                except Exception:
                    pass
            with self._lock:
                self._cmd = (base_pos,) + arm_pos

            self._sync_ui_to_ticks(arm_pos[0], arm_pos[1], arm_pos[2], base_pos)

            # Store all 5 joints: (shoulder, elbow, wrist, base, hand)
            with self._lock:
                hand_ticks = self._hand_cmd[0] if self._hand_cmd else HAND_OPEN
            self._waypoints.append(arm_pos + (base_pos, hand_ticks))
            self._refresh_listbox()
            self._wp_listbox.selection_clear(0, tk.END)
            self._wp_listbox.selection_set(tk.END)
            self._wp_listbox.see(tk.END)
        else:
            self._wp_status.config(
                text="⚠  Could not read positions (sim mode?)", fg=RED)

    def _clear_waypoints(self):
        if self._teach_mode:
            self._teach_mode = False
            threading.Thread(target=self._torque_on, daemon=True).start()
            self._record_btn.config(fg=TEXT, text="⏺  POSE & RECORD  (T)")
        self._waypoints.clear()
        self._refresh_listbox()
        self._replay_status.config(text="—", fg=MUTED)

    def _toggle_replay(self):
        if self._replaying:
            self._stop_replay()
        else:
            self._start_replay()

    def _start_replay(self):
        if not self._waypoints:
            self._replay_status.config(text="⚠  No waypoints to replay", fg=RED)
            return
        try:
            speed = float(self._speed_var.get())
            if speed <= 0:
                raise ValueError
        except ValueError:
            self._replay_status.config(text="⚠  Invalid speed value", fg=RED)
            return
        try:
            hold = float(self._gap_var.get())
            if hold < 0:
                raise ValueError
        except ValueError:
            self._replay_status.config(text="⚠  Invalid hold time", fg=RED)
            return

        self._replaying = True
        self._replay_btn.config(text="■  STOP", fg=RED)
        self._replay_thread = threading.Thread(
            target=self._replay_loop, args=(speed, hold), daemon=True)
        self._replay_thread.start()

    def _stop_replay(self):
        self._replaying = False
        self._replay_btn.config(text="▶  PLAY", fg=YELLOW)

    def _move_to_ticks(self, target, speed, stop_flag=None):
        """Smoothly interpolate from the current position to target (shoulder, elbow, wrist, base).
        Runs on whichever thread calls it. stop_flag is a callable returning True to abort."""
        STEP_DT = 0.02   # 50 Hz

        with self._lock:
            cmd0 = self._cmd
        if cmd0 and len(cmd0) >= 4:
            current = [cmd0[1], cmd0[2], cmd0[3], cmd0[0]]   # → (s, e, w, base)
        else:
            current = list(target)

        target = list(target)
        max_delta = max(abs(target[i] - current[i]) for i in range(len(target)))
        n_steps   = max(1, int(math.ceil(max_delta / (speed * STEP_DT))))

        for step in range(1, n_steps + 1):
            if stop_flag and stop_flag():
                return
            t   = step / n_steps
            t   = t * t * (3 - 2 * t)   # smooth-step easing
            pos = tuple(int(current[i] + (target[i] - current[i]) * t)
                        for i in range(len(target)))
            arm_pos  = list(pos[:3])   # shoulder, elbow, wrist
            base_pos = pos[3]

            if self.hw_ok:
                try:
                    sync_write_positions(self.gsw, self.ids, arm_pos)
                except Exception:
                    pass
                try:
                    self.pk.write4ByteTxRx(
                        self.ph, ID_BASE, ADDR_GOAL_POSITION, base_pos)
                except Exception:
                    pass

            with self._lock:
                self._cmd = (base_pos,) + tuple(arm_pos)

            s, e, w = pos[0], pos[1], pos[2]
            self.root.after(0, lambda sv=s, ev=e, wv=w, bv=base_pos: self._sync_ui_to_ticks(sv, ev, wv, bv))

            time.sleep(STEP_DT)

    def _replay_loop(self, speed: float, hold: float):
        """Background thread: smoothly move through waypoints at speed ticks/sec.
        Handles position tuples, STOP dicts, and WAIT dicts."""
        idx = 0

        with self._lock:
            cmd0 = self._cmd
        if cmd0 and len(cmd0) >= 4:
            current = [cmd0[1], cmd0[2], cmd0[3], cmd0[0]]
        else:
            # Find the first position waypoint to use as starting reference
            first_pos = next((wp for wp in self._waypoints if not isinstance(wp, dict)), None)
            current = list(first_pos[:4]) if first_pos else [2048, 2048, 2048, 0]

        while self._replaying:
            wp_now = self._waypoints[idx]
            n      = len(self._waypoints)

            # ── STOP ─────────────────────────────────────────────────────────
            if isinstance(wp_now, dict) and wp_now.get("type") == "STOP":
                self.root.after(0, lambda i=idx: self._replay_status.config(
                    text=f"⏹  STOP at waypoint {i+1} — replay halted", fg=RED))
                self._stop_replay()
                return

            # ── WAIT ─────────────────────────────────────────────────────────
            elif isinstance(wp_now, dict) and wp_now.get("type") == "WAIT":
                secs = float(wp_now.get("seconds", 1.0))
                self.root.after(0, lambda i=idx, s=secs: self._replay_status.config(
                    text=f"⏸  Waiting {s:.1f}s at waypoint {i+1}…", fg=YELLOW))
                deadline = time.perf_counter() + secs
                while time.perf_counter() < deadline and self._replaying:
                    time.sleep(0.02)
                idx = (idx + 1) % n
                continue

            # ── POSITION ─────────────────────────────────────────────────────
            else:
                target = list(wp_now[:4])   # (s, e, w, base)

                self._move_to_ticks(target, speed, stop_flag=lambda: not self._replaying)
                current = target[:]

                # Apply hand position if stored (index 4)
                if len(wp_now) > 4 and self.hand_ok:
                    h_ticks = wp_now[4]
                    with self._lock:
                        if self._hand_cmd is not None:
                            _, cur = self._hand_cmd
                            self._hand_cmd = (h_ticks, cur)
                        else:
                            self._hand_cmd = (h_ticks, 0)
                    try:
                        with self._lock:
                            self.pk.write4ByteTxRx(
                                self.ph, ID_HAND, ADDR_GOAL_POSITION, h_ticks)
                    except Exception:
                        pass
                    self.root.after(0, lambda h=h_ticks:
                        self._hand_pos_var.set(max(0, min(8191, h))))

                msg = (f"Waypoint {idx + 1} / {n}  →  "
                       f"S={target[0]}  E={target[1]}  W={target[2]}  B={target[3]}")
                self.root.after(0, lambda m=msg: self._replay_status.config(text=m, fg=YELLOW))

                idx = (idx + 1) % n

                # Hold at waypoint
                deadline = time.perf_counter() + hold
                while time.perf_counter() < deadline and self._replaying:
                    time.sleep(0.02)

        self.root.after(0, lambda: self._replay_status.config(
            text="Replay stopped", fg=MUTED))

    # ── Hardware ──────────────────────────────────────────────────────────────
    def _setup_hardware(self):
        """Initialise hardware state and start the background connection loop."""
        self.gsw      = None
        self.ph       = None
        self.pk       = None
        self.ids      = [ID_SHOULDER, ID_ELBOW, ID_WRIST]
        self.hw_ok    = False
        self.hand_ok  = False

        if not DYNAMIXEL_AVAILABLE:
            self.hw_badge.config(text="● SDK not installed — sim only", fg=MUTED)
            return

        # Start background thread that retries every second until connected
        threading.Thread(target=self._connection_loop, daemon=True).start()

    def _reconnect(self):
        """Called when comms drop mid-session. Closes port cleanly then retries."""
        # Close the old port outside the lock — _comms_loop won't touch it since hw_ok=False
        try:
            if self.ph is not None:
                self.ph.closePort()
        except Exception:
            pass
        self.ph  = None
        self.pk  = None
        self.gsw = None

        # Reuse the connection loop — it retries every second until hw_ok is True
        attempt = 0
        while self._running and not self.hw_ok:
            attempt += 1
            self.root.after(0, lambda a=attempt: self.hw_badge.config(
                text=f"● Reconnecting… (attempt {a})", fg=YELLOW))
            if self._try_connect():
                return
            time.sleep(1.0)

    def _connection_loop(self):
        """Background thread: attempt to connect every second until successful."""
        attempt = 0
        while self._running and not self.hw_ok:
            attempt += 1
            self.root.after(0, lambda a=attempt: self.hw_badge.config(
                text=f"● Connecting… (attempt {a})", fg=YELLOW))
            if self._try_connect():
                return   # success — _try_connect updated hw_badge
            time.sleep(1.0)

    def _try_connect(self):
        """Single connection attempt. Returns True on success, False on failure."""
        ph  = None
        pk  = None
        gsw = None
        try:
            ph  = PortHandler(DEVICENAME)
            pk  = PacketHandler(PROTOCOL_VERSION)

            if not ph.openPort():
                raise IOError(f"Cannot open {DEVICENAME}")
            if not ph.setBaudRate(BAUDRATE):
                raise IOError(f"Cannot set baud {BAUDRATE}")

            gsw = GroupSyncWrite(ph, pk, ADDR_GOAL_POSITION, 4)

            # ── Arm motors ───────────────────────────────────────────────────────
            startup_positions = []
            for did in self.ids:
                val, res, err = pk.read4ByteTxRx(ph, did, ADDR_PRESENT_POSITION)
                if res != COMM_SUCCESS:
                    raise IOError(
                        f"Read present pos failed ID {did}: "
                        f"{pk.getTxRxResult(res)}")
                if val > 0x7FFFFFFF:
                    val -= 0x100000000
                startup_positions.append(max(DXL_MIN, min(DXL_MAX, val)))

            sync_write_positions(gsw, self.ids, startup_positions)
            for did in self.ids:
                res, err = pk.write1ByteTxRx(ph, did, ADDR_TORQUE_ENABLE, 1)
                if res != COMM_SUCCESS:
                    raise IOError(
                        f"Torque enable failed ID {did}: "
                        f"{pk.getTxRxResult(res)}")

            # ── Base motor ───────────────────────────────────────────────────────
            # Set Extended Position (multi-turn) mode BEFORE enabling torque.
            # Torque must be off to change operating mode — it is off at this point.
            ADDR_OPERATING_MODE = 11   # same address as other XM/XH series motors
            EXTENDED_POSITION    = 4   # mode 4 = Extended Position (multi-turn)
            pk.write1ByteTxRx(ph, ID_BASE, ADDR_OPERATING_MODE, EXTENDED_POSITION)

            val, res, err = pk.read4ByteTxRx(ph, ID_BASE, ADDR_PRESENT_POSITION)
            if res != COMM_SUCCESS:
                raise IOError(
                    f"Read present pos failed ID {ID_BASE}: "
                    f"{pk.getTxRxResult(res)}")
            if val > 0x7FFFFFFF:
                val -= 0x100000000
            base_motor_start = val
            pk.write4ByteTxRx(ph, ID_BASE, ADDR_GOAL_POSITION, base_motor_start)
            res, err = pk.write1ByteTxRx(ph, ID_BASE, ADDR_TORQUE_ENABLE, 1)
            if res != COMM_SUCCESS:
                raise IOError(
                    f"Torque enable failed ID {ID_BASE}: "
                    f"{pk.getTxRxResult(res)}")

            # All hardware ready — commit to self atomically
            self.ph  = ph
            self.pk  = pk
            self.gsw = gsw
            self._base_home_ticks = base_motor_start
            self._cmd = (base_motor_start,) + tuple(startup_positions)
            self.hw_ok = True

        except Exception as e:
            # Clean up the local port — self.ph/pk/gsw are untouched
            try:
                if ph is not None:
                    ph.closePort()
            except Exception:
                pass
            self.root.after(0, lambda err=str(e): self.hw_badge.config(
                text=f"● {err}", fg=RED))
            return False

        # ── Hand motor ───────────────────────────────────────────────────────────
        try:
            ADDR_OPERATING_MODE = 11
            pk.write1ByteTxRx(ph, ID_HAND, ADDR_TORQUE_ENABLE, 0)
            pk.write1ByteTxRx(ph, ID_HAND, ADDR_OPERATING_MODE, 5)
            res, err = pk.write1ByteTxRx(ph, ID_HAND, ADDR_TORQUE_ENABLE, 1)
            if res != COMM_SUCCESS:
                raise IOError(f"Hand torque enable: {pk.getTxRxResult(res)}")
            hand_pos, res, err = pk.read4ByteTxRx(ph, ID_HAND, ADDR_PRESENT_POSITION)
            if res == COMM_SUCCESS:
                if hand_pos > 0x7FFFFFFF:
                    hand_pos -= 0x100000000
                self._hand_cmd = (int(hand_pos), 0)
                self.root.after(0, lambda p=int(hand_pos):
                    self._hand_pos_var.set(max(0, min(8191, p))))
            self.hand_ok = True
            self.root.after(0, lambda: self.hw_badge.config(
                text=f"● {DEVICENAME} connected  (arm + hand)", fg=ACCENT))
        except Exception as e:
            self.root.after(0, lambda err=str(e): self.hw_badge.config(
                text=f"● {DEVICENAME} connected  (hand error: {err})", fg=YELLOW))

        # Sync sliders to physical position once connected
        self.root.after(200, self._sync_sliders_to_hardware)
        return True

    # ── Comms thread ──────────────────────────────────────────────────────────
    def _comms_loop(self):
        dt = 1.0 / 50
        _fail_count  = 0
        _FAIL_LIMIT  = 5    # consecutive failed heartbeats before reconnect
        _hb_interval = 25   # check heartbeat every N cycles (~0.5s at 50Hz)
        _cycle       = 0

        while self._running:
            t0 = time.perf_counter()
            _cycle += 1

            if self.hw_ok:
                with self._lock:
                    # ── Write arm + base ──────────────────────────────────────
                    if not self._teach_mode and self._cmd is not None:
                        cmd = self._cmd
                        sync_write_positions(self.gsw, self.ids, list(cmd[1:4]))
                        self.pk.write4ByteTxRx(
                            self.ph, ID_BASE, ADDR_GOAL_POSITION, cmd[0])

                    # ── Heartbeat read (every _hb_interval cycles) ────────────
                    if _cycle % _hb_interval == 0:
                        try:
                            _, res, _ = self.pk.read4ByteTxRx(
                                self.ph, ID_SHOULDER, ADDR_PRESENT_POSITION)
                            if res == COMM_SUCCESS:
                                _fail_count = 0
                            else:
                                _fail_count += 1
                        except Exception:
                            _fail_count += 1

                        if _fail_count >= _FAIL_LIMIT:
                            _fail_count  = 0
                            self.hw_ok   = False
                            self.hand_ok = False
                            self.root.after(0, lambda: self.hw_badge.config(
                                text="● Connection lost — reconnecting…", fg=RED))
                            threading.Thread(
                                target=self._reconnect, daemon=True).start()

            # ── Hand motor ────────────────────────────────────────────────────
            if self.hand_ok:
                with self._lock:
                    if not self._teach_mode and self._hand_cmd is not None:
                        pos_ticks, cur_ticks = self._hand_cmd
                        try:
                            self.pk.write4ByteTxRx(
                                self.ph, ID_HAND, ADDR_GOAL_POSITION, pos_ticks)
                        except Exception:
                            pass

            rem = dt - (time.perf_counter() - t0)
            if rem > 0:
                time.sleep(rem)

    # ── Cleanup ───────────────────────────────────────────────────────────────
    # ── Safe exit ─────────────────────────────────────────────────────────────
    def _safe_exit(self):
        """Move arm to safe storage position then shut down."""
        if self._replaying:
            self._stop_replay()
        if self._teach_mode:
            self._teach_mode = False

        self.hw_badge.config(text="● Moving to safe position…", fg=YELLOW)
        self.root.update_idletasks()

        def _do_exit():
            if self.hw_ok:
                # Safe position: x=0.066, y=0, z=0.105, roll=39°
                SAFE_X, SAFE_Y, SAFE_Z, SAFE_ROLL = 0.066, 0.0, 0.105, 39.0
                sols = inverse_kinematics(SAFE_X, SAFE_Y, SAFE_Z,
                                          math.radians(SAFE_ROLL))
                if sols:
                    t1, t2, t3, t4 = sols[0]
                    with self._lock:
                        pb = self._cmd[0] if self._cmd else self._base_home_ticks
                    ps = angle_to_dxl(math.degrees(t2))
                    pe = angle_to_dxl(math.degrees(t3) + math.degrees(_ELBOW_OFF))
                    pw = angle_to_dxl(math.degrees(t4))
                    safe_pos = (ps, pe, pw, pb)
                    try:
                        speed = float(self._speed_var.get())
                        if speed <= 0:
                            speed = 200.0
                    except ValueError:
                        speed = 200.0
                    self._move_to_ticks(safe_pos, speed)

            self.root.after(0, self._on_close)

        import threading as _t
        _t.Thread(target=_do_exit, daemon=True).start()

    # ── Cleanup ───────────────────────────────────────────────────────────────
    def _on_close(self):
        # 1. Stop replay loop
        self._replaying = False

        # 2. Signal comms thread to exit and wait for it to finish
        #    so we have exclusive access to the port for torque-off writes
        self._running = False
        if hasattr(self, '_thread') and self._thread.is_alive():
            self._thread.join(timeout=0.5)

        # 3. Disable torque on all motors — retried a few times for reliability
        if self.hw_ok:
            for attempt in range(3):
                try:
                    for did in self.ids:
                        self.pk.write1ByteTxRx(
                            self.ph, did, ADDR_TORQUE_ENABLE, 0)
                    # Base motor on RS485 — individual write
                    self.pk.write1ByteTxRx(
                        self.ph, ID_BASE, ADDR_TORQUE_ENABLE, 0)
                    if self.hand_ok:
                        self.pk.write1ByteTxRx(
                            self.ph, ID_HAND, ADDR_TORQUE_ENABLE, 0)
                    break   # success
                except Exception:
                    time.sleep(0.05)
            try:
                self.ph.closePort()
            except Exception:
                pass

        self.root.destroy()


# ─── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TSL Robot Arm GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python robot_arm_gui_46.py                      # normal launch\n"
            "  python robot_arm_gui_46.py sequence.json        # load & auto-play\n"
            "  python robot_arm_gui_46.py C:/paths/demo.json   # full path\n"
        )
    )
    parser.add_argument(
        "waypoints",
        nargs="?",
        default=None,
        metavar="FILE",
        help="Optional JSON waypoint file to load and replay automatically on startup"
    )
    args = parser.parse_args()

    root = tk.Tk()

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Horizontal.TScale",
                    background=PANEL,
                    troughcolor=BORDER,
                    sliderthickness=20,
                    sliderrelief="flat",
                    borderwidth=0)
    style.map("Horizontal.TScale",
              background=[("active", PANEL)],
              troughcolor=[("active", BORDER)])

    app = RobotArmGUI(root, autorun_file=args.waypoints)
    root.mainloop()
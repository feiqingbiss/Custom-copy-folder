import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import shutil
import os
from datetime import datetime

# -------------------- 自定义滚动文本框（带占位符） --------------------
class CustomScrolledText(tk.Frame):
    def __init__(self, master, placeholder="", **kwargs):
        super().__init__(master, bg="#FFFFFF")
        self.placeholder = placeholder
        self.has_placeholder = False
        
        self.text = tk.Text(self, **kwargs)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=v_scroll.set)
        h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.text.config(xscrollcommand=h_scroll.set)
        
        self.text.bind("<FocusIn>", self._on_focus_in)
        self.text.bind("<FocusOut>", self._on_focus_out)
        self.text.bind("<Key>", self._on_key)
        self._show_placeholder()
    
    def _show_placeholder(self):
        if self.placeholder and not self.text.get(1.0, tk.END).strip():
            self.text.config(state='normal')
            self.text.delete(1.0, tk.END)
            self.text.insert(1.0, self.placeholder)
            self.text.config(fg="#9CA3AF")
            self.has_placeholder = True
            self.text.config(state='normal')
    
    def _hide_placeholder(self):
        if self.has_placeholder:
            self.text.config(state='normal')
            self.text.delete(1.0, tk.END)
            self.text.config(fg="#1E293B")
            self.has_placeholder = False
            self.text.config(state='normal')
    
    def _on_focus_in(self, event):
        if self.has_placeholder:
            self._hide_placeholder()
    
    def _on_focus_out(self, event):
        if not self.text.get(1.0, tk.END).strip():
            self._show_placeholder()
    
    def _on_key(self, event):
        if self.has_placeholder:
            self._hide_placeholder()
    
    def delete(self, *args):
        self.text.delete(*args)
    def insert(self, *args):
        if self.has_placeholder:
            self._hide_placeholder()
        self.text.insert(*args)
    def config(self, **kwargs):
        self.text.config(**kwargs)
    def get(self, *args):
        return self.text.get(*args)
    def see(self, *args):
        self.text.see(*args)
    def __getattr__(self, name):
        if hasattr(self.text, name):
            return getattr(self.text, name)
        return super().__getattr__(name)

# -------------------- 样式定义 --------------------
def setup_styles():
    style = ttk.Style()
    style.theme_use('clam')
    
    bg_main = "#F0F4F8"
    bg_card = "#FFFFFF"
    primary = "#4A90D9"
    primary_light = "#6BB3F0"
    primary_dark = "#2E6BB0"
    success = "#10B981"
    success_light = "#34D399"
    text_primary = "#1E293B"
    text_secondary = "#6B7280"
    border_color = "#E2E8F0"
    focus_color = primary
    
    style.configure(".", background=bg_main, foreground=text_primary,
                    font=("Segoe UI", 9))
    style.configure("TFrame", background=bg_main)
    style.configure("TLabelframe", background=bg_main, foreground=text_primary,
                    borderwidth=1, relief="solid", bordercolor=border_color)
    style.configure("TLabelframe.Label", background=bg_main, foreground=text_primary,
                    font=("Segoe UI", 10, "bold"))
    
    style.configure("TButton", background=primary, foreground="white",
                    borderwidth=0, focusthickness=0, padding=(8, 6),
                    font=("Segoe UI", 9, "bold"))
    style.map("TButton",
              background=[('active', primary_light), ('pressed', primary_dark)])
    
    style.configure("Accent.TButton", background=success, foreground="white",
                    borderwidth=0, focusthickness=0, padding=(12, 8),
                    font=("Segoe UI", 10, "bold"))
    style.map("Accent.TButton",
              background=[('active', success_light), ('pressed', '#059669')])
    
    style.configure("TEntry", fieldbackground="white", borderwidth=1,
                    relief="solid", bordercolor=border_color, padding=4,
                    font=("Segoe UI", 9))
    style.map("TEntry",
              bordercolor=[('focus', focus_color)])
    
    style.configure("TProgressbar", background=primary, troughcolor="#E5E7EB",
                    borderwidth=0, thickness=6)
    
    style.configure("Treeview", background="white", foreground=text_primary,
                    rowheight=30, font=("Segoe UI", 9), borderwidth=0)
    style.configure("Treeview.Heading", background="#E5E7EB", foreground=text_primary,
                    font=("Segoe UI", 9, "bold"), borderwidth=0)
    style.map("Treeview", background=[('selected', primary)],
              foreground=[('selected', 'white')])
    
    style.configure("TRadiobutton", background=bg_main, foreground=text_primary,
                    font=("Segoe UI", 9))
    style.map("TRadiobutton",
              background=[('active', bg_main)],
              foreground=[('active', text_primary)])
    
    style.configure("TScrollbar",
                    background=bg_main,
                    troughcolor=bg_main,
                    borderwidth=0,
                    arrowcolor=text_secondary,
                    gripcount=0,
                    thickness=8)
    style.map("TScrollbar",
              background=[('active', primary_light), ('pressed', primary_dark)])
    
    return style

# -------------------- 主应用 --------------------
class BatchCopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("批量路径复制工具")
        self.root.geometry("1100x800")
        self.root.minsize(850, 600)
        self.root.configure(bg="#F0F4F8")
        
        self.style = setup_styles()
        self.mapping = []
        self.is_running = False
        self.error_list = []
        self.error_count = 0
        self.success_count = 0
        
        # ---- 主容器 ----
        main = tk.Frame(root, bg="#F0F4F8")
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        main.rowconfigure(0, weight=0)
        main.rowconfigure(1, weight=1)
        main.rowconfigure(2, weight=0)
        main.rowconfigure(3, weight=1, minsize=150)
        main.rowconfigure(4, weight=0)
        main.columnconfigure(0, weight=1)
        
        # ---- 标题 ----
        header = tk.Frame(main, bg="#F0F4F8")
        header.grid(row=0, column=0, sticky="ew", pady=(0,12))
        tk.Label(header, text="📂 批量路径复制工具", font=("Segoe UI", 20, "bold"),
                 fg="#1E293B", bg="#F0F4F8").pack(side=tk.LEFT)
        tk.Label(header, text="v7.3-fix", font=("Segoe UI", 12),
                 fg="#6B7280", bg="#F0F4F8").pack(side=tk.LEFT, padx=(12,0))
        
        # ---- 路径列表框 ----
        path_frame = tk.Frame(main, bg="#F0F4F8")
        path_frame.grid(row=1, column=0, sticky="nsew", pady=(0,8))
        path_frame.columnconfigure(0, weight=1)
        path_frame.columnconfigure(1, weight=1)
        path_frame.rowconfigure(0, weight=1)
        
        # 左列
        left_card = tk.Frame(path_frame, bg="white", relief="solid", bd=1,
                            highlightthickness=0, highlightbackground="#E2E8F0")
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0,6))
        left_card.rowconfigure(2, weight=1)
        left_card.columnconfigure(0, weight=1)
        left_header = tk.Frame(left_card, bg="#F0F4F8")
        left_header.grid(row=0, column=0, sticky="ew", pady=(6,4), padx=6)
        tk.Label(left_header, text="📁 源路径列表", font=("Segoe UI", 11, "bold"),
                 fg="#1E293B", bg="#F0F4F8").pack(side=tk.LEFT)
        ttk.Button(left_header, text="📂 浏览目录", command=self.browse_source_dir).pack(side=tk.RIGHT)
        # 左侧占位
        self.left_placeholder = tk.Frame(left_card, height=60, bg="white")
        self.left_placeholder.grid(row=1, column=0, sticky="ew", pady=(0,0), padx=6)
        self.left_placeholder.grid_propagate(False)
        self.src_text = CustomScrolledText(left_card, font=("Consolas", 10),
                                           bg="white", fg="#1E293B",
                                           relief="flat", borderwidth=1,
                                           highlightthickness=1,
                                           highlightcolor="#4A90D9",
                                           highlightbackground="#E2E8F0")
        self.src_text.grid(row=2, column=0, sticky="nsew", pady=(0,0), padx=6)
        src_btn = tk.Frame(left_card, bg="white")
        src_btn.grid(row=3, column=0, sticky="ew", padx=6, pady=(6,0))
        ttk.Button(src_btn, text="📄 导入 txt", command=self.load_src_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(src_btn, text="🗑️ 清空", command=lambda: self.src_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=2)
        
        # 右列
        right_card = tk.Frame(path_frame, bg="white", relief="solid", bd=1,
                             highlightthickness=0, highlightbackground="#E2E8F0")
        right_card.grid(row=0, column=1, sticky="nsew", padx=(6,0))
        right_card.rowconfigure(3, weight=1)
        right_card.columnconfigure(0, weight=1)
        
        # 标题
        right_header = tk.Frame(right_card, bg="#F0F4F8")
        right_header.grid(row=0, column=0, sticky="ew", pady=(6,4), padx=6)
        tk.Label(right_header, text="🎯 目标设置", font=("Segoe UI", 11, "bold"),
                 fg="#1E293B", bg="#F0F4F8").pack(side=tk.LEFT)
        radio_frame = tk.Frame(right_header, bg="#F0F4F8")
        radio_frame.pack(side=tk.RIGHT)
        self.mode_var = tk.StringVar(value="root")
        ttk.Radiobutton(radio_frame, text="统一目标目录", variable=self.mode_var,
                        value="root", command=self.on_mode_change).pack(side=tk.LEFT, padx=(0,12))
        ttk.Radiobutton(radio_frame, text="一对一映射", variable=self.mode_var,
                        value="mapping", command=self.on_mode_change).pack(side=tk.LEFT, padx=(0,12))
        ttk.Radiobutton(radio_frame, text="多对一映射", variable=self.mode_var,
                        value="multi", command=self.on_mode_change).pack(side=tk.LEFT)
        
        # 控制区：目标根目录
        self.row1 = tk.Frame(right_card, bg="white")
        self.row1.grid(row=1, column=0, sticky="ew", pady=(0,4), padx=6)
        self.row1.columnconfigure(1, weight=1)
        tk.Label(self.row1, text="目标根目录：", font=("Segoe UI", 9),
                 bg="white").grid(row=0, column=0, sticky="w", padx=(0,4))
        self.root_target_entry = ttk.Entry(self.row1, font=("Consolas", 10))
        self.root_target_entry.grid(row=0, column=1, sticky="ew", padx=(4,4))
        self.browse_root_btn = ttk.Button(self.row1, text="浏览", command=self.browse_root_target)
        self.browse_root_btn.grid(row=0, column=2, padx=(4,0))
        
        # 控制区：公共父目录
        self.row2 = tk.Frame(right_card, bg="white")
        self.row2.grid(row=2, column=0, sticky="ew", pady=(0,4), padx=6)
        self.row2.columnconfigure(1, weight=1)
        self.row2_label = tk.Label(self.row2, text="公共父目录：", font=("Segoe UI", 9), bg="white")
        self.row2_label.grid(row=0, column=0, sticky="w", padx=(0,4))
        self.prefix_entry = ttk.Entry(self.row2, font=("Consolas", 10))
        self.prefix_entry.grid(row=0, column=1, sticky="ew", padx=(4,4))
        self.generate_btn = ttk.Button(self.row2, text="生成路径", command=self.generate_target_paths)
        self.generate_btn.grid(row=0, column=2, padx=(4,4))
        self.prefix_hint = tk.Label(self.row2, text="留空自动检测", font=("Segoe UI", 8),
                                    fg="#6B7280", bg="white")
        self.prefix_hint.grid(row=0, column=3, sticky="w", padx=(4,0))
        
        # 目标文本框
        self.dst_text = CustomScrolledText(right_card, placeholder="",
                                           font=("Consolas", 10),
                                           bg="white", fg="#1E293B",
                                           relief="flat", borderwidth=1,
                                           highlightthickness=1,
                                           highlightcolor="#4A90D9",
                                           highlightbackground="#E2E8F0")
        self.dst_text.grid(row=3, column=0, sticky="nsew", pady=(0,0), padx=6)
        dst_btn = tk.Frame(right_card, bg="white")
        dst_btn.grid(row=4, column=0, sticky="ew", padx=6, pady=(6,0))
        ttk.Button(dst_btn, text="📄 导入 txt", command=self.load_dst_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(dst_btn, text="🗑️ 清空", command=lambda: self.dst_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=2)
        
        # ---- 操作按钮 ----
        action_frame = tk.Frame(main, bg="#F0F4F8")
        action_frame.grid(row=2, column=0, sticky="ew", pady=(8,8))
        action_frame.columnconfigure(1, weight=1)
        btn_group = tk.Frame(action_frame, bg="#F0F4F8")
        btn_group.grid(row=0, column=0, sticky="w")
        ttk.Button(btn_group, text="👁️ 预览映射", command=self.preview_mapping).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_group, text="🚀 开始复制", command=self.start_copy, style="Accent.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_group, text="🧹 清空预览", command=self.clear_preview_only).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_group, text="❓ 帮助", command=self.show_help).pack(side=tk.LEFT, padx=4)
        progress_frame = tk.Frame(action_frame, bg="#F0F4F8")
        progress_frame.grid(row=0, column=1, sticky="e", padx=(10,0))
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_label = tk.Label(progress_frame, text="就绪", anchor="w",
                                     font=("Segoe UI", 9), bg="#F0F4F8")
        self.status_label.pack(side=tk.RIGHT, padx=(10,0))
        
        # ---- 映射预览 ----
        preview_frame = ttk.LabelFrame(main, text="📋 映射预览", padding="8")
        preview_frame.grid(row=3, column=0, sticky="nsew", pady=(6,8))
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        tree_container = tk.Frame(preview_frame, bg="#F0F4F8")
        tree_container.grid(row=0, column=0, sticky="nsew")
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_container, columns=("src", "dst"), show="headings", height=6)
        self.tree.heading("src", text="源路径")
        self.tree.heading("dst", text="目标路径")
        self.tree.column("src", width=400)
        self.tree.column("dst", width=400)
        v_scroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        # ---- 运行日志 ----
        log_frame = ttk.LabelFrame(main, text="📝 运行日志", padding="6")
        log_frame.grid(row=4, column=0, sticky="ew", pady=(0,0))
        log_frame.pack_propagate(False)
        log_frame.config(height=100)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = CustomScrolledText(log_frame, height=3, font=("Consolas", 9),
                                           bg="#F8FAFC", fg="#1E293B",
                                           relief="flat", borderwidth=1,
                                           highlightthickness=1,
                                           highlightcolor="#4A90D9",
                                           highlightbackground="#E2E8F0",
                                           state='disabled')
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6,4))
        
        log_btn = tk.Frame(log_frame, bg="#F0F4F8")
        log_btn.grid(row=1, column=0, sticky="ew", padx=6, pady=(0,6))
        log_btn.columnconfigure(0, weight=0)
        log_btn.columnconfigure(1, weight=0)
        log_btn.columnconfigure(2, weight=1)
        log_btn.columnconfigure(3, weight=0)
        log_btn.columnconfigure(4, weight=0)
        log_btn.columnconfigure(5, weight=0)
        
        ttk.Button(log_btn, text="🗑️ 清空日志", command=self.clear_log).grid(row=0, column=0, padx=2)
        ttk.Button(log_btn, text="💾 导出日志", command=self.export_log).grid(row=0, column=1, padx=2)
        self.success_label = tk.Label(log_btn, text="成功: 0", font=("Segoe UI", 9),
                                      fg="#10B981", bg="#F0F4F8")
        self.success_label.grid(row=0, column=3, padx=(20,4))
        self.error_label = tk.Label(log_btn, text="错误: 0", font=("Segoe UI", 9),
                                    fg="#EF4444", bg="#F0F4F8")
        self.error_label.grid(row=0, column=4, padx=(4,4))
        ttk.Button(log_btn, text="📋 导出错误", command=self.export_error_log).grid(row=0, column=5, padx=2)
        
        # 绑定窗口事件，同步占位高度
        self.root.bind("<Configure>", self.on_window_resize)
        
        self.log("✅ 程序启动，就绪")
        self.on_mode_change()
        self.root.after(100, self.sync_placeholder_height)
    
    # ------------------ 像素级对齐：同步左侧占位高度 ------------------
    def on_window_resize(self, event):
        self.root.after_idle(self.sync_placeholder_height)
    
    def sync_placeholder_height(self):
        h1 = self.row1.winfo_height() if self.row1.winfo_ismapped() else 0
        h2 = self.row2.winfo_height() if self.row2.winfo_ismapped() else 0
        total = h1 + h2
        if total > 0:
            self.left_placeholder.config(height=total)
            self.left_placeholder.grid_propagate(False)
    
    # ------------------ 模式切换（修复 columnspan 问题） ------------------
    def on_mode_change(self):
        mode = self.mode_var.get()
        self.dst_text.delete(1.0, tk.END)
        
        if mode == "root":
            self.root_target_entry.config(state='normal')
            self.browse_root_btn.config(state='normal')
            self.row2_label.grid()
            self.prefix_entry.grid()
            # 修复：重置 columnspan=1，确保按钮只占一列
            self.generate_btn.grid(row=0, column=2, padx=(4,4), columnspan=1)
            self.prefix_hint.grid()
            self.prefix_entry.config(state='normal')
            self.generate_btn.config(state='normal')
            self.prefix_hint.config(text="留空自动检测")
            self.dst_text.placeholder = (
                "示例：源 D:\\ABC\\DEF\\GHI\\JKL\n"
                "公共父目录 D:\\ABC\\DEF\n"
                "目标根目录 F:\\MNO\n"
                "→ F:\\MNO\\GHI\\JKL"
            )
            self.dst_text._show_placeholder()
            self.log("切换到「统一目标目录」模式")
        
        elif mode == "mapping":
            self.root_target_entry.config(state='disabled')
            self.browse_root_btn.config(state='disabled')
            self.row2_label.grid()
            self.prefix_entry.grid()
            # 修复：重置 columnspan=1
            self.generate_btn.grid(row=0, column=2, padx=(4,4), columnspan=1)
            self.prefix_hint.grid()
            self.prefix_entry.config(state='disabled')
            self.generate_btn.config(state='disabled')
            self.prefix_hint.config(text="(已禁用)")
            self.dst_text.placeholder = "💡 请手动输入目标路径（每行一个），或导入 txt"
            self.dst_text._show_placeholder()
            self.log("切换到「一对一映射」模式")
        
        else:  # multi
            self.root_target_entry.config(state='normal')
            self.browse_root_btn.config(state='normal')
            self.row2_label.grid_remove()
            self.prefix_entry.grid_remove()
            self.prefix_hint.grid_remove()
            # 多对一模式：按钮跨4列
            self.generate_btn.grid(row=0, column=0, columnspan=4, sticky="ew", padx=(4,4))
            self.generate_btn.config(state='normal')
            self.dst_text.placeholder = (
                "示例：源 D:\\ABC\\DEF\\GHI\\JKL\n"
                "目标根目录 F:\\MNO\n"
                "→ F:\\MNO\\JKL（仅保留末级目录）"
            )
            self.dst_text._show_placeholder()
            self.log("切换到「多对一映射」模式")
        
        self.tree.delete(*self.tree.get_children())
        self.mapping.clear()
        self.clear_counts()
        self.root.after(100, self.sync_placeholder_height)
    
    # ------------------ 计数管理 ------------------
    def clear_counts(self):
        self.error_list.clear()
        self.error_count = 0
        self.success_count = 0
        self.success_label.config(text="成功: 0")
        self.error_label.config(text="错误: 0")
    
    def add_success(self):
        self.success_count += 1
        self.success_label.config(text=f"成功: {self.success_count}")
    
    def add_error(self, src, dst, error_msg):
        self.error_list.append((src, dst, error_msg))
        self.error_count += 1
        self.error_label.config(text=f"错误: {self.error_count}")
    
    # ------------------ 清空预览 ------------------
    def clear_preview_only(self):
        self.tree.delete(*self.tree.get_children())
        self.mapping.clear()
        self.progress['value'] = 0
        self.status_label.config(text="预览已清空")
        self.log("🧹 清空了映射预览")
    
    # ------------------ 复制功能 ------------------
    def _copy_recursive(self, src, dst):
        try:
            if os.path.isdir(src):
                if not os.path.exists(dst):
                    os.makedirs(dst, exist_ok=True)
                    self.log(f"📁 创建目录: {dst}")
                for item in os.listdir(src):
                    src_item = os.path.join(src, item)
                    dst_item = os.path.join(dst, item)
                    self._copy_recursive(src_item, dst_item)
            else:
                self._copy_file(src, dst)
        except Exception as e:
            self.add_error(src, dst, str(e))
            self.log(f"❌ 复制失败: {src} -> {dst}, 错误: {e}")
    
    def _copy_file(self, src, dst):
        try:
            dst_dir = os.path.dirname(dst)
            if dst_dir and not os.path.exists(dst_dir):
                os.makedirs(dst_dir, exist_ok=True)
            shutil.copy2(src, dst)
            self.add_success()
            self.log(f"✅ 复制文件: {src} -> {dst}")
        except Exception as e:
            self.add_error(src, dst, str(e))
            self.log(f"❌ 复制文件失败: {src} -> {dst}, 错误: {e}")
    
    # ------------------ 日志与导出 ------------------
    def log(self, msg):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{timestamp} {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        self.clear_counts()
        self.log("🧹 日志已清空，成功/错误计数重置")
    
    def export_log(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("文本文件", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log(f"💾 日志已导出至 {file_path}")
    
    def export_error_log(self):
        if not self.error_list:
            messagebox.showinfo("提示", "没有错误记录可导出。")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                 filetypes=[("文本文件", "*.txt")],
                                                 initialfile="error_log.txt")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"错误总数: {self.error_count}\n")
                f.write("=" * 50 + "\n")
                for src, dst, err in self.error_list:
                    f.write(f"源: {src}\n")
                    f.write(f"目标: {dst}\n")
                    f.write(f"错误: {err}\n")
                    f.write("-" * 30 + "\n")
            self.log(f"📋 错误列表已导出至 {file_path}")
            messagebox.showinfo("完成", f"已导出 {self.error_count} 条错误记录。")
    
    # ------------------ 其他功能方法 ------------------
    def browse_source_dir(self):
        folder = filedialog.askdirectory(title="选择源目录（将获取所有最底层子文件夹）")
        if not folder:
            return
        leaf_dirs = []
        for root, dirs, files in os.walk(folder):
            if not dirs:
                leaf_dirs.append(root)
        if not leaf_dirs:
            messagebox.showinfo("提示", "所选目录下没有找到最底层子文件夹。")
            return
        self.src_text.delete(1.0, tk.END)
        self.src_text.insert(tk.END, "\n".join(leaf_dirs))
        self.log(f"📂 已从目录 {folder} 获取到 {len(leaf_dirs)} 个最底层子文件夹")
    
    def load_src_file(self):
        file_path = filedialog.askopenfilename(title="选择源路径列表", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.src_text.delete(1.0, tk.END)
            self.src_text.insert(tk.END, content)
            self.log(f"📂 已导入源列表: {file_path}")
    
    def load_dst_file(self):
        file_path = filedialog.askopenfilename(title="选择目标路径列表", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.dst_text.delete(1.0, tk.END)
            self.dst_text.insert(tk.END, content)
            self.log(f"📂 已导入目标列表: {file_path}")
    
    def browse_root_target(self):
        folder = filedialog.askdirectory(title="选择目标根目录")
        if folder:
            self.root_target_entry.delete(0, tk.END)
            self.root_target_entry.insert(0, folder)
            self.log(f"设置目标根目录: {folder}")
    
    def generate_target_paths(self):
        mode = self.mode_var.get()
        if mode == "mapping":
            messagebox.showinfo("提示", "一对一映射模式不支持自动生成，请手动输入或导入目标路径。")
            return
        
        src_lines = self.src_text.get(1.0, tk.END).strip().splitlines()
        src_lines = [line.strip() for line in src_lines if line.strip()]
        if not src_lines:
            messagebox.showwarning("警告", "源路径列表为空！")
            return
        root_target = self.root_target_entry.get().strip()
        if not root_target:
            messagebox.showwarning("警告", "请先输入或选择目标根目录！")
            return
        
        for src in src_lines:
            if not os.path.exists(src):
                messagebox.showwarning("警告", f"源路径不存在：{src}")
                return
        
        dst_paths = []
        if mode == "root":
            prefix = self.prefix_entry.get().strip()
            if prefix:
                if not prefix.endswith(os.sep):
                    prefix += os.sep
                self.log(f"使用用户指定的剥离前缀: {prefix}")
            else:
                try:
                    prefix = os.path.commonpath(src_lines)
                except ValueError:
                    prefix = os.path.dirname(src_lines[0])
                if prefix and not prefix.endswith(os.sep):
                    prefix += os.sep
                self.log(f"自动检测的公共前缀: {prefix}")
            
            for src in src_lines:
                if not src.startswith(prefix):
                    messagebox.showerror("错误", f"源路径 \"{src}\" 不以剥离前缀 \"{prefix}\" 开头，请检查！")
                    return
                rel_path = src[len(prefix):]
                dst = os.path.join(root_target, rel_path)
                dst_paths.append(dst)
        else:  # multi
            for src in src_lines:
                base = os.path.basename(src)
                dst = os.path.join(root_target, base)
                dst_paths.append(dst)
            self.log(f"多对一模式：所有源复制到 {root_target} 下，保留各自的末级目录名")
        
        dst_paths = [p.replace('/', '\\') for p in dst_paths]
        self.dst_text.delete(1.0, tk.END)
        self.dst_text.insert(tk.END, "\n".join(dst_paths))
        self.dst_text.placeholder = ""
        self.log(f"✅ 已生成 {len(dst_paths)} 个目标路径")
        messagebox.showinfo("生成完成", f"已生成 {len(dst_paths)} 个目标路径，请预览确认。")
    
    def show_help(self):
        help_text = """📖 使用说明

1. 左侧输入源路径列表（每行一个完整路径）。
   - 可使用「浏览目录」自动获取所有最底层子文件夹。
   - 也可「导入 txt」加载列表。

2. 选择目标模式：
   • 统一目标目录：保留完整子目录层级（剥离公共父目录后拼接）
   • 一对一映射：手动输入或导入目标路径（每行一个）
   • 多对一映射：所有源复制到同一根目录，保留末级目录名（扁平化）

3. 点击「生成路径」自动填充右侧文本框（统一/多对一模式）。
   一对一模式需手动输入或导入。

4. 点击「预览映射」检查对应关系。

5. 确认后点击「开始复制」。

6. 复制过程会逐文件记录进度，成功和错误分别计数。
   可在日志区查看成功/错误数量，并导出错误列表。

⚠️ 文件夹复制若目标存在，会合并（覆盖同名文件）。"""
        messagebox.showinfo("帮助", help_text)
    
    def preview_mapping(self):
        src_lines = self.src_text.get(1.0, tk.END).strip().splitlines()
        src_lines = [line.strip() for line in src_lines if line.strip()]
        if not src_lines:
            messagebox.showwarning("警告", "源路径列表为空！")
            return
        
        mode = self.mode_var.get()
        if mode == "multi":
            dst_text_content = self.dst_text.get(1.0, tk.END).strip()
            dst_lines = [line.strip() for line in dst_text_content.splitlines() if line.strip()]
            if len(dst_lines) != len(src_lines):
                self.log("多对一模式：自动生成目标路径...")
                self.generate_target_paths()
                dst_text_content = self.dst_text.get(1.0, tk.END).strip()
                dst_lines = [line.strip() for line in dst_text_content.splitlines() if line.strip()]
        
        dst_text_content = self.dst_text.get(1.0, tk.END).strip()
        dst_lines = [line.strip() for line in dst_text_content.splitlines() if line.strip()]
        if not dst_lines:
            messagebox.showwarning("警告", "目标路径列表为空！请先生成路径或手动输入。")
            return
        
        if len(src_lines) != len(dst_lines):
            messagebox.showerror("错误", f"源数量 ({len(src_lines)}) 与目标数量 ({len(dst_lines)}) 不匹配！\n请重新生成路径。")
            return
        
        self.mapping = []
        for src, dst in zip(src_lines, dst_lines):
            if not os.path.exists(src):
                messagebox.showwarning("警告", f"源路径不存在：{src}")
                return
            self.mapping.append((src, dst))
        self.tree.delete(*self.tree.get_children())
        for src, dst in self.mapping:
            self.tree.insert("", tk.END, values=(src, dst))
        self.log(f"👁️ 预览成功，共 {len(self.mapping)} 个映射")
        self.status_label.config(text=f"已加载 {len(self.mapping)} 个映射")
    
    def start_copy(self):
        if self.is_running:
            messagebox.showinfo("提示", "复制正在进行中...")
            return
        if not self.mapping:
            messagebox.showwarning("警告", "请先「预览映射」确认列表。")
            return
        if not messagebox.askyesno("确认", f"即将复制 {len(self.mapping)} 个映射项，是否继续？"):
            return
        
        self.is_running = True
        self.clear_counts()
        self.progress['value'] = 0
        self.progress['maximum'] = len(self.mapping)
        self.status_label.config(text="复制中...")
        self.log(f"🚀 开始复制，共 {len(self.mapping)} 个映射项")
        thread = threading.Thread(target=self._copy_worker, daemon=True)
        thread.start()
    
    def _copy_worker(self):
        total = len(self.mapping)
        for idx, (src, dst) in enumerate(self.mapping, 1):
            if not self.is_running:
                break
            self.root.after(0, self._update_status, f"正在处理: {src}")
            self._copy_recursive(src, dst)
            self.root.after(0, self._update_progress, idx, f"完成: {os.path.basename(src)}")
        self.root.after(0, self._copy_finished)
    
    def _update_status(self, msg):
        self.status_label.config(text=msg)
    
    def _update_progress(self, value, status_text):
        self.progress['value'] = value
        self.status_label.config(text=f"{status_text} ({value}/{self.progress['maximum']})")
    
    def _copy_finished(self):
        self.is_running = False
        self.progress['value'] = self.progress['maximum']
        total_errors = self.error_count
        total_success = self.success_count
        if total_errors > 0:
            self.status_label.config(text=f"✅ 复制完成，成功 {total_success}，错误 {total_errors}")
            self.log(f"🎉 复制完成，成功 {total_success} 个文件，错误 {total_errors} 个。")
            messagebox.showwarning("完成", f"复制完成，成功 {total_success} 个文件，{total_errors} 个错误。\n请查看错误列表。")
        else:
            self.status_label.config(text=f"✅ 全部复制完成，成功 {total_success} 个文件")
            self.log(f"🎉 所有任务复制成功，共 {total_success} 个文件。")
            messagebox.showinfo("完成", f"批量复制成功，共 {total_success} 个文件，无错误。")

# -------------------- 启动 --------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = BatchCopyApp(root)
    root.mainloop()

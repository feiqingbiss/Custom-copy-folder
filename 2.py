import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import shutil
import os
from datetime import datetime

# -------------------- 样式 --------------------
def setup_styles():
    style = ttk.Style()
    style.theme_use('clam')
    
    # 主色
    primary = "#4A90D9"
    primary_light = "#5BA3E6"
    primary_dark = "#2E6BB0"
    bg = "#F0F6FC"
    
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, font=("Segoe UI", 9))
    style.configure("TLabelframe", background=bg, foreground="#1E293B",
                    borderwidth=1, relief="solid", bordercolor="#D1D5DB")
    style.configure("TLabelframe.Label", background=bg, foreground="#1E293B",
                    font=("Segoe UI", 10, "bold"))
    
    style.configure("TButton", background=primary, foreground="white",
                    borderwidth=0, focusthickness=0, padding=(8, 6),
                    font=("Segoe UI", 9, "bold"))
    style.map("TButton",
              background=[('active', primary_light), ('pressed', primary_dark)])
    
    style.configure("Accent.TButton", background="#10B981", foreground="white",
                    padding=(12, 8), font=("Segoe UI", 10, "bold"))
    style.map("Accent.TButton",
              background=[('active', '#34D399'), ('pressed', '#059669')])
    
    style.configure("TEntry", fieldbackground="white", borderwidth=1,
                    relief="solid", bordercolor="#D1D5DB", padding=4,
                    font=("Consolas", 9))
    style.configure("TProgressbar", background=primary, troughcolor="#E5E7EB",
                    borderwidth=0, thickness=10)
    
    style.configure("Treeview", background="white", foreground="#1E293B",
                    rowheight=30, font=("Segoe UI", 9), borderwidth=0)
    style.configure("Treeview.Heading", background="#E5E7EB", foreground="#1E293B",
                    font=("Segoe UI", 9, "bold"), borderwidth=0)
    style.map("Treeview", background=[('selected', primary)])
    
    style.configure("TRadiobutton", background=bg, foreground="#1E293B",
                    font=("Segoe UI", 9))
    
    # 添加圆角效果（通过边框模拟）
    style.configure("TButton", relief="flat", borderwidth=0)
    style.configure("TEntry", relief="solid", borderwidth=1)
    style.configure("TFrame", relief="flat")
    
    return style

# -------------------- 主应用 --------------------
class BatchCopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("批量路径复制工具 · 现代版")
        self.root.geometry("1150x850")
        self.root.minsize(1000, 700)
        self.root.configure(bg="#F0F6FC")
        
        self.style = setup_styles()
        self.mapping = []
        self.is_running = False
        
        # ---- 主容器 ----
        main = tk.Frame(root, bg="#F0F6FC")
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # ---- 标题 ----
        header = tk.Frame(main, bg="#F0F6FC")
        header.pack(fill=tk.X, pady=(0,10))
        tk.Label(header, text="📂 批量路径复制工具", font=("Segoe UI", 18, "bold"),
                 fg="#1E293B", bg="#F0F6FC").pack(side=tk.LEFT)
        tk.Label(header, text="v5.1 · 现代版", font=("Segoe UI", 11),
                 fg="#6B7280", bg="#F0F6FC").pack(side=tk.LEFT, padx=(10,0))
        
        # ---- 路径列表框（左右两列） ----
        path_frame = tk.Frame(main, bg="#F0F6FC")
        path_frame.pack(fill=tk.BOTH, expand=True, pady=(0,6))
        
        # 左列
        left_frame = tk.Frame(path_frame, bg="#F0F6FC")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,6))
        left_header = tk.Frame(left_frame, bg="#F0F6FC")
        left_header.pack(fill=tk.X, pady=(0,4))
        tk.Label(left_header, text="📁 源路径列表", font=("Segoe UI", 10, "bold"),
                 fg="#1E293B", bg="#F0F6FC").pack(side=tk.LEFT)
        ttk.Button(left_header, text="📂 浏览目录", command=self.browse_source_dir).pack(side=tk.RIGHT)
        
        left_placeholder = tk.Frame(left_frame, height=60, bg="#F0F6FC")
        left_placeholder.pack(fill=tk.X, pady=(0,4))
        left_placeholder.pack_propagate(False)
        
        self.src_text = scrolledtext.ScrolledText(left_frame, font=("Consolas", 9),
                                                  bg="white", fg="#1E293B",
                                                  relief="flat", borderwidth=1,
                                                  highlightthickness=1,
                                                  highlightcolor="#4A90D9",
                                                  highlightbackground="#D1D5DB")
        self.src_text.pack(fill=tk.BOTH, expand=True, pady=(0,4))
        
        src_btn = tk.Frame(left_frame, bg="#F0F6FC")
        src_btn.pack(fill=tk.X)
        ttk.Button(src_btn, text="📄 导入 txt", command=self.load_src_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(src_btn, text="🗑️ 清空", command=lambda: self.src_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=2)
        
        # 右列
        right_frame = tk.Frame(path_frame, bg="#F0F6FC")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6,0))
        right_header = tk.Frame(right_frame, bg="#F0F6FC")
        right_header.pack(fill=tk.X, pady=(0,4))
        tk.Label(right_header, text="🎯 目标设置", font=("Segoe UI", 10, "bold"),
                 fg="#1E293B", bg="#F0F6FC").pack(side=tk.LEFT)
        radio_frame = tk.Frame(right_header, bg="#F0F6FC")
        radio_frame.pack(side=tk.RIGHT)
        self.mode_var = tk.StringVar(value="root")
        ttk.Radiobutton(radio_frame, text="统一目标目录", variable=self.mode_var,
                        value="root", command=self.toggle_mode).pack(side=tk.LEFT, padx=(0,12))
        ttk.Radiobutton(radio_frame, text="一对一映射", variable=self.mode_var,
                        value="mapping", command=self.toggle_mode).pack(side=tk.LEFT)
        
        # 控制区固定两行
        row1 = tk.Frame(right_frame, bg="#F0F6FC")
        row1.pack(fill=tk.X, pady=(0,4))
        row1.columnconfigure(1, weight=1)
        tk.Label(row1, text="目标根目录：", font=("Segoe UI", 9),
                 bg="#F0F6FC").grid(row=0, column=0, sticky="w", padx=(0,4))
        self.root_target_entry = ttk.Entry(row1, font=("Consolas", 9))
        self.root_target_entry.grid(row=0, column=1, sticky="ew", padx=(4,4))
        ttk.Button(row1, text="浏览", command=self.browse_root_target).grid(row=0, column=2, padx=(4,0))
        
        row2 = tk.Frame(right_frame, bg="#F0F6FC")
        row2.pack(fill=tk.X, pady=(0,4))
        row2.columnconfigure(1, weight=1)
        tk.Label(row2, text="公共父目录：", font=("Segoe UI", 9),
                 bg="#F0F6FC").grid(row=0, column=0, sticky="w", padx=(0,4))
        self.prefix_entry = ttk.Entry(row2, font=("Consolas", 9))
        self.prefix_entry.grid(row=0, column=1, sticky="ew", padx=(4,4))
        ttk.Button(row2, text="生成路径", command=self.generate_target_paths).grid(row=0, column=2, padx=(4,4))
        tk.Label(row2, text="留空自动检测", font=("Segoe UI", 8),
                 fg="#6B7280", bg="#F0F6FC").grid(row=0, column=3, sticky="w", padx=(4,0))
        
        self.dst_text = scrolledtext.ScrolledText(right_frame, font=("Consolas", 9),
                                                  bg="white", fg="#1E293B",
                                                  relief="flat", borderwidth=1,
                                                  highlightthickness=1,
                                                  highlightcolor="#4A90D9",
                                                  highlightbackground="#D1D5DB")
        self.dst_text.pack(fill=tk.BOTH, expand=True, pady=(0,4))
        
        dst_btn = tk.Frame(right_frame, bg="#F0F6FC")
        dst_btn.pack(fill=tk.X)
        ttk.Button(dst_btn, text="📄 导入 txt", command=self.load_dst_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(dst_btn, text="🗑️ 清空", command=lambda: self.dst_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=2)
        
        # ---- 操作按钮与进度条 ----
        action_frame = tk.Frame(main, bg="#F0F6FC")
        action_frame.pack(fill=tk.X, pady=(4,6))
        
        btn_group = tk.Frame(action_frame, bg="#F0F6FC")
        btn_group.pack(side=tk.LEFT)
        ttk.Button(btn_group, text="👁️ 预览映射", command=self.preview_mapping).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_group, text="🚀 开始复制", command=self.start_copy, style="Accent.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_group, text="🧹 全部清空", command=self.clear_all).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_group, text="❓ 帮助", command=self.show_help).pack(side=tk.LEFT, padx=4)
        
        progress_frame = tk.Frame(action_frame, bg="#F0F6FC")
        progress_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10,0))
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_label = tk.Label(progress_frame, text="就绪", anchor="w",
                                     font=("Segoe UI", 9), bg="#F0F6FC")
        self.status_label.pack(side=tk.RIGHT, padx=(10,0))
        
        # ---- 映射预览 ----
        preview_frame = ttk.LabelFrame(main, text="📋 映射预览", padding="6")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(4,6))
        tree_container = tk.Frame(preview_frame, bg="#F0F6FC")
        tree_container.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(tree_container, columns=("src", "dst"), show="headings", height=5)
        self.tree.heading("src", text="源路径")
        self.tree.heading("dst", text="目标路径")
        self.tree.column("src", width=400)
        self.tree.column("dst", width=400)
        v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)
        
        # ---- 运行日志 ----
        log_frame = ttk.LabelFrame(main, text="📝 运行日志", padding="6")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0,0))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=4, font=("Consolas", 9),
                                                  bg="#F8FAFC", fg="#1E293B",
                                                  relief="flat", borderwidth=1,
                                                  highlightthickness=1,
                                                  highlightcolor="#4A90D9",
                                                  highlightbackground="#D1D5DB",
                                                  state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0,4))
        log_btn = tk.Frame(log_frame, bg="#F0F6FC")
        log_btn.pack(fill=tk.X)
        ttk.Button(log_btn, text="🗑️ 清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_btn, text="💾 导出日志", command=self.export_log).pack(side=tk.LEFT, padx=2)
        
        self.log("✅ 程序启动，就绪")
        self.toggle_mode()
    
    # ------------------ 功能方法 ------------------
    def log(self, msg):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{timestamp} {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def browse_source_dir(self):
        """选择目录，获取所有叶子目录（没有子目录的目录）"""
        folder = filedialog.askdirectory(title="选择源目录（将获取所有最底层子文件夹）")
        if not folder:
            return
        leaf_dirs = []
        # 递归遍历，只收集没有子目录的目录
        for root, dirs, files in os.walk(folder):
            if not dirs:  # 没有子目录，即为叶子
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
            self.dst_text.config(state='normal')
            self.dst_text.delete(1.0, tk.END)
            self.dst_text.insert(tk.END, content)
            self.dst_text.config(state='normal')
            self.log(f"📂 已导入目标列表: {file_path}")
    
    def browse_root_target(self):
        folder = filedialog.askdirectory(title="选择目标根目录")
        if folder:
            self.root_target_entry.delete(0, tk.END)
            self.root_target_entry.insert(0, folder)
            self.log(f"设置目标根目录: {folder}")
    
    def toggle_mode(self):
        if self.mode_var.get() == "root":
            self.dst_text.config(state='normal')
            self.dst_text.delete(1.0, tk.END)
            self.dst_text.config(state='normal')
            self.log("切换到「统一目标目录」模式")
        else:
            self.dst_text.config(state='normal')
            self.dst_text.delete(1.0, tk.END)
            self.dst_text.insert(tk.END, "💡 请手动输入目标路径（每行一个）")
            self.dst_text.config(state='normal')
            self.log("切换到「一对一映射」模式")
    
    def generate_target_paths(self):
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
        
        dst_paths = []
        for src in src_lines:
            rel_path = src[len(prefix):]
            dst = os.path.join(root_target, rel_path)
            dst_paths.append(dst)
        
        self.dst_text.config(state='normal')
        self.dst_text.delete(1.0, tk.END)
        self.dst_text.insert(tk.END, "\n".join(dst_paths))
        self.dst_text.config(state='normal')
        self.log(f"✅ 已生成 {len(dst_paths)} 个目标路径")
        messagebox.showinfo("生成完成", f"已生成 {len(dst_paths)} 个目标路径，请预览确认。")
    
    def clear_all(self):
        self.src_text.delete(1.0, tk.END)
        self.dst_text.config(state='normal')
        self.dst_text.delete(1.0, tk.END)
        self.dst_text.config(state='normal')
        if self.mode_var.get() == "root":
            self.root_target_entry.delete(0, tk.END)
            self.prefix_entry.delete(0, tk.END)
        self.tree.delete(*self.tree.get_children())
        self.mapping.clear()
        self.progress['value'] = 0
        self.status_label.config(text="已清空")
        self.log("🧹 已清空所有输入")
    
    def show_help(self):
        help_text = """📖 使用说明：

1. 左侧输入源路径列表（每行一个完整路径）。
   可使用「浏览目录」自动获取所有最底层子文件夹（没有子目录的目录）。
   也可「导入 txt」加载列表。

2. 选择目标模式：
   • 统一目标目录：
        - 设置「目标根目录」（存放目标文件的顶层文件夹）
        - 设置「公共父目录」（即从源路径开头剪掉的部分，留空则自动检测）
        - 点击「公共父目录」旁的「生成路径」按钮，自动填充右侧目标路径列表
   • 一对一映射：手动在右侧文本框输入目标路径（每行一个）

3. 点击「预览映射」检查对应关系。

4. 确认后点击「开始复制」。

5. 复制过程显示进度和日志。

⚠️ 文件夹复制若目标存在，会合并（覆盖同名文件）。"""
        messagebox.showinfo("帮助", help_text)
    
    def preview_mapping(self):
        src_lines = self.src_text.get(1.0, tk.END).strip().splitlines()
        src_lines = [line.strip() for line in src_lines if line.strip()]
        if not src_lines:
            messagebox.showwarning("警告", "源路径列表为空！")
            return
        dst_text_content = self.dst_text.get(1.0, tk.END).strip()
        dst_lines = [line.strip() for line in dst_text_content.splitlines() if line.strip()]
        if not dst_lines:
            messagebox.showwarning("警告", "目标路径列表为空！")
            return
        if len(src_lines) != len(dst_lines):
            messagebox.showerror("错误", f"源数量 ({len(src_lines)}) 与目标数量 ({len(dst_lines)}) 不匹配！")
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
        if not messagebox.askyesno("确认", f"即将复制 {len(self.mapping)} 个项目，是否继续？"):
            return
        self.is_running = True
        self.progress['value'] = 0
        self.progress['maximum'] = len(self.mapping)
        self.status_label.config(text="复制中...")
        self.log(f"🚀 开始复制，共 {len(self.mapping)} 项")
        thread = threading.Thread(target=self._copy_worker, daemon=True)
        thread.start()
    
    def _copy_worker(self):
        for idx, (src, dst) in enumerate(self.mapping, 1):
            if not self.is_running:
                break
            try:
                parent = os.path.dirname(dst)
                if parent and not os.path.exists(parent):
                    os.makedirs(parent, exist_ok=True)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
                self.root.after(0, self._update_progress, idx, f"完成: {os.path.basename(src)}")
            except Exception as e:
                self.root.after(0, self._show_error, f"复制失败: {src} -> {dst}\n错误: {e}")
                self.is_running = False
                return
        self.root.after(0, self._copy_finished)
    
    def _update_progress(self, value, status_text):
        self.progress['value'] = value
        self.status_label.config(text=f"{status_text} ({value}/{self.progress['maximum']})")
    
    def _show_error(self, msg):
        messagebox.showerror("错误", msg)
        self.is_running = False
        self.log(f"❌ 错误: {msg}")
        self.status_label.config(text="复制出错")
    
    def _copy_finished(self):
        self.is_running = False
        self.progress['value'] = self.progress['maximum']
        self.status_label.config(text="✅ 全部复制完成！")
        self.log("🎉 所有任务复制成功！")
        messagebox.showinfo("完成", "批量复制成功！")
    
    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def export_log(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("文本文件", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log(f"💾 日志已导出至 {file_path}")

# -------------------- 启动 --------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = BatchCopyApp(root)
    root.mainloop()

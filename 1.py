import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import shutil
import os
import time
from datetime import datetime

class BatchCopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("批量路径复制工具 v2.0")
        self.root.geometry("950x700")
        self.root.minsize(800, 600)

        # 样式
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=4, relief="flat")
        style.configure("TLabel", background="#f0f0f0")
        style.configure("TFrame", background="#f0f0f0")

        # 主容器
        main_frame = ttk.Frame(root, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title = ttk.Label(main_frame, text="批量路径复制工具 v2.0", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=4, pady=(0,10), sticky="w")

        # ==== 源路径区域 ====
        src_frame = ttk.LabelFrame(main_frame, text="源路径列表", padding="5")
        src_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(0,5))
        self.src_text = scrolledtext.ScrolledText(src_frame, height=10, width=45, font=("Consolas", 9))
        self.src_text.pack(fill=tk.BOTH, expand=True)
        src_btn_frame = ttk.Frame(src_frame)
        src_btn_frame.pack(fill=tk.X, pady=(5,0))
        ttk.Button(src_btn_frame, text="导入源列表 (txt)", command=self.load_src_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(src_btn_frame, text="清空", command=lambda: self.src_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=2)

        # ==== 目标模式选择 ====
        mode_frame = ttk.LabelFrame(main_frame, text="目标模式", padding="5")
        mode_frame.grid(row=1, column=2, columnspan=2, sticky="nsew", padx=(5,0))

        self.mode_var = tk.StringVar(value="root")  # "root" 或 "mapping"
        ttk.Radiobutton(mode_frame, text="统一目标目录 (保持子路径)", variable=self.mode_var, value="root",
                        command=self.toggle_mode).pack(anchor="w")
        ttk.Radiobutton(mode_frame, text="一对一映射 (手动对应)", variable=self.mode_var, value="mapping",
                        command=self.toggle_mode).pack(anchor="w")

        # 目标输入区（根据模式切换显示）
        self.target_frame = ttk.Frame(mode_frame)
        self.target_frame.pack(fill=tk.BOTH, expand=True, pady=(5,0))

        # --- 统一目标目录模式 ---
        self.root_target_frame = ttk.Frame(self.target_frame)
        ttk.Label(self.root_target_frame, text="目标根目录:").pack(anchor="w")
        self.root_target_entry = ttk.Entry(self.root_target_frame, width=40)
        self.root_target_entry.pack(fill=tk.X, pady=(2,2))
        btn_frame = ttk.Frame(self.root_target_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="浏览目录", command=self.browse_root_target).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="清空", command=lambda: self.root_target_entry.delete(0, tk.END)).pack(side=tk.LEFT, padx=2)
        self.root_target_frame.pack(fill=tk.X)

        # --- 一对一映射模式 ---
        self.mapping_target_frame = ttk.Frame(self.target_frame)
        ttk.Label(self.mapping_target_frame, text="目标路径列表 (每行一个):").pack(anchor="w")
        self.dst_text = scrolledtext.ScrolledText(self.mapping_target_frame, height=8, font=("Consolas", 9))
        self.dst_text.pack(fill=tk.BOTH, expand=True)
        dst_btn_frame = ttk.Frame(self.mapping_target_frame)
        dst_btn_frame.pack(fill=tk.X, pady=(5,0))
        ttk.Button(dst_btn_frame, text="导入目标列表 (txt)", command=self.load_dst_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(dst_btn_frame, text="清空", command=lambda: self.dst_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=2)

        # 默认显示统一目标模式
        self.mapping_target_frame.pack_forget()
        self.root_target_frame.pack(fill=tk.X)

        # ==== 操作按钮 ====
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=2, column=0, columnspan=4, pady=10, sticky="ew")
        ttk.Button(action_frame, text="预览映射", command=self.preview_mapping).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="开始复制", command=self.start_copy, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="清空所有", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="帮助", command=self.show_help).pack(side=tk.LEFT, padx=5)

        # ==== 映射预览表格 ====
        preview_frame = ttk.LabelFrame(main_frame, text="映射预览", padding="5")
        preview_frame.grid(row=3, column=0, columnspan=4, sticky="nsew", pady=5)
        self.tree = ttk.Treeview(preview_frame, columns=("src", "dst"), show="headings", height=6)
        self.tree.heading("src", text="源路径")
        self.tree.heading("dst", text="目标路径")
        self.tree.column("src", width=350)
        self.tree.column("dst", width=350)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ==== 进度条 & 状态 ====
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=5)
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_label = ttk.Label(progress_frame, text="就绪", anchor="w")
        self.status_label.pack(side=tk.RIGHT, padx=(10,0))

        # ==== 日志区域 ====
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="5")
        log_frame.grid(row=5, column=0, columnspan=4, sticky="nsew", pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9), state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.pack(fill=tk.X, pady=(5,0))
        ttk.Button(log_btn_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_btn_frame, text="导出日志", command=self.export_log).pack(side=tk.LEFT, padx=2)

        # 网格权重设置
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_rowconfigure(5, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(2, weight=1)
        main_frame.grid_columnconfigure(3, weight=1)

        # 内部状态
        self.mapping = []       # [(src, dst), ...]
        self.is_running = False
        self.log_counter = 0

        self.log("程序启动，欢迎使用！")

    # ---- 辅助方法 ----
    def log(self, msg):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{timestamp} {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.log_counter += 1

    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

    def export_log(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("文本文件", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log(f"日志已导出至 {file_path}")

    def toggle_mode(self):
        if self.mode_var.get() == "root":
            self.mapping_target_frame.pack_forget()
            self.root_target_frame.pack(fill=tk.X)
        else:
            self.root_target_frame.pack_forget()
            self.mapping_target_frame.pack(fill=tk.BOTH, expand=True)

    def load_src_file(self):
        file_path = filedialog.askopenfilename(title="选择源路径列表", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.src_text.delete(1.0, tk.END)
            self.src_text.insert(tk.END, content)
            self.log(f"已导入源列表: {file_path}")

    def load_dst_file(self):
        file_path = filedialog.askopenfilename(title="选择目标路径列表", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.dst_text.delete(1.0, tk.END)
            self.dst_text.insert(tk.END, content)
            self.log(f"已导入目标列表: {file_path}")

    def browse_root_target(self):
        folder = filedialog.askdirectory(title="选择目标根目录")
        if folder:
            self.root_target_entry.delete(0, tk.END)
            self.root_target_entry.insert(0, folder)

    def clear_all(self):
        self.src_text.delete(1.0, tk.END)
        if self.mode_var.get() == "mapping":
            self.dst_text.delete(1.0, tk.END)
        else:
            self.root_target_entry.delete(0, tk.END)
        self.tree.delete(*self.tree.get_children())
        self.mapping.clear()
        self.progress['value'] = 0
        self.status_label.config(text="已清空")
        self.log("已清空所有输入")

    def show_help(self):
        help_text = """使用说明：
1. 输入源路径列表（每行一个完整路径）。
2. 选择目标模式：
   - 统一目标目录：所有源复制到同一根目录下，保留子路径结构。
   - 一对一映射：源路径与目标路径逐行对应。
3. 点击「预览映射」检查对应关系。
4. 确认无误后点击「开始复制」。
5. 复制过程中可查看进度和日志。
注意：复制文件夹时，若目标已存在，会进行合并（覆盖同名文件）。
        """
        messagebox.showinfo("帮助", help_text)

    # ---- 预览映射 ----
    def preview_mapping(self):
        src_lines = self.src_text.get(1.0, tk.END).strip().splitlines()
        src_lines = [line.strip() for line in src_lines if line.strip()]
        if not src_lines:
            messagebox.showwarning("警告", "源路径列表为空！")
            return

        mode = self.mode_var.get()
        if mode == "root":
            root_target = self.root_target_entry.get().strip()
            if not root_target:
                messagebox.showwarning("警告", "请输入目标根目录！")
                return
            # 构建映射
            mapping = []
            for src in src_lines:
                if not os.path.exists(src):
                    messagebox.showwarning("警告", f"源路径不存在：{src}")
                    return
                # 计算相对路径（相对于源路径的父目录？这里保持原结构）
                # 实际上，我们希望保持从根目录开始的相对路径，但源路径可能包含多层。
                # 简单做法：直接使用源路径的完整相对路径（除去盘符）？
                # 更合理：用户期望保持源路径的子目录结构，我们取源路径的最后几个层级？
                # 但用户示例是复制到 1 文件夹下，且路径是 D:\...\alveolar\XX_Rec\...，目标根目录是 D:\...\alveolar\1，
                # 所以相对路径应该是从 alveolar 开始的。
                # 但如果源路径各不相同，我们应如何确定基准？
                # 通常，用户希望保留源路径中从某个公共父目录开始的相对结构。
                # 我们可以让用户指定一个“公共前缀”或自动检测最长的公共前缀。
                # 为了通用，我们采用：如果源路径是文件夹，则复制该文件夹下的所有内容，目标路径 = root_target + 源路径相对于根目录的路径。
                # 但是，根目录是什么？可能是某个公共父目录。
                # 简单起见，我们让用户自己决定：他们可以将源路径写成完整路径，目标根目录设置为想要存放的父目录，程序会取源路径的最后一层及其子目录。
                # 例如：源 D:\a\b\c\VOI，目标根目录 E:\backup，则目标为 E:\backup\VOI。
                # 如果源 D:\a\b\c\25_Rec\R1\VOI，目标为 E:\backup\25_Rec\R1\VOI。
                # 这样更符合直觉：保留源路径的最后一部分（文件夹名）及其下层结构。
                # 我们可以取源路径的 basename 作为第一层，但如果有多个源在同一个父目录下，可能会冲突。
                # 最好由用户指定一个公共父目录，我们计算相对路径。
                # 为了简化，我们采用：目标 = root_target + 源路径去掉盘符和根目录路径？
                # 其实，更通用的做法是：让用户选择是否“保持相对路径”，并让他们提供一个“根目录”作为参照。
                # 但为了快速实现，我们将源路径的完整绝对路径除盘符外的部分作为相对路径。
                # 即：src = D:\a\b\c，则相对路径为 a\b\c，目标为 root_target\a\b\c。
                # 这样确保所有文件都放在 root_target 下且保持完整结构。
                # 但用户可能不希望包含驱动器根目录？所以我们先取源路径的绝对路径，去掉盘符和第一个反斜杠。
                # 示例：D:\2026-...\alveolar\25_Rec\R1\VOI → 相对路径为 "2026-...\alveolar\25_Rec\R1\VOI"
                # 目标 = root_target + "\\" + 相对路径
                # 但这样会导致路径过长，用户可能只想要从某个子目录开始。
                # 鉴于用户示例中，他们的公共父目录是 "D:\2026-7-6 没有腹肌的长颈鹿 alveolar"，目标根目录是 "D:\...\alveolar\1"，他们希望将 25_Rec 等放到 1 下。
                # 所以他们的源是完整路径，目标根目录是 1，他们希望保留 25_Rec 及其子目录。
                # 所以我们可以让用户输入“公共前缀”作为去掉的部分。
                # 这里我们增加一个可选的“公共前缀”输入框，用于指定从哪个目录开始作为根。
                # 为了简化，我们就默认取源路径的最后一个文件夹名？但那样多个不同源可能丢失结构。
                # 更合理的做法：让用户手工指定“公共前缀”，比如 D:\2026-7-6 没有腹肌的长颈鹿 alveolar\，那么相对路径就是 25_Rec\R1\VOI。
                # 我们可以在界面加一个输入框，但会让界面复杂。
                # 现临时采用：源路径的 basename 作为根，但若多个源在同一个父目录下，会丢失中间层次。
                # 所以，我们采用：使用源路径相对于其所在驱动器的完整路径（去掉盘符），即 src[3:]（如果src以 D:\ 开头）。
                # 这可能会把不必要的上层目录也带进去。
                # 我决定提供一个“公共前缀”输入框，默认为空，如果用户填写，则从源路径中去掉此前缀，剩余部分作为相对路径。
                # 例如，公共前缀为 "D:\2026-7-6 没有腹肌的长颈鹿 alveolar\"，则相对路径为 "25_Rec\R1\VOI"。
                # 这样完全满足用户需求。
                # 我们在界面添加一个公共前缀输入框？可以放在目标模式区域。
                # 但为保持界面简洁，我们使用约定：如果源路径包含相同的父目录，用户可以在源列表中只写子路径，然后指定公共前缀。
                # 另一种方式：源列表写完整路径，但程序自动检测最长的公共前缀，自动去掉。
                # 我们实现自动检测公共前缀：
                # 找出所有源路径的最长公共前缀（目录级别）。
                # 例如：所有源都在 D:\...\alveolar\ 下，那么公共前缀是 D:\...\alveolar\，则相对路径为 25_Rec\... 等。
                # 这很好！
                # 我们实现这个逻辑。
            # 自动计算公共前缀
            common_prefix = os.path.commonpath(src_lines)
            # 确保 common_prefix 以路径分隔符结尾，以便去掉后得到相对路径
            if common_prefix and not common_prefix.endswith(os.sep):
                common_prefix += os.sep
            # 构建映射
            self.mapping = []
            for src in src_lines:
                rel_path = src[len(common_prefix):]  # 去掉公共前缀
                dst = os.path.join(root_target, rel_path)
                self.mapping.append((src, dst))
        else:  # mapping 模式
            dst_lines = self.dst_text.get(1.0, tk.END).strip().splitlines()
            dst_lines = [line.strip() for line in dst_lines if line.strip()]
            if len(src_lines) != len(dst_lines):
                messagebox.showerror("错误", f"源数量 ({len(src_lines)}) 与目标数量 ({len(dst_lines)}) 不匹配！")
                return
            self.mapping = []
            for src, dst in zip(src_lines, dst_lines):
                if not os.path.exists(src):
                    messagebox.showwarning("警告", f"源路径不存在：{src}")
                    return
                self.mapping.append((src, dst))

        # 显示映射表格
        self.tree.delete(*self.tree.get_children())
        for src, dst in self.mapping:
            self.tree.insert("", tk.END, values=(src, dst))

        self.log(f"预览成功，共 {len(self.mapping)} 个映射")
        self.status_label.config(text=f"已加载 {len(self.mapping)} 个映射")

    # ---- 复制启动 ----
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
        self.log(f"开始复制，共 {len(self.mapping)} 项")

        # 启动后台线程
        thread = threading.Thread(target=self._copy_worker, daemon=True)
        thread.start()

    def _copy_worker(self):
        total = len(self.mapping)
        for idx, (src, dst) in enumerate(self.mapping, 1):
            if not self.is_running:
                break
            try:
                # 确保目标父目录存在
                parent = os.path.dirname(dst)
                if parent and not os.path.exists(parent):
                    os.makedirs(parent, exist_ok=True)

                if os.path.isdir(src):
                    # 目录复制，合并模式
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
        self.log(f"错误: {msg}")
        self.status_label.config(text="复制出错")

    def _copy_finished(self):
        self.is_running = False
        self.progress['value'] = self.progress['maximum']
        self.status_label.config(text="全部复制完成！")
        self.log("所有任务复制完成！")
        messagebox.showinfo("完成", "批量复制成功！")


# ---- 启动程序 ----
if __name__ == "__main__":
    root = tk.Tk()
    # 设置主题颜色
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Accent.TButton", foreground="white", background="#4caf50")
    style.map("Accent.TButton", background=[("active", "#45a049")])
    app = BatchCopyApp(root)
    root.mainloop()

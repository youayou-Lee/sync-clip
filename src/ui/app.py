"""Enhanced Tkinter UI for clipboard sharing application with device display."""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk
import threading
import time
from datetime import datetime

from core.clipboard_manager import ClipboardManager
from interfaces import ClipboardType, DeviceInfo

class ClipboardApp:
    """Main application UI."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("剪贴板共享 - Clipboard Share")
        self.root.geometry("800x600")
        self.root.minsize(500, 400)

        # Initialize clipboard manager
        self.manager = ClipboardManager()

        # Device list storage
        self.connected_devices: list[DeviceInfo] = []

        # Setup UI
        self.setup_ui()

        # Setup device callback
        self.manager.add_device_callback(self.on_device_event)

        # Start UI update loops
        self.update_ui()
        self.update_devices()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Setup keyboard shortcuts
        self.root.bind('<Control-l>', lambda event: self.clear_history())
        self.root.bind('<Control-L>', lambda event: self.clear_history())

    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3)  # History takes more space
        main_frame.columnconfigure(1, weight=1)  # Device list takes less space
        main_frame.rowconfigure(0, weight=1)

        # Left side - Clipboard history
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.rowconfigure(1, weight=1)
        left_frame.columnconfigure(0, weight=1)

        # Title and clear button frame
        title_frame = ttk.Frame(left_frame)
        title_frame.grid(row=0, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        title_frame.columnconfigure(0, weight=1)

        # Title for history
        title_label = ttk.Label(title_frame, text="剪贴板历史", font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)

        # Clear history button
        clear_button = ttk.Button(title_frame, text="清空历史 (Ctrl+L)", command=self.clear_history)
        clear_button.grid(row=0, column=1, padx=(10, 0))

        # History frame
        self.history_frame = ttk.Frame(left_frame)
        self.history_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.history_frame.columnconfigure(0, weight=1)
        self.history_frame.rowconfigure(0, weight=1)

        # Create scrollable frame for history items
        history_canvas = tk.Canvas(self.history_frame, bg='white')
        history_scrollbar = ttk.Scrollbar(self.history_frame, orient="vertical", command=history_canvas.yview)
        self.scrollable_frame = ttk.Frame(history_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: history_canvas.configure(scrollregion=history_canvas.bbox("all"))
        )

        history_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        history_canvas.configure(yscrollcommand=history_scrollbar.set)

        history_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        history_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Right side - Connected devices
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)

        # Device list title
        device_title_frame = ttk.Frame(right_frame)
        device_title_frame.grid(row=0, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        device_title_frame.columnconfigure(1, weight=1)

        device_label = ttk.Label(device_title_frame, text="连接的设备", font=('Arial', 14, 'bold'))
        device_label.grid(row=0, column=0, sticky=tk.W)

        self.device_count_var = tk.StringVar(value="(0)")
        device_count_label = ttk.Label(device_title_frame, textvariable=self.device_count_var, foreground="gray")
        device_count_label.grid(row=0, column=1, sticky=tk.E)

        # Device list frame
        device_frame = ttk.LabelFrame(right_frame, text="在线设备", padding="5")
        device_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        device_frame.columnconfigure(0, weight=1)
        device_frame.rowconfigure(0, weight=1)

        # Device list with scrollbar
        device_canvas = tk.Canvas(device_frame, bg='white')
        device_scrollbar = ttk.Scrollbar(device_frame, orient="vertical", command=device_canvas.yview)
        self.device_frame_inner = ttk.Frame(device_canvas)

        self.device_frame_inner.bind(
            "<Configure>",
            lambda e: device_canvas.configure(scrollregion=device_canvas.bbox("all"))
        )

        device_canvas.create_window((0, 0), window=self.device_frame_inner, anchor="nw")
        device_canvas.configure(yscrollcommand=device_scrollbar.set)

        device_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        device_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Refresh devices button
        refresh_btn = ttk.Button(right_frame, text="刷新设备", command=self.refresh_devices)
        refresh_btn.grid(row=2, column=0, pady=(5, 0), sticky=(tk.W, tk.E))

        # Status bar
        self.status_var = tk.StringVar(value="运行中...")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

    def create_history_item(self, data, index):
        """Create a UI item for clipboard data."""
        frame = ttk.Frame(self.scrollable_frame, relief=tk.RIDGE, borderwidth=1)
        frame.pack(fill=tk.X, padx=5, pady=5)

        # Device and time
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

        device_label = ttk.Label(header_frame, text=f"设备: {data.device_name}",
                                 font=('Arial', 10, 'bold'))
        device_label.pack(side=tk.LEFT)

        time_label = ttk.Label(header_frame,
                               text=f"时间: {datetime.fromtimestamp(data.timestamp).strftime('%H:%M:%S')}")
        time_label.pack(side=tk.RIGHT)

        # Content type
        type_frame = ttk.Frame(frame)
        type_frame.pack(fill=tk.X, padx=5, pady=(2, 5))

        if data.type == ClipboardType.TEXT:
            type_label = ttk.Label(type_frame, text="[文本]", foreground="blue")
            type_label.pack(side=tk.LEFT)

            # Text preview (limit to 100 characters)
            preview = data.content[:100] + "..." if len(data.content) > 100 else data.content
            preview_label = ttk.Label(type_frame, text=preview, wraplength=500)
            preview_label.pack(side=tk.LEFT, padx=(10, 0))

        elif data.type == ClipboardType.IMAGE:
            type_label = ttk.Label(type_frame, text="[图片]", foreground="green")
            type_label.pack(side=tk.LEFT)

            # Small thumbnail
            try:
                if isinstance(data.content, str) and data.content.endswith('.png'):
                    # Load from file
                    image = Image.open(data.content)
                else:
                    # Load from bytes
                    from io import BytesIO
                    image = Image.open(BytesIO(data.content))

                # Create thumbnail
                image.thumbnail((100, 100), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)

                img_label = ttk.Label(type_frame, image=photo)
                img_label.pack(side=tk.LEFT, padx=(10, 0))
                img_label.image = photo  # Keep reference
            except Exception as e:
                error_label = ttk.Label(type_frame, text="[无法加载图片]", foreground="red")
                error_label.pack(side=tk.LEFT, padx=(10, 0))

        # Copy button
        copy_btn = ttk.Button(frame, text="复制到剪贴板",
                             command=lambda d=data: self.copy_to_clipboard(d))
        copy_btn.pack(side=tk.RIGHT, padx=5, pady=5)

    def create_device_item(self, device: DeviceInfo):
        """Create a UI item for a connected device."""
        frame = ttk.Frame(self.device_frame_inner, relief=tk.RIDGE, borderwidth=1)
        frame.pack(fill=tk.X, padx=2, pady=3)

        # Device name and platform
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

        # Platform icon/color based on OS
        platform_color = {
            'Windows': 'blue',
            'Linux': 'green',
            'Darwin': 'purple'  # macOS
        }.get(device.platform, 'gray')

        device_name_label = ttk.Label(header_frame, text=device.name,
                                     font=('Arial', 11, 'bold'), foreground=platform_color)
        device_name_label.pack(side=tk.LEFT)

        # Platform badge
        platform_badge = ttk.Label(header_frame, text=f"[{device.platform}]",
                                   foreground=platform_color, font=('Arial', 9))
        platform_badge.pack(side=tk.LEFT, padx=(5, 0))

        # IP address and last seen
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, padx=5, pady=(2, 5))

        ip_label = ttk.Label(info_frame, text=f"IP: {device.ip_address}",
                            font=('Arial', 9), foreground='gray')
        ip_label.pack(side=tk.LEFT)

        # Last seen time
        time_diff = time.time() - device.last_seen
        if time_diff < 60:
            last_seen_text = "刚刚"
        elif time_diff < 3600:
            last_seen_text = f"{int(time_diff/60)} 分钟前"
        else:
            last_seen_text = datetime.fromtimestamp(device.last_seen).strftime('%H:%M:%S')

        time_label = ttk.Label(info_frame, text=f"最后在线: {last_seen_text}",
                              font=('Arial', 9), foreground='gray')
        time_label.pack(side=tk.RIGHT)

        # Online indicator
        if time_diff < 30:  # Consider online if seen within last 30 seconds
            status_dot = ttk.Label(frame, text="●", foreground='green', font=('Arial', 12))
        else:
            status_dot = ttk.Label(frame, text="●", foreground='orange', font=('Arial', 12))
        status_dot.place(relx=0.95, rely=0.3, anchor='e')

    def update_devices(self):
        """Update the device list display."""
        # Clear existing device items
        for widget in self.device_frame_inner.winfo_children():
            widget.destroy()

        # Get current devices
        devices = self.manager.get_connected_devices()
        self.connected_devices = devices

        # Add device items
        for device in devices:
            self.create_device_item(device)

        # Update device count
        self.device_count_var.set(f"({len(devices)})")

        # Schedule next update
        self.root.after(2000, self.update_devices)  # Update devices every 2 seconds

    def on_device_event(self, event_type: str, device: DeviceInfo):
        """Handle device join/leave events."""
        if event_type == 'device_joined':
            self.status_var.set(f"设备 {device.name} 已加入")
        elif event_type == 'device_left':
            self.status_var.set(f"设备 {device.name} 已离开")

    def refresh_devices(self):
        """Trigger device discovery."""
        self.manager.discover_devices()
        self.status_var.set("正在搜索设备...")

    def update_ui(self):
        """Update the UI with current history."""
        # Clear existing items
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Add current history items
        history = self.manager.get_history()
        for i, data in enumerate(reversed(history)):
            self.create_history_item(data, i)

        # Update status
        self.status_var.set(f"运行中... {len(history)} 条历史记录")

        # Schedule next update
        self.root.after(1000, self.update_ui)

    def copy_to_clipboard(self, data):
        """Copy data to clipboard."""
        try:
            # For images, we need to handle differently
            if data.type == ClipboardType.IMAGE and isinstance(data.content, str):
                # Load image from file
                with open(data.content, 'rb') as f:
                    image_data = f.read()
                # Create new data with actual image bytes
                from interfaces import ClipboardData
                new_data = ClipboardData(
                    content=image_data,
                    type=data.type,
                    timestamp=data.timestamp,
                    device_name=data.device_name
                )
                self.manager.copy_to_clipboard(new_data)
            else:
                self.manager.copy_to_clipboard(data)

            self.status_var.set(f"已复制: {data.device_name} 的内容")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {str(e)}")

    def clear_history(self):
        """Clear clipboard history."""
        if messagebox.askyesno("确认清空", "确定要清空所有剪贴板历史记录吗？\n此操作不可恢复。"):
            self.manager.clear_history()
            self.update_ui()  # Refresh UI to show empty history

    def on_closing(self):
        """Handle window closing."""
        self.manager.shutdown()
        self.root.destroy()

    def run(self):
        """Run the application."""
        self.root.mainloop()

def main():
    """Main entry point."""
    app = ClipboardApp()
    app.run()

if __name__ == "__main__":
    main()
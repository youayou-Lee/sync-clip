"""Simple Tkinter UI for clipboard sharing application."""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk
import threading
import time
from datetime import datetime

from core.clipboard_manager import ClipboardManager
from interfaces import ClipboardType

class ClipboardApp:
    """Main application UI."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("剪贴板共享 - Clipboard Share")
        self.root.geometry("600x500")
        self.root.minsize(400, 300)

        # Initialize clipboard manager
        self.manager = ClipboardManager()

        # Setup UI
        self.setup_ui()

        # Start UI update loop
        self.update_ui()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="剪贴板历史", font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)

        # History frame
        self.history_frame = ttk.Frame(main_frame)
        self.history_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.history_frame.columnconfigure(0, weight=1)
        self.history_frame.rowconfigure(0, weight=1)

        # Create scrollable frame for history items
        canvas = tk.Canvas(self.history_frame, bg='white')
        scrollbar = ttk.Scrollbar(self.history_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Status bar
        self.status_var = tk.StringVar(value="运行中...")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

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
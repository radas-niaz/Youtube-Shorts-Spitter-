import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import os
import subprocess
import threading

class VideoSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Splitter")
        self.root.geometry("400x300")
        self.root.configure(bg="#f0f0f0")
        
        # Create GUI components
        self.create_widgets()

    def create_widgets(self):
        # Input file selection
        self.input_label = tk.Label(self.root, text="Select video file:", bg="#f0f0f0", font=('Arial', 12))
        self.input_label.pack(pady=10)

        self.select_button = tk.Button(self.root, text="Browse", command=self.load_video, bg="#4CAF50", fg="white", font=('Arial', 10))
        self.select_button.pack(pady=5)

        self.input_file_label = tk.Label(self.root, text="No file selected", bg="#f0f0f0", font=('Arial', 10, 'italic'))
        self.input_file_label.pack(pady=5)

        # Output resolution input
        self.resolution_button = tk.Button(self.root, text="Set Output Resolution", command=self.set_resolution, bg="#2196F3", fg="white", font=('Arial', 10))
        self.resolution_button.pack(pady=5)

        self.resolution_label = tk.Label(self.root, text="Resolution: Not set", bg="#f0f0f0", font=('Arial', 10))
        self.resolution_label.pack(pady=5)

        # Split button
        self.split_button = tk.Button(self.root, text="Split Video", command=self.start_split, bg="#FF5722", fg="white", font=('Arial', 12, 'bold'))
        self.split_button.pack(pady=20)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient='horizontal', length=300, mode='determinate')
        self.progress.pack(pady=10)

        # Status message
        self.status_message = tk.Label(self.root, text="", bg="#f0f0f0", font=('Arial', 10))
        self.status_message.pack(pady=5)

        # Initialize variables
        self.input_file = None
        self.output_resolution = None
        self.total_clips = 0

    def load_video(self):
        self.input_file = filedialog.askopenfilename(
            filetypes=[("Video Files", "*.mp4;*.avi;*.mov;*.mkv")]
        )
        if self.input_file:
            self.input_file_label.config(text=os.path.basename(self.input_file))
            self.status_message.config(text="File selected. Set the output resolution and split the video.")

    def set_resolution(self):
        # Prompt user for resolution
        resolution = simpledialog.askstring("Set Resolution", "Enter resolution (widthxheight, e.g., 1080x1920):")
        if resolution:
            try:
                width, height = map(int, resolution.split('x'))
                self.output_resolution = (width, height)
                self.resolution_label.config(text=f"Resolution: {width}x{height}")
                self.status_message.config(text="Resolution set. Ready to split the video.")
            except ValueError:
                messagebox.showerror("Error", "Invalid resolution format. Use widthxheight format.")

    def start_split(self):
        if not self.input_file:
            messagebox.showerror("Error", "No video file selected")
            return
        
        if not self.output_resolution:
            messagebox.showerror("Error", "No output resolution set")
            return

        # Check for ffmpeg and ffprobe
        if not self.check_ffmpeg():
            return

        # Reset progress bar
        self.progress['value'] = 0
        self.root.update_idletasks()

        # Start video splitting in a new thread
        threading.Thread(target=self.split_video, daemon=True).start()

    def check_ffmpeg(self):
        try:
            subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['ffprobe', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            messagebox.showerror("Error", "ffmpeg or ffprobe not found. Ensure they are installed and added to PATH.")
            return False

    def split_video(self):
        try:
            # Define paths and parameters
            video_path = self.input_file
            output_dir = 'shorts'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Use ffprobe to get video duration
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path], capture_output=True, text=True)
            video_duration = float(result.stdout.strip())

            # Calculate total clips and set progress bar maximum
            clip_duration = 15  # Duration of each clip in seconds
            self.total_clips = int(video_duration / clip_duration) + 1
            self.progress['maximum'] = self.total_clips
            
            width, height = self.output_resolution

            # Split the video into clips
            for clip_number in range(1, self.total_clips + 1):
                start_time = (clip_number - 1) * clip_duration
                end_time = min(start_time + clip_duration, video_duration)
                output_file = os.path.join(output_dir, f'short_{clip_number}.mp4')

                # Crop and scale parameters
                scale_filter = f"scale=-1:{height}, crop={width}:{height}"
                command = [
                    'ffmpeg', '-i', video_path, '-ss', str(start_time), '-to', str(end_time),
                    '-vf', scale_filter,
                    '-c:v', 'h264_nvenc', '-c:a', 'aac', '-strict', 'experimental', output_file
                ]
                subprocess.run(command, check=True)
                
                # Update progress bar
                self.update_progress_bar(clip_number)

            self.show_message("Success", "Video successfully split into 15-second clips.")
        except Exception as e:
            self.show_message("Error", f"An error occurred: {e}")

    def update_progress_bar(self, value):
        # Update progress bar value in the main thread
        self.progress['value'] = value
        self.root.update_idletasks()

    def show_message(self, title, message):
        # Show a message box in the main thread
        self.root.after(0, messagebox.showinfo, title, message)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoSplitterApp(root)
    root.mainloop()

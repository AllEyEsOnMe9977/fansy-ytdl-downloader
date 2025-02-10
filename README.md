# 🎥 YouTube Video & Audio Downloader

A **YouTube downloader** that supports downloading **single videos and entire playlists** with both **manual and automatic selection**. The script automatically chooses the **best quality combination (video + audio)** up to **1080p** and merges them using **FFmpeg** when needed.

## 🚀 Features

✔ **Download single videos or full playlists**  
✔ **Manual & Auto Selection**:  
   - **Manual Mode**: Select your desired stream manually  
   - **Auto Mode**: Automatically selects the best resolution (up to 1080p) & highest bitrate audio  
✔ **Audio-only Download**: Download the best available audio-only stream  
✔ **FFmpeg Integration**: Merges separate video & audio streams  
✔ **Organized Folder Structure** for downloaded files  
✔ **Supports Age-Restricted & OAuth-Protected Videos**  

---

## 🔧 Installation

### **1️⃣ Prerequisites**
Ensure you have Python **3.7+** installed. If not, download and install it from [python.org](https://www.python.org/downloads/).

### **2️⃣ Install Required Python Packages**
Use `pip` to install dependencies:

```bash
pip install pytubefix
```

### **3️⃣ Install FFmpeg**
FFmpeg is required for merging video and audio files. Install it via:

- **Windows**:  
  Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html), extract it, and add the `bin` directory to your system `PATH`.
  
- **Mac (Homebrew)**:  
  ```bash
  brew install ffmpeg
  ```

- **Linux (APT/YUM)**:  
  ```bash
  sudo apt install ffmpeg  # Ubuntu/Debian
  sudo yum install ffmpeg  # CentOS/RHEL
  ```

To verify installation, run:

```bash
ffmpeg -version
```

---

## 🎯 Usage

### **🔹 Run the script**
To start downloading videos:

```bash
python app.py
```

### **🔹 Choose Download Type**
Once the script starts, you will be asked to choose:

1️⃣ **Single Video**  
2️⃣ **Playlist**  

### **🔹 Single Video Download Modes**
- **Manual Mode (`m`)**: Lists all available streams and allows you to select manually.  
- **Auto Video+Audio (`va`)**: Automatically selects the best resolution (up to 1080p) and highest-bitrate audio.  
- **Auto Audio-only (`aa`)**: Downloads the highest quality audio-only stream.  

### **🔹 Playlist Download Modes**
- **Audio Mode (`a`)**: Downloads the best available audio from all videos in a playlist.  
- **Video Mode (`v`)**: Automatically selects the best video & audio combination (up to 1080p) and merges when necessary.  

---

## 📁 Folder Structure

Downloads are saved under a **structured `downloads/` directory**, which is automatically created.  
For example:

```
downloads/
├── My_Playlist/                # Playlist Folder
│   ├── audio/                  # Audio-only mode
│   │   ├── Video1_audio.mp4
│   │   ├── Video2_audio.mp4
│   │   ├── ...
│   ├── video/                  # Video+Audio mode
│       ├── Video1.mp4
│       ├── Video2.mp4
│       ├── ...
├── Single_Video_Title/         # Individual Video Folder
│   ├── Video.mp4
│   ├── Video_audio.mp4 (temporary, deleted after merging)
│   ├── Video_video.mp4 (temporary, deleted after merging)
```

---

## ❗ Troubleshooting

### **1️⃣ pytubefix errors (`KeyError`, `RegexMatchError`)**
If you encounter errors, try updating pytubefix:

```bash
pip install --upgrade pytubefix
```

### **2️⃣ FFmpeg error parsing Opus header**
You may see:

```
[opus @ ...] Error parsing Opus packet header.
```

✅ **Solution:** This is harmless if the merged video plays fine. If you notice issues, try using different audio bitrates (`-b:a 192k` instead of `128k`) in the merge function.

### **3️⃣ FFmpeg not recognized**
If `ffmpeg` is not found, ensure it's installed and in your system’s `PATH`.  

**Windows Users**: Add FFmpeg's `bin` folder to your system environment variables.

---

## 🛠 Contributing

Contributions are welcome!  
1. Fork this repository  
2. Clone the repository  
   ```bash
   git clone https://github.com/yourusername/fansy-ytdl-downloader.git
   ```
3. Create a new branch for your changes  
   ```bash
   git checkout -b feature-branch
   ```
4. Commit and push your changes  
   ```bash
   git commit -m "Add new feature"
   git push origin feature-branch
   ```
5. Submit a pull request 🚀  

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 🙌 Credits

- **[pytubefix](https://pytubefix.readthedocs.io/)** – a fork of **[pytube](https://github.com/pytube/pytube)** that includes fixes for OAuth, signature, and age-restricted videos.
- **[FFmpeg](https://ffmpeg.org/)** – used for merging video and audio streams.

Special thanks to the maintainers of these projects for making this downloader possible! 🎉

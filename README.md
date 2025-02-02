# Real Time Whisper Transcription

![Demo gif](demo.gif)

To see the GUI on linux, you will likely need to export the QPA platform. For example, when running on Wayland, please export as so:


```
export QT_QPA_PLATFORM=wayland
python qt_whisper_rt.py
```

If encountering a "Can't connect to display :0", consider running

```
xhost +
```

prior to running the application.

=====

This is a demo of real time speech to text with OpenAI's Whisper model. It works by constantly recording audio in a thread and concatenating the raw bytes over multiple recordings.

To install dependencies simply run
```
pip install -r requirements.txt
```
in an environment of your choosing.

Whisper also requires the command-line tool [`ffmpeg`](https://ffmpeg.org/) to be installed on your system, which is available from most package managers:

```
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
sudo pacman -S ffmpeg

# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg

# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
```

For more information on Whisper please see https://github.com/openai/whisper

The code in this repository is public domain.

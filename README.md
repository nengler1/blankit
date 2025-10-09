# BlankIt
BlankIt is an open-source local AI-based image redaction program. Input an image and blur the personal information and faces to your liking to make them safe online

## Dependencies
Create a new Python Virtual Environment. Make sure you are running **Python 3.12**
```bash
python3.12 -m venv venv
```

Activate your Virtual Environment
```bash
/venv/Scripts/activate
```

Install the necessary libraries using requirements.txt
```bash
pip install -r requirements.txt
```

## Important Note!
This build currently only works with Python 3.12 on Windows, as a precompiled `dlib` wheel is used instead of manually installing CMake.

If you are running any other OS or Python version, please manually install [CMake](https://cmake.org/download/) and `pip install dlib` in your virtual environment.

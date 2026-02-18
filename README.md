# BlankIt
BlankIt is an open-source local AI-based image redaction program. Input an image and blur the personal information and faces to your liking to make them safe online

# Releases
Download the v1.0.0 from Releases tab

[![tag](https://img.shields.io/github/v/tag/nengler1/blankit)](https://github.com/nengler1/blankit/releases/tag/v1.0.0)

**The project .exe is located in the exec folder in this project**

# Dependencies (if compiling project)
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

## Docker Support
You can also run BlankIt using Docker, which handles all dependencies automatically and works on any OS:

### Building the Image
```bash
docker build -t blankit:latest .
```

### Running the Container
Create an output directory and run the container:
```bash
# Create output directory (if it doesn't exist)
mkdir -p docker_output

# Run the container with mounted output volume
docker run --name blankit_run --rm -v ${PWD}/docker_output:/blankit/output blankit:latest
```

The processed images will be saved in your local `docker_output` directory.

### Debugging
If you need to debug or inspect the container:
```bash
# Run container with interactive shell
docker run --name blankit_debug -it blankit:latest /bin/bash

# View container logs
docker logs -f blankit_run

# Copy files from container
docker cp blankit_run:/blankit/output/result.jpg ./result.jpg
```

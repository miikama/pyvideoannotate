import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyviannotate",
    version="0.0.1",
    author="Example Author",
    author_email="author@example.com",
    description="A python tool for annotating images or videos.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/miikama/pyvideoannotate",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'opencv-contrib-python',
        'pillow'
    ],
    entry_points={
        'console_scripts': [
            'ann_images = pyannotate.annotate_images:main',
            'ann_video = pyannotate.annotate_video:main',
        ],
    },
    python_requires='>=3.6',        
)

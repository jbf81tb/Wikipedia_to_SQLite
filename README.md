# Wikipedia to SQLite

This repo provides a function to get the top 20 most viewed articles from Wikipedia yesterday, convert the text of those pages into Markdown, and stores the results in a SQLite database.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)

## Installation

It's ideal to work in a [virtual environment](https://docs.python.org/3/library/venv.html).
```
pip install -r requirements.txt
```

## Usage

The tool can be executed at the command line.
```
python main.py
```

It can take an argument `--verbose (-v)` in order to output the full path of the SQLite database (pages.db).

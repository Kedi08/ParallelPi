# ParallelPi

School project for parallel and distributed systems.

## Overview

`ParallelPi` is a Python program to approximate π using the Leibniz series, implemented with multiple parallel and distributed computation strategies. It includes:

* **GIL-bound threading** (mode: `--with-gil`)
* **Producer–Consumer threading** (mode: `--with-thread`)
* **Producer–Consumer multiprocessing** (mode: `--with-process`)
* **Multiprocessing pool** (mode: `--pool`)
* **Distributed computation via SSH** (mode: `--hosts`)
* **Sequential fallback** using `map`/`filter`/`reduce`
* **Timing & error reporting**

## Requirements

* Python 3.6+
* `argparse`, `threading`, `multiprocessing`, `queue`, `subprocess`, `time`, `math`, `functools`, `operator`, `os`
* SSH access and Python installed on remote hosts (for distributed mode)

## Usage

Clone the repository and run `pi.py` with the desired mode:

```bash
# Sequential computation (map/filter/reduce)
python pi.py -i 1000000

# GIL-bound threads (4 threads)
python pi.py -i 1000000 --with-gil -t 4

# Producer–Consumer threads (8 threads)
python pi.py -i 1000000 --with-thread -t 8

# Producer–Consumer processes (4 processes)
python pi.py -i 1000000 --with-process -p 4

# Multiprocessing pool (8 workers)
python pi.py -i 1000000 --pool 8

# Distributed across hosts (2 hosts, 500k terms each)
python pi.py -s 2 --seg-size 500000 --hosts host1,host2
```

## Arguments

| Flag                 | Description                                                           |
| -------------------- | --------------------------------------------------------------------- |
| `-i`, `--iterations` | Number of series terms to sum                                         |
| `-t`, `--threads`    | Number of threads (for threading modes)                               |
| `-p`, `--processes`  | Number of processes (for process modes)                               |
| `--with-gil`         | Use GIL-bound threading                                               |
| `--with-thread`      | Use producer–consumer threading                                       |
| `--with-process`     | Use producer–consumer multiprocessing                                 |
| `--pool`             | Use multiprocessing pool (specify number of workers)                  |
| `--hosts`            | Comma-separated list of remote hosts (requires `-s` and `--seg-size`) |
| `-s`, `--segments`   | Number of segments for manual or distributed mode                     |
| `--seg-size`         | Size of each segment (for manual or distributed mode)                 |

## Architecture

The project follows a modular design. Below is a simplified PlantUML diagram of the producer–consumer architecture:

[![](https://img.plantuml.biz/plantuml/svg/SoWkIImgAStDuUKg038oapCB4lDA57mJC_DGHG9BKqjJKOMSy_EAItDJYmon2_lnSe6CKT2rWsYsKaZDAmGnD8fJqtDJWIfB4ekpYpLvkU068QbDIKLHYwuAPBAL0jZQn1o5ejJYqfmIX18_eWpomssGGsfU2Z1G0000)](https://editor.plantuml.com/uml/SoWkIImgAStDuUKg038oapCB4lDA57mJC_DGHG9BKqjJKOMSy_EAItDJYmon2_lnSe6CKT2rWsYsKaZDAmGnD8fJqtDJWIfB4ekpYpLvkU068QbDIKLHYwuAPBAL0jZQn1o5ejJYqfmIX18_eWpomssGGsfU2Z1G0000)
## License

This project is licensed under the MIT License. Feel free to use and modify.

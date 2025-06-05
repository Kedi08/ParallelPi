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

```plantuml
@startuml
participant Main
participant Queue
participant Consumer1
participant ConsumerN
Main -> Queue: enqueue(segment tasks)
Consumer1 -> Queue: dequeue(segment)
Consumer1 -> Main: partial result
ConsumerN -> Queue: dequeue(segment)
ConsumerN -> Main: partial result
@enduml
```

Here are some thoughts for the calculation with multiple hosts

```plantuml
@startuml
participant Master
participant Host1
participant Host2

== Aufteilen der Arbeit ==
Master -> Master : Berechne chunk = iterations / 2
Master -> Master : host_segments = [(host1,0,chunk),(host2,chunk,iterations)]

== Aufrufen von Host1 ==
Master -> Host1 : ssh host1 "python3 pi.py --start 0 --end chunk"
activate Host1
Host1 -> Host1 : compute_segment(0, chunk) × 4
Host1 --> Master : partial1
deactivate Host1

== Aufrufen von Host2 ==
Master -> Host2 : ssh host2 "python3 pi.py --start chunk --end iterations"
activate Host2
Host2 -> Host2 : compute_segment(chunk, iterations) × 4
Host2 --> Master : partial2
deactivate Host2

== Ergebnis aggregieren ==
Master -> Master : total = partial1 + partial2
Master -> Master : error = |π – total|
Master --> Master : Ausgabe: π ≈ total, Error, Time elapsed
@enduml


```

## Evaluation-Grid
| Features                                                    | Punkte | Erfüllt | Geschätzte Punkte | Comment |
|-------------------------------------------------------------|:------:|:-------:|:-----------------:|:-------:|
| calc pi with k GIL threads                                  |  3.5   |  Ja     |  3.5              |         |
| calc pi with k parallel (non-GIL) threads                   |  0.2   |  Ja     |  0.2              |         |
| calc pi with k processes                                    |  0.2   |  Ja     |  0.2              |         |
| producer/consumer architecture                              |  0.5   |  Ja     |  0.5              |         |
| producer/consumer architecture mit map/filter/reduce        |  0.5   |  Ja     |  0.5              |         |
| using a thread pool                                         |  0.2   |  Ja     |  0.2              |         |
| timing and error data                                       |  0.2   |  Ja     |  0.2              |Wird immer ausgegeben|
| calc pi with k processes on n hosts                         |  1.0   |Teilweise|  0.2              |Konnte nicht getestet getestet werden.|
| complete set of image/sketch for architecture               |  0.2   |  Ja     |  0.2              |Plantuml in README.md|
| Documentation API                                           |  0.2   |  Ja     |  0.2              |README.md|

## License

This project is licensed under the MIT License. Feel free to use and modify.

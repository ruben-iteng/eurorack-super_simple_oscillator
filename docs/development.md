# Working with the Super Simple Oscillator source

## Prerequisites

To start working on this project you will need the following. 

### Step 1

Install the following programs:

- [Visual Code Studio](https://code.visualstudio.com/)
- [Python 3](https://www.python.org/) (add to PATH)
- [KiCad 6](https://www.kicad.org/)
- [git](https://git-scm.com/)

### Step 2

Clone this repository and install the requirements

```bash
git clone git@github.com:ruben-iteng/eurorack-super_simple_oscillator.git
```

```bash
cd eurorack-super_simple_oscillator
git submodule init
git submodule update
pip install -r requirements.txt
```

In some cases you have to run the last command in this way:

```bash
python3 -m pip install -r ./requirements.txt
```


Running samples

```bash
mkdir my_faebryk_project
cd my_faebryk_project
# download a sample from the github repo in /samples
python3 <sample_name.py> | tail -n1 > netlist.net
```

### From source

Setup

```bash
git clone git@github.com:ruben-iteng/eurorack-super_simple_oscillator.git
cd faebryk
git submodule init
git submodule update
pip install -r requirements.txt
```

Running samples

```bash
./samples/<sample_name>.py | tail -n1 > netlist.net
```
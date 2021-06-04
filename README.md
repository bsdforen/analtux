# A.N.A.L.T.U.X. IRC Bot

A.N.A.L.T.U.X. (Artificial Networked Android Limited to Troubleshooting
and Ultimate Xenocide) is a simple info bot, lurking in ##bsdforen.de on
Freenode.


## Installation on FreeBSD

Make sure that you've got a more or less up to date Python 3 and FFI version installed: 

```
pkg install python3 pure-ffi
```

Create a virtual enironment for the required Python packages:

```bash
python3 -m venv /path/to/venv
```

Install the the Package Requirements from `requirements.txt`:

```bash
LDFLAGS=/usr/local/lib/path/to/venv/bin/pip install -r requirements.txt
```

Now you ready to run the bot: 
```bash
/path/to/venv/bin/python3 analtux.py -c config.ini -l logdir/
```

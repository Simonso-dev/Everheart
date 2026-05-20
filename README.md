# Everheart
Everheart is a visualization tool focused on Holter electrocardiograms (ECG) and visualizing machine learning predicted arythmic events.

The name Everheart is a combination of Everlasting and Heart bearing a double meaning. One way to interpert the name is that Ever or Everlasting is a reference to the tools ability to visualize long-term high-resolution ECGs. The other is by having a everlasting heart indicates that the heart is healthy.

# Development and running
The current version requires to set up a development environment to run the app.

After downloading change path to the Everheart in the terminal.
```bash
change/path/to/Everheart
```

Then create a python virtual environment.
```bash
python -m venv everheart-venv
```

Then activate it depedning on your os.
On windows use.
```ps
everheart-venv\Scripts\activate
````

On linux use.
```bash
soruce everheart-venv/bin/activate
````

Then install the necesarry packages.
```bash
pip install -r requirements.txt
```

To start running Everheart.
```bash
flask run
```

To stop Everheart.
```bash
ctrl+c
```
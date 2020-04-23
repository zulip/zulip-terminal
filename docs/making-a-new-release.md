The thrilling process of making a new release has (sadly) been automated. Worry not, we still have a few things to check and a few steps to follow!
To install the required dependencies for making a release, in the venv activated zulip-terminal directory, run:
```
pip install twine wheel
```
As much as we would love to hurry and make the final release, it's always better to check if the release works as we want it to. So let's start by making a release to the [Test PyPI](https://test.pypi.org/project/zulip-term/):
```
python setup.py upload
```
Now install the zulip-term in a new terminal tab via:
```
pip install -i https://test.pypi.org/simple/ zulip-term
```
If everything looks good then you are ready to push the release to the main PyPI:
```
python setup.py upload --final-release=True
```
This will automatically set the tags to the commit and push them upstream.
Congrats! You just made a new zulip-term release. Don't forget to make a new release announcement on czo! :tada:
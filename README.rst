Wsynphot
==========

.. image:: https://dev.azure.com/starkit/wsynphot/_apis/build/status/wsynphot-CI?branchName=master
   :target: https://dev.azure.com/starkit/wsynphot/_build/latest?definitionId=1&branchName=master

Installation
-------------

.. role:: inst-beg

1. If you are already using `starkit package <https://github.com/starkit/starkit>`_, use the same conda environment of starkit. And do a simple install of wsynphot:
::

    $ source activate starkit
    $ pip install git+https://github.com/starkit/wsynphot

2. Else if you are directly using wsynphot for 1st time, then:
::

    $ curl -O https://raw.githubusercontent.com/starkit/starkit/master/starkit_env27.yml
    $ conda env create --file starkit_env27.yml -n starkit
    $ source activate starkit
    $ pip install git+https://github.com/starkit/wsynphot

~ For advanced uses, instead of ``pip installing`` package, you can clone the repository and use its ``setup.py`` file. Simply replace the ``$ pip install git+https://github.com/starkit/wsynphot`` used above, by following:
::

    $ git clone https://github.com/starkit/wsynphot.git
    $ cd wsynphot
    $ python setup.py <CMD>
    # <CMD> may be install, develop, build, etc.

.. role:: inst-end

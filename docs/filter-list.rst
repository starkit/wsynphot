List of the available filters
=============================

.. list-table:: 
   :widths: 30 40 30
   :header-rows: 1

   * - Observation Facility
     - Instruments
     - No. of Filters

   {% for obsv in obsvList %}
   {% set obsv_data=data[data['Obs. Facility']==obsv] %}
   * - :doc:`{{ obsv|string() }} <obsv-filters/{{ obsv|string() }}>`
     - {% for inst in obsv_data['Instrument'].unique().tolist() %}
       {% if inst == 'NA' %}
       \-
       {% else %}
       #. `{{ inst }} <obsv-filters/{{ obsv|string() }}.html#{{ inst }}>`__
       {% endif %}
       {% endfor %}
     - {{ obsv_data|length() }}
   {% endfor %}

.. toctree::
   :hidden:
   :glob:

   obsv-filters/*
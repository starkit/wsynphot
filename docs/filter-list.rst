List of the available filters
=============================

.. list-table:: 
   :widths: 30 40 30
   :header-rows: 1

   * - Observation Facility
     - Instruments
     - No. of Filters

   {% for facility in facility_list %}
   {% set facility_data=data[data['Obs. Facility']==facility] %}
   * - :doc:`{{ facility|string() }} <_facility_pages/{{ facility|string() }}>`
     - {% for inst in facility_data['Instrument'].unique().tolist() %}
       {% if inst == 'NA' %}
       \-
       {% else %}
       #. `{{ inst }} <_facility_pages/{{ facility|string() }}.html#{{ inst|lower()|replace('_','-') }}>`__
       {% endif %}
       {% endfor %}
     - {{ facility_data|length() }}
   {% endfor %}

.. toctree::
   :hidden:
   :glob:

   _facility_pages/*
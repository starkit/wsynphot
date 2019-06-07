Filters of Observation Facility: {{ facility }}
====================================================

{% set facility_data=data[data['Obs. Facility']==facility] %}
{% set inst_list=facility_data['Instrument'].unique().tolist() %}
{% for inst in inst_list %}

{% if inst!='NA' %}
{% if loop.first %}
Following **Instruments** are present:

{% endif %}

{{ inst }}
--------------------------

{% endif %}

{% set inst_data=facility_data[facility_data['Instrument']==inst] %}

.. list-table::
   :header-rows: 1

   * - {{ inst_data.index.name }}
{% for col_name in inst_data.columns.values %}
     - {{ col_name }}
{% endfor %}

{% for filter_info in inst_data.itertuples() %}
   * - {{ filter_info[0] }}
     - {{ filter_info[1] }}
     - {{ filter_info[2] }}
     - {{ filter_info[3] }}
     - {{ filter_info[4] }}
     - {{ filter_info[5] }}
     - {{ filter_info[6] }}
     - {{ filter_info[7] }}
     - {{ filter_info[8] }}
     - {{ filter_info[9] }}
     - {{ filter_info[10]|replace('_ ','\_ ') }}
{% endfor %}


<Plots>

{% endfor %}
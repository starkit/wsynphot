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
{% for info in filter_info %}
{% if loop.first %}
   * - {{ info }}
{% elif loop.last %}
     - {{ info|replace('_ ','\_ ') }}
{% else %}
     - {{ info }}
{% endif %}
{% endfor %}
{% endfor %}


<Plots>

{% endfor %}
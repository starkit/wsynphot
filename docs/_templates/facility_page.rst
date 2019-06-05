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
{# % for filter in inst_data % #}
No. of filters = {{ inst_data|length() }}

<Table of Filters>

<Plots>

{% endfor %}
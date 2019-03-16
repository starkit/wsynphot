Filters of Observation Facility: {{ obsv }}
====================================================

{% set obsv_data=data[data['Obs. Facility']==obsv] %}
{% set inst_list=obsv_data['Instrument'].unique().tolist() %}
{% for inst in inst_list %}

{% if inst!='NA' %}
{% if loop.first %}
Filters belong to each of the following **instruments**:

{% endif %}

{{ inst }}
--------------------------

{% endif %}

{% set inst_data=obsv_data[obsv_data['Instrument']==inst] %}
{# % for filter in inst_data % #}
No. of filters = {{ inst_data|length() }}

<Table of Filters>

<Plots>

{% endfor %}
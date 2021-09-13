% {{ title}}
% {{ author }}
% {{ date }}

## Table of Contents

### [Introduction](#Introduction)
* [Analysis Summary](#Summary)
* [Notable Changes](#Notable-Changes)

### [Aggregate Changes](#Aggregate-Changes)
### [Distributional Analysis](#Distributional-Analysis)
### [Summary of Policy Changes](#Summary-of-Policy-Changes)
### [Baseline Policy](#Policy-Baseline)
### [Assumptions](#Assumptions)
* [Behavioral Assumptions](#Behavioral-Assumptions)
* [Consumption Assumptions](#Consumption-Assumptions)
* [Growth Assumptions](#Growth-Assumptions)

### [Citations](#citations)

\vfill
![]({{ taxbrain }}){.center}

\pagebreak

## Introduction

This report summarizes the fiscal impact of {{ introduction }}. The baseline for this analysis is current law as of {{ baseline_intro }}.

## Summary

Over the budget window  ({{ start_year }} to {{ end_year }}), this policy is expected to {{ rev_direction }} aggregate tax liability by ${{ rev_change }}. Those with expanded income {{ largest_change_group}} are expected to see the largest change in tax liability. On average, this group can expect to see their tax liability {{ largest_change_str }}.

{{ ati_change_graph }}

## Notable Changes

{% for change in notable_changes %}
{{ change }}
{% endfor %}

## Aggregate Changes

**Table 1: Total Tax Liability (Billions)**

{{ agg_table }}

**Table 2: Total Tax Liability Change by Tax Type (Billions)**

{{ agg_tax_type }}

![Change in Aggregate Tax Liability]({{ agg_graph }})
\ 

## Distributional Analysis

**Table 3: Differences Table - {{ start_year }}**^[The _0-10n_ bin is comprised of tax units with negative income, the _0-10z_ bin is comprised of tax units with no income, and the _0-10p_ bin is comprised of tax units in the bottom decile with positive income.]

{{ differences_table }}

{% if stacked_table %}
**Table 4: Stacked Revenue Estimates (Billions)**

{{ stacked_table }}
{% endif %}

![Percentage Change in After Tax Income]({{ distribution_graph }})
\ 

## Summary of Policy Changes

{% for year, summary in reform_summary.items() %}
_{{ year }}_

{{ summary }}
{% endfor %}

## Policy Baseline

{{ policy_baseline }}

## Assumptions

### Behavioral Assumptions

{% for item in behavior_assumps %}
* {{item}}
{% endfor %}

### Consumption Assumptions

{% for year, summary in consump_assumps.items() %}
{{ year }}

{{ summary }}
{% endfor %}

### Growth Assumptions

{% for year, summary in growth_assumps.items() %}
{{ year }}

{{ summary }}
{% endfor %}

## Citations

This analysis was conducted using the following open source economic models:

{% for model in model_versions %}
* {{ model.name }} release {{ model.release }}
{% endfor %}

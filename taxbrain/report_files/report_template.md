~article id="cover"

# {{ title}} {: #title}

### {{ author }} {: #author}
{{ date }}
{: #date}

~/article

~article id="contents"

## Table of Contents

### [Introduction](#introduction-title)
* [Analysis Summary](#summary-title)
* [Notable Changes](#notable-title)
### [Aggregate Changes](#aggregate-title)
### [Distributional Analysis](#distributional-title)
### [Summary of Policy Changes](#policychange-title)
### [Baseline Policy](#baseline-title)
### [Assumptions](#assumptions-title)
* [Behavioral Assumptions](#behavior-title)
* [Consumption Assumptions](#consumption-title)
* [Growth Assumptions](#growth-title)
### [Citations](#citations-title)

~/article

~article id="introduction"

## Introduction

This report summarizes the fiscal impact of {{ introduction }}. The baseline for this analysis is current law as of {{ baseline_intro }}.

## Summary {: #summary}

Over the budget window  ({{ start_year }} to {{ end_year }}), this policy is expected to {{ rev_direction }} aggregate tax liability by ${{ rev_change }}. Those with expanded income {{ largest_change_group}} are expected to see the largest change in tax liability. On average, this group can expect to see their tax liability {{ largest_change_str }}.

{{ ati_change_graph }}

## Notable Changes {: #notable}

{% for change in notable_changes %}
* {{ change }}
{% endfor %}

~/article

~article id="aggregate"

## Aggregate Changes

#### Total Tax Liability Change (Billions)

{{ agg_table }}

#### Total Tax Liability Change by Tax Type (Billions)

{{ agg_tax_type }}

<img src="{{ agg_graph }}">

~/article

~article id="distributional"

## Distributional Analysis

{{ differences_table }}

<img src="{{ distribution_graph }}">

~/article

~article id="policychange"

## Summary of Policy Changes {: #policysummary}

{% for year, summary in reform_summary.items() %}
_{{ year }}_

{{ summary }}
{% endfor %}

~/article

~article id="baseline"

## Policy Baseline

{{ policy_baseline }}

~/article

~article id="assumptions"

## Assumptions

### Behavioral Assumptions {: #behavior}

{% for item in behavior_assumps %}
* {{item}}
{% endfor %}

### Consumption Assumptions {: #consumption}

{% for year, summary in consump_assumps.items() %}
{{ year }}

{{ summary }}
{% endfor %}

### Growth Assumptions {: #growth}

{% for year, summary in growth_assumps.items() %}
{{ year }}

{{ summary }}
{% endfor %}

~/article

~article id="citations"

## Citations

This analysis was conducted using the following open source economic models:

{% for model in model_versions %}
* {{ model.name }} release {{ model.release }}
{% endfor %}

~/article
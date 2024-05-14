# Distributing the Corporate Income Tax

This section of the documentation describes how Tax-Brain can be used to distribute the corporate income tax burden across individual taxpayers.

## Theoretical considerations

The while the statutory incidence of the corporate income tax is on the corporate entity, the economic incidence (as for any tax) will be born by people.  In this case, the people who may bear this incidence could be shareholders in the corporation (through changes in dividends or capital gains), its employees (through changes in wages), its consumers (though changes in prices of goods and services), or other owners of capital (through the reallocation of productive assets across the corporate and non-corporate sectors or between the United States and the rest of the world).

Economists generally believe that shareholders initially bear the full burden of the corporate income tax.  This is because $1 in corporate income tax paid means one less dollar for dividend distributions (or one less dollar held in retained earnings and thus one less dollar of capital gains) and there is not sufficient time for wages or prices to adjust or for capital to be relocated in way that shifts the burden the corporate income tax.

In addition, it's generally believed that the market for goods and services is competitive and that if corporations were to try to pass on any increase in the corporate income tax to their consumers, that those consumers could shift their consumption towards the product of non-corporate businesses.  Because of this, the consensus among economists is that consumers to not bear any part of the corporate income tax.


While users should form their own judgments about the incidence of the corporate income tax, some considerations they may bear in mind are the following:
1. What share of corporate profits represent a normal return to capital and what share represent super normal (or above market) rate of return?  Generally speaking, the incidence of the super normal return will tend to fall fully on shareholders of the firm, while the normal return will be split between workers, shareholders, and other owners of capital.
2. How mobile is productive capital or corporate income? That is, can corporations easily shift production or profits abroad -- or even to non-corporate entities.  The more mobile is capital, the smaller share of the incidence it will bear in the long run -- and the faster it will get to this long run state.
3. How rigid are wages?  If adjusting wages is very easy, then the long run incidence on workers will be achieved in fewer years.  However, do note that research suggests asymmetries in the ability of wages to adjust upward or downward.


## Mechanics in `Tax-Brain`

## Defining revenue and distribution assumptions

`Tax-Brain` follows the assumptions above and assumes that the burden of the corporate income tax will be split across shareholders, workers, and owners of other capital.  It further allows for the user to specify the long-run shares of incidence across these three groups (which must sum to one) and the time it takes to achieve the long run incidence.  `Tax-Brain` then assumes a linear transition from the initial incidence (where 100% of the burden falls on shareholders) to this long run incidence.

To distribute the corporate income tax, `Tax-Brain` users must have the following:
1. Year by year totals of the corporate income tax burden (in dollars).  This can be specied as a list, Numpy array, or dictionary with `{"year": value}` pairs.
2. A dictionary specifying the assumptions about long-run incidence.  This dictionary should be formatted as:
```python
{
 "Incidence": {
     "Labor share": value_float,
     "Shareholder share": value_float,
     "All capital share": value_float,
 },
 "Long run years": value_int
}
```

The two objects above will then be passed as arguments when instantiating an instance of the `TaxBrain` class object through its `corp_revenue` and `corp_incidence_assumptions` keyword arguments (the default is to run `Tax-Brain` without accounting for any corporate tax incidence).

After instantiating a `TaxBrain` object with these arguments, one can use the normal `TaxBrain.run()` to run `Tax-Brain` and produce the standard output.

The difference when running the model with a consideration of the corporate incidence is that before any individual income tax or payroll tax reforms are considered, the incidence of the corporate income tax is distributed across records in the individual tax file.  This will change their income (relative to the baseline before the CIT change), which will affect their tax liability.

### Distribution of the CIT across individual taxpayers

The corporate income tax is distributed across individual taxpayers in a proportional manner.  For example, assume that 50% of the corporate income tax is borne by shareholders and that corporate income taxes paid are \$50 billion.  When distributing the corporate income tax, `Tax-Brain` will change aggregate shareholder income (short-term capital gains, `p22250`, long-term capital gains, `p23250`, and dividends,`e00600`) by \$50 billion $\times$ 0.50 = \$25 billion.  To allocate this \$25 billion across individual taxpayers, we assume equal percentage changes across taxpayers.  Thus, taxpayers with more shareholder income have larger dollar value changes in their income.  The percentage shareholder income is adjusted by is determined as $ pct = \frac{\text{shareholder incidence} \times \text{CIT Revenue}}{\text{Aggregate shareholder income}}$.  So, continuing with our example, suppose aggregate shareholder income is \$500 billion, then the percentage change in shareholder income applied to each taxpayer is $\frac{0.5 * 50}{500} = \frac{25}{500} = \frac{1}{20} = 5\%$.

Analogous adjustments are made to wage income (`e00200`, `e00200p`, `e00200s`) and other capital income, which is made up of:
* Taxable interest: `e00300`
* Tax exempt interest: `e00400`
* Capital gains not on Schedule D: `e01100`
* Other gains/losses: `e01200`
* Schedule E income from rents, royalties, S corporations, and partnerships: `e02000`

## What about macroeconomic effects?

Changes in the corporate income tax rate affect the cost of capital and thus demand for investment.  Aggregate demand for investment and the stock of capital affect wages and interest rates.  These in turn affect income of individual taxpayers.

While these responses may be quantitatively important, `Tax-Brain` does not itself compute these macroeconomics effects.  However, users can incorporate them into the analysis `Tax-Brain` produces.

The first step to doing this is to use a macroeconomic model capable of simulating changes in aggregate wages, corporate profits, GDP, and interest rates for a given tax policy change.  For example, one could use the PSL-cataloged [`OG-UGA`](http://pslmodels.github.io/OG-USA/) model. Or perhaps the [FRB/US model](https://www.federalreserve.gov/econres/us-models-about.htm).

With a measure of change in these variables relative to the CBO baseline, one can update the extrapolation of the tax microdata used in `Tax-Brain` to account for the macroeconomic changes of the tax reform.  The can be passed to the `TaxBrain` class object through the `assump` keyword argument when instantiating the object.  The `assump` object will need to be a dictionary and one will pass the updated growth factors via the `{growdiff_response: value}` pair in that dictionary.
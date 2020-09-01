from typing import Union, Mapping, Any, List

import paramtools


TaxcalcReform = Union[str, Mapping[int, Any]]
ParamToolsAdjustment = Union[str, List[paramtools.ValueObject]]

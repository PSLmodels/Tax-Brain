from typing import Union, Mapping, Any, List, Tuple

import paramtools


TaxcalcReform = Union[str, Mapping[int, Any]]
ParamToolsAdjustment = Union[str, List[paramtools.ValueObject]]
PlotColors = Union[str, Tuple[float, float, float]]

/**
 * @name misc-api-calls
 * @description Find calls to various APIs from diff libraries
 * @kind problem
 */

import python
import semmle.python.ApiGraphs

from API::CallNode call, API::Node targetFunction
where
  (
    // networkx (https://networkx.github.io/documentation/stable/reference/index.html)
    targetFunction = API::moduleImport("networkx").getMember("OrderedGraph")
    or
    targetFunction = API::moduleImport("networkx").getMember("from_numpy_matrix")
    or
    targetFunction = API::moduleImport("networkx").getMember("to_numpy_matrix")
    or
    // numpy (https://numpy.org/doc/stable/reference/index.html)
    targetFunction = API::moduleImport("numpy").getMember("fastCopyAndTranspose")
    or
    targetFunction = API::moduleImport("numpy").getMember("msort")
    or
    // pandas (https://pandas.pydata.org/docs/reference/index.html)
    targetFunction =
      API::moduleImport("pandas").getMember("Categorical").getReturn().getMember("to_dense")
    or
    targetFunction =
      API::moduleImport("pandas").getMember("ExcelWriter").getReturn().getMember("save")
    or
    targetFunction =
      API::moduleImport("pandas").getMember("Index").getReturn().getMember("is_boolean")
    or
    targetFunction =
      API::moduleImport("pandas").getMember("Index").getReturn().getMember("is_mixed")
    or
    targetFunction = API::moduleImport("pandas").getMember("to_datetime") and
    exists(call.getParameter(-1, "infer_datetime_format"))
    or
    targetFunction = API::moduleImport("pandas").getMember("factorize") and
    exists(call.getParameter(-1, "na_sentinel"))
  ) and
  call = targetFunction.getACall() and
  exists(call.getLocation().getFile().getRelativePath())
select targetFunction.toString(), call.getLocation()

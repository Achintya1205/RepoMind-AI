(
  function_definition
    name: (identifier) @function.name
)

(
  class_definition
    name: (identifier) @class.name
)

(
  import_statement
) @import

(
  import_from_statement
) @import

(
  decorator
) @decorator
(
  call
    function: (identifier) @call.name
)
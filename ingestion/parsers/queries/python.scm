(
  function_definition
    name: (identifier) @function.name
) @function.definition

(
  class_definition
    name: (identifier) @class.name
) @class.definition

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
(
  call
    function: (attribute) @call.name
)
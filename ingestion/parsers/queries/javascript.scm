(
  function_declaration
    name: (identifier) @function.name
) @function.definition

(
  class_declaration
    name: (identifier) @class.name
) @class.definition

(
  import_statement
) @import

(
  export_statement
) @export

(
  call_expression
    function: (identifier) @call.name
)

(
  call_expression
    function: (member_expression) @call.name
)

(
  variable_declarator
    name: (identifier) @arrow.name
    value: (arrow_function) @arrow.definition
)

(
  jsx_element
) @jsx

(
  jsx_self_closing_element
) @jsx
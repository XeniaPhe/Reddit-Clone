from django.test import TestCase
from graphene.utils.str_converters import to_camel_case, to_snake_case

scr = to_camel_case("SCREAMING_SNAKE_CASE")
print(scr)
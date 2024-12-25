
def to_camel_case(string: str) -> str:
    camel_case = ''
    upper = False
    
    for ch in string:
        if ch == '_':
            upper = True
            continue
        
        if upper:
            ch = ch.upper()
            upper = False
        
        camel_case += ch
    
    return camel_case
        
def to_snake_case(string: str) -> str:
    snake_case = ''
    prev_lower = False
    
    for ch in string:
        is_lower = ch.islower()
        
        if prev_lower and not is_lower: #hump!
            ch = '_' + ch.lower()
        
        snake_case += ch
        prev_lower = is_lower
    
    return snake_case
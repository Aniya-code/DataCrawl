

def outer_generator():
    yield 
    print(';;;')

# 使用 outer_generator
g = outer_generator()

next(g)
print('123')
next(g, '123')
print('456')
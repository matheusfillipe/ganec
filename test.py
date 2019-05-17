a=1
b=2
a+b
print(str(a+b))

def fact(n):
    if n==1:
        return 1

    elif n<1:
        return 1
    else:
        return fact(n-1)*n

print(fact(5))

a=[1,"asd", 234, [2,3,4]]

b={1: "a", "b": 2}

a.reverse()

print(b["b"])

for i,v in enumerate(a):
    print("valor " + str(v) + "   indice"+str(i))

class rect():
    def __init__(self, a, b):
        self.a=a
        self.b=b
    
    def area(self):
        return self.a*self.b

r=rect(3,2)
print(r.area())
        
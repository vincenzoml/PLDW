#%% 

# A basic crash course of minimal python code
# Install the vscode extensions "python" and "jupyter" from microsoft
# or use google colab, or whatever you like


# First and foremost:
print("Hello, World!")

# %% A function definition
def add(a, b):
    return a + b

print(add(2, 3))

# Basic string manipulation

# %% 
a = "Hello"
b = "World"

c = "Hello" + " " + "World"
d = a + " " + b

a = a + " " + a

print(a)
print(c)
print(d)

print(f"{a+a} {b} \n OR: {c} {d}")

# Let's use python 3.10 - type system

a: int = 3
b: float = 4.5
c: str = "Hello"
d: bool = True # False

# %% Lists 

my_list = [1, 2, "ciao", 4, 5]
print(my_list)
print(my_list[0]) # first element
print(my_list[-1]) # last element
print(my_list[1:3]) # slicing

my_list.append(6)
print(my_list)

# %% Lists comprehension

my_list_2 = [1, 2, 3, 4, 5]

squared = [x**2 for x in my_list_2]
print(squared)




# %% 



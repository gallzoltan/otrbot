import subprocess

# A másik Python szkript neve
other_script = "myscript.py"

# Futtasd a másik szkriptet
subprocess.run(["python", other_script])

import subprocess

other_script = "myscript.py"

# Futtasd a másik szkriptet háttérben
process = subprocess.Popen(["python", other_script], shell=True)

# Folytasd a program futását, miközben a másik szkript is fut
# ...

# Várj a másik szkript befejeződésére, ha szükséges
process.wait()

class Calculator:
    def __init__(self, value=0):
        self.value = value

    def add(self, x):
        self.value += x
        return self

    def subtract(self, x):
        self.value -= x
        return self

    def multiply(self, x):
        self.value *= x
        return self

    def divide(self, x):
        self.value /= x
        return self

# Példa láncolási függvények használatára
result = Calculator(0).add(5).multiply(2).subtract(3).divide(2).value
print(result)  # Eredmény: 5.0

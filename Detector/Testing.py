from multiprocessing import Process, Manager


class Start:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        #child = Child(self)
        processes = []
        for i in range(10):
            p = Process(target=Child, args=(self.name, self.age))
            # Add the process to the list
            processes.append(p)
            # Start the process
            p.start()

            # Wait for all the processes to finish
        for p in processes:
            p.join()

    def test(self):

        # Call the greet method of the child
        print(f"Hello, I am {self.name} and I am {self.age} years old.")


# Define a custom class called Child that inherits from Parent
class Child:
    def __init__(self, name, age):
        # Call the parent constructor with the parent name
        self.name = name
        # Assign the age argument to the self age attribute
        self.age = age
        # Print the name and age of the child
        print(f"Hello, I am {self.name} and I am {self.age} years old.")



def none():   # Create a manager object
    manager = Manager()

    # Create a shared list of child objects
    child_list = manager.list()

    # Create an empty list of processes
    processes = []

    # Create four parent objects with different names
    parents = [Parent("Alice"), Parent("Bob"), Parent("Charlie"), Parent("David")]

    # Create four processes that run the create_child function with different arguments
    for parent, age in zip(parents, [10, 12, 11, 9]):
        # Create a process object
        p = Process(target=create_child, args=(parent, age, child_list))
        # Add the process to the list
        processes.append(p)
        # Start the process
        p.start()

    # Wait for all the processes to finish
    for p in processes:
        p.join()

    # Print the shared list of child objects
    print(child_list)

if __name__ == "__main__":
    child = Start("Ahoj", 10)
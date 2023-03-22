import cmd

class MyShell(cmd.Cmd):
    prompt = '> '
    intro = 'Welcome to the virtual shell. Type "help" to see a list of commands.'

    def do_greet(self, line):
        print('Hello,', line)

    def do_add(self, line):
        nums = line.split()
        if len(nums) != 2:
            print('Usage: add <num1> <num2>')
            return
        try:
            result = int(nums[0]) + int(nums[1])
            print(result)
        except ValueError:
            print('Invalid input')

    def do_quit(self, line):
        return True

if __name__ == '__main__':
    MyShell().cmdloop()

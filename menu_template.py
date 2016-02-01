#!/usr/bin/env python

print (30 * '-')
print ("   M A I N - M E N U")
print (30 * '-')
print ("1. Backup")
print ("2. User management")
print ("3. Reboot the server")
print (30 * '-')

is_valid=0

while not is_valid :
        try :
                choice = int ( raw_input('Enter your choice [1-3] : ') )
                is_valid = 1    # set it to 1 to validate input and to terminate the while..not loop
        except ValueError, e :
                print ("'%s' is not a valid integer." % e.args[0].split(": ")[1])

# Take action as per selected menu-option
if choice == 1:
        print ("Starting backup...")
elif choice == 2:
        print ("Starting user management...")
elif choice == 3:
        print ("Rebooting the server...")
else:
        print ("Invalid number. Try again...")


# prints out the UUID as C/C++ array as hex values

import uuid


# make a random UUID # print as C/C++ array as hex values
print('{ 0x' + ', 0x'.join([ uuid.uuid4().hex[i:i+2].upper() for i in range(0, 32, 2)  ]) + ' };')

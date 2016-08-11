This directory contains the app to test the messaging libraries that will interface between the HTLx and BOOM Box. 

The libraries were developed using Google Protocol Buffers (hence the .proto files). The compiled .proto files are contained in the "src_gen" directory.

All messages are defined in the "Boombox-HTLx_Messaging.proto" file

The PracticalSocket files are the libraries used for creating a socket to send/receive data. The code for these files can be found here: http://cs.ecs.baylor.edu/~donahoo/practical/CSockets/practical/

NOTE: I chose to use this simple socket as I did not need to test the intricacies of sending data over 10GigE. This test was designed to see that the messaging library worked, NOT the actual transfer mechanism. 

xxx.out USAGE:
xxx.out <hostIP> <portNumber>

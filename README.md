# Python-UDP-Socket
UDP based file transfer

Currently working files:
MoreExperimentalRecv.py & MoreExperimentalSending.py

All other files are old/outdated/not working, simply just there to see the progression of the work.

This is a UDP Transfer system written in Python. The protocol implements TCP acknowledgements that are sent between server and client to ensure no data is lost. Should data be lost, the necessary data will be retransmitted. The purpose of this project was to transfer several TB worth of data via 10Gb ethernet in under several hours (speed + accuracy/retention).

Features:
	
	-TCP acknowledgments
	
	-Multithreading (one for receiving socket data, one for writing data to file)
	
	-Reatransmission of dropped packets (on a per packet basis)
	

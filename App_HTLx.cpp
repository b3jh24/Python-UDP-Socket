/*//
 *   C++ sockets on Unix and Windows
 *   Copyright (C) 2002
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation; either version 2 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with this program; if not, write to the Free Software
 *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include "PracticalSocket.h"  // For Socket and SocketException
#include <iostream>           // For cerr and cout
#include <cstdlib>            // For atoi()
#include <cstring>
#include <stdlib.h>
#include <stdint.h>
#include <arpa/inet.h>
#include "src_gen/Boombox_HTLx_Messaging.pb.h"

const int RCVBUFSIZE = 4;    // Size of receive buffer (bytes = 32 bits a la uint32_t)

using namespace std;

int main(int argc, char *argv[]) {

	//GOOGLE_PROTOBUF_VERIFY_VERSION;

	if ((argc < 3) || (argc > 4)) {     // Test for correct number of arguments
		cerr << "Usage: " << argv[0]
				<< " <Server>[<Server Port>]" << endl;
		exit(1);
	}

	string servAddress = argv[1]; // First arg: server address

	//CRequestCompleted::CRequestCompleted rc(5);
	//rc::RequestCompleted req_comp;

	HTL_Messaging_schema1::SchemaAgreement schema;
	uint32_t schemaVersion = schema.schemaversion();

	//req_comp.set_transferid(55);
	//uint32_t transID = int(req_comp.transferid());
	//cout << "TransID: " << transID << endl;
	cout << "Schema Version: " << schemaVersion << endl;

	/*
	 * Get the transferID as our message,
	 * Convert it from host byte order to network byte order (to allow us to send it properly)
	 */
	//uint32_t msg = rc.getTransferID();
	//uint32_t m = htonl(transID);
	uint32_t netOrderSchemaVersion = htonl(schemaVersion);
	//cout << netOrderSchemaVersion << endl;

	unsigned short echoServPort = (argc == 3) ? atoi(argv[2]) : 7;

	cout << "Address --  " << servAddress;
	cout << "\nPort: " << echoServPort << endl;

	/*
	 * Configure Session Overview (using dummy values)
	 * In practice, these values would be set by the HTLx UI from the operator
	 */
	HTL_Messaging_schema1::SessionData sessionData;
	sessionData.set_bytesperlba(512);
	sessionData.set_firstblock(0);
	sessionData.set_maxblocksperpacket(100);
	sessionData.set_totalblocks(500);


	try {
		// Establish connection with the echo server
		TCPSocket sock(servAddress, echoServPort);

		//Send the schema version to the server
		sock.send(&netOrderSchemaVersion, sizeof(netOrderSchemaVersion));
		cout << "Sent: " << &netOrderSchemaVersion << endl;
		//Wait for confirmation (or not) of schema version
		int netOrderSchemaConfirm;
		int hostOrderSchemaConfirm;
		sock.recv(&netOrderSchemaConfirm, RCVBUFSIZE);
		hostOrderSchemaConfirm = ntohl(netOrderSchemaConfirm);
		if(hostOrderSchemaConfirm == 1){
			cout << "Same schema" << endl;
			//Now prepare Session Overview info and send it to Boombox
			uint32_t no_bytesPerLBA = htonl(sessionData.bytesperlba());
			uint32_t no_firstBlock = htonl(sessionData.firstblock());
			uint32_t no_maxBlocksPerPacket = htonl(sessionData.maxblocksperpacket());
			uint32_t no_totalBlocks = htonl(sessionData.totalblocks());

			sock.send(&no_bytesPerLBA, sizeof(no_bytesPerLBA));
			sock.send(&no_maxBlocksPerPacket, sizeof(no_maxBlocksPerPacket));
			sock.send(&no_totalBlocks, sizeof(no_totalBlocks));
			sock.send(&no_firstBlock, sizeof(no_firstBlock));


			//Now receive the transfer request from the BOOM Box
			uint32_t no_transferID;
			uint32_t no_startAddr;
			uint32_t no_blocksInTrans;
			cout << "\n\nTransfer Request..." << endl;
			sock.recv(&no_transferID, RCVBUFSIZE);
			sock.recv(&no_startAddr, RCVBUFSIZE);
			sock.recv(&no_blocksInTrans, RCVBUFSIZE);

			uint32_t ho_transferID = ntohl(no_transferID);
			uint32_t ho_startAddr = ntohl(no_startAddr);
			uint32_t ho_blocksInTrans = ntohl(no_blocksInTrans);

			//DEBUG
			cout << "\nTransferID: " << ho_transferID;
			cout << "\nStart Addr: " << ho_startAddr << endl;
			cout << "Blocks in Transfer: " << ho_blocksInTrans << endl;


			//Now we pretend to send frames to the BOOM Box...
			cout << "\nSending data..." << endl;
			cout << "Sending data..." << endl;

			//Would you look at that, we've sent all our request data, now we send a Request Completed Message
			HTL_Messaging_schema1::RequestCompleted reqCompl;

			//Get the transfer ID of the completed request (it should be the ID of the most recent request - and that was given to us)
			reqCompl.set_transferid(ho_transferID);

			//Convert ID to network byte order and send it
			uint32_t no_completedTransferID = htonl(reqCompl.transferid());
			sock.send(&no_completedTransferID, sizeof(no_completedTransferID));
		}
		else{
			cout << "Different schemas" << endl;
		}

	} catch (SocketException &e) {
		cerr << e.what() << endl;
		exit(1);
	}

	return 0;
}

'''
Created on Jun 14, 2016

Packet sniffer to gather info about UDP packets being sent and received, namely their checksums
Modification of code from: http://www.binarytides.com/python-packet-sniffer-code-linux/

@author: bhornak
'''
import socket, sys
from struct import *
 
#Convert a string of 6 characters of ethernet address into a dash separated hex string
def eth_addr (a) :
  b = "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % (ord(a[0]) , ord(a[1]) , ord(a[2]), ord(a[3]), ord(a[4]) , ord(a[5]))
  return b
 
#create a AF_PACKET type raw socket (thats basically packet level)
#define ETH_P_ALL    0x0003          /* Every packet (be careful!!!) */
try:
    s = socket.socket( socket.AF_PACKET , socket.SOCK_RAW , socket.ntohs(0x0003))
except socket.error , msg:
    print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()
 
 
def get_checksum():
    """Get the checksum of each UDP packet (and only the UDP packets)
    Used by the Server and Client (server knows checksum of packet sent)
    Client needs to see if the checksum it received matches
        
    Return:
    checksum -- a string representing the checksum of a given packet
    """
    u = iph_length + eth_length
    udp_header = packet[u:u+8]
 
    #now unpack them :)
    udph = unpack('!HHHH' , udp_header)
    checksum = udph[3]
    return str(checksum)
    
def get_source_port():
    """Get the source port of each UDP packet
    Used to filter packets, so we only look at the ones we want
        
    Return:
    source -- the number of the source port as a string
    """
    u = iph_length + eth_length
    udp_header = packet[u:u+8]
 
    #now unpack them :)
    udph = unpack('!HHHH' , udp_header)
    source = udph[0]
    return str(source)
    
def get_dest_port():
    """Get the dest port of each UDP packet
    Used to filter packets, so we only look at the ones we want
        
    Return:
    dest -- the number of the dest port as a string
    """
    u = iph_length + eth_length
    udp_header = packet[u:u+8]
 
    #now unpack them :)
    udph = unpack('!HHHH' , udp_header)
    dest = udph[1]
    return str(dest)


f = open("sp.txt","w")

# receive a packet
while True:
    packet = s.recvfrom(32000)
     
    #packet string from tuple
    packet = packet[0]
    print "stuff"
    #parse ethernet header
    eth_length = 14
     
    eth_header = packet[:eth_length]
    eth = unpack('!6s6sH' , eth_header)
    eth_protocol = socket.ntohs(eth[2])
        
    #Parse IP packets, IP Protocol number = 8
    if eth_protocol == 8 :
        #Parse IP header
        #take first 20 characters for the ip header
        ip_header = packet[eth_length:20+eth_length]
         
        #now unpack them :)
        iph = unpack('!BBHHHBBH4s4s' , ip_header)
 
        version_ihl = iph[0]
        version = version_ihl >> 4
        ihl = version_ihl & 0xF
 
        iph_length = ihl * 4
 
        ttl = iph[5]
        protocol = iph[6]
        s_addr = socket.inet_ntoa(iph[8]);
        d_addr = socket.inet_ntoa(iph[9]);
         
        #UDP packets
        if protocol == 17 :
            print "Checksum: "+ get_checksum()
            f.write( "DP: "+ get_dest_port())
            f.write("\n")
            f.write("S_IP: " + str(s_addr))
            f.write("\n")
        print
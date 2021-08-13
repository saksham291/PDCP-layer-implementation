
#   ---------------UDP STARTS----------------

import string
import random
import struct
import pprint
import time


def checksum_func(data): #Calculates the Checksum for UDP header
    checksum = 0
    data_len = len(data)
    if (data_len % 2):
        data_len += 1
        data += struct.pack('!B', 0)

    for i in range(0, data_len, 2):
        w = (data[i] << 8) + (data[i + 1])
        checksum += w

    checksum = (checksum >> 16) + (checksum & 0xFFFF)
    checksum = ~checksum & 0xFFFF
    return checksum

def verify_checksum(data, checksum): #Verifies Checksum for udp
    data_len = len(data)
    if (data_len % 2) == 1:
        data_len += 1
        data += struct.pack('!B', 0)

    for i in range(0, data_len, 2):
        w = (data[i] << 8) + (data[i + 1])
        checksum += w
        checksum = (checksum >> 16) + (checksum & 0xFFFF)

    return checksum

def udp_setup():
    print('Enter payload size:')    #For user-defined input enter any random payload size
    pack_len = input()              #Payload size in Bytes
    pckt_len=int(pack_len)
    print('Enter Packet(Bytes) per sec')
    pckt_rate=input()
    throughput=int(pckt_rate)

    ip_header  = "0x45000020"  # Version(4-IpV4), IHL(5), Type of Service(defaults-0) | Total Length(header length+data)
    ip_header += "abcd0000"  # Identification | Flags, Fragment Offset
    ip_header += "4011a6ec"  # TTL, Protocol(17-UDP) | Header Checksum
    ip_header += "7f000001"  # Source Address
    ip_header += "7f000001"  # Destination Address

    udp_header  = "1f401f40" # Source Port | Destination Port
    udp_header += "ffff0000" # length | check_sum


    N=pckt_len
    time_exe=throughput//pckt_len
    # packet_header= ip_header+udp_header

    while 1:
        #For random string generation uncomment the following two lines
        #res = ''.join(random.choices(string.ascii_uppercase + string.digits, k = N))   #Random string generation
        #data=str(res)

        #For a user defined string uncomment the following line
        data="Siddharth"

        data_str=data.encode() #Encoding data to Byte format
        data_hex=data_str.hex() #Generating Hexadecimal
        packet=ip_header+udp_header+data_hex #Complete Packet
        # test=packet.decode()
        print("UDP Packet: "+packet)
        receive_PDCP_PDU(packet)  #Transmitting to PDCP
        # udp_downlink(packet)
        time.sleep(time_exe)
def udp_downlink(data_str):
        payload=data_str[58:]
        print("Payload: ")
        print(''.join([chr(int(''.join(c), 16)) for c in zip(payload[0::2],payload[1::2])])) #Prints out the actual payload

#   ---------------UDP ENDS----------------




#   ---------------PDCP STARTS----------------

#Variable initialization
Num_SN_Bits = 0
SN_Bits = 0
Next_PDCP_TX_SN = 0
headerCompOn = 0

def PDCP_setup():                   #Configuring PDCP
  global headerCompOn
  global SN_Bits
  global Next_PDCP_TX_SN
  global Num_SN_Bits
  Num_SN_Bits = [5, 7, 12, 15, 18]
  SN_Bits = Num_SN_Bits[2]                  #Number of Sequence number bits can be changed here
  Next_PDCP_TX_SN = 0                       #starts from SN = 0
  headerCompOn = 1                          # 1 - Header Compression On | 0 - Header Compression Off
  file = open("header.txt","w")
  file.write('')
  file.close()
  print('PDCP Initiated!')


def receive_PDCP_PDU(dataStream):        #Receive PDCP_PDU, TO BE CALLED BY UDP ON SENDING SIDE
  global Next_PDCP_TX_SN
  global SN_Bits
  Max_PDCP_SN = 2**(SN_Bits)-1
  Next_PDCP_TX_SN += 1                  #increment SN
  if Next_PDCP_TX_SN > Max_PDCP_SN:
    Next_PDCP_TX_SN = 1
  to_RLC = setHeader(dataStream, Next_PDCP_TX_SN, SN_Bits)      #set header
  print('PDCP SDU: '+ to_RLC)         #this string will be sent to RLC
  send_PDCP_PDU(to_RLC)               #for now it is being directly sent to PDCP on the receiver side

def headerCompression(dataStream, Next_PDCP_TX_SN):
  if Next_PDCP_TX_SN == 1:            # For first time transmission
    print('First Packet. Hence header not compressed!')
    return dataStream
  else:                                 #Compress header 2nd packet onwards
    dataStream = dataStream[2:]
    out = '0xff' + dataStream[4:8] + dataStream[20:28] + dataStream[48:]
    print('Header Compressed Data: '+ out)
    return out


def setHeader(dataStream, Next_PDCP_TX_SN, SN_Bits):        #Set header function
  if dataStream[:2]!='0x':
    dataStream = '0x'+ dataStream          #if '0x' not present in input

  if headerCompOn == 1:
    dataStream = headerCompression(dataStream, Next_PDCP_TX_SN)

  if SN_Bits == 5:              #FOR THE CASE OF SRB
    outputStream = hex(Next_PDCP_TX_SN)[2:].zfill(2) + str(dataStream[2:]) + '0CF36E17'
    return outputStream

  elif SN_Bits == 7:              #FOR THE CASE OF DRB-7
    outputStream = hex(0b10000000 | Next_PDCP_TX_SN) + str(dataStream[2:])
    return outputStream[2:]

  elif SN_Bits == 12:              #FOR THE CASE OF DRB-12
    outputStream = hex(0b1000000000000000 | Next_PDCP_TX_SN) + str(dataStream[2:])
    return outputStream[2:]

  elif SN_Bits == 15:              #FOR THE CASE OF DRB-15
    outputStream = hex(0b1000000000000000 | Next_PDCP_TX_SN) + str(dataStream[2:])
    return outputStream[2:]

  elif SN_Bits == 18:              #FOR THE CASE OF DRB-18
    outputStream = hex(0b100000000000000000000000 | Next_PDCP_TX_SN) + str(dataStream[2:])
    return outputStream[2:]

  if SN_Bits != 5 or SN_Bits != 7 or SN_Bits != 12 or SN_Bits != 15 or SN_Bits != 18:
    raise Exception("Supported SN Bits is limited to 5, 7, 12, 15 and 18!")


def send_PDCP_PDU(dataStream):           #send PDCP_PDU, TO BE CALLED BY RLC ON RECEIVING SIDE
  dataStream,SN = removeHeader(dataStream)
  print('PDCP SDU (Receiver): ' + dataStream)
  udp_downlink(dataStream)                            #Calling a function given by UDP team here for receiving side


def removeHeader(PDCP_PDU):             #Removing header on the receiving side
  global SN_Bits
  if PDCP_PDU[:2]=='0x':
    PDCP_PDU = PDCP_PDU[2:]          #if '0x' present in input
  if SN_Bits == 5:              #FOR THE CASE OF SRB
    out1 = PDCP_PDU[2:]
    out = out1[:-8]
    hexSN = PDCP_PDU[:2]
    intSN = int(hexSN, 16)

  elif SN_Bits == 7:              #FOR THE CASE OF DRB-7
    out = PDCP_PDU[2:]
    hexSN = PDCP_PDU[:2]
    intSN = int(hexSN, 16) - 128

  elif SN_Bits == 12:              #FOR THE CASE OF DRB-12
    out = PDCP_PDU[4:]
    hexSN = PDCP_PDU[:4]
    intSN = int(hexSN, 16) - 32768

  elif SN_Bits == 15:              #FOR THE CASE OF DRB-15
    out = PDCP_PDU[4:]
    hexSN = PDCP_PDU[:4]
    intSN = int(hexSN, 16) - 32768

  elif SN_Bits == 18:              #FOR THE CASE OF DRB-18
    out = PDCP_PDU[6:]
    hexSN = PDCP_PDU[:6]
    intSN = int(hexSN, 16) - 8388608

  # elif DataChannel == 0:
  #   raise Exception("Control Channel not supported!")
  # if SN_Bits != 5 or SN_Bits != 7 or SN_Bits != 12 or SN_Bits != 15 or SN_Bits != 18:
  #   raise Exception("Supported SN Bits is limited to 5, 7, 12, 15 and 18!")

  if headerCompOn == 1:
    out = headerDecompression(out, intSN)           #Decompressing the header
  out = '0x' + out
  return (out, intSN)

def headerDecompression(dataStream, Next_PDCP_TX_SN):       #Header Decompression function
  if Next_PDCP_TX_SN == 1:            # For first time transmission
    header = dataStream[:56]
    file = open("header.txt","w")
    file.write(header)
    file.close()
    return dataStream
  elif dataStream[:2] == 'ff':
    dataStream = dataStream[2:]
    file = open("header.txt","r+")
    header = file.read()
    file.close()
    out = header[:4] + dataStream[:4] + header[8:20] + dataStream[4:12] + header[28:48] + dataStream[12:]
    return out

PDCP_setup()

#   ---------------PDCP ENDS----------------


#   ---------------RLC HERE----------------


#   ---------------EXECUTION STARTS----------------
udp_setup()
